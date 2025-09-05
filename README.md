# AI Chat Service

A comprehensive AI-powered chat service with RAG (Retrieval-Augmented Generation) capabilities, SQL chatbot with natural language to database query conversion, time series forecasting, and interactive web interface. Built with FastAPI, OpenAI/Azure OpenAI integration, and Streamlit.

## Features

- **AI Chat Service** - OpenAI/Azure OpenAI integration with conversation memory
- **RAG System** - FAQ-based knowledge retrieval using TF-IDF embeddings  
- **SQL Chatbot** - Natural language to SQL query conversion with database validation
- **Dual-Mode Chat** - Intelligent switching between RAG and SQL modes based on query analysis
- **Asset Management Database** - Comprehensive SQLite database with customers, vendors, assets, and transactions
- **Real-time Token Tracking** - Accurate OpenAI API token usage monitoring across all operations
- **Database Validation** - SQL queries are validated by execution against SQLite database
- **Time Series Forecasting** - ARIMA-based predictions with confidence intervals
- **Authentication** - Optional Bearer token security
- **Rate Limiting** - Built-in protection (10 requests/minute per IP)
- **Web Interface** - Interactive Streamlit chat application with mode switching
- **API Documentation** - Interactive Swagger UI at `/docs`
- **Comprehensive Testing** - Unit and integration tests with 90%+ coverage
- **Docker Support** - Containerized deployment ready
- **Health Monitoring** - System status and metrics endpoint

## Project Structure

```
ai-chat-service/
├── src/                      # Core application source
│   ├── main.py                  # FastAPI application entry point
│   ├── api/routes.py           # REST API endpoints
│   ├── services/               # Business logic services
│   │   ├── openai_service.py   # OpenAI integration & RAG
│   │   ├── sql_chatbot_service.py  # Natural language to SQL conversion
│   │   ├── database_service.py # SQLite database management
│   │   └── forecasting_service.py  # Time series forecasting
│   └── models/chat_models.py   # Pydantic data models
├── streamlit_app/           # Web interface
│   └── app.py                  # Streamlit chat application
├── tests/                   # Test suite
│   ├── test_rag_service.py     # RAG service unit tests
│   ├── test_chat_api.py        # API integration tests
│   ├── test_sql_chatbot.py     # SQL chatbot tests
│   └── README.md               # Testing documentation
├── asset_management.db      # SQLite database with sample data
├── faq.json                 # Knowledge base for RAG
├── requirements.txt         # Python dependencies
├── Dockerfile              # Container configuration
├── docker-compose.yml      # Multi-service orchestration
├── .env.example            # Environment template
└── README.md               # This file
```

## Quick Start

### Option 1: Docker (Recommended)
```bash
# Clone repository
git clone https://github.com/nooreldeenmagdy/ai-chat-service.git
cd ai-chat-service

# Configure environment
cp .env.example .env
# Edit .env with your OpenAI API key

# Launch with Docker Compose
docker-compose up --build
```

### Option 2: Local Development
```bash
# Clone and setup
git clone https://github.com/nooreldeenmagdy/ai-chat-service.git
cd ai-chat-service

# Create virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your configuration

# Start services
uvicorn src.main:app --reload --port 8000  # API
streamlit run streamlit_app/app.py --server.port 8501  # Web UI
```

## Configuration

Create `.env` file from template and configure:

```bash
# AI Provider
PROVIDER=openai                    # or 'azure'
MODEL_NAME=gpt-4o                 # AI model to use
OPENAI_API_KEY=your_key_here      # Required for OpenAI

# Optional Authentication  
BEARER_TOKEN=your_token_here      # Enable API authentication

# Application Ports
FASTAPI_PORT=8000
STREAMLIT_PORT=8501
```

## API Endpoints

### Chat & AI
- `POST /api/chat` - Send message to AI with RAG enhancement
- `POST /api/sql-chat` - Convert natural language to SQL queries with database validation
- `POST /api/dual-mode-chat` - Unified endpoint with intelligent mode switching
- `GET /api/health` - Service health and status
- `DELETE /api/chat/{session_id}` - Clear conversation history
- `GET /api/sessions` - List active chat sessions

### Forecasting  
- `POST /api/forecast` - Generate time series predictions
- `POST /api/forecast/validate` - Validate data for forecasting

### Documentation
- `GET /docs` - Interactive Swagger UI
- `GET /redoc` - ReDoc documentation

## Usage Examples

### Chat API
```bash
# Simple chat
curl -X POST "http://localhost:8000/api/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "user-123",
    "message": "What is artificial intelligence?"
  }'

# SQL Chat - Natural language to SQL
curl -X POST "http://localhost:8000/api/sql-chat" \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "sql-user-123",
    "message": "Show me all products with stock levels below 50"
  }'

# Dual-mode chat with auto-detection
curl -X POST "http://localhost:8000/api/dual-mode-chat" \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "dual-user-123",
    "message": "Find customers in New York",
    "mode": "sql"
  }'

# With authentication
curl -X POST "http://localhost:8000/api/chat" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your-token" \
  -d '{
    "session_id": "user-123", 
    "message": "Explain machine learning",
    "context": {"user_level": "beginner"}
  }'
```

### Forecasting API
```bash
# Generate forecast
curl -X POST "http://localhost:8000/api/forecast" \
  -H "Content-Type: application/json" \
  -d '{
    "data": [10, 12, 15, 18, 22, 25, 28, 30],
    "dates": ["2024-01", "2024-02", "2024-03", "2024-04", "2024-05", "2024-06", "2024-07", "2024-08"],
    "steps": 3,
    "confidence_level": 0.95  }'
```

## SQL Chatbot Features

### Database Schema
The SQL chatbot has built-in knowledge of a comprehensive asset management database with these tables:

- **Customers** - Customer information for sales orders (CustomerId, CustomerCode, CustomerName, Email, Phone, BillingAddress, etc.)
- **Vendors** - Vendor/supplier information for asset purchases (VendorId, VendorCode, VendorName, Contact details, etc.)
- **Sites** - Physical sites/locations where assets are deployed (SiteId, SiteCode, SiteName, Address, TimeZone, etc.)
- **Locations** - Specific locations within sites for asset placement (LocationId, SiteId, LocationCode, LocationName, etc.)
- **Items** - Item catalog/master data for purchase and sales orders (ItemId, ItemCode, ItemName, Category, UnitOfMeasure, etc.)
- **Assets** - Physical assets tracked in the system (AssetId, AssetTag, AssetName, SiteId, SerialNumber, Category, Status, Cost, etc.)
- **Bills** - Accounts payable - bills from vendors (BillId, VendorId, BillNumber, BillDate, DueDate, TotalAmount, etc.)
- **PurchaseOrders** - Purchase orders for procurement (POId, PONumber, VendorId, PODate, Status, SiteId, etc.)
- **PurchaseOrderLines** - Line items for purchase orders (POLineId, POId, ItemId, Quantity, UnitPrice, etc.)
- **SalesOrders** - Sales orders from customers (SOId, SONumber, CustomerId, SODate, Status, SiteId, etc.)
- **SalesOrderLines** - Line items for sales orders (SOLineId, SOId, ItemId, Quantity, UnitPrice, etc.)
- **AssetTransactions** - Asset movement/adjustment/disposal history (AssetTxnId, AssetId, TxnType, FromLocation, ToLocation, etc.)

### Natural Language Examples
The SQL chatbot can understand queries like:

- "Show me all active assets at each site"
- "Find customers who placed sales orders last month"  
- "List the most expensive assets by cost"
- "Get all vendors from New York"
- "Show recent purchase orders with vendor details"
- "Find assets that were moved between locations"
- "What are the total sales by customer this year"
- "Show bills that are overdue"

### Advanced Features
- **Two-Step LLM Workflow** - First understands user intent and selects relevant tables, then generates optimized SQL
- **SQLite Database Validation** - All generated queries are validated by actual execution against the database
- **Token Usage Tracking** - Real-time monitoring of OpenAI API token consumption across all operations
- **Intelligent Mode Detection** - Dual-mode endpoint automatically determines whether to use RAG or SQL based on query content
- **Query Result Explanation** - Converts database results back into natural language responses

### Safety & Validation  
- 3-attempt retry mechanism for query generation and validation
- SQL validation prevents destructive operations (DROP, DELETE, UPDATE, ALTER)
- Query safety checks before execution against SQLite database
- Natural language explanation of results with actual data analysis
- Comprehensive error handling and logging

## Testing

Run the comprehensive test suite:

```bash
# Run all tests
python -m pytest tests/ -v

# Run with coverage
python -m pytest tests/ --cov=src --cov-report=html

# Run specific test categories
python -m pytest tests/test_rag_service.py -v    # RAG tests
python -m pytest tests/test_chat_api.py -v       # API tests
```

**Test Coverage:**
- RAG Service: 23 tests (FAQ loading, embeddings, similarity search)
- Chat API: 23 tests (endpoints, validation, auth, rate limiting)
- SQL Chatbot: 25 tests (query generation, validation, dual-mode)  
- Integration: End-to-end workflow testing
- Error Handling: Comprehensive exception testing

## RAG Knowledge Base

The system uses `faq.json` for knowledge retrieval:

```json
{
  "faqs": [
    {
      "id": 1,
      "question": "What is artificial intelligence?",
      "answer": "AI is computer systems performing human-like tasks..."
    }
  ]
}
```

**RAG Features:**
- TF-IDF vectorization for semantic similarity
- Configurable similarity thresholds
- Context injection into AI prompts
- FAQ source attribution in responses

## Docker Deployment

### Single Container
```bash
# Build image
docker build -t ai-chat-service .

# Run container
docker run -p 8000:8000 -p 8501:8501 \
  -e OPENAI_API_KEY=your_key \
  ai-chat-service
```

### Multi-Service with Compose
```bash
# Production deployment
docker-compose -f docker-compose.yml up -d

# Development with hot reload
docker-compose -f docker-compose.dev.yml up
```

## Security Features

- **Authentication**: Optional Bearer token validation
- **Rate Limiting**: IP-based request throttling  
- **Input Validation**: Pydantic model validation
- **Error Handling**: Secure error responses
- **Environment Variables**: Sensitive data protection
- **CORS Configuration**: Cross-origin request control

## Monitoring & Health

Health endpoint provides system status:
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00Z",
  "provider": "openai", 
  "model": "gpt-4o",
  "uptime_seconds": 3600.5
}
```

## Development

### Project Setup
```bash
# Install development dependencies
pip install -r requirements.txt

# Run pre-commit hooks
pre-commit install

# Code formatting
black src/ tests/
isort src/ tests/

# Linting
flake8 src/ tests/
```

### Contributing
1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Make changes and add tests
4. Ensure tests pass (`pytest`)
5. Commit changes (`git commit -m 'Add amazing feature'`)
6. Push to branch (`git push origin feature/amazing-feature`)
7. Open Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- OpenAI for GPT models and API
- FastAPI for the excellent web framework  
- Streamlit for rapid UI development
- scikit-learn for machine learning utilities