import os
import time
import logging
from typing import Optional, Dict
from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException, Depends, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from src.models.chat_models import (
    ChatRequest, ChatResponse, HealthResponse, 
    ForecastRequest, ForecastResponse
)
from src.services.openai_service import openai_service, AIServiceError
from src.services.forecasting_service import forecasting_service

# Configure logging
logger = logging.getLogger(__name__)

# Simple rate limiting storage
rate_limit_store: Dict[str, list] = {}

def check_rate_limit(request: Request, max_requests: int = 10, window_minutes: int = 1):
    """Simple rate limiting based on IP address"""
    client_ip = request.client.host
    current_time = datetime.now()
    
    if client_ip not in rate_limit_store:
        rate_limit_store[client_ip] = []
    
    # Remove old requests outside the time window
    cutoff_time = current_time - timedelta(minutes=window_minutes)
    rate_limit_store[client_ip] = [
        req_time for req_time in rate_limit_store[client_ip] 
        if req_time > cutoff_time
    ]
    
    # Check if rate limit exceeded
    if len(rate_limit_store[client_ip]) >= max_requests:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Rate limit exceeded: {max_requests} requests per {window_minutes} minute(s)"
        )
    
    # Add current request
    rate_limit_store[client_ip].append(current_time)

router = APIRouter()

# Security
security = HTTPBearer(auto_error=False)

def verify_bearer_token(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)):
    """Verify Bearer token if authentication is enabled"""
    bearer_token = os.getenv('BEARER_TOKEN')
    if not bearer_token:
        return True  # No authentication required
    
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Bearer token required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if credentials.credentials != bearer_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid bearer token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return True

@router.post("/api/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    http_request: Request,
    authenticated: bool = Depends(verify_bearer_token)
):
    """
    Send a message to the AI model and receive a response.
    
    - **session_id**: Unique identifier for the chat session
    - **message**: User message to send to the AI
    - **context**: Optional context object for additional information
    """
    try:
        # Apply rate limiting
        check_rate_limit(http_request)
        
        if not request.message.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Message cannot be empty"
            )
        
        if len(request.message) > 2000:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Message too long (max 2000 characters)"
            )
        
        response = await openai_service.send_message(request)
        return response
        
    except HTTPException:
        raise
    except AIServiceError as e:
        logger.error(f"AI service error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected error in chat endpoint: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.get("/api/health", response_model=HealthResponse)
async def health_check():
    """
    Check the health status of the service.
    
    Returns system status, provider information, model details, and uptime.
    """
    try:
        return openai_service.get_health_status()
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service unhealthy"
        )

@router.delete("/api/chat/{session_id}")
async def clear_session(
    session_id: str,
    authenticated: bool = Depends(verify_bearer_token)
):
    """
    Clear a specific chat session and its history.
    
    - **session_id**: The session ID to clear
    """
    try:
        success = openai_service.clear_session(session_id)
        if success:
            return {"message": f"Session {session_id} cleared successfully"}
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found"
            )
    except Exception as e:
        logger.error(f"Error clearing session {session_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error clearing session"
        )

@router.get("/api/sessions")
async def list_sessions(authenticated: bool = Depends(verify_bearer_token)):
    """
    List all active chat sessions.
    """
    try:
        sessions = list(openai_service.sessions.keys())
        return {
            "active_sessions": sessions,
            "total_count": len(sessions)
        }
    except Exception as e:
        logger.error(f"Error listing sessions: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving sessions"
        )

@router.post("/api/forecast", response_model=ForecastResponse)
async def forecast(
    request: ForecastRequest,
    authenticated: bool = Depends(verify_bearer_token)
):
    """
    Generate time series forecasts using ARIMA model.
    
    - **data**: List of numerical values for time series
    - **dates**: Optional list of date strings
    - **steps**: Number of forecast steps (default: 5)
    - **confidence_level**: Confidence level for prediction intervals (default: 0.95)
    """
    try:
        if len(request.data) < 10:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Need at least 10 data points for reliable forecasting"
            )
        
        if request.steps < 1 or request.steps > 30:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Forecast steps must be between 1 and 30"
            )
        
        if not 0.8 <= request.confidence_level <= 0.99:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Confidence level must be between 0.8 and 0.99"
            )
        
        # Generate forecast
        result = forecasting_service.forecast(
            data=request.data,
            dates=request.dates,
            steps=request.steps,
            confidence_level=request.confidence_level
        )
        
        # Log successful forecast
        logger.info(f"Forecast generated - Data points: {len(request.data)}, Steps: {request.steps}")
        
        return ForecastResponse(**result)
        
    except ValueError as e:
        logger.error(f"Forecasting validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Forecasting error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Forecasting service error"
        )

@router.post("/api/forecast/validate")
async def validate_time_series(
    request: dict,
    authenticated: bool = Depends(verify_bearer_token)
):
    """
    Validate time series data and get recommendations.
    
    - **data**: List of numerical values to validate
    """
    try:
        data = request.get("data", [])
        if not data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Data array is required"
            )
        
        validation_result = forecasting_service.validate_time_series(data)
        return validation_result
        
    except Exception as e:
        logger.error(f"Time series validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Validation service error"
        )