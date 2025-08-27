# Quick Setup Guide with Conda Environment

## 📋 Prerequisites
- Conda (Anaconda or Miniconda) installed
- Git (optional, for cloning)

## 🚀 Quick Start Steps

### 1. Navigate to Project Directory
```cmd
cd d:\PF2\ai_chat_service\ai-chat-service
```

### 2. Create and Activate Conda Environment
```cmd
conda create -n fastenv python=3.11 -y
conda activate fastenv
```

### 3. Install Dependencies
```cmd
pip install -r requirements.txt
```

### 4. Verify Environment Setup
```cmd
conda list | findstr fastapi
conda list | findstr streamlit
conda list | findstr openai
```

### 5. Start the Services

#### Option A: Use the Automated Startup Script (Recommended)
```cmd
start.bat
```

#### Option B: Manual Start (Two separate terminals)
**Terminal 1 - FastAPI (run from project root):**
```cmd
conda activate fastenv
uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload
```

**Terminal 2 - Streamlit (run from project root):**
```cmd
conda activate fastenv
streamlit run streamlit_app/app.py --server.port 8501
```

### 6. Access the Applications
- **Streamlit UI**: http://localhost:8501
- **FastAPI API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/api/health

## 🔧 Conda Environment Management

### List all environments
```cmd
conda env list
```

### Activate the environment
```cmd
conda activate fastenv
```

### Deactivate the environment
```cmd
conda deactivate
```

### Remove the environment (if needed)
```cmd
conda env remove -n fastenv
```

### Export environment for sharing
```cmd
conda activate fastenv
conda env export > environment.yml
```

## 🧪 Testing with Conda

### Run tests
```cmd
conda activate fastenv
pytest tests/ -v
```

### Run specific test
```cmd
conda activate fastenv
pytest tests/test_api.py::TestChatEndpoint -v
```

## 🐛 Troubleshooting

### Issue: "conda: command not found"
**Solution**: Install Anaconda or Miniconda and restart your terminal

### Issue: Environment activation fails
**Solution**: 
```cmd
conda init cmd.exe
# Restart terminal and try again
```

### Issue: Package installation fails
**Solution**:
```cmd
conda activate fastenv
conda install pip -y
pip install -r requirements.txt
```

### Issue: Can't find fastenv environment
**Solution**:
```cmd
# Check if it exists
conda env list
# If not found, create it
conda create -n fastenv python=3.11 -y
```

## 📝 Notes
- The `fastenv` environment name is now used throughout all scripts
- All dependencies are installed via pip within the conda environment
- The startup scripts automatically handle environment creation and activation
- Environment isolation ensures no conflicts with system Python packages
