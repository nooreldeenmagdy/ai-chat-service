#!/bin/bash

# AI Chat Service Startup Script

set -e

echo "🚀 Starting AI Chat Service..."

# Check if .env file exists
if [ ! -f .env ]; then
    echo "❌ .env file not found. Creating from template..."
    cp .env.example .env
    echo "✅ Please edit .env file with your API keys and restart"
    exit 1
fi

# Check if conda environment exists
echo "🔧 Checking conda environment 'fastenv'..."
if ! conda info --envs | grep -q fastenv; then
    echo "🔧 Creating conda environment 'fastenv'..."
    conda create -n fastenv python=3.11 -y
fi

# Activate conda environment
echo "🔧 Activating conda environment 'fastenv'..."
source $(conda info --base)/etc/profile.d/conda.sh
conda activate fastenv

# Install dependencies
echo "📦 Installing dependencies..."
pip install -r requirements.txt

# Check if FAQ file exists
if [ ! -f "faq.json" ]; then
    echo "❌ faq.json file not found. Please ensure it exists in the project root."
    exit 1
fi

# Start FastAPI server in background
echo "🌐 Starting FastAPI server..."
uvicorn src.main:app --host 0.0.0.0 --port 8000 &
FASTAPI_PID=$!

# Wait for FastAPI to start
sleep 3

# Start Streamlit app
echo "🎨 Starting Streamlit interface..."
streamlit run streamlit_app/app.py --server.port 8501 &
STREAMLIT_PID=$!

echo ""
echo "✅ Services started successfully!"
echo "📡 FastAPI API: http://localhost:8000"
echo "📖 API Docs: http://localhost:8000/docs"  
echo "🎨 Streamlit UI: http://localhost:8501"
echo "❤️ Health Check: http://localhost:8000/api/health"
echo ""
echo "Press Ctrl+C to stop all services"

# Function to cleanup processes
cleanup() {
    echo ""
    echo "🛑 Stopping services..."
    kill $FASTAPI_PID 2>/dev/null || true
    kill $STREAMLIT_PID 2>/dev/null || true
    echo "✅ Services stopped"
    exit 0
}

# Trap interrupt signal
trap cleanup INT

# Wait for both processes
wait
