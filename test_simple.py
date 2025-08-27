#!/usr/bin/env python3
"""
Minimal test to isolate OpenAI client issue
"""
import os

# Test 1: Try importing OpenAI
try:
    print("Testing OpenAI import...")
    from openai import OpenAI
    import openai
    print(f"✅ OpenAI imported successfully, version: {openai.__version__}")
except Exception as e:
    print(f"❌ OpenAI import failed: {e}")
    exit(1)

# Test 2: Check available parameters for OpenAI constructor
try:
    import inspect
    sig = inspect.signature(OpenAI.__init__)
    params = list(sig.parameters.keys())
    print(f"✅ OpenAI constructor parameters: {params}")
    
    if 'proxies' in params:
        print("⚠️  'proxies' parameter is available in constructor")
    else:
        print("ℹ️  'proxies' parameter NOT in constructor parameters")
        
except Exception as e:
    print(f"❌ Could not inspect OpenAI constructor: {e}")

# Test 3: Try creating client with minimal parameters
try:
    print("\nTesting minimal OpenAI client creation...")
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        raise ValueError("OPENAI_API_KEY environment variable is required")
    
    # Method 1: Only api_key
    client = OpenAI(api_key=api_key)
    print("✅ OpenAI client created successfully!")
    
except Exception as e:
    print(f"❌ OpenAI client creation failed: {e}")
    import traceback
    print("Full traceback:")
    traceback.print_exc()
