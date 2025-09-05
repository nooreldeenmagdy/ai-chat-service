import streamlit as st
import requests
import json
import os
import uuid
import pandas as pd
from datetime import datetime
from typing import Dict, Any
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
BEARER_TOKEN = os.getenv("BEARER_TOKEN")

class ChatUI:
    def __init__(self):
        self.api_base_url = API_BASE_URL
        self.headers = {
            "Content-Type": "application/json"
        }
        if BEARER_TOKEN:
            self.headers["Authorization"] = f"Bearer {BEARER_TOKEN}"
    
    def send_message(self, session_id: str, message: str, mode: str = "rag") -> Dict[str, Any]:
        """Send message to the chat API with mode support"""
        # Choose endpoint based on mode
        if mode == "sql":
            url = f"{self.api_base_url}/api/sql-chat"
        elif mode == "dual":
            url = f"{self.api_base_url}/api/dual-mode-chat"
        else:  # rag mode (default)
            url = f"{self.api_base_url}/api/chat"
        
        payload = {
            "session_id": session_id,
            "message": message
        }
        
        # Add mode for dual-mode endpoint
        if mode == "dual":
            # Auto-detect mode based on message content
            detected_mode = self._detect_mode(message)
            payload["mode"] = detected_mode
        
        try:
            response = requests.post(url, json=payload, headers=self.headers, timeout=30)
            if response.status_code == 200:
                return {"success": True, "data": response.json(), "mode": mode}
            else:
                return {"success": False, "error": f"API Error: {response.status_code} - {response.text}"}
        except requests.exceptions.RequestException as e:
            return {"success": False, "error": f"Network Error: {str(e)}"}
    
    def _detect_mode(self, message: str) -> str:
        """Auto-detect whether to use RAG or SQL mode based on message content"""
        message_lower = message.lower()
        
        # Keywords that suggest SQL/database queries
        sql_keywords = [
            'show me', 'list', 'find', 'get', 'select', 'count', 'how many',
            'products', 'orders', 'customers', 'suppliers', 'inventory',
            'stock', 'price', 'sales', 'revenue', 'category', 'categories',
            'low stock', 'out of stock', 'reorder', 'supplier', 'customer',
            'order', 'purchase', 'total', 'sum', 'average', 'maximum', 'minimum'
        ]
        
        # Check for SQL-related keywords
        for keyword in sql_keywords:
            if keyword in message_lower:
                return "sql"
        
        # Default to RAG mode for general questions
        return "rag"
    
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
        st.header("Configuration")
        st.text(f"API URL: {API_BASE_URL}")
        
        # Chat Mode Selection
        st.subheader("Chat Mode")
        chat_mode = st.selectbox(
            "Select chat mode:",
            options=["rag", "sql", "dual"],
            format_func=lambda x: {
                "rag": "RAG Chat (Knowledge-based)",
                "sql": "SQL Chat (Database queries)",
                "dual": "Auto-Detect Mode"
            }[x],
            index=2,  # Default to dual mode
            key="chat_mode"
        )
        
        # Mode descriptions
        if chat_mode == "rag":
            st.info("RAG mode uses knowledge base and FAQs to answer questions.")
        elif chat_mode == "sql":
            st.info("SQL mode converts natural language to database queries.")
        else:  # dual
            st.info("Auto-detect mode automatically chooses between RAG and SQL based on your question.")
        
        # Database Schema Info (for SQL mode)
        if chat_mode in ["sql", "dual"]:
            with st.expander("Database Schema"):
                st.markdown("""
                **Available Tables:**
                - **Customers** - Customer information for sales orders
                - **Vendors** - Vendor/supplier information for asset purchases  
                - **Sites** - Physical sites/locations where assets are deployed
                - **Locations** - Specific locations within sites for asset placement
                - **Items** - Item catalog/master data for purchase and sales orders
                - **Assets** - Physical assets tracked in the system
                - **Bills** - Accounts payable - bills from vendors
                - **PurchaseOrders** - Purchase orders for procurement
                - **PurchaseOrderLines** - Line items for purchase orders
                - **SalesOrders** - Sales orders from customers
                - **SalesOrderLines** - Line items for sales orders
                - **AssetTransactions** - Asset movement/adjustment/disposal history
                
                **Example Queries:**
                - "Show me all active assets at each site"
                - "List all sales orders from this month"
                - "Find customers in New York"
                - "What are our most expensive assets?"
                - "Show recent purchase orders with vendor details"
                - "Find assets that need maintenance"
                """)
        
        st.divider()
        
        # LLM Model Information
        st.subheader("AI Model")
        provider = os.getenv('PROVIDER', 'openai')
        model_name = os.getenv('MODEL_NAME', 'gpt-4o')
        st.info(f"**Provider**: {provider.upper()}")
        st.info(f"**Model**: {model_name}")
        
        st.divider()
        
        # Authentication status
        st.subheader("Authentication")
        if BEARER_TOKEN and BEARER_TOKEN != "your_bearer_token_here":
            st.success("Bearer token configured")
            st.text("Token: ••••••••••")  # Hide token for security
        else:
            st.warning("No bearer token configured")
            
            # Allow manual token input
            manual_token = st.text_input("Enter Bearer Token:", type="password", key="manual_token")
            if manual_token:
                chat_ui.headers["Authorization"] = f"Bearer {manual_token}"
                st.success("Manual token set")
        
        if st.button("Check Health"):
            with st.spinner("Checking API health..."):
                health_result = chat_ui.check_health()
                if health_result["success"]:
                    health_data = health_result["data"]
                    st.success("API is healthy")
                    st.json({
                        "Status": health_data.get("status", "Unknown"),
                        "Provider": health_data.get("provider", "Unknown"),
                        "Model": health_data.get("model", "Unknown"),
                        "Uptime": f"{health_data.get('uptime_seconds', 0):.1f}s"
                    })
                else:
                    st.error(f"API Health Check Failed: {health_result['error']}")
        
        st.divider()
        st.header("Session Info")
        
        # Session management
        if "session_id" not in st.session_state:
            st.session_state.session_id = str(uuid.uuid4())
        
        st.text(f"Session ID: {st.session_state.session_id[:8]}...")
        
        if st.button("New Session"):
            st.session_state.session_id = str(uuid.uuid4())
            st.session_state.messages = []
            st.rerun()
    
    # Main chat interface
    current_mode = st.session_state.get("chat_mode", "dual")
    mode_names = {"rag": "RAG Chat", "sql": "SQL Chat", "dual": "Dual-Mode"}
    
    st.title(f"AI Chat Service - {mode_names.get(current_mode, 'Chat')}")
    
    if current_mode == "rag":
        st.markdown("Knowledge-based chat with Retrieval-Augmented Generation (RAG) capabilities!")
    elif current_mode == "sql":
        st.markdown("Natural language to SQL query conversion for database insights!")
    else:  # dual mode
        st.markdown("Auto-detecting mode - ask general questions or database queries!")
    
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
                        st.caption(f"Latency: {metadata.get('latency_ms', 0):.0f}ms")
                    with col2:
                        st.caption(f"Tokens: {metadata.get('total_tokens', 0)}")
                    with col3:
                        st.caption(f"{metadata.get('timestamp', '')}")
                    
                    # Show mode-specific information
                    used_mode = metadata.get('mode', 'rag')
                    if used_mode == 'sql':
                        # Enhanced SQL-specific information for history
                        if metadata.get('sql_query'):
                            with st.expander("Generated SQL Query"):
                                st.code(metadata['sql_query'], language='sql')
                                st.caption("Validated by execution against SQLite database")
                        
                        if metadata.get('table_info'):
                            with st.expander("Database Tables Used"):
                                for table in metadata['table_info']:
                                    st.markdown(f"• **{table}**")
                                st.caption(f"Total tables: {len(metadata['table_info'])}")
                        
                        
                        # Validation status
                        attempts = metadata.get('validation_attempts', 1)
                        if attempts > 1:
                            st.caption(f"SQL Validation: {attempts} attempts required")
                        else:
                            st.caption("SQL Validation: Success on first attempt")
                        
                        # Query results for history
                        if metadata.get('query_results'):
                            query_results = metadata['query_results']
                            with st.expander("Query Results Summary"):
                                st.markdown(f"**Rows returned**: {len(query_results)} records")
                                if query_results and len(query_results) > 0:
                                    # Show results in table format for history
                                    df = pd.DataFrame(query_results)
                                    st.dataframe(df, use_container_width=True)
                                else:
                                    st.info("No data found.")
                    
                    else:  # RAG mode
                        # Show relevant FAQs if available
                        if metadata.get('relevant_faqs'):
                            with st.expander("Related FAQ Information"):
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
            with st.spinner("Processing your request..."):
                result = chat_ui.send_message(st.session_state.session_id, prompt, current_mode)
                
                if result["success"]:
                    response_data = result["data"]
                    used_mode = response_data.get("mode", result.get("mode", current_mode))
                    
                    # Handle different response formats
                    if used_mode == "sql" and "natural_language_answer" in response_data:
                        # Direct SQL endpoint response
                        response_text = response_data.get("natural_language_answer", "No response received")
                    else:
                        # Dual-mode or RAG endpoint response  
                        response_text = response_data.get("response", "No response received")
                    
                    st.markdown(response_text)
                    
                    # Display mode indicator with enhanced info for SQL
                    if used_mode == 'sql':
                        status_icon = "✅" if response_data.get("status") == "success" else "⚠️"
                        mode_indicator = f"Mode: {status_icon} {mode_names.get(used_mode, used_mode.upper())}"
                        
                        # Show validation status prominently
                        if response_data.get("status") == "success":
                            st.success("SQLite Database Validation: PASSED - Query executed successfully against database")
                        elif response_data.get("status") == "warning":
                            st.warning("SQLite Database Validation: WARNING - Query generated but validation had issues")
                        else:
                            st.error(f"SQLite Database Validation: ERROR - Status: {response_data.get('status', 'unknown')}")
                        
                        # Debug info for status
                        st.caption(f"Debug: Response status = '{response_data.get('status', 'not_set')}'")
                    else:
                        mode_indicator = f"Mode: {mode_names.get(used_mode, used_mode.upper())}"
                    
                    st.caption(mode_indicator)
                    
                    # Display metadata
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.caption(f"Latency: {response_data.get('latency_ms', 0):.0f}ms")
                    with col2:
                        # Debug token usage
                        token_usage_raw = response_data.get('token_usage', {})
                        tokens = token_usage_raw.get('total_tokens', 0)
                        st.caption(f"Tokens: {tokens}")
                        # Debug info (only show if tokens is 0)
                        if tokens == 0:
                            st.caption(f"DEBUG - token_usage: {token_usage_raw}")
                    with col3:
                        timestamp = response_data.get('timestamp', datetime.now().isoformat()[:19])
                        st.caption(f"{timestamp}")
                    
                    # Show mode-specific information
                    if used_mode == 'sql':
                        # Enhanced SQL-specific information display
                        st.markdown("---")
                        st.markdown("### SQL Query Details")
                        
                        # Validation status with detailed info
                        col1, col2 = st.columns(2)
                        with col1:
                            if response_data.get("status") == "success":
                                st.success("Database Validation: PASSED")
                                st.caption("Query successfully executed against SQLite database")
                            else:
                                st.warning("Database Validation: WARNING") 
                                st.caption("Query generated but may have validation issues")
                        
                        with col2:
                            attempts = response_data.get('validation_attempts', 1)
                            if attempts > 1:
                                st.info(f"Validation Attempts: {attempts}")
                                st.caption(f"Required {attempts} attempts to generate valid SQL")
                            else:
                                st.success("First Attempt: Success")
                                st.caption("Query validated on first generation attempt")
                        
                        # Generated SQL Query
                        if response_data.get('sql_query'):
                            with st.expander("Generated SQL Query", expanded=True):
                                st.code(response_data['sql_query'], language='sql')
                                st.caption("This query was validated by executing it against the SQLite database")
                        
                        # Database Tables Used
                        if response_data.get('table_info'):
                            with st.expander("Database Tables Used", expanded=True):
                                st.markdown("**Tables accessed in this query:**")
                                for table in response_data['table_info']:
                                    st.markdown(f"• **{table}**")
                                st.caption(f"Total tables involved: {len(response_data['table_info'])}")
                        
                        # Query Results Summary (if available)
                        if response_data.get('query_results'):
                            query_results = response_data['query_results']
                            with st.expander("Query Results Summary", expanded=True):
                                st.markdown(f"**Rows returned**: {len(query_results)} records")
                                if query_results and len(query_results) > 0:
                                    st.markdown("**Complete data preview:**")
                                    
                                    # Show all results in a more user-friendly format
                                    for i, row in enumerate(query_results, 1):
                                        with st.container():
                                            st.markdown(f"**Record {i}:**")
                                            col_data = []
                                            for key, value in row.items():
                                                col_data.append(f"• **{key}**: {value}")
                                            st.markdown("\n".join(col_data))
                                            if i < len(query_results):
                                                st.divider()
                                    
                                    # Also show as a table for better overview
                                    if len(query_results) > 1:
                                        st.markdown("**Table View:**")
                                        df = pd.DataFrame(query_results)
                                        st.dataframe(df, use_container_width=True)
                                else:
                                    st.info("No data found matching your query criteria.")
                    
                    else:  # RAG mode
                        # Show relevant FAQs if available
                        if response_data.get('relevant_faqs'):
                            with st.expander("Related FAQ Information"):
                                for faq in response_data['relevant_faqs']:
                                    st.markdown(f"• {faq}")
                    
                    # Add assistant message to history with metadata
                    metadata = {
                        "latency_ms": response_data.get('latency_ms', 0),
                        "total_tokens": response_data.get('token_usage', {}).get('total_tokens', 0),
                        "timestamp": response_data.get('timestamp', ''),
                        "relevant_faqs": response_data.get('relevant_faqs', []),
                        "mode": used_mode,
                        "sql_query": response_data.get('sql_query'),
                        "table_info": response_data.get('table_info', []),
                        "validation_attempts": response_data.get('validation_attempts', 1),
                        "status": response_data.get('status', 'unknown'),
                        "query_results": response_data.get('query_results', [])
                    }
                    
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": response_text,
                        "metadata": metadata
                    })
                else:
                    error_message = f"Error: {result['error']}"
                    st.error(error_message)
                    
                    # Add error to history
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": error_message
                    })

if __name__ == "__main__":
    main()