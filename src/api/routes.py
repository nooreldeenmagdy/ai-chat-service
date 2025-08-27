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

@router.post("/api/chat", response_model=ChatResponse, tags=["Chat"])
async def chat(
    request: ChatRequest,
    http_request: Request,
    authenticated: bool = Depends(verify_bearer_token)
):
    """
    🤖 Send a message to the AI model and receive a response
    
    This endpoint processes user messages through an AI model (OpenAI/Azure OpenAI) 
    and returns intelligent responses with conversation context maintained per session.
    
    **Features:**
    - Conversation history maintained per session
    - FAQ knowledge base integration (RAG)
    - Token usage tracking
    - Response latency monitoring
    - Rate limiting (10 requests/minute per IP)
    
    **Example Usage:**
    ```json
    {
        "session_id": "user-123-chat",
        "message": "Explain quantum computing in simple terms",
        "context": {"user_level": "beginner", "topic_preference": "technology"}
    }
    ```
    
    **Parameters:**
    - **session_id**: Unique identifier for maintaining conversation context
    - **message**: Your question or message to the AI (max 2000 characters)
    - **context**: Optional metadata to enhance AI responses
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

@router.get("/api/health", response_model=HealthResponse, tags=["System"])
async def health_check():
    """
    ⚡ Check the health status of the AI Chat Service
    
    This endpoint provides comprehensive health information including:
    - Service status and uptime
    - AI provider and model information
    - System performance metrics
    - Configuration validation
    
    **Returns:**
    - Service health status (healthy/unhealthy)
    - Current AI provider (openai/azure)
    - Active model name
    - Service uptime in seconds
    - Timestamp of health check
    
    **Use Cases:**
    - Monitoring and alerting systems
    - Load balancer health checks
    - Service discovery and readiness probes
    - Debugging connection issues
    """
    try:
        return openai_service.get_health_status()
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service unhealthy"
        )

@router.delete("/api/chat/{session_id}", tags=["Sessions"])
async def clear_session(
    session_id: str,
    authenticated: bool = Depends(verify_bearer_token)
):
    """
    🗑️ Clear a specific chat session and its conversation history
    
    This endpoint removes all conversation history for a specific session ID,
    effectively resetting the conversation context for that session.
    
    **Example Usage:**
    ```
    DELETE /api/chat/user-123-chat
    ```
    
    **Parameters:**
    - **session_id**: The unique session identifier to clear (e.g., "user-123-chat")
    
    **Response:**
    - Success: `{"message": "Session {session_id} cleared successfully"}`
    - Not Found: `404` if session doesn't exist
    
    **Use Cases:**
    - Reset conversation context
    - Privacy compliance (data deletion)
    - Start fresh conversation
    - Memory management for long-running sessions
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
    except HTTPException:
        # Re-raise HTTP exceptions (like 404)
        raise
    except Exception as e:
        logger.error(f"Error clearing session {session_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error clearing session"
        )

@router.get("/api/sessions", tags=["Sessions"])
async def list_sessions(authenticated: bool = Depends(verify_bearer_token)):
    """
    📋 List all active chat sessions
    
    This endpoint returns information about all currently active chat sessions
    in the system, useful for monitoring and management purposes.
    
    **Returns:**
    ```json
    {
        "active_sessions": ["user-123-chat", "guest-456-session", "admin-789"],
        "total_count": 3
    }
    ```
    
    **Use Cases:**
    - Monitor active users
    - System administration
    - Session management
    - Analytics and reporting
    - Resource usage tracking
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

@router.post("/api/forecast", response_model=ForecastResponse, tags=["Forecasting"])
async def forecast(
    request: ForecastRequest,
    authenticated: bool = Depends(verify_bearer_token)
):
    """
    📈 Generate time series forecasts using advanced ARIMA modeling
    
    This endpoint provides sophisticated time series forecasting capabilities using
    ARIMA (AutoRegressive Integrated Moving Average) models with automatic parameter
    selection and comprehensive performance metrics.
    
    **Features:**
    - Automatic ARIMA model selection (optimal p,d,q parameters)
    - Confidence intervals for predictions
    - Performance metrics (MAE, RMSE, etc.)
    - Support for date-indexed time series
    - Model quality assessment (AIC scores)
    
    **Example Request:**
    ```json
    {
        "data": [10.5, 12.3, 13.8, 15.2, 14.9, 16.1, 18.4, 20.2, 19.8, 21.5, 23.1, 24.7, 22.9, 25.3, 27.2],
        "dates": ["2024-01-01", "2024-01-02", "2024-01-03", "2024-01-04", "2024-01-05"],
        "steps": 5,
        "confidence_level": 0.95
    }
    ```
    
    **Parameters:**
    - **data**: Historical time series values (minimum 10 points required)
    - **dates**: Optional date strings corresponding to data points
    - **steps**: Number of future periods to forecast (1-30)
    - **confidence_level**: Statistical confidence level (0.8-0.99)
    
    **Use Cases:**
    - Sales forecasting
    - Demand planning
    - Financial projections
    - Resource capacity planning
    - Trend analysis
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

@router.post("/api/forecast/validate", tags=["Forecasting"])
async def validate_time_series(
    request: dict,
    authenticated: bool = Depends(verify_bearer_token)
):
    """
    ✅ Validate time series data and get expert recommendations
    
    This endpoint analyzes your time series data and provides detailed validation
    results with actionable recommendations for improving forecast quality.
    
    **Analysis Includes:**
    - Data quality assessment
    - Trend and seasonality detection
    - Outlier identification
    - Stationarity testing
    - Recommended preprocessing steps
    - Forecast readiness score
    
    **Example Request:**
    ```json
    {
        "data": [10.5, 12.3, 13.8, 15.2, 14.9, 16.1, 18.4, 20.2, 19.8, 21.5]
    }
    ```
    
    **Example Response:**
    ```json
    {
        "is_valid": true,
        "data_quality_score": 0.85,
        "recommendations": [
            "Data looks suitable for forecasting",
            "Consider adding more historical data for better accuracy"
        ],
        "issues": [],
        "statistics": {
            "mean": 16.38,
            "std": 4.12,
            "trend": "increasing",
            "seasonality": "none_detected"
        }
    }
    ```
    
    **Parameters:**
    - **data**: Array of numerical values to validate and analyze
    
    **Use Cases:**
    - Pre-forecast data validation
    - Data quality assessment
    - Identify data preprocessing needs
    - Forecast feasibility analysis
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