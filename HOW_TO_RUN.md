# 🚀 How to Run the AI Chat Service

## Important: Always run from the project root directory!

### Current Directory Structure
```
ai-chat-service/  ← Run commands from HERE
├── src/
│   ├── main.py
│   ├── api/
│   ├── models/
│   └── services/
├── streamlit_app/
├── requirements.txt
└── start.bat
```

## ✅ Correct Way to Run

### Method 1: Using the Startup Script (Recommended)
```cmd
# Navigate to project root
cd d:\PF2\ai_chat_service\ai-chat-service

# Run the startup script (automatically installs dependencies)
start.bat
```

### Method 2: Manual Commands
```cmd
# Navigate to project root
cd d:\PF2\ai_chat_service\ai-chat-service

# Create and activate conda environment
conda create -n fastenv python=3.11 -y
conda activate fastenv

# Install dependencies
pip install -r requirements.txt

# Start FastAPI (from project root)
uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload

# In another terminal, start Streamlit
conda activate fastenv
streamlit run streamlit_app/app.py --server.port 8501
```

## ❌ Incorrect Ways (These will cause import errors)

### Don't run from src directory:
```cmd
# This will fail with "ModuleNotFoundError: No module named 'src'"
cd d:\PF2\ai_chat_service\ai-chat-service\src
python main.py
```

### Don't use relative imports:
```cmd
# This will fail with import errors
cd d:\PF2\ai_chat_service\ai-chat-service\src
uvicorn main:app --reload
```

## 🔧 Troubleshooting

### If you get "ModuleNotFoundError: No module named 'src'":
1. Make sure you're in the project root directory (`ai-chat-service/`)
2. Use the full module path: `src.main:app`
3. Don't run Python files directly from the src directory

### Check your current directory:
```cmd
# Should show: D:\PF2\ai_chat_service\ai-chat-service
cd

# Should show files like: src/, streamlit_app/, requirements.txt, start.bat
dir
```

### Verify conda environment:
```cmd
# Should show (fastenv) in your prompt
conda activate fastenv

# Should show: fastapi, streamlit, openai, etc.
pip list
```

## 📡 Access URLs
Once running correctly:
- **Streamlit UI**: http://localhost:8501
- **FastAPI Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/api/health
