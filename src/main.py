import os
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from src.api.routes import router as api_router

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=getattr(logging, os.getenv('LOG_LEVEL', 'INFO')),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    logger.info("Starting AI Chat Service...")
    # Startup logic here if needed
    yield
    # Cleanup logic here if needed
    logger.info("Shutting down AI Chat Service...")

# Create FastAPI app with enhanced documentation
app = FastAPI(
    title="🤖 AI Chat Service API",
    description="""
    ## Advanced AI Chat Service with RAG and Forecasting

    A comprehensive AI-powered chat service featuring:
    
    ### 🚀 **Core Features**
    * **Intelligent Conversations** - Powered by OpenAI/Azure OpenAI models
    * **RAG Integration** - Context-aware responses using FAQ knowledge base
    * **Session Management** - Persistent conversation history per user
    * **Time Series Forecasting** - ARIMA-based predictions with confidence intervals
    * **Rate Limiting** - Built-in protection (10 requests/minute per IP)
    * **Authentication** - Optional Bearer token security
    
    ### 🛠 **Technical Stack**
    * **FastAPI** - High-performance async API framework
    * **OpenAI/Azure OpenAI** - State-of-the-art language models
    * **Streamlit** - Interactive web interface
    * **Docker** - Containerized deployment
    * **ARIMA** - Statistical forecasting models
    
    ### 📚 **Quick Start**
    1. **Health Check**: `GET /api/health` - Verify service status
    2. **Start Chatting**: `POST /api/chat` - Send your first message
    3. **Forecast Data**: `POST /api/forecast` - Generate predictions
    4. **Validate Data**: `POST /api/forecast/validate` - Check data quality
    
    ### 🔐 **Authentication**
    Optional Bearer token authentication can be enabled via `BEARER_TOKEN` environment variable.
    
    ### 📖 **Documentation**
    * **Interactive Docs**: Available at `/docs` (this page)
    * **ReDoc**: Alternative docs at `/redoc`
    * **OpenAPI JSON**: Schema available at `/openapi.json`
    
    ---
    
    **Ready to explore? Try the endpoints below! 🚀**
    """,
    version="1.0.0",
    lifespan=lifespan,
    contact={
        "name": "AI Chat Service Support",
        "url": "https://github.com/nooreldeenmagdy/ai-chat-service",
        "email": "support@ai-chat-service.com"
    },
    license_info={
        "name": "MIT License",
        "url": "https://opensource.org/licenses/MIT"
    },
    servers=[
        {
            "url": "http://localhost:8000",
            "description": "Local development server"
        },
        {
            "url": "https://api.ai-chat-service.com",
            "description": "Production server"
        }
    ],
    tags_metadata=[
        {
            "name": "Chat",
            "description": "💬 Intelligent conversation endpoints with AI models"
        },
        {
            "name": "Forecasting", 
            "description": "📈 Time series forecasting and data validation"
        },
        {
            "name": "System",
            "description": "⚡ Health checks and system management"
        },
        {
            "name": "Sessions",
            "description": "👥 Session and conversation management"
        }
    ]
)

# Middleware for CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust this for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(api_router)

@app.get("/")
def read_root():
    """Root endpoint with welcome message"""
    return {
        "message": "Welcome to the AI Chat Service",
        "version": "1.0.0",
        "docs_url": "/docs",
        "health_url": "/api/health"
    }

# Entry point for the application
if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv('FASTAPI_PORT', 8000))
    uvicorn.run(
        "src.main:app", 
        host="0.0.0.0", 
        port=port,
        reload=True,
        log_level="info"
    )