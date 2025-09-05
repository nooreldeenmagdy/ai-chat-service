import pytest
import json
from unittest.mock import Mock, patch, AsyncMock
from fastapi.testclient import TestClient
from fastapi import status
from datetime import datetime

from src.main import app
from src.services.sql_chatbot_service import sql_chatbot_service, SqlChatbotService
from src.models.chat_models import SqlQueryRequest, SqlQueryResponse

class TestSqlChatbotService:
    """Test cases for the SQL Chatbot Service"""
    
    def setup_method(self):
        """Set up test fixtures before each test"""
        self.service = SqlChatbotService()
        self.client = TestClient(app)
        
        # Sample test request
        self.test_request = SqlQueryRequest(
            session_id="sql-test-session",
            message="Show me all products with low stock levels",
            context={"database": "inventory", "user_role": "analyst"}
        )
    
    def teardown_method(self):
        """Clean up after each test"""
        # Clear any test sessions
        self.service.sessions.clear()
    
    def test_database_schema_loading(self):
        """Test database schema is properly loaded"""
        schema = self.service.database_schema
        
        assert schema is not None
        assert len(schema.tables) == 6  # products, categories, suppliers, orders, order_items, customers
        
        # Check for key tables
        table_names = [table.name for table in schema.tables]
        assert "products" in table_names
        assert "orders" in table_names
        assert "customers" in table_names
        
        # Check relationships exist
        assert len(schema.relationships) > 0
    
    def test_get_schema_context(self):
        """Test schema context generation for LLM"""
        context = self.service._get_schema_context()
        
        assert "DATABASE SCHEMA:" in context
        assert "products" in context
        assert "orders" in context
        assert "RELATIONSHIPS:" in context
        assert isinstance(context, str)
        assert len(context) > 100  # Should be substantial content
    
    @patch('src.services.sql_chatbot_service.openai_service._call_openai_api')
    async def test_understand_goal_and_select_tables(self, mock_openai_api):
        """Test goal understanding and table selection"""
        # Mock OpenAI response
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = json.dumps({
            "goal": "Find products with stock levels below reorder threshold",
            "relevant_tables": ["products"],
            "reasoning": "Need products table to check stock_quantity and reorder_level"
        })
        mock_openai_api.return_value = mock_response
        
        goal, tables = await self.service._understand_goal_and_select_tables(
            "Show me products with low stock"
        )
        
        assert goal == "Find products with stock levels below reorder threshold"
        assert "products" in tables
        mock_openai_api.assert_called_once()
    
    @patch('src.services.sql_chatbot_service.openai_service._call_openai_api')
    async def test_generate_sql_query_success(self, mock_openai_api):
        """Test successful SQL query generation"""
        # Mock OpenAI response
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = """
        SELECT product_name, stock_quantity, reorder_level 
        FROM products 
        WHERE stock_quantity < reorder_level 
        ORDER BY stock_quantity ASC;
        """
        mock_openai_api.return_value = mock_response
        
        sql_query, is_valid = await self.service._generate_sql_query(
            "Find products with low stock",
            ["products"],
            "Show me products with low stock"
        )
        
        assert sql_query.strip().startswith("SELECT")
        assert "products" in sql_query.lower()
        assert is_valid == True
        mock_openai_api.assert_called_once()
    
    def test_validate_sql_query_valid(self):
        """Test SQL query validation with valid query"""
        valid_sql = "SELECT product_name, stock_quantity FROM products WHERE stock_quantity < 50"
        is_valid = self.service._validate_sql_query(valid_sql, ["products"])
        
        assert is_valid == True
    
    def test_validate_sql_query_invalid_dangerous(self):
        """Test SQL query validation rejects dangerous operations"""
        dangerous_queries = [
            "DROP TABLE products;",
            "DELETE FROM products WHERE id = 1;",
            "UPDATE products SET price = 0;",
            "INSERT INTO products VALUES (1, 'hack');",
            "ALTER TABLE products ADD COLUMN hack TEXT;"
        ]
        
        for query in dangerous_queries:
            is_valid = self.service._validate_sql_query(query, ["products"])
            assert is_valid == False, f"Should reject dangerous query: {query}"
    
    def test_validate_sql_query_invalid_structure(self):
        """Test SQL query validation rejects malformed queries"""
        invalid_queries = [
            "INVALID SQL QUERY",
            "products WHERE stock_quantity < 50",  # Missing SELECT
            ""  # Empty query
        ]
        
        for query in invalid_queries:
            is_valid = self.service._validate_sql_query(query, ["products"])
            assert is_valid == False, f"Should reject invalid query: {query}"
    
    @patch('src.services.sql_chatbot_service.openai_service._call_openai_api')
    async def test_explain_query_results(self, mock_openai_api):
        """Test natural language explanation generation"""
        # Mock OpenAI response
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "This query finds all products that need to be reordered by checking where current stock is below the reorder level."
        mock_openai_api.return_value = mock_response
        
        explanation = await self.service._explain_query_results(
            "Show me products with low stock",
            "SELECT * FROM products WHERE stock_quantity < reorder_level",
            "Find products needing reorder"
        )
        
        assert len(explanation) > 10
        assert "reorder" in explanation.lower()
        mock_openai_api.assert_called_once()
    
    @patch('src.services.sql_chatbot_service.openai_service._call_openai_api')
    async def test_process_sql_query_complete_flow(self, mock_openai_api):
        """Test complete SQL query processing flow"""
        # Mock responses for the three LLM calls
        mock_responses = [
            # Goal understanding response
            Mock(),
            # SQL generation response  
            Mock(),
            # Explanation response
            Mock()
        ]
        
        # Configure goal understanding mock
        mock_responses[0].choices = [Mock()]
        mock_responses[0].choices[0].message.content = json.dumps({
            "goal": "Find products with low stock levels",
            "relevant_tables": ["products"],
            "reasoning": "Need products table for inventory data"
        })
        
        # Configure SQL generation mock
        mock_responses[1].choices = [Mock()]
        mock_responses[1].choices[0].message.content = """
        SELECT product_name, stock_quantity 
        FROM products 
        WHERE stock_quantity < reorder_level 
        ORDER BY stock_quantity ASC;
        """
        
        # Configure explanation mock
        mock_responses[2].choices = [Mock()]
        mock_responses[2].choices[0].message.content = "This query identifies products that need restocking by comparing current stock levels to reorder thresholds."
        
        mock_openai_api.side_effect = mock_responses
        
        # Process the request
        response = await self.service.process_sql_query(self.test_request)
        
        assert isinstance(response, SqlQueryResponse)
        assert response.session_id == "sql-test-session"
        assert "restock" in response.natural_language_answer.lower()
        assert response.sql_query.strip().startswith("SELECT")
        assert "products" in response.table_info
        assert response.validation_attempts == 1
        assert response.latency_ms > 0
        
        # Verify session was stored
        assert "sql-test-session" in self.service.sessions
    
    @patch('src.services.sql_chatbot_service.openai_service._call_openai_api')
    async def test_process_sql_query_with_retries(self, mock_openai_api):
        """Test SQL query processing with retry mechanism"""
        # Mock responses where first two SQL generations fail validation
        mock_responses = [
            # Goal understanding (successful)
            Mock(),
            # SQL generation attempt 1 (invalid)
            Mock(), 
            # SQL generation attempt 2 (invalid)
            Mock(),
            # SQL generation attempt 3 (valid)
            Mock(),
            # Explanation
            Mock()
        ]
        
        # Configure goal understanding mock
        mock_responses[0].choices = [Mock()]
        mock_responses[0].choices[0].message.content = json.dumps({
            "goal": "Find products",
            "relevant_tables": ["products"],
            "reasoning": "Need products table"
        })
        
        # Configure invalid SQL attempts
        for i in [1, 2]:
            mock_responses[i].choices = [Mock()]
            mock_responses[i].choices[0].message.content = "INVALID SQL QUERY"
        
        # Configure valid SQL attempt
        mock_responses[3].choices = [Mock()]
        mock_responses[3].choices[0].message.content = "SELECT product_name FROM products;"
        
        # Configure explanation mock
        mock_responses[4].choices = [Mock()]
        mock_responses[4].choices[0].message.content = "This query lists all product names."
        
        mock_openai_api.side_effect = mock_responses
        
        # Process the request
        response = await self.service.process_sql_query(self.test_request)
        
        assert response.validation_attempts == 3  # Should have made 3 attempts
        assert response.sql_query.strip() == "SELECT product_name FROM products;"
    
    def test_session_management(self):
        """Test session creation and management"""
        # Initially no sessions
        assert len(self.service.sessions) == 0
        
        # Create session by processing query (mocked)
        session_id = "test-session-123"
        self.service.sessions[session_id] = [
            {"role": "user", "content": "test message", "timestamp": datetime.now()}
        ]
        
        # Test session exists
        assert session_id in self.service.sessions
        history = self.service.get_session_history(session_id)
        assert len(history) == 1
        
        # Test clear session
        success = self.service.clear_session(session_id)
        assert success == True
        assert session_id not in self.service.sessions
        
        # Test clear non-existent session
        success = self.service.clear_session("non-existent")
        assert success == False
    
    @patch('src.services.sql_chatbot_service.openai_service._call_openai_api')
    async def test_error_handling(self, mock_openai_api):
        """Test error handling in SQL processing"""
        # Mock OpenAI API to raise an exception
        mock_openai_api.side_effect = Exception("API Error")
        
        response = await self.service.process_sql_query(self.test_request)
        
        assert isinstance(response, SqlQueryResponse)
        assert "error" in response.natural_language_answer.lower()
        assert response.sql_query == "-- Error generating SQL query"
        assert response.latency_ms > 0

class TestSqlChatAPI:
    """Test cases for the SQL Chat API endpoints"""
    
    def setup_method(self):
        """Set up test fixtures before each test"""
        self.client = TestClient(app)
    
    @patch('src.services.sql_chatbot_service.sql_chatbot_service.process_sql_query')
    async def test_sql_chat_endpoint_success(self, mock_process_sql):
        """Test successful SQL chat API call"""
        # Mock service response
        mock_response = SqlQueryResponse(
            natural_language_answer="This query finds products with stock below 50 units.",
            sql_query="SELECT product_name, stock_quantity FROM products WHERE stock_quantity < 50;",
            session_id="sql-test-session",
            query_results=None,
            table_info=["products"],
            validation_attempts=1,
            latency_ms=850.3,
            timestamp=datetime.now()
        )
        
        mock_process_sql.return_value = mock_response
        
        # Make API request
        response = self.client.post(
            "/api/sql-chat",
            json={
                "session_id": "sql-test-session",
                "message": "Show me products with low stock",
                "context": {"database": "inventory"}
            }
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert data["session_id"] == "sql-test-session"
        assert "stock below 50 units" in data["natural_language_answer"]
        assert "SELECT" in data["sql_query"]
        assert "products" in data["table_info"]
        assert data["validation_attempts"] == 1
        assert data["latency_ms"] == 850.3
    
    def test_sql_chat_endpoint_empty_message(self):
        """Test SQL chat API with empty message"""
        response = self.client.post(
            "/api/sql-chat",
            json={
                "session_id": "sql-test-session",
                "message": ""
            }
        )
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Message cannot be empty" in response.json()["detail"]
    
    def test_sql_chat_endpoint_message_too_long(self):
        """Test SQL chat API with message exceeding length limit"""
        long_message = "x" * 2001  # Exceeds 2000 character limit
        
        response = self.client.post(
            "/api/sql-chat",
            json={
                "session_id": "sql-test-session",
                "message": long_message
            }
        )
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Message too long" in response.json()["detail"]
    
    @patch('src.services.sql_chatbot_service.sql_chatbot_service.process_sql_query')
    async def test_sql_chat_endpoint_service_error(self, mock_process_sql):
        """Test SQL chat API handling of service errors"""
        mock_process_sql.side_effect = Exception("SQL service error")
        
        response = self.client.post(
            "/api/sql-chat",
            json={
                "session_id": "sql-test-session",
                "message": "Show me all products"
            }
        )
        
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert "Error processing SQL query" in response.json()["detail"]

class TestDualModeChatAPI:
    """Test cases for the Dual-Mode Chat API endpoints"""
    
    def setup_method(self):
        """Set up test fixtures before each test"""
        self.client = TestClient(app)
    
    @patch('src.services.openai_service.openai_service.send_message')
    async def test_dual_mode_chat_rag_mode(self, mock_send_message):
        """Test dual-mode chat API in RAG mode"""
        from src.models.chat_models import ChatResponse
        
        # Mock RAG service response
        mock_response = ChatResponse(
            response="Artificial Intelligence is the simulation of human intelligence in machines.",
            session_id="dual-test-session",
            latency_ms=1200.0,
            token_usage={"prompt_tokens": 25, "completion_tokens": 35, "total_tokens": 60},
            relevant_faqs=["What is AI?", "How does AI work?"],
            timestamp=datetime.now()
        )
        
        mock_send_message.return_value = mock_response
        
        # Make API request in RAG mode
        response = self.client.post(
            "/api/dual-mode-chat",
            json={
                "session_id": "dual-test-session",
                "message": "What is artificial intelligence?",
                "mode": "rag"
            }
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert data["mode"] == "rag"
        assert data["session_id"] == "dual-test-session"
        assert "Artificial Intelligence" in data["response"]
        assert data["relevant_faqs"] is not None
        assert data["sql_query"] is None
        assert data["table_info"] is None
    
    @patch('src.services.sql_chatbot_service.sql_chatbot_service.process_sql_query')
    async def test_dual_mode_chat_sql_mode(self, mock_process_sql):
        """Test dual-mode chat API in SQL mode"""
        # Mock SQL service response
        mock_response = SqlQueryResponse(
            natural_language_answer="Here are the products with low stock levels.",
            sql_query="SELECT product_name FROM products WHERE stock_quantity < 50;",
            session_id="dual-test-session",
            query_results=None,
            table_info=["products"],
            validation_attempts=1,
            latency_ms=950.2,
            timestamp=datetime.now()
        )
        
        mock_process_sql.return_value = mock_response
        
        # Make API request in SQL mode
        response = self.client.post(
            "/api/dual-mode-chat",
            json={
                "session_id": "dual-test-session",
                "message": "Show me products with low stock",
                "mode": "sql"
            }
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert data["mode"] == "sql"
        assert data["session_id"] == "dual-test-session"
        assert "low stock" in data["response"]
        assert data["sql_query"] is not None
        assert data["table_info"] == ["products"]
        assert data["relevant_faqs"] is None
    
    def test_dual_mode_chat_invalid_mode(self):
        """Test dual-mode chat API with invalid mode"""
        response = self.client.post(
            "/api/dual-mode-chat",
            json={
                "session_id": "dual-test-session",
                "message": "Test message",
                "mode": "invalid_mode"
            }
        )
        
        # Should return validation error due to Literal type constraint
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    def test_dual_mode_chat_missing_message(self):
        """Test dual-mode chat API with missing message"""
        response = self.client.post(
            "/api/dual-mode-chat",
            json={
                "session_id": "dual-test-session",
                "mode": "rag"
            }
        )
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
