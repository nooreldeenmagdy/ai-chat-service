# 🔧 Troubleshooting OpenAI Client Issues

## Error: `__init__() got an unexpected keyword argument 'proxies'`

This error typically occurs when:
1. There are environment variables that the OpenAI library is trying to use automatically
2. The OpenAI library version has compatibility issues
3. There are conflicting configurations

## 🚀 Quick Fix Steps

### Step 1: Check and Clear Environment Variables
```cmd
# Check for any proxy-related environment variables
set | findstr -i proxy

# If you see any proxy variables, clear them completely:
set HTTP_PROXY=
set HTTPS_PROXY=
set http_proxy=
set https_proxy=
set ALL_PROXY=
set all_proxy=
```

### Step 2: Complete OpenAI Reinstallation
```cmd
conda activate fastenv
pip uninstall openai -y
pip cache purge
pip install openai --upgrade
```

### Step 3: Test OpenAI Setup
```cmd
conda activate fastenv
python test_openai.py
```

### Step 4: If Test Passes, Run the Application
```cmd
conda activate fastenv
uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload
```

## 🔍 Alternative Solutions

### Solution 1: Update .env file
Make sure your `.env` file only contains necessary variables:
```env
PROVIDER=openai
MODEL_NAME=gpt-4o
OPENAI_API_KEY=your_openai_api_key_here
FASTAPI_PORT=8000
STREAMLIT_PORT=8501
LOG_LEVEL=INFO
```

### Solution 2: Clean Installation
```cmd
# Remove conda environment and recreate
conda deactivate
conda env remove -n fastenv -y
conda create -n fastenv python=3.11 -y
conda activate fastenv
pip install -r requirements.txt
```

### Solution 3: Test Different OpenAI Versions
```cmd
conda activate fastenv

# Try latest version
pip install openai --upgrade

# Or try a specific stable version
pip install openai==1.10.0
```

## 🧪 Debug Commands

### Check Python and Package Versions
```cmd
conda activate fastenv
python --version
pip list | findstr openai
pip list | findstr fastapi
pip list | findstr pydantic
```

### Test Minimal OpenAI Setup
```cmd
conda activate fastenv
python -c "
import sys
print('Python version:', sys.version)

try:
    import openai
    print('OpenAI import: SUCCESS')
    print('OpenAI version:', openai.__version__)
    
    client = openai.OpenAI(api_key='test-key')
    print('OpenAI client creation: SUCCESS')
except Exception as e:
    print('Error:', type(e).__name__, str(e))
"
```

## 📋 If All Else Fails

### Manual Environment Setup
```cmd
conda activate fastenv

# Install packages one by one
pip install fastapi==0.104.1
pip install streamlit==1.28.1
pip install openai==1.12.0
pip install uvicorn[standard]==0.24.0
pip install pydantic==2.5.0
pip install python-dotenv==1.0.0
pip install numpy==1.24.3
pip install scikit-learn==1.3.2

# Test each installation
python -c "import fastapi; print('FastAPI OK')"
python -c "import streamlit; print('Streamlit OK')"
python -c "import openai; print('OpenAI OK')"
```

## 🎯 Expected Output After Fix
When everything works correctly, you should see:
```
INFO:src.services.openai_service:Initializing OpenAI client
INFO:src.services.openai_service:OpenAI service initialized with provider: openai, model: gpt-4o
```

Run these steps in order, and the OpenAI client initialization error should be resolved!
