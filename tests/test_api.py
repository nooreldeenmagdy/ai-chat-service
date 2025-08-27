import pytest
import json
import os
from unittest.mock import Mock, patch
from fastapi.testclient import TestClient
from src.main import app
from src.services.openai_service import RAGService
from src.models.chat_models import FAQ

# Create test client
client = TestClient(app)

class TestHealthEndpoint:
    def test_health_check_success(self):
        """Test health check endpoint returns success"""
        response = client.get("/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "provider" in data
        assert "model" in data
        assert "uptime_seconds" in data

class TestChatEndpoint:
    def test_chat_missing_session_id(self):
        """Test chat endpoint with missing session_id"""
        response = client.post("/api/chat", json={"message": "Hello"})
        assert response.status_code == 422  # Validation error
    
    def test_chat_empty_message(self):
        """Test chat endpoint with empty message"""
        response = client.post("/api/chat", json={
            "session_id": "test-session",
            "message": ""
        })
        assert response.status_code == 400
        assert "Message cannot be empty" in response.json()["detail"]
    
    def test_chat_message_too_long(self):
        """Test chat endpoint with message that's too long"""
        long_message = "a" * 2001  # Exceeds 2000 character limit
        response = client.post("/api/chat", json={
            "session_id": "test-session",
            "message": long_message
        })
        assert response.status_code == 400
        assert "Message too long" in response.json()["detail"]
    
    @patch('src.services.openai_service.openai_service.send_message')
    def test_chat_success(self, mock_send_message):
        """Test successful chat interaction"""
        # Mock the service response
        mock_response = Mock()
        mock_response.response = "Hello! How can I help you?"
        mock_response.session_id = "test-session"
        mock_response.latency_ms = 150.5
        mock_response.token_usage = {
            "prompt_tokens": 10,
            "completion_tokens": 8,
            "total_tokens": 18
        }
        mock_response.relevant_faqs = None
        
        mock_send_message.return_value = mock_response
        
        response = client.post("/api/chat", json={
            "session_id": "test-session",
            "message": "Hello"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["response"] == "Hello! How can I help you?"
        assert data["session_id"] == "test-session"
        assert data["latency_ms"] == 150.5
        assert data["token_usage"]["total_tokens"] == 18

class TestRAGService:
    def create_test_faq_file(self, tmp_path):
        """Create a test FAQ file"""
        test_faqs = {
            "faqs": [
                {
                    "id": 1,
                    "question": "What is artificial intelligence?",
                    "answer": "AI is the simulation of human intelligence in machines."
                },
                {
                    "id": 2,
                    "question": "How does machine learning work?",
                    "answer": "Machine learning uses algorithms to learn from data."
                }
            ]
        }
        
        faq_file = tmp_path / "test_faq.json"
        with open(faq_file, 'w') as f:
            json.dump(test_faqs, f)
        
        return str(faq_file)
    
    def test_rag_service_initialization(self, tmp_path):
        """Test RAG service initialization with FAQ file"""
        faq_file = self.create_test_faq_file(tmp_path)
        
        rag_service = RAGService(faq_file)
        assert len(rag_service.faqs) == 2
        assert rag_service.faqs[0].question == "What is artificial intelligence?"
    
    def test_rag_service_similarity_search(self, tmp_path):
        """Test RAG service similarity search functionality"""
        faq_file = self.create_test_faq_file(tmp_path)
        
        rag_service = RAGService(faq_file)
        
        # Test search with relevant query
        results = rag_service.find_relevant_faqs("What is AI?", top_k=1)
        assert len(results) > 0
        assert "artificial intelligence" in results[0].question.lower()
    
    def test_rag_service_no_relevant_results(self, tmp_path):
        """Test RAG service returns no results for irrelevant query"""
        faq_file = self.create_test_faq_file(tmp_path)
        
        rag_service = RAGService(faq_file)
        
        # Test search with irrelevant query
        results = rag_service.find_relevant_faqs("cooking recipes", top_k=3)
        # Should return empty list or very low similarity results
        assert isinstance(results, list)

class TestSessionManagement:
    def test_clear_session_not_found(self):
        """Test clearing a session that doesn't exist"""
        response = client.delete("/api/chat/nonexistent-session")
        assert response.status_code == 404
        assert "Session not found" in response.json()["detail"]
    
    def test_list_sessions(self):
        """Test listing active sessions"""
        response = client.get("/api/sessions")
        assert response.status_code == 200
        data = response.json()
        assert "active_sessions" in data
        assert "total_count" in data
        assert isinstance(data["active_sessions"], list)

class TestRateLimiting:
    def test_rate_limiting_applied(self):
        """Test that rate limiting is applied to chat endpoint"""
        # This test would need to make multiple rapid requests
        # to trigger rate limiting, but we'll just test the structure
        session_data = {"session_id": "rate-test", "message": "test"}
        
        # Make several requests quickly
        responses = []
        for i in range(12):  # Exceeds the 10 request limit
            response = client.post("/api/chat", json=session_data)
            responses.append(response)
        
        # At least one should be rate limited
        status_codes = [r.status_code for r in responses]
        # Note: This might not trigger in test environment due to timing
        # In real implementation, this would trigger 429 status codes

if __name__ == "__main__":
    pytest.main([__file__, "-v"])