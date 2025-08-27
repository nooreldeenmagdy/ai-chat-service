# Unit Tests for AI Chat Service

This directory contains comprehensive unit tests for the AI Chat Service, focusing on the retrieval (RAG) system and chat API functionality.

## Test Structure

```
tests/
├── __init__.py                 # Test package initialization
├── test_rag_service.py         # RAG and OpenAI service tests
├── test_chat_api.py            # Chat API endpoint tests
└── README.md                   # This file
```

## Test Coverage

### RAG Service Tests (`test_rag_service.py`)

#### `TestRAGService` - Retrieval-Augmented Generation Testing
- **FAQ Loading**: Tests loading FAQ data from JSON files
- **Error Handling**: Tests file not found and invalid JSON scenarios
- **TF-IDF Embeddings**: Tests vector building and similarity calculations
- **FAQ Retrieval**: Tests finding relevant FAQs with various query types
- **Similarity Filtering**: Tests threshold filtering for low-relevance results
- **Edge Cases**: Empty queries, insufficient data, malformed input

#### `TestOpenAIService` - AI Service Integration Testing
- **Initialization**: Tests OpenAI and Azure OpenAI client setup
- **Session Management**: Tests session creation, retrieval, and clearing
- **Context Building**: Tests prompt enhancement with FAQ context
- **Message Processing**: Tests end-to-end message handling with mocking
- **Health Checks**: Tests service health status reporting
- **Error Handling**: Tests API failures and service errors

### Chat API Tests (`test_chat_api.py`)

#### `TestChatAPI` - REST API Endpoint Testing
- **Successful Requests**: Tests normal chat API operations
- **Input Validation**: Tests empty messages, length limits, required fields
- **Error Responses**: Tests proper HTTP status codes and error messages
- **Rate Limiting**: Tests IP-based rate limiting functionality
- **Authentication**: Tests Bearer token validation when enabled
- **Health Endpoint**: Tests health check API responses
- **Session Management**: Tests session clearing and listing endpoints

#### `TestChatAPIIntegration` - End-to-End Integration Testing
- **RAG Integration**: Tests chat API with actual RAG functionality
- **Context Enhancement**: Tests FAQ context injection into AI prompts
- **Response Enrichment**: Tests inclusion of relevant FAQ information

## Running Tests

### Quick Start
```bash
# Windows
run_tests.bat

# Linux/Mac
chmod +x run_tests.sh
./run_tests.sh
```

### Manual Execution
```bash
# Install test dependencies
pip install pytest pytest-asyncio pytest-mock

# Run all tests
python -m pytest tests/ -v

# Run specific test file
python -m pytest tests/test_rag_service.py -v
python -m pytest tests/test_chat_api.py -v

# Run tests with coverage
python -m pytest tests/ --cov=src --cov-report=html

# Run only unit tests (exclude slow integration tests)
python -m pytest tests/ -v -m "not slow"
```

## Test Configuration

### `pytest.ini`
- Configured test discovery patterns
- Verbose output by default
- Custom test markers for categorization
- Warning filters for clean output

### Environment Variables for Testing
Tests use mocking to avoid requiring actual API keys, but you can set these for integration testing:
```bash
export PROVIDER=openai
export OPENAI_API_KEY=test-key-123
export MODEL_NAME=gpt-4o
```

## Test Features

### Comprehensive Mocking
- **OpenAI API**: All AI service calls are mocked to avoid API costs
- **File System**: FAQ files are created in temporary locations
- **Environment Variables**: Environment is isolated for each test

### Realistic Test Data
- **FAQ Content**: Actual AI-related questions and answers
- **API Responses**: Realistic token usage and response formats
- **Error Scenarios**: Common failure modes and edge cases

### Async Support
- Full support for testing async/await patterns
- Proper mocking of async service calls
- Integration with FastAPI's async request handling

## Test Quality Standards

### Coverage Goals
- **RAG Service**: >95% line coverage
- **Chat API**: >90% line coverage  
- **Error Paths**: All error conditions tested
- **Edge Cases**: Boundary conditions and malformed input

### Test Types
- **Unit Tests**: Individual function/method testing
- **Integration Tests**: Component interaction testing
- **API Tests**: End-to-end HTTP request/response testing
- **Error Tests**: Exception handling and error recovery

## Mock Strategy

### External Dependencies
```python
# OpenAI API calls are mocked
@patch('src.services.openai_service.OpenAI')
def test_openai_integration(mock_openai):
    mock_client = Mock()
    mock_openai.return_value = mock_client
    # Test implementation
```

### File System Operations
```python
# FAQ files are created as temporary files
def setup_method(self):
    self.temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False)
    json.dump(self.test_faqs, self.temp_file)
    self.temp_file.close()
```

### Async Operations
```python
# Async service calls are properly mocked
@patch('asyncio.to_thread')
async def test_async_message(mock_to_thread):
    mock_to_thread.return_value = mock_response
    # Test implementation
```

## Continuous Integration

These tests are designed to run in CI/CD environments:
- No external API dependencies (all mocked)
- Temporary file cleanup
- Deterministic test execution
- Clear success/failure reporting

## Adding New Tests

When adding new functionality, ensure you add corresponding tests:

1. **RAG System Changes**: Add tests to `test_rag_service.py`
2. **API Endpoint Changes**: Add tests to `test_chat_api.py`  
3. **New Features**: Create new test files following naming convention `test_*.py`

### Test Template
```python
import pytest
from unittest.mock import Mock, patch

class TestNewFeature:
    def setup_method(self):
        """Set up test fixtures"""
        pass
    
    def test_basic_functionality(self):
        """Test basic feature operation"""
        assert True  # Replace with actual test
    
    def test_error_handling(self):
        """Test error conditions"""
        with pytest.raises(ExpectedException):
            # Test code that should raise exception
            pass
```

## Troubleshooting

### Common Issues
- **Import Errors**: Ensure `PYTHONPATH` includes project root
- **Async Errors**: Use `pytest-asyncio` for async test support
- **Mock Failures**: Verify patch paths match actual import structure
- **File Cleanup**: Temporary files should be cleaned up in teardown methods

### Debug Mode
```bash
# Run with extra debugging info
python -m pytest tests/ -v -s --tb=long

# Run specific test with pdb debugger
python -m pytest tests/test_rag_service.py::TestRAGService::test_find_relevant_faqs_exact_match -v -s --pdb
```
