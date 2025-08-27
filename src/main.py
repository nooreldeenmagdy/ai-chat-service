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

# Create FastAPI app with lifespan management
app = FastAPI(
    title="AI Chat Service",
    description="A minimal AI chat service with RAG capabilities",
    version="1.0.0",
    lifespan=lifespan
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