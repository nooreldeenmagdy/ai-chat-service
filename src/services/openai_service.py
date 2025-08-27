import os
import json
import time
import logging
import asyncio
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from openai import OpenAI, AzureOpenAI
from dotenv import load_dotenv

from src.models.chat_models import (
    ChatRequest, ChatResponse, ChatSession, ChatMessage, 
    HealthResponse, TokenUsage, FAQ
)

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=getattr(logging, os.getenv('LOG_LEVEL', 'INFO')))
logger = logging.getLogger(__name__)

class AIServiceError(Exception):
    """Custom exception for AI service errors"""
    pass

class RAGService:
    """Retrieval-Augmented Generation service for FAQ similarity search"""
    
    def __init__(self, faq_file: str = "faq.json"):
        self.faqs: List[FAQ] = []
        self.vectorizer = None
        self.faq_vectors = None
        self._load_faqs(faq_file)
        self._build_embeddings()
    
    def _load_faqs(self, faq_file: str):
        """Load FAQ data from JSON file"""
        try:
            with open(faq_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                for faq_data in data.get('faqs', []):
                    self.faqs.append(FAQ(**faq_data))
            logger.info(f"Loaded {len(self.faqs)} FAQs")
        except FileNotFoundError:
            logger.error(f"FAQ file {faq_file} not found")
            raise AIServiceError(f"FAQ file {faq_file} not found")
        except Exception as e:
            logger.error(f"Error loading FAQs: {e}")
            raise AIServiceError(f"Error loading FAQs: {e}")
    
    def _build_embeddings(self):
        """Build TF-IDF embeddings for FAQ questions"""
        if not self.faqs:
            return
        
        questions = [faq.question for faq in self.faqs]
        self.vectorizer = TfidfVectorizer(stop_words='english', lowercase=True)
        self.faq_vectors = self.vectorizer.fit_transform(questions)
        logger.info("FAQ embeddings built successfully")
    
    def find_relevant_faqs(self, query: str, top_k: int = 3) -> List[FAQ]:
        """Find top-k most relevant FAQs using cosine similarity"""
        if not self.vectorizer or self.faq_vectors is None:
            return []
        
        try:
            query_vector = self.vectorizer.transform([query])
            similarities = cosine_similarity(query_vector, self.faq_vectors).flatten()
            
            # Get top-k indices
            top_indices = similarities.argsort()[-top_k:][::-1]
            
            # Filter out low similarity results (threshold = 0.1)
            relevant_faqs = []
            for idx in top_indices:
                if similarities[idx] > 0.1:
                    relevant_faqs.append(self.faqs[idx])
            
            return relevant_faqs
        except Exception as e:
            logger.error(f"Error finding relevant FAQs: {e}")
            return []

class OpenAIService:
    """Main AI service for chat completions with RAG support"""
    
    def __init__(self):
        self.provider = os.getenv('PROVIDER', 'openai').lower()
        self.model = os.getenv('MODEL_NAME', 'gpt-4o')
        self.client = self._initialize_client()
        self.sessions: Dict[str, ChatSession] = {}
        self.rag_service = RAGService()
        self.start_time = datetime.now()
        self.system_prompt = """You are a helpful AI assistant. Use the provided FAQ context to answer questions when relevant, but also use your general knowledge. Be conversational and helpful."""
        
        logger.info(f"OpenAI service initialized with provider: {self.provider}, model: {self.model}")
    
    def _initialize_client(self):
        """Initialize OpenAI or Azure OpenAI client based on configuration"""
        try:
            # Clear any proxy-related environment variables that might interfere
            proxy_vars = ['HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy', 'ALL_PROXY', 'all_proxy']
            original_proxy_values = {}
            for var in proxy_vars:
                if var in os.environ:
                    original_proxy_values[var] = os.environ[var]
                    del os.environ[var]
            
            if self.provider == 'azure':
                api_key = os.getenv('AZURE_OPENAI_API_KEY')
                endpoint = os.getenv('AZURE_OPENAI_ENDPOINT')
                if not api_key or not endpoint:
                    raise AIServiceError("Azure OpenAI configuration incomplete")
                
                logger.info(f"Initializing Azure OpenAI client with endpoint: {endpoint}")
                client = AzureOpenAI(
                    api_key=api_key,
                    api_version="2024-02-01",
                    azure_endpoint=endpoint
                )
            else:
                api_key = os.getenv('OPENAI_API_KEY')
                if not api_key:
                    raise AIServiceError("OpenAI API key not provided")
                
                logger.info("Initializing OpenAI client")
                client = OpenAI(api_key=api_key)
            
            # Restore proxy environment variables if they existed
            for var, value in original_proxy_values.items():
                os.environ[var] = value
            
            return client
                
        except Exception as e:
            logger.error(f"Failed to initialize AI client: {e}")
            # Try alternative initialization method
            try:
                api_key = os.getenv('OPENAI_API_KEY')
                if api_key and self.provider == 'openai':
                    logger.info("Trying alternative OpenAI client initialization")
                    # Use environment variable method instead
                    os.environ['OPENAI_API_KEY'] = api_key
                    client = OpenAI()  # No explicit api_key parameter
                    return client
            except Exception as fallback_error:
                logger.error(f"Fallback initialization failed: {fallback_error}")
            
            raise AIServiceError(f"Failed to initialize AI client: {e}")
    
    def get_or_create_session(self, session_id: str) -> ChatSession:
        """Get existing session or create new one"""
        if session_id not in self.sessions:
            self.sessions[session_id] = ChatSession(session_id=session_id)
        return self.sessions[session_id]
    
    def _build_context_prompt(self, user_message: str, relevant_faqs: List[FAQ]) -> str:
        """Build context prompt with relevant FAQ information"""
        if not relevant_faqs:
            return user_message
        
        context = "Here's some relevant information from our FAQ:\n\n"
        for i, faq in enumerate(relevant_faqs, 1):
            context += f"{i}. Q: {faq.question}\n   A: {faq.answer}\n\n"
        
        context += f"User question: {user_message}\n\n"
        context += "Please answer the user's question, using the FAQ context if relevant, but also drawing from your general knowledge."
        
        return context
    
    async def send_message(self, request: ChatRequest) -> ChatResponse:
        """Send message to AI service and return response with metadata"""
        start_time = time.time()
        session = self.get_or_create_session(request.session_id)
        
        try:
            # Find relevant FAQs
            relevant_faqs = self.rag_service.find_relevant_faqs(request.message)
            relevant_faq_texts = [f"Q: {faq.question} A: {faq.answer}" for faq in relevant_faqs]
            
            # Build enhanced prompt with context
            enhanced_message = self._build_context_prompt(request.message, relevant_faqs)
            
            # Prepare messages for API call
            messages = [{"role": "system", "content": self.system_prompt}]
            
            # Add conversation history
            for msg in session.messages[-10:]:  # Last 10 messages for context
                messages.append({"role": msg.role, "content": msg.content})
            
            # Add current enhanced message
            messages.append({"role": "user", "content": enhanced_message})
            
            # Log request
            logger.info(f"Chat request - Session: {request.session_id}, Message length: {len(request.message)}")
            
            # Call AI service
            if self.provider == 'azure':
                response = await self._call_azure_openai(messages)
            else:
                response = await self._call_openai(messages)
            
            # Calculate latency
            latency_ms = (time.time() - start_time) * 1000
            
            # Update session
            session.messages.append(ChatMessage(role="user", content=request.message))
            session.messages.append(ChatMessage(role="assistant", content=response.choices[0].message.content))
            session.updated_at = datetime.now()
            
            # Extract token usage
            token_usage = {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens
            }
            
            # Log response
            logger.info(f"Chat response - Session: {request.session_id}, Latency: {latency_ms:.2f}ms, Tokens: {token_usage['total_tokens']}")
            
            return ChatResponse(
                response=response.choices[0].message.content,
                session_id=request.session_id,
                latency_ms=latency_ms,
                token_usage=token_usage,
                relevant_faqs=relevant_faq_texts if relevant_faqs else None
            )
            
        except Exception as e:
            latency_ms = (time.time() - start_time) * 1000
            error_msg = f"Error processing chat request: {str(e)}"
            logger.error(f"Chat error - Session: {request.session_id}, Error: {error_msg}, Latency: {latency_ms:.2f}ms")
            raise AIServiceError(error_msg)
    
    async def _call_openai(self, messages: List[dict]):
        """Call OpenAI API"""
        return await asyncio.to_thread(
            self.client.chat.completions.create,
            model=self.model,
            messages=messages,
            max_tokens=1000,
            temperature=0.7
        )
    
    async def _call_azure_openai(self, messages: List[dict]):
        """Call Azure OpenAI API"""
        deployment_name = os.getenv('AZURE_OPENAI_DEPLOYMENT', self.model)
        return await asyncio.to_thread(
            self.client.chat.completions.create,
            model=deployment_name,
            messages=messages,
            max_tokens=1000,
            temperature=0.7
        )
    
    def get_health_status(self) -> HealthResponse:
        """Get service health status"""
        uptime = (datetime.now() - self.start_time).total_seconds()
        
        return HealthResponse(
            status="healthy",
            provider=self.provider,
            model=self.model,
            uptime_seconds=uptime
        )
    
    def clear_session(self, session_id: str) -> bool:
        """Clear a specific chat session"""
        if session_id in self.sessions:
            del self.sessions[session_id]
            logger.info(f"Cleared session: {session_id}")
            return True
        return False

# Global service instance
openai_service = OpenAIService()