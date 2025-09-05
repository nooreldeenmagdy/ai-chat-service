from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Union, Literal
from datetime import datetime

class ChatRequest(BaseModel):
    session_id: str = Field(
        ...,
        example="test-session-123",
        description="Unique identifier for the chat session"
    )
    message: str = Field(
        ...,
        example="What is artificial intelligence and how does it work?",
        description="User message to send to the AI assistant"
    )
    context: Optional[Dict[str, Any]] = Field(
        None,
        example={"user_preference": "technical", "language": "en"},
        description="Optional context object for additional information"
    )

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
    response: str = Field(
        ...,
        example="Artificial Intelligence (AI) refers to computer systems that can perform tasks typically requiring human intelligence, such as learning, reasoning, and problem-solving...",
        description="AI-generated response to the user's message"
    )
    session_id: str = Field(
        ...,
        example="test-session-123",
        description="The session ID for this conversation"
    )
    latency_ms: float = Field(
        ...,
        example=1250.5,
        description="Response time in milliseconds"
    )
    token_usage: Dict[str, int] = Field(
        ...,
        example={"prompt_tokens": 85, "completion_tokens": 120, "total_tokens": 205},
        description="Token usage statistics for the API call"
    )
    relevant_faqs: Optional[List[str]] = Field(
        None,
        example=["What are the main types of AI?", "How does machine learning work?"],
        description="List of relevant FAQ questions found in the knowledge base"
    )
    timestamp: datetime = Field(
        default_factory=datetime.now,
        example="2024-01-15T10:30:45.123456",
        description="Timestamp when the response was generated"
    )

class HealthResponse(BaseModel):
    status: str = Field(
        ...,
        example="healthy",
        description="Overall service health status"
    )
    timestamp: datetime = Field(
        default_factory=datetime.now,
        example="2024-01-15T10:30:45.123456",
        description="Timestamp of the health check"
    )
    provider: str = Field(
        ...,
        example="openai",
        description="AI service provider (openai or azure)"
    )
    model: str = Field(
        ...,
        example="gpt-4o",
        description="AI model being used"
    )
    uptime_seconds: float = Field(
        ...,
        example=3600.5,
        description="Service uptime in seconds"
    )

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
    data: List[float] = Field(
        ...,
        example=[10.5, 12.3, 13.8, 15.2, 14.9, 16.1, 18.4, 20.2, 19.8, 21.5, 23.1, 24.7, 22.9, 25.3, 27.2],
        description="List of numerical time series values (minimum 10 points required)"
    )
    dates: Optional[List[str]] = Field(
        None,
        example=["2024-01-01", "2024-01-02", "2024-01-03", "2024-01-04", "2024-01-05", 
                "2024-01-06", "2024-01-07", "2024-01-08", "2024-01-09", "2024-01-10",
                "2024-01-11", "2024-01-12", "2024-01-13", "2024-01-14", "2024-01-15"],
        description="Optional list of date strings corresponding to data points"
    )
    steps: int = Field(
        5,
        example=5,
        ge=1,
        le=30,
        description="Number of forecast steps to generate (1-30)"
    )
    confidence_level: float = Field(
        0.95,
        example=0.95,
        ge=0.8,
        le=0.99,
        description="Confidence level for prediction intervals (0.8-0.99)"
    )

class ForecastPoint(BaseModel):
    date: str = Field(
        ...,
        example="2024-01-16",
        description="Date for this forecast point"
    )
    value: float = Field(
        ...,
        example=28.5,
        description="Predicted value"
    )
    index: int = Field(
        ...,
        example=1,
        description="Forecast step index (1-based)"
    )

class ModelInfo(BaseModel):
    model_type: str = Field(
        ...,
        example="ARIMA",
        description="Type of forecasting model used"
    )
    order: List[int] = Field(
        ...,
        example=[2, 1, 1],
        description="ARIMA model order [p, d, q]"
    )
    aic: float = Field(
        ...,
        example=45.23,
        description="Akaike Information Criterion (model quality metric)"
    )
    data_points_used: int = Field(
        ...,
        example=15,
        description="Number of historical data points used for training"
    )

class PerformanceMetrics(BaseModel):
    mae: float = Field(
        ...,
        example=1.23,
        description="Mean Absolute Error"
    )
    rmse: float = Field(
        ...,
        example=1.87,
        description="Root Mean Square Error"
    )
    mean_residual: float = Field(
        ...,
        example=0.12,
        description="Mean of residuals"
    )
    residual_std: float = Field(
        ...,
        example=1.45,
        description="Standard deviation of residuals"
    )

class ForecastMetadata(BaseModel):
    processing_time_ms: float = Field(
        ...,
        example=234.5,
        description="Time taken to generate forecast in milliseconds"
    )
    confidence_level: float = Field(
        ...,
        example=0.95,
        description="Confidence level used for prediction intervals"
    )
    forecast_horizon: int = Field(
        ...,
        example=5,
        description="Number of steps forecasted"
    )
    timestamp: str = Field(
        ...,
        example="2024-01-15T10:30:45.123456",
        description="Timestamp when forecast was generated"
    )

class ForecastResponse(BaseModel):
    forecasts: List[ForecastPoint] = Field(
        ...,
        example=[
            {"date": "2024-01-16", "value": 28.5, "index": 1},
            {"date": "2024-01-17", "value": 29.2, "index": 2},
            {"date": "2024-01-18", "value": 30.1, "index": 3},
            {"date": "2024-01-19", "value": 31.0, "index": 4},
            {"date": "2024-01-20", "value": 31.8, "index": 5}
        ],
        description="List of forecast points with predictions"
    )
    model_info: ModelInfo = Field(
        ...,
        description="Information about the forecasting model used"
    )
    performance_metrics: PerformanceMetrics = Field(
        ...,
        description="Model performance metrics"
    )
    metadata: ForecastMetadata = Field(
        ...,
        description="Metadata about the forecasting process"
    )

class SqlQueryRequest(BaseModel):
    session_id: str = Field(
        ...,
        example="sql-session-123",
        description="Unique identifier for the SQL chat session"
    )
    message: str = Field(
        ...,
        example="Show me all products with low stock levels",
        description="Natural language query to convert to SQL"
    )
    context: Optional[Dict[str, Any]] = Field(
        None,
        example={"database": "inventory", "user_role": "analyst"},
        description="Optional context for the SQL query"
    )

class SqlQueryResponse(BaseModel):
    natural_language_answer: str = Field(
        ...,
        example="You have 1,245 assets in your inventory.",
        description="Natural language explanation of the query results"
    )
    sql_query: str = Field(
        ...,
        example="SELECT COUNT(*) AS AssetCount FROM Assets WHERE Status <> 'Disposed';",
        description="Generated SQL query that would be executed"
    )
    token_usage: Dict[str, int] = Field(
        ...,
        example={"prompt_tokens": 85, "completion_tokens": 45, "total_tokens": 130},
        description="Token usage statistics for the API call"
    )
    latency_ms: int = Field(
        ...,
        example=850,
        description="Response time in milliseconds (integer)"
    )
    provider: str = Field(
        ...,
        example="openai",
        description="AI service provider used"
    )
    model: str = Field(
        ...,
        example="gpt-4o",
        description="AI model used for generation"
    )
    status: str = Field(
        ...,
        example="ok",
        description="Status of the query generation"
    )
    
    # Keep some internal fields for compatibility but don't expose in API
    session_id: Optional[str] = Field(None, description="Internal session tracking")
    query_results: Optional[List[Dict[str, Any]]] = Field(None, description="Internal query results")
    table_info: Optional[List[str]] = Field(None, description="Internal table tracking")
    validation_attempts: Optional[int] = Field(None, description="Internal validation tracking")
    timestamp: Optional[datetime] = Field(None, description="Internal timestamp")

class ChatModeRequest(BaseModel):
    session_id: str = Field(
        ...,
        example="multi-mode-session-123",
        description="Unique identifier for the chat session"
    )
    message: str = Field(
        ...,
        example="What is artificial intelligence?",
        description="User message to send to the AI assistant"
    )
    mode: Literal["rag", "sql"] = Field(
        "rag",
        example="rag",
        description="Chat mode: 'rag' for knowledge-based chat or 'sql' for database queries"
    )
    context: Optional[Dict[str, Any]] = Field(
        None,
        example={"user_preference": "technical", "language": "en"},
        description="Optional context object for additional information"
    )

class ChatModeResponse(BaseModel):
    response: str = Field(
        ...,
        description="AI-generated response based on the selected mode"
    )
    mode: str = Field(
        ...,
        description="The mode used to generate this response"
    )
    session_id: str = Field(
        ...,
        description="The session ID for this conversation"
    )
    # Union type to support both RAG and SQL response fields
    sql_query: Optional[str] = Field(
        None,
        description="Generated SQL query (only for SQL mode)"
    )
    query_results: Optional[List[Dict[str, Any]]] = Field(
        None,
        description="SQL query results (only for SQL mode)"
    )
    table_info: Optional[List[str]] = Field(
        None,
        description="Database tables referenced (only for SQL mode)"
    )
    validation_attempts: Optional[int] = Field(
        None,
        description="SQL validation attempts made (only for SQL mode)"
    )
    relevant_faqs: Optional[List[str]] = Field(
        None,
        description="Relevant FAQ questions (only for RAG mode)"
    )
    latency_ms: float = Field(
        ...,
        description="Response time in milliseconds"
    )
    token_usage: Dict[str, int] = Field(
        ...,
        description="Token usage statistics for the API call"
    )
    timestamp: datetime = Field(
        default_factory=datetime.now,
        description="Timestamp when the response was generated"
    )
    status: Optional[str] = Field(
        None,
        description="Status of the query processing (for SQL mode)"
    )

# Database schema information for SQL mode
class DatabaseTable(BaseModel):
    name: str
    description: str
    columns: List[Dict[str, str]]  # {name, type, description}
    
class DatabaseSchema(BaseModel):
    tables: List[DatabaseTable]
    relationships: List[Dict[str, str]]  # Foreign key relationships