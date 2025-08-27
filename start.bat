@echo off
REM AI Chat Service Startup Script for Windows

echo 🚀 Starting AI Chat Service...

REM Check if .env file exists
if not exist ".env" (
    echo ❌ .env file not found. Creating from template...
    copy ".env.example" ".env" >nul
    echo ✅ Please edit .env file with your API keys and restart
    pause
    exit /b 1
)

REM Check if conda environment exists
echo 🔧 Checking conda environment 'fastenv'...
conda info --envs | findstr fastenv >nul
if errorlevel 1 (
    echo 🔧 Creating conda environment 'fastenv'...
    conda create -n fastenv python=3.11 -y
)

REM Activate conda environment
echo 🔧 Activating conda environment 'fastenv'...
call conda activate fastenv

REM Install dependencies
echo 📦 Installing dependencies...
pip install -r requirements.txt

REM Check if FAQ file exists
if not exist "faq.json" (
    echo ❌ faq.json file not found. Please ensure it exists in the project root.
    pause
    exit /b 1
)

REM Start FastAPI server
echo 🌐 Starting FastAPI server...
start "FastAPI Server" cmd /k "conda activate fastenv && uvicorn src.main:app --host 0.0.0.0 --port 8000"

REM Wait a moment for FastAPI to start
timeout /t 3 /nobreak >nul

REM Start Streamlit app
echo 🎨 Starting Streamlit interface...
start "Streamlit UI" cmd /k "conda activate fastenv && streamlit run streamlit_app/app.py --server.port 8501"

echo.
echo ✅ Services started successfully!
echo 📡 FastAPI API: http://localhost:8000
echo 📖 API Docs: http://localhost:8000/docs  
echo 🎨 Streamlit UI: http://localhost:8501
echo ❤️ Health Check: http://localhost:8000/api/health
echo.
echo Press any key to continue...
pause >nul
