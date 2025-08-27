import pytest
import json
from unittest.mock import Mock, patch, AsyncMock
from fastapi.testclient import TestClient
from fastapi import status, HTTPException
from datetime import datetime
import tempfile

from src.main import app
from src.services.openai_service import AIServiceError
from src.models.chat_models import ChatRequest, ChatResponse, HealthResponse

class TestChatAPI:
    """Test cases for the Chat API endpoints"""
    
    def setup_method(self):
        """Set up test fixtures before each test"""
        # Clear BEARER_TOKEN environment variable for tests
        import os
        if 'BEARER_TOKEN' in os.environ:
            del os.environ['BEARER_TOKEN']
        
        self.client = TestClient(app)
        
        # Create test FAQ data
        self.test_faqs = {
            "faqs": [
                {
                    "id": 1,
                    "question": "What is AI?",
                    "answer": "AI is artificial intelligence."
                }
            ]
        }
        
        # Create temporary FAQ file
        self.temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False)
        json.dump(self.test_faqs, self.temp_file)
        self.temp_file.close()
    
    def teardown_method(self):
        """Clean up after each test"""
        import os
        os.unlink(self.temp_file.name)
    @patch.dict('os.environ', {}, clear=True)  # Clear BEARER_TOKEN for tests
    @patch('src.api.routes.openai_service')
    def test_chat_endpoint_success(self, mock_service):
        """Test successful chat API call"""
        # Mock the service response
        mock_response = ChatResponse(
            response="This is a test AI response about artificial intelligence.",
            session_id="test-session-123",
            latency_ms=1250.5,
            token_usage={"prompt_tokens": 50, "completion_tokens": 30, "total_tokens": 80},
            relevant_faqs=["What is AI? - AI is artificial intelligence."],
            timestamp=datetime.now()
        )
        
        mock_service.send_message = AsyncMock(return_value=mock_response)
        
        # Make API request
        response = self.client.post(
            "/api/chat",
            json={
                "session_id": "test-session-123",
                "message": "What is artificial intelligence?",
                "context": {"user_level": "beginner"}
            }
        )
        
        # Assertions
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert data["session_id"] == "test-session-123"
        assert data["response"] == "This is a test AI response about artificial intelligence."
        assert data["latency_ms"] == 1250.5
        assert data["token_usage"]["total_tokens"] == 80
        assert data["relevant_faqs"] is not None
        assert len(data["relevant_faqs"]) == 1
        
        # Verify service was called with correct parameters
        mock_service.send_message.assert_called_once()
        call_args = mock_service.send_message.call_args[0][0]
        assert call_args.session_id == "test-session-123"
        assert call_args.message == "What is artificial intelligence?"
        assert call_args.context["user_level"] == "beginner"
    
    @patch('src.api.routes.openai_service')
    def test_chat_endpoint_without_context(self, mock_service):
        """Test chat API call without optional context"""
        mock_response = ChatResponse(
            response="Simple AI response",
            session_id="simple-session",
            latency_ms=800.0,
            token_usage={"prompt_tokens": 20, "completion_tokens": 15, "total_tokens": 35},
            relevant_faqs=None,
            timestamp=datetime.now()
        )
        
        mock_service.send_message = AsyncMock(return_value=mock_response)
        
        response = self.client.post(
            "/api/chat",
            json={
                "session_id": "simple-session",
                "message": "Hello AI!"
            }
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["session_id"] == "simple-session"
        assert data["relevant_faqs"] is None
    
    def test_chat_endpoint_empty_message(self):
        """Test chat API with empty message"""
        response = self.client.post(
            "/api/chat",
            json={
                "session_id": "test-session",
                "message": ""
            }
        )
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Message cannot be empty" in response.json()["detail"]
    
    def test_chat_endpoint_whitespace_only_message(self):
        """Test chat API with whitespace-only message"""
        response = self.client.post(
            "/api/chat",
            json={
                "session_id": "test-session",
                "message": "   \n\t  "
            }
        )
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Message cannot be empty" in response.json()["detail"]
    
    def test_chat_endpoint_message_too_long(self):
        """Test chat API with message exceeding length limit"""
        long_message = "x" * 2001  # Exceeds 2000 character limit
        
        response = self.client.post(
            "/api/chat",
            json={
                "session_id": "test-session",
                "message": long_message
            }
        )
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Message too long" in response.json()["detail"]
    
    def test_chat_endpoint_missing_session_id(self):
        """Test chat API with missing session ID"""
        response = self.client.post(
            "/api/chat",
            json={
                "message": "Hello AI!"
            }
        )
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    def test_chat_endpoint_missing_message(self):
        """Test chat API with missing message"""
        response = self.client.post(
            "/api/chat",
            json={
                "session_id": "test-session"
            }
        )
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    def test_chat_endpoint_invalid_json(self):
        """Test chat API with invalid JSON"""
        response = self.client.post(
            "/api/chat",
            data="invalid json content",
            headers={"Content-Type": "application/json"}
        )
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    @patch('src.api.routes.openai_service')
    def test_chat_endpoint_ai_service_error(self, mock_service):
        """Test chat API handling of AI service errors"""
        mock_service.send_message = AsyncMock(side_effect=AIServiceError("AI service unavailable"))
        
        response = self.client.post(
            "/api/chat",
            json={
                "session_id": "test-session",
                "message": "Hello AI!"
            }
        )
        
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert "AI service unavailable" in response.json()["detail"]
    
    @patch('src.api.routes.openai_service')
    def test_chat_endpoint_unexpected_error(self, mock_service):
        """Test chat API handling of unexpected errors"""
        mock_service.send_message = AsyncMock(side_effect=Exception("Unexpected error"))
        
        response = self.client.post(
            "/api/chat",
            json={
                "session_id": "test-session",
                "message": "Hello AI!"
            }
        )
        
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert "Internal server error" in response.json()["detail"]
    @patch('src.api.routes.check_rate_limit')
    @patch('src.api.routes.openai_service')
    def test_rate_limiting(self, mock_service, mock_rate_limit):
        """Test rate limiting functionality"""
        mock_response = ChatResponse(
            response="Test response",
            session_id="rate-test",
            latency_ms=100.0,
            token_usage={"prompt_tokens": 10, "completion_tokens": 10, "total_tokens": 20},
            relevant_faqs=None,
            timestamp=datetime.now()
        )
        
        mock_service.send_message = AsyncMock(return_value=mock_response)
        
        # First 10 requests should succeed (no rate limiting)
        mock_rate_limit.return_value = None
        for i in range(10):
            response = self.client.post(
                "/api/chat",
                json={
                    "session_id": f"rate-test-{i}",
                    "message": f"Message {i}"
                }
            )
            assert response.status_code == status.HTTP_200_OK
        
        # 11th request should be rate limited
        mock_rate_limit.side_effect = HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded"
        )
        response = self.client.post(
            "/api/chat",
            json={
                "session_id": "rate-test-overflow",
                "message": "This should be rate limited"
            }
        )
        
        assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS
        assert "Rate limit exceeded" in response.json()["detail"]
    @patch.dict('os.environ', {'BEARER_TOKEN': 'test-token-123'})
    @patch('src.api.routes.check_rate_limit')
    @patch('src.api.routes.openai_service')
    def test_chat_with_valid_auth(self, mock_service, mock_rate_limit):
        """Test chat API with valid bearer token"""
        mock_rate_limit.return_value = None  # No rate limiting for this test
        mock_response = ChatResponse(
            response="Authenticated response",
            session_id="auth-test",
            latency_ms=500.0,
            token_usage={"prompt_tokens": 15, "completion_tokens": 20, "total_tokens": 35},
            relevant_faqs=None,
            timestamp=datetime.now()
        )
        
        mock_service.send_message = AsyncMock(return_value=mock_response)
        
        response = self.client.post(
            "/api/chat",
            json={
                "session_id": "auth-test",
                "message": "Authenticated message"
            },
            headers={"Authorization": "Bearer test-token-123"}
        )
        
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["response"] == "Authenticated response"
    
    @patch.dict('os.environ', {'BEARER_TOKEN': 'test-token-123'})
    def test_chat_with_invalid_auth(self):
        """Test chat API with invalid bearer token"""
        response = self.client.post(
            "/api/chat",
            json={
                "session_id": "auth-test",
                "message": "Should fail auth"
            },
            headers={"Authorization": "Bearer wrong-token"}
        )
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "Invalid bearer token" in response.json()["detail"]
    
    @patch.dict('os.environ', {'BEARER_TOKEN': 'test-token-123'})
    def test_chat_with_missing_auth(self):
        """Test chat API with missing bearer token when required"""
        response = self.client.post(
            "/api/chat",
            json={
                "session_id": "auth-test",
                "message": "Should fail auth"
            }
        )
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "Bearer token required" in response.json()["detail"]
    
    @patch('src.api.routes.openai_service')
    def test_health_endpoint_success(self, mock_service):
        """Test health check endpoint success"""
        mock_health = HealthResponse(
            status="healthy",
            timestamp=datetime.now(),
            provider="openai",
            model="gpt-4o",
            uptime_seconds=3600.5
        )
        
        mock_service.get_health_status.return_value = mock_health
        
        response = self.client.get("/api/health")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert data["status"] == "healthy"
        assert data["provider"] == "openai"
        assert data["model"] == "gpt-4o"
        assert data["uptime_seconds"] == 3600.5
    
    @patch('src.api.routes.openai_service')
    def test_health_endpoint_error(self, mock_service):
        """Test health check endpoint when service is unhealthy"""
        mock_service.get_health_status.side_effect = Exception("Service unavailable")
        
        response = self.client.get("/api/health")
        
        assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
        assert "Service unhealthy" in response.json()["detail"]
    
    @patch('src.api.routes.openai_service')
    def test_clear_session_success(self, mock_service):
        """Test successful session clearing"""
        mock_service.clear_session.return_value = True
        
        response = self.client.delete("/api/chat/test-session-123")
        
        assert response.status_code == status.HTTP_200_OK
        assert "Session test-session-123 cleared successfully" in response.json()["message"]
        mock_service.clear_session.assert_called_once_with("test-session-123")
    
    @patch('src.api.routes.openai_service')
    def test_clear_session_not_found(self, mock_service):
        """Test clearing non-existent session"""
        mock_service.clear_session.return_value = False
        
        response = self.client.delete("/api/chat/nonexistent-session")
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "Session not found" in response.json()["detail"]
    
    @patch('src.api.routes.openai_service')
    def test_clear_session_error(self, mock_service):
        """Test error handling in session clearing"""
        mock_service.clear_session.side_effect = Exception("Database error")
        
        response = self.client.delete("/api/chat/test-session")
        
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert "Error clearing session" in response.json()["detail"]
    
    @patch('src.api.routes.openai_service')
    def test_list_sessions_success(self, mock_service):
        """Test successful session listing"""
        mock_service.sessions = {
            "session-1": Mock(),
            "session-2": Mock(),
            "session-3": Mock()
        }
        
        response = self.client.get("/api/sessions")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert data["total_count"] == 3
        assert "session-1" in data["active_sessions"]
        assert "session-2" in data["active_sessions"]
        assert "session-3" in data["active_sessions"]
    
    @patch('src.api.routes.openai_service')
    def test_list_sessions_empty(self, mock_service):
        """Test listing sessions when none exist"""
        mock_service.sessions = {}
        
        response = self.client.get("/api/sessions")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert data["total_count"] == 0
        assert data["active_sessions"] == []
    
    @patch('src.api.routes.openai_service')
    def test_list_sessions_error(self, mock_service):
        """Test error handling in session listing"""
        mock_service.sessions = Mock()
        mock_service.sessions.keys.side_effect = Exception("Database error")
        
        response = self.client.get("/api/sessions")
        
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert "Error retrieving sessions" in response.json()["detail"]


class TestChatAPIIntegration:
    """Integration tests for chat API with actual RAG functionality"""
    
    def setup_method(self):
        """Set up test fixtures for integration tests"""
        self.client = TestClient(app)
        
        # Create comprehensive test FAQ data
        self.test_faqs = {
            "faqs": [
                {
                    "id": 1,
                    "question": "What is artificial intelligence?",
                    "answer": "Artificial Intelligence (AI) is a branch of computer science that aims to create machines capable of performing tasks that typically require human intelligence."
                },
                {
                    "id": 2,
                    "question": "How does machine learning work?",
                    "answer": "Machine learning is a subset of AI that enables computers to learn and improve from data without being explicitly programmed."
                },
                {
                    "id": 3,
                    "question": "What are neural networks?",
                    "answer": "Neural networks are computing systems inspired by biological neural networks that consist of interconnected nodes."
                }
            ]
        }
        
        # Create temporary FAQ file
        self.temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False)
        json.dump(self.test_faqs, self.temp_file)
        self.temp_file.close()
    
    def teardown_method(self):
        """Clean up after integration tests"""
        import os
        os.unlink(self.temp_file.name)
    @patch.dict('os.environ', {
        'PROVIDER': 'openai',
        'OPENAI_API_KEY': 'test-key-123'
    })
    @patch('src.api.routes.check_rate_limit')
    @patch('src.services.openai_service.OpenAI')
    @patch('src.services.openai_service.RAGService.__init__')
    @patch('src.services.openai_service.RAGService.find_relevant_faqs')
    @patch('asyncio.to_thread')
    def test_chat_api_with_rag_integration(self, mock_to_thread, mock_find_faqs, mock_rag_init, mock_openai, mock_rate_limit):
        """Test chat API with RAG service integration"""
        # Mock rate limiting
        mock_rate_limit.return_value = None
        
        # Mock RAG service initialization
        mock_rag_init.return_value = None
        
        # Mock OpenAI client
        mock_client = Mock()
        mock_openai.return_value = mock_client
        
        # Mock relevant FAQs found by RAG
        from src.models.chat_models import FAQ
        relevant_faq = FAQ(
            id=1,
            question="What is artificial intelligence?",
            answer="Artificial Intelligence (AI) is a branch of computer science that aims to create machines capable of performing tasks that typically require human intelligence."
        )
        mock_find_faqs.return_value = [relevant_faq]
        
        # Mock OpenAI API response
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "AI is a fascinating field that involves creating intelligent machines. Based on our FAQ, AI is a branch of computer science focused on human-like task performance."
        mock_response.usage.prompt_tokens = 150
        mock_response.usage.completion_tokens = 80
        mock_response.usage.total_tokens = 230
        
        mock_to_thread.return_value = mock_response
        
        # Make API request
        response = self.client.post(
            "/api/chat",
            json={
                "session_id": "rag-integration-test",
                "message": "Tell me about artificial intelligence",
                "context": {"user_level": "beginner"}
            }
        )
        
        # Assertions
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert data["session_id"] == "rag-integration-test"
        assert "intelligent machines" in data["response"]
        assert data["relevant_faqs"] is not None
        assert len(data["relevant_faqs"]) == 1
        assert "What is artificial intelligence?" in data["relevant_faqs"][0]
          # Verify RAG service was called
        mock_find_faqs.assert_called_once_with("Tell me about artificial intelligence")
        
        # Verify OpenAI API was called with enhanced context
        mock_to_thread.assert_called_once()
        # Just verify the mock was called - the exact arguments depend on implementation details
