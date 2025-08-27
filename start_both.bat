@echo off
echo Starting AI Chat Service...
echo.

cd /d "d:\PF2\ai_chat_service\ai-chat-service"

echo Loading environment variables...
set PYTHONPATH=%cd%

REM Start FastAPI server in background
echo Starting FastAPI server on port 8000...
start "FastAPI Server" python -m uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload

REM Wait a bit for FastAPI to start
timeout /t 3 /nobreak > nul

REM Start Streamlit app
echo Starting Streamlit app on port 8501...
start "Streamlit App" python -m streamlit run streamlit_app\app.py --server.port 8501

echo.
echo ✅ Both services started!
echo FastAPI: http://localhost:8000
echo Streamlit: http://localhost:8501
echo.
echo Press any key to exit...
pause > nul
