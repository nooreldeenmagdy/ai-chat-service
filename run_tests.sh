#!/bin/bash
# Test runner script for Unix/Linux

echo "🧪 Running AI Chat Service Tests..."
echo

# Check if pytest is installed
if ! python -m pytest --version >/dev/null 2>&1; then
    echo "❌ pytest not found. Installing test dependencies..."
    pip install pytest pytest-asyncio pytest-mock
    echo
fi

echo "🔧 Running Unit Tests for RAG Service..."
python -m pytest tests/test_rag_service.py -v -m "not slow"
echo

echo "🔧 Running Unit Tests for Chat API..."
python -m pytest tests/test_chat_api.py -v -m "not slow"
echo

echo "🔧 Running All Tests..."
python -m pytest tests/ -v --tb=short
echo

echo "✅ Test execution completed!"
