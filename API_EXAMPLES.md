# Example API Test Requests for Postman or similar tools

## Environment Variables
BASE_URL = http://localhost:8000
BEARER_TOKEN = my-secure-token-123 (if authentication enabled)

## 1. Health Check
GET {{BASE_URL}}/api/health

## 2. Simple Chat Request
POST {{BASE_URL}}/api/chat
Content-Type: application/json

{
  "session_id": "test-session-001",
  "message": "Hello! What is artificial intelligence?"
}

## 3. Chat with Authentication (if enabled)
POST {{BASE_URL}}/api/chat
Content-Type: application/json
Authorization: Bearer {{BEARER_TOKEN}}

{
  "session_id": "secure-session-001",
  "message": "Explain machine learning"
}

## 4. FAQ-related Query (should trigger RAG)
POST {{BASE_URL}}/api/chat
Content-Type: application/json

{
  "session_id": "rag-test-session",
  "message": "How do neural networks work?"
}

## 5. List Active Sessions
GET {{BASE_URL}}/api/sessions

## 6. Clear Specific Session
DELETE {{BASE_URL}}/api/chat/test-session-001

## 7. Time Series Forecasting (Bonus Feature)
POST {{BASE_URL}}/api/forecast
Content-Type: application/json

{
  "data": [10, 12, 13, 15, 14, 16, 18, 20, 22, 25, 24, 26, 28, 30],
  "steps": 5,
  "confidence_level": 0.95
}

## 8. Validate Time Series Data
POST {{BASE_URL}}/api/forecast/validate
Content-Type: application/json

{
  "data": [100, 102, 105, 103, 108, 110, 112, 115, 118, 120]
}

## Expected Response Formats

### Chat Response
{
  "response": "Artificial Intelligence (AI) is...",
  "session_id": "test-session-001",
  "latency_ms": 245.7,
  "token_usage": {
    "prompt_tokens": 25,
    "completion_tokens": 50,
    "total_tokens": 75
  },
  "relevant_faqs": ["Q: What is AI? A: AI is..."],
  "timestamp": "2024-01-01T12:00:00"
}

### Health Response
{
  "status": "healthy",
  "provider": "openai",
  "model": "gpt-4o",
  "uptime_seconds": 3600.5,
  "timestamp": "2024-01-01T12:00:00"
}

### Forecast Response
{
  "forecasts": [
    {"date": "2024-01-15", "value": 32.5, "index": 1},
    {"date": "2024-01-16", "value": 34.2, "index": 2}
  ],
  "model_info": {
    "model_type": "ARIMA",
    "order": [2, 1, 1],
    "aic": 45.67,
    "data_points_used": 14
  },
  "performance_metrics": {
    "mae": 1.23,
    "rmse": 1.89
  },
  "metadata": {
    "processing_time_ms": 125.4,
    "confidence_level": 0.95,
    "forecast_horizon": 5
  }
}
