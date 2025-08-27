from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime

class ChatRequest(BaseModel):
    session_id: str
    message: str
    context: Optional[Dict[str, Any]] = None

class ChatMessage(BaseModel):
    role: str  # "user" or "assistant"
    content: str
    timestamp: datetime = datetime.now()

class ChatSession(BaseModel):
    session_id: str
    messages: List[ChatMessage] = []
    created_at: datetime = datetime.now()
    updated_at: datetime = datetime.now()

class ChatResponse(BaseModel):
    response: str
    session_id: str
    latency_ms: float
    token_usage: Dict[str, int]
    relevant_faqs: Optional[List[str]] = None
    timestamp: datetime = datetime.now()

class HealthResponse(BaseModel):
    status: str
    timestamp: datetime = datetime.now()
    provider: str
    model: str
    uptime_seconds: float

class TokenUsage(BaseModel):
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int

class FAQ(BaseModel):
    id: int
    question: str
    answer: str
    embedding: Optional[List[float]] = None

class ForecastRequest(BaseModel):
    data: List[float]
    dates: Optional[List[str]] = None
    steps: int = 5
    confidence_level: float = 0.95

class ForecastPoint(BaseModel):
    date: str
    value: float
    index: int

class ModelInfo(BaseModel):
    model_type: str
    order: List[int]
    aic: float
    data_points_used: int

class PerformanceMetrics(BaseModel):
    mae: float
    rmse: float
    mean_residual: float
    residual_std: float

class ForecastMetadata(BaseModel):
    processing_time_ms: float
    confidence_level: float
    forecast_horizon: int
    timestamp: str

class ForecastResponse(BaseModel):
    forecasts: List[ForecastPoint]
    model_info: ModelInfo
    performance_metrics: PerformanceMetrics
    metadata: ForecastMetadata