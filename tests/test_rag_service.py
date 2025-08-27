import pytest
import json
import tempfile
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
from src.services.openai_service import RAGService, OpenAIService, AIServiceError
from src.models.chat_models import FAQ, ChatRequest, ChatResponse, ChatSession

class TestRAGService:
    """Test cases for the RAG (Retrieval-Augmented Generation) service"""
    
    def setup_method(self):
        """Set up test fixtures before each test"""
        # Create a temporary FAQ file for testing
        self.test_faqs = {
            "faqs": [
                {
                    "id": 1,
                    "question": "What is artificial intelligence?",
                    "answer": "AI is computer systems that perform human-like tasks."
                },
                {
                    "id": 2,
                    "question": "How does machine learning work?",
                    "answer": "ML uses algorithms to learn patterns from data."
                },
                {
                    "id": 3,
                    "question": "What are neural networks?",
                    "answer": "Neural networks are computing systems inspired by biological neurons."
                }
            ]
        }
        
        # Create temporary file
        self.temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False)
        json.dump(self.test_faqs, self.temp_file)
        self.temp_file.close()
        
        # Initialize RAG service with test data
        self.rag_service = RAGService(self.temp_file.name)
    
    def teardown_method(self):
        """Clean up after each test"""
        import os
        os.unlink(self.temp_file.name)
    
    def test_load_faqs_success(self):
        """Test successful loading of FAQ data"""
        assert len(self.rag_service.faqs) == 3
        assert self.rag_service.faqs[0].question == "What is artificial intelligence?"
        assert self.rag_service.faqs[1].id == 2
    
    def test_load_faqs_file_not_found(self):
        """Test error handling when FAQ file doesn't exist"""
        with pytest.raises(AIServiceError, match="FAQ file .* not found"):
            RAGService("nonexistent_file.json")
    
    def test_load_faqs_invalid_json(self):
        """Test error handling for invalid JSON"""
        # Create invalid JSON file
        invalid_file = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False)
        invalid_file.write("invalid json content")
        invalid_file.close()
        
        try:
            with pytest.raises(AIServiceError, match="Error loading FAQs"):
                RAGService(invalid_file.name)
        finally:
            import os
            os.unlink(invalid_file.name)
    
    def test_build_embeddings(self):
        """Test TF-IDF embedding creation"""
        assert self.rag_service.vectorizer is not None
        assert self.rag_service.faq_vectors is not None
        assert self.rag_service.faq_vectors.shape[0] == 3  # 3 FAQs
    
    def test_find_relevant_faqs_exact_match(self):
        """Test finding FAQs with exact question match"""
        relevant_faqs = self.rag_service.find_relevant_faqs("What is artificial intelligence?", top_k=2)
        
        assert len(relevant_faqs) > 0
        assert relevant_faqs[0].question == "What is artificial intelligence?"
    
    def test_find_relevant_faqs_partial_match(self):
        """Test finding FAQs with partial/semantic match"""
        relevant_faqs = self.rag_service.find_relevant_faqs("machine learning algorithms", top_k=2)
        
        assert len(relevant_faqs) > 0
        # Should find the machine learning FAQ
        ml_faq_found = any("machine learning" in faq.question.lower() for faq in relevant_faqs)
        assert ml_faq_found
    
    def test_find_relevant_faqs_low_similarity(self):
        """Test filtering out low similarity results"""
        # Query with very different content should return fewer results
        relevant_faqs = self.rag_service.find_relevant_faqs("cooking recipes pasta", top_k=5)
        
        # Should return empty or very few results due to low similarity threshold
        assert len(relevant_faqs) <= 1
    
    def test_find_relevant_faqs_empty_query(self):
        """Test handling of empty query"""
        relevant_faqs = self.rag_service.find_relevant_faqs("", top_k=2)
        assert len(relevant_faqs) == 0
    
    def test_find_relevant_faqs_top_k_limit(self):
        """Test that top_k parameter limits results"""
        relevant_faqs = self.rag_service.find_relevant_faqs("intelligence learning", top_k=1)
        assert len(relevant_faqs) <= 1
        
        relevant_faqs = self.rag_service.find_relevant_faqs("intelligence learning", top_k=2)
        assert len(relevant_faqs) <= 2
    
    def test_find_relevant_faqs_no_vectorizer(self):
        """Test behavior when vectorizer is not initialized"""
        # Create RAG service with no FAQs
        empty_faqs = {"faqs": []}
        empty_file = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False)
        json.dump(empty_faqs, empty_file)
        empty_file.close()
        
        try:
            empty_rag = RAGService(empty_file.name)
            relevant_faqs = empty_rag.find_relevant_faqs("test query", top_k=2)
            assert len(relevant_faqs) == 0
        finally:
            import os
            os.unlink(empty_file.name)


class TestOpenAIService:
    """Test cases for the OpenAI service"""
    
    def setup_method(self):
        """Set up test fixtures before each test"""
        # Create mock FAQ file
        self.test_faqs = {
            "faqs": [
                {
                    "id": 1,
                    "question": "What is AI?",
                    "answer": "AI is artificial intelligence."
                }
            ]
        }
        
        self.temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False)
        json.dump(self.test_faqs, self.temp_file)
        self.temp_file.close()
    
    def teardown_method(self):
        """Clean up after each test"""
        import os
        os.unlink(self.temp_file.name)
    
    @patch.dict('os.environ', {
        'PROVIDER': 'openai',
        'MODEL_NAME': 'gpt-4o',
        'OPENAI_API_KEY': 'test-key-123'
    })
    @patch('src.services.openai_service.OpenAI')
    @patch('src.services.openai_service.RAGService')
    def test_initialization_openai(self, mock_rag, mock_openai):
        """Test OpenAI service initialization with OpenAI provider"""
        mock_rag.return_value = Mock()
        mock_openai.return_value = Mock()
        
        service = OpenAIService()
        
        assert service.provider == 'openai'
        assert service.model == 'gpt-4o'
        mock_openai.assert_called_once_with(api_key='test-key-123')
    
    @patch.dict('os.environ', {
        'PROVIDER': 'azure',
        'MODEL_NAME': 'gpt-4',
        'AZURE_OPENAI_API_KEY': 'azure-key-123',
        'AZURE_OPENAI_ENDPOINT': 'https://test.openai.azure.com/'
    })
    @patch('src.services.openai_service.AzureOpenAI')
    @patch('src.services.openai_service.RAGService')
    def test_initialization_azure(self, mock_rag, mock_azure):
        """Test OpenAI service initialization with Azure provider"""
        mock_rag.return_value = Mock()
        mock_azure.return_value = Mock()
        
        service = OpenAIService()
        
        assert service.provider == 'azure'
        assert service.model == 'gpt-4'
        mock_azure.assert_called_once()
    
    @patch.dict('os.environ', {'PROVIDER': 'openai'}, clear=True)
    @patch('src.services.openai_service.RAGService')
    def test_initialization_missing_api_key(self, mock_rag):
        """Test error handling when API key is missing"""
        mock_rag.return_value = Mock()
        
        with pytest.raises(AIServiceError, match="OpenAI API key not provided"):
            OpenAIService()
    
    @patch.dict('os.environ', {
        'PROVIDER': 'openai',
        'OPENAI_API_KEY': 'test-key-123'
    })
    @patch('src.services.openai_service.OpenAI')
    @patch('src.services.openai_service.RAGService')
    def test_get_or_create_session_new(self, mock_rag, mock_openai):
        """Test creating a new chat session"""
        mock_rag.return_value = Mock()
        mock_openai.return_value = Mock()
        
        service = OpenAIService()
        session = service.get_or_create_session("test-session-123")
        
        assert session.session_id == "test-session-123"
        assert len(session.messages) == 0
        assert "test-session-123" in service.sessions
    
    @patch.dict('os.environ', {
        'PROVIDER': 'openai',
        'OPENAI_API_KEY': 'test-key-123'
    })
    @patch('src.services.openai_service.OpenAI')
    @patch('src.services.openai_service.RAGService')
    def test_get_or_create_session_existing(self, mock_rag, mock_openai):
        """Test retrieving an existing chat session"""
        mock_rag.return_value = Mock()
        mock_openai.return_value = Mock()
        
        service = OpenAIService()
        
        # Create first session
        session1 = service.get_or_create_session("test-session-123")
        session1.messages.append(Mock(role="user", content="test message"))
        
        # Get same session again
        session2 = service.get_or_create_session("test-session-123")
        
        assert session1 is session2
        assert len(session2.messages) == 1
    
    @patch.dict('os.environ', {
        'PROVIDER': 'openai',
        'OPENAI_API_KEY': 'test-key-123'
    })
    @patch('src.services.openai_service.OpenAI')
    @patch('src.services.openai_service.RAGService')
    def test_clear_session_success(self, mock_rag, mock_openai):
        """Test successfully clearing a session"""
        mock_rag.return_value = Mock()
        mock_openai.return_value = Mock()
        
        service = OpenAIService()
        
        # Create session
        service.get_or_create_session("test-session-123")
        assert "test-session-123" in service.sessions
        
        # Clear session
        result = service.clear_session("test-session-123")
        
        assert result is True
        assert "test-session-123" not in service.sessions
    
    @patch.dict('os.environ', {
        'PROVIDER': 'openai',
        'OPENAI_API_KEY': 'test-key-123'
    })
    @patch('src.services.openai_service.OpenAI')
    @patch('src.services.openai_service.RAGService')
    def test_clear_session_not_found(self, mock_rag, mock_openai):
        """Test clearing a non-existent session"""
        mock_rag.return_value = Mock()
        mock_openai.return_value = Mock()
        
        service = OpenAIService()
        result = service.clear_session("nonexistent-session")
        
        assert result is False
    
    @patch.dict('os.environ', {
        'PROVIDER': 'openai',
        'OPENAI_API_KEY': 'test-key-123'
    })
    @patch('src.services.openai_service.OpenAI')
    @patch('src.services.openai_service.RAGService')
    def test_build_context_prompt_no_faqs(self, mock_rag, mock_openai):
        """Test building context prompt with no relevant FAQs"""
        mock_rag.return_value = Mock()
        mock_openai.return_value = Mock()
        
        service = OpenAIService()
        result = service._build_context_prompt("Test message", [])
        
        assert result == "Test message"
    
    @patch.dict('os.environ', {
        'PROVIDER': 'openai',
        'OPENAI_API_KEY': 'test-key-123'
    })
    @patch('src.services.openai_service.OpenAI')
    @patch('src.services.openai_service.RAGService')
    def test_build_context_prompt_with_faqs(self, mock_rag, mock_openai):
        """Test building context prompt with relevant FAQs"""
        mock_rag.return_value = Mock()
        mock_openai.return_value = Mock()
        
        service = OpenAIService()
        
        # Create mock FAQs
        faq1 = FAQ(id=1, question="What is AI?", answer="AI is artificial intelligence.")
        faq2 = FAQ(id=2, question="How does ML work?", answer="ML learns from data.")
        
        result = service._build_context_prompt("Tell me about AI", [faq1, faq2])
        
        assert "Here's some relevant information from our FAQ:" in result
        assert "What is AI?" in result
        assert "AI is artificial intelligence." in result
        assert "How does ML work?" in result
        assert "Tell me about AI" in result
    
    @patch.dict('os.environ', {
        'PROVIDER': 'openai',
        'OPENAI_API_KEY': 'test-key-123'
    })
    @patch('src.services.openai_service.OpenAI')
    @patch('src.services.openai_service.RAGService')
    def test_get_health_status(self, mock_rag, mock_openai):
        """Test getting health status"""
        mock_rag.return_value = Mock()
        mock_openai.return_value = Mock()
        
        service = OpenAIService()
        health = service.get_health_status()
        assert health.status == "healthy"
        assert health.provider == "openai"
        assert health.uptime_seconds >= 0

    @pytest.mark.asyncio
    @patch.dict('os.environ', {
        'PROVIDER': 'openai',
        'OPENAI_API_KEY': 'test-key-123'
    })
    @patch('src.services.openai_service.OpenAI')
    @patch('src.services.openai_service.RAGService')
    @patch('asyncio.to_thread')
    async def test_send_message_success(self, mock_to_thread, mock_rag, mock_openai):
        """Test successful message sending"""
        # Mock RAG service
        mock_rag_instance = Mock()
        mock_rag_instance.find_relevant_faqs.return_value = []
        mock_rag.return_value = mock_rag_instance
        
        # Mock OpenAI client
        mock_client = Mock()
        mock_openai.return_value = mock_client
        
        # Mock API response
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "This is a test response"
        mock_response.usage.prompt_tokens = 50
        mock_response.usage.completion_tokens = 30
        mock_response.usage.total_tokens = 80
        
        mock_to_thread.return_value = mock_response
        
        service = OpenAIService()
        request = ChatRequest(
            session_id="test-session",
            message="What is AI?",
            context=None
        )
        response = await service.send_message(request)
        assert isinstance(response, ChatResponse)
        assert response.response == "This is a test response"
        assert response.session_id == "test-session"
        assert response.token_usage["total_tokens"] == 80
        assert response.latency_ms >= 0  # In mocked tests, latency might be 0

    @pytest.mark.asyncio
    @patch.dict('os.environ', {
        'PROVIDER': 'openai',
        'OPENAI_API_KEY': 'test-key-123'
    })
    @patch('src.services.openai_service.OpenAI')
    @patch('src.services.openai_service.RAGService')
    @patch('asyncio.to_thread')
    async def test_send_message_with_relevant_faqs(self, mock_to_thread, mock_rag, mock_openai):
        """Test message sending with relevant FAQs"""
        # Mock RAG service with relevant FAQs
        mock_rag_instance = Mock()
        faq = FAQ(id=1, question="What is AI?", answer="AI is artificial intelligence.")
        mock_rag_instance.find_relevant_faqs.return_value = [faq]
        mock_rag.return_value = mock_rag_instance
        
        # Mock OpenAI client
        mock_client = Mock()
        mock_openai.return_value = mock_client
        
        # Mock API response
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "AI response with context"
        mock_response.usage.prompt_tokens = 100
        mock_response.usage.completion_tokens = 50
        mock_response.usage.total_tokens = 150
        
        mock_to_thread.return_value = mock_response
        
        service = OpenAIService()
        request = ChatRequest(
            session_id="test-session",
            message="What is AI?",
            context=None
        )
        
        response = await service.send_message(request)
        assert response.relevant_faqs is not None
        assert len(response.relevant_faqs) == 1
        assert "What is AI?" in response.relevant_faqs[0]

    @pytest.mark.asyncio
    @patch.dict('os.environ', {
        'PROVIDER': 'openai',
        'OPENAI_API_KEY': 'test-key-123'
    })
    @patch('src.services.openai_service.OpenAI')
    @patch('src.services.openai_service.RAGService')
    @patch('asyncio.to_thread')
    async def test_send_message_api_error(self, mock_to_thread, mock_rag, mock_openai):
        """Test error handling when API call fails"""
        mock_rag.return_value = Mock()
        mock_rag.return_value.find_relevant_faqs.return_value = []
        mock_openai.return_value = Mock()
        
        # Mock API error
        mock_to_thread.side_effect = Exception("API error occurred")
        
        service = OpenAIService()
        request = ChatRequest(
            session_id="test-session",
            message="What is AI?",
            context=None
        )
        
        with pytest.raises(AIServiceError, match="Error processing chat request"):
            await service.send_message(request)
