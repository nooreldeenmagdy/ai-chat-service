import streamlit as st
import requests
import json
import os
import uuid
from datetime import datetime
from typing import Dict, Any
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
BEARER_TOKEN = os.getenv("BEARER_TOKEN", "my-secure-token-123")

class ChatUI:
    def __init__(self):
        self.api_base_url = API_BASE_URL
        self.headers = {
            "Content-Type": "application/json"
        }
        if BEARER_TOKEN:
            self.headers["Authorization"] = f"Bearer {BEARER_TOKEN}"
    
    def send_message(self, session_id: str, message: str) -> Dict[str, Any]:
        """Send message to the chat API"""
        url = f"{self.api_base_url}/api/chat"
        payload = {
            "session_id": session_id,
            "message": message
        }
        
        try:
            response = requests.post(url, json=payload, headers=self.headers, timeout=30)
            if response.status_code == 200:
                return {"success": True, "data": response.json()}
            else:
                return {"success": False, "error": f"API Error: {response.status_code} - {response.text}"}
        except requests.exceptions.RequestException as e:
            return {"success": False, "error": f"Network Error: {str(e)}"}
    
    def check_health(self) -> Dict[str, Any]:
        """Check API health status"""
        url = f"{self.api_base_url}/api/health"
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            if response.status_code == 200:
                return {"success": True, "data": response.json()}
            else:
                return {"success": False, "error": f"Health check failed: {response.status_code}"}
        except requests.exceptions.RequestException as e:
            return {"success": False, "error": f"Health check error: {str(e)}"}

def main():
    st.set_page_config(
        page_title="AI Chat Service",
        page_icon="🤖",
        layout="wide"
    )
    
    # Initialize chat UI
    chat_ui = ChatUI()
    
    # Sidebar for configuration and status
    with st.sidebar:
        st.header("🔧 Configuration")
        st.text(f"API URL: {API_BASE_URL}")
        
        # Authentication status
        st.subheader("🔐 Authentication")
        if BEARER_TOKEN:
            st.success("✅ Bearer token configured")
            st.text(f"Token: {BEARER_TOKEN[:10]}...")
        else:
            st.warning("⚠️ No bearer token found")
            
            # Allow manual token input
            manual_token = st.text_input("Enter Bearer Token:", type="password", key="manual_token")
            if manual_token:
                chat_ui.headers["Authorization"] = f"Bearer {manual_token}"
                st.success("✅ Manual token set")
        
        if st.button("Check Health"):
            with st.spinner("Checking API health..."):
                health_result = chat_ui.check_health()
                if health_result["success"]:
                    health_data = health_result["data"]
                    st.success("✅ API is healthy")
                    st.json({
                        "Status": health_data.get("status", "Unknown"),
                        "Provider": health_data.get("provider", "Unknown"),
                        "Model": health_data.get("model", "Unknown"),
                        "Uptime": f"{health_data.get('uptime_seconds', 0):.1f}s"
                    })
                else:
                    st.error(f"❌ API Health Check Failed: {health_result['error']}")
        
        st.divider()
        st.header("📊 Session Info")
        
        # Session management
        if "session_id" not in st.session_state:
            st.session_state.session_id = str(uuid.uuid4())
        
        st.text(f"Session ID: {st.session_state.session_id[:8]}...")
        
        if st.button("New Session"):
            st.session_state.session_id = str(uuid.uuid4())
            st.session_state.messages = []
            st.rerun()
    
    # Main chat interface
    st.title("🤖 AI Chat Service")
    st.markdown("Welcome to the AI Chat Service with Retrieval-Augmented Generation (RAG) capabilities!")
    
    # Initialize chat history
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    # Display chat history
    chat_container = st.container()
    with chat_container:
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
                
                # Display metadata for assistant messages
                if message["role"] == "assistant" and "metadata" in message:
                    metadata = message["metadata"]
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.caption(f"⏱️ Latency: {metadata.get('latency_ms', 0):.0f}ms")
                    with col2:
                        st.caption(f"🔢 Tokens: {metadata.get('total_tokens', 0)}")
                    with col3:
                        st.caption(f"📅 {metadata.get('timestamp', '')}")
                    
                    # Show relevant FAQs if available
                    if metadata.get('relevant_faqs'):
                        with st.expander("📚 Related FAQ Information"):
                            for faq in metadata['relevant_faqs']:
                                st.markdown(f"• {faq}")
    
    # Chat input
    if prompt := st.chat_input("Type your message here..."):
        # Display user message
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Add user message to history
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        # Get AI response
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                result = chat_ui.send_message(st.session_state.session_id, prompt)
                
                if result["success"]:
                    response_data = result["data"]
                    response_text = response_data.get("response", "No response received")
                    
                    st.markdown(response_text)
                    
                    # Display metadata
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.caption(f"⏱️ Latency: {response_data.get('latency_ms', 0):.0f}ms")
                    with col2:
                        tokens = response_data.get('token_usage', {}).get('total_tokens', 0)
                        st.caption(f"🔢 Tokens: {tokens}")
                    with col3:
                        timestamp = response_data.get('timestamp', datetime.now().isoformat()[:19])
                        st.caption(f"📅 {timestamp}")
                    
                    # Show relevant FAQs if available
                    if response_data.get('relevant_faqs'):
                        with st.expander("📚 Related FAQ Information"):
                            for faq in response_data['relevant_faqs']:
                                st.markdown(f"• {faq}")
                    
                    # Add assistant message to history with metadata
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": response_text,
                        "metadata": {
                            "latency_ms": response_data.get('latency_ms', 0),
                            "total_tokens": response_data.get('token_usage', {}).get('total_tokens', 0),
                            "timestamp": response_data.get('timestamp', ''),
                            "relevant_faqs": response_data.get('relevant_faqs', [])
                        }
                    })
                else:
                    error_message = f"❌ Error: {result['error']}"
                    st.error(error_message)
                    
                    # Add error to history
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": error_message
                    })

if __name__ == "__main__":
    main()