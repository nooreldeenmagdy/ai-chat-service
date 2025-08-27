@echo off
REM Test runner script for Windows

echo 🧪 Running AI Chat Service Tests...
echo.

REM Check if pytest is installed
python -m pytest --version >nul 2>&1
if errorlevel 1 (
    echo ❌ pytest not found. Installing test dependencies...
    pip install pytest pytest-asyncio pytest-mock
    echo.
)

echo 🔧 Running Unit Tests for RAG Service...
python -m pytest tests/test_rag_service.py -v -m "not slow"
echo.

echo 🔧 Running Unit Tests for Chat API...
python -m pytest tests/test_chat_api.py -v -m "not slow"
echo.

echo 🔧 Running All Tests...
python -m pytest tests/ -v --tb=short
echo.

echo ✅ Test execution completed!
echo.
pause
