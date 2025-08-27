#!/usr/bin/env python3
"""
Simple test script to debug OpenAI client initialization issues
Run this to identify the exact problem with OpenAI setup
"""

import os
import sys

def clear_proxy_vars():
    """Clear proxy environment variables"""
    proxy_vars = ['HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy', 'ALL_PROXY', 'all_proxy']
    cleared = []
    for var in proxy_vars:
        if var in os.environ:
            cleared.append(f"{var}={os.environ[var]}")
            del os.environ[var]
    return cleared

def test_openai_import():
    """Test OpenAI library import"""
    try:
        import openai
        print(f"✅ OpenAI import successful - version: {openai.__version__}")
        return True
    except Exception as e:
        print(f"❌ OpenAI import failed: {e}")
        return False

def test_openai_client():
    """Test OpenAI client creation"""
    try:
        from openai import OpenAI
        
        # Set API key from environment variable
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable is required")
        
        print("🔧 Testing OpenAI client creation methods...")
          # Method 1: Using api_key parameter
        try:
            client1 = OpenAI(api_key=api_key)
            print("✅ Method 1 (api_key parameter): SUCCESS")
        except Exception as e:
            print(f"❌ Method 1 (api_key parameter): FAILED - {e}")
            import traceback
            traceback.print_exc()
        
        # Method 2: Using environment variable only
        try:
            client2 = OpenAI()
            print("✅ Method 2 (env variable): SUCCESS")
        except Exception as e:
            print(f"❌ Method 2 (env variable): FAILED - {e}")
        
        # Method 3: Minimal initialization
        try:
            client3 = OpenAI(api_key=api_key, timeout=30)
            print("✅ Method 3 (with timeout): SUCCESS")
        except Exception as e:
            print(f"❌ Method 3 (with timeout): FAILED - {e}")
            
        # Method 4: Check OpenAI constructor signature
        try:
            import inspect
            print("\n🔍 OpenAI constructor signature:")
            sig = inspect.signature(OpenAI.__init__)
            print(f"Parameters: {list(sig.parameters.keys())}")
        except Exception as e:
            print(f"❌ Could not inspect OpenAI constructor: {e}")
            
        return True
        
    except Exception as e:
        print(f"❌ OpenAI client test failed: {e}")
        return False

def main():
    print("🚀 OpenAI Client Debug Test")
    print("=" * 50)
    
    print(f"Python version: {sys.version}")
    print(f"Current directory: {os.getcwd()}")
    
    # Clear proxy variables
    print("\n🔧 Clearing proxy environment variables...")
    cleared = clear_proxy_vars()
    if cleared:
        print(f"Cleared: {cleared}")
    else:
        print("No proxy variables found")
    
    # Test import
    print("\n📦 Testing OpenAI import...")
    if not test_openai_import():
        print("❌ Cannot proceed - OpenAI library not available")
        return
    
    # Test client creation
    print("\n🔗 Testing OpenAI client creation...")
    test_openai_client()
    
    print("\n✅ Test complete!")

if __name__ == "__main__":
    main()
