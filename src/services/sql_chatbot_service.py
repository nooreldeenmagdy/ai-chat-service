# filepath: d:\PF2\ai_chat_service\ai-chat-service\src\services\sql_chatbot_service.py
import os
import re
import json
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
import asyncio

from src.models.chat_models import SqlQueryRequest, SqlQueryResponse, DatabaseSchema, DatabaseTable
from src.services.openai_service import openai_service
from src.services.database_service import database_service

# Configure logging
logger = logging.getLogger(__name__)

class SqlChatbotService:
    """
    SQL Chatbot Service for natural language to SQL query conversion
    
    Features:    - Two-step LLM workflow: goal understanding + SQL generation
    - 3-attempt retry mechanism with validation
    - Database schema awareness
    - Query result explanation in natural language
    """
    
    def __init__(self):
        self.sessions: Dict[str, List] = {}  # Store conversation history
        self.database_schema = self._load_database_schema()
    
    def _load_database_schema(self) -> DatabaseSchema:
        """Load the database schema definition for asset management system"""
        schema_data = {
            "tables": [
                {
                    "name": "Customers",
                    "description": "Customer information for sales orders",
                    "columns": [
                        {"name": "CustomerId", "type": "INTEGER", "description": "Primary key, unique customer identifier"},
                        {"name": "CustomerCode", "type": "VARCHAR(50)", "description": "Unique customer code"},
                        {"name": "CustomerName", "type": "TEXT", "description": "Customer company or individual name"},
                        {"name": "Email", "type": "TEXT", "description": "Contact email address"},
                        {"name": "Phone", "type": "TEXT", "description": "Contact phone number"},
                        {"name": "BillingAddress1", "type": "TEXT", "description": "Billing address line 1"},
                        {"name": "BillingCity", "type": "TEXT", "description": "Billing city"},
                        {"name": "BillingCountry", "type": "TEXT", "description": "Billing country"},
                        {"name": "CreatedAt", "type": "DATETIME", "description": "Customer creation timestamp"},
                        {"name": "UpdatedAt", "type": "DATETIME", "description": "Last update timestamp"},
                        {"name": "IsActive", "type": "BOOLEAN", "description": "Whether customer is active"}
                    ]
                },
                {
                    "name": "Vendors",
                    "description": "Vendor/supplier information for asset purchases",
                    "columns": [
                        {"name": "VendorId", "type": "INTEGER", "description": "Primary key, unique vendor identifier"},
                        {"name": "VendorCode", "type": "VARCHAR(50)", "description": "Unique vendor code"},
                        {"name": "VendorName", "type": "TEXT", "description": "Vendor company name"},
                        {"name": "Email", "type": "TEXT", "description": "Contact email address"},
                        {"name": "Phone", "type": "TEXT", "description": "Contact phone number"},
                        {"name": "AddressLine1", "type": "TEXT", "description": "Vendor address line 1"},
                        {"name": "City", "type": "TEXT", "description": "Vendor city"},
                        {"name": "Country", "type": "TEXT", "description": "Vendor country"},
                        {"name": "CreatedAt", "type": "DATETIME", "description": "Vendor creation timestamp"},
                        {"name": "UpdatedAt", "type": "DATETIME", "description": "Last update timestamp"},
                        {"name": "IsActive", "type": "BOOLEAN", "description": "Whether vendor is active"}
                    ]
                },
                {
                    "name": "Sites",
                    "description": "Physical sites/locations where assets are deployed",
                    "columns": [
                        {"name": "SiteId", "type": "INTEGER", "description": "Primary key, unique site identifier"},
                        {"name": "SiteCode", "type": "VARCHAR(50)", "description": "Unique site code"},
                        {"name": "SiteName", "type": "TEXT", "description": "Site name or location description"},
                        {"name": "AddressLine1", "type": "TEXT", "description": "Site address line 1"},
                        {"name": "City", "type": "TEXT", "description": "Site city"},
                        {"name": "Country", "type": "TEXT", "description": "Site country"},
                        {"name": "TimeZone", "type": "TEXT", "description": "Site timezone"},
                        {"name": "CreatedAt", "type": "DATETIME", "description": "Site creation timestamp"},
                        {"name": "UpdatedAt", "type": "DATETIME", "description": "Last update timestamp"},
                        {"name": "IsActive", "type": "BOOLEAN", "description": "Whether site is active"}
                    ]
                },
                {
                    "name": "Locations",
                    "description": "Specific locations within sites for asset placement",
                    "columns": [
                        {"name": "LocationId", "type": "INTEGER", "description": "Primary key, unique location identifier"},
                        {"name": "SiteId", "type": "INTEGER", "description": "Foreign key to Sites table"},
                        {"name": "LocationCode", "type": "VARCHAR(50)", "description": "Location code within site"},
                        {"name": "LocationName", "type": "TEXT", "description": "Location name or description"},
                        {"name": "ParentLocationId", "type": "INTEGER", "description": "Self-referencing foreign key for hierarchical locations"},
                        {"name": "CreatedAt", "type": "DATETIME", "description": "Location creation timestamp"},
                        {"name": "UpdatedAt", "type": "DATETIME", "description": "Last update timestamp"},
                        {"name": "IsActive", "type": "BOOLEAN", "description": "Whether location is active"}
                    ]
                },
                {
                    "name": "Items",
                    "description": "Item catalog/master data for purchase and sales orders",
                    "columns": [
                        {"name": "ItemId", "type": "INTEGER", "description": "Primary key, unique item identifier"},
                        {"name": "ItemCode", "type": "TEXT", "description": "Unique item code"},
                        {"name": "ItemName", "type": "TEXT", "description": "Item name or description"},
                        {"name": "Category", "type": "TEXT", "description": "Item category"},
                        {"name": "UnitOfMeasure", "type": "TEXT", "description": "Unit of measure (Each, Box, etc.)"},
                        {"name": "CreatedAt", "type": "DATETIME", "description": "Item creation timestamp"},
                        {"name": "UpdatedAt", "type": "DATETIME", "description": "Last update timestamp"},
                        {"name": "IsActive", "type": "BOOLEAN", "description": "Whether item is active"}
                    ]
                },
                {
                    "name": "Assets",
                    "description": "Physical assets tracked in the system",
                    "columns": [
                        {"name": "AssetId", "type": "INTEGER", "description": "Primary key, unique asset identifier"},
                        {"name": "AssetTag", "type": "VARCHAR(100)", "description": "Unique asset tag/barcode"},
                        {"name": "AssetName", "type": "TEXT", "description": "Asset name or description"},
                        {"name": "SiteId", "type": "INTEGER", "description": "Foreign key to Sites table"},
                        {"name": "LocationId", "type": "INTEGER", "description": "Foreign key to Locations table"},
                        {"name": "SerialNumber", "type": "TEXT", "description": "Manufacturer serial number"},
                        {"name": "Category", "type": "TEXT", "description": "Asset category"},
                        {"name": "Status", "type": "VARCHAR(30)", "description": "Asset status (Active, InRepair, Disposed)"},
                        {"name": "Cost", "type": "DECIMAL(18,2)", "description": "Asset cost/purchase price"},
                        {"name": "PurchaseDate", "type": "DATE", "description": "Date when asset was purchased"},
                        {"name": "VendorId", "type": "INTEGER", "description": "Foreign key to Vendors table"},
                        {"name": "CreatedAt", "type": "DATETIME", "description": "Asset creation timestamp"},
                        {"name": "UpdatedAt", "type": "DATETIME", "description": "Last update timestamp"}
                    ]
                },
                {
                    "name": "Bills",
                    "description": "Accounts payable - bills from vendors",
                    "columns": [
                        {"name": "BillId", "type": "INTEGER", "description": "Primary key, unique bill identifier"},
                        {"name": "VendorId", "type": "INTEGER", "description": "Foreign key to Vendors table"},
                        {"name": "BillNumber", "type": "VARCHAR(100)", "description": "Bill/invoice number"},
                        {"name": "BillDate", "type": "DATE", "description": "Bill date"},
                        {"name": "DueDate", "type": "DATE", "description": "Payment due date"},
                        {"name": "TotalAmount", "type": "DECIMAL(18,2)", "description": "Total bill amount"},
                        {"name": "Currency", "type": "VARCHAR(10)", "description": "Currency code (USD, EUR, etc.)"},
                        {"name": "Status", "type": "VARCHAR(30)", "description": "Bill status (Open, Paid, Void)"},
                        {"name": "CreatedAt", "type": "DATETIME", "description": "Bill creation timestamp"},
                        {"name": "UpdatedAt", "type": "DATETIME", "description": "Last update timestamp"}
                    ]
                },
                {
                    "name": "PurchaseOrders",
                    "description": "Purchase orders for procurement",
                    "columns": [
                        {"name": "POId", "type": "INTEGER", "description": "Primary key, unique purchase order identifier"},
                        {"name": "PONumber", "type": "VARCHAR(100)", "description": "Purchase order number"},
                        {"name": "VendorId", "type": "INTEGER", "description": "Foreign key to Vendors table"},
                        {"name": "PODate", "type": "DATE", "description": "Purchase order date"},
                        {"name": "Status", "type": "VARCHAR(30)", "description": "PO status (Open, Approved, Closed, Cancelled)"},
                        {"name": "SiteId", "type": "INTEGER", "description": "Foreign key to Sites table"},
                        {"name": "CreatedAt", "type": "DATETIME", "description": "PO creation timestamp"},
                        {"name": "UpdatedAt", "type": "DATETIME", "description": "Last update timestamp"}
                    ]
                },
                {
                    "name": "PurchaseOrderLines",
                    "description": "Line items for purchase orders",
                    "columns": [
                        {"name": "POLineId", "type": "INTEGER", "description": "Primary key, unique PO line identifier"},
                        {"name": "POId", "type": "INTEGER", "description": "Foreign key to PurchaseOrders table"},
                        {"name": "LineNumber", "type": "INTEGER", "description": "Line number within the PO"},
                        {"name": "ItemId", "type": "INTEGER", "description": "Foreign key to Items table"},
                        {"name": "ItemCode", "type": "TEXT", "description": "Item code being ordered"},
                        {"name": "Description", "type": "TEXT", "description": "Item description"},
                        {"name": "Quantity", "type": "DECIMAL(18,4)", "description": "Quantity ordered"},
                        {"name": "UnitPrice", "type": "DECIMAL(18,4)", "description": "Unit price"}
                    ]
                },
                {
                    "name": "SalesOrders",
                    "description": "Sales orders from customers",
                    "columns": [
                        {"name": "SOId", "type": "INTEGER", "description": "Primary key, unique sales order identifier"},
                        {"name": "SONumber", "type": "VARCHAR(100)", "description": "Sales order number"},
                        {"name": "CustomerId", "type": "INTEGER", "description": "Foreign key to Customers table"},
                        {"name": "SODate", "type": "DATE", "description": "Sales order date"},
                        {"name": "Status", "type": "VARCHAR(30)", "description": "SO status (Open, Shipped, Closed, Cancelled)"},
                        {"name": "SiteId", "type": "INTEGER", "description": "Foreign key to Sites table"},
                        {"name": "CreatedAt", "type": "DATETIME", "description": "SO creation timestamp"},
                        {"name": "UpdatedAt", "type": "DATETIME", "description": "Last update timestamp"}
                    ]
                },
                {
                    "name": "SalesOrderLines",
                    "description": "Line items for sales orders",
                    "columns": [
                        {"name": "SOLineId", "type": "INTEGER", "description": "Primary key, unique SO line identifier"},
                        {"name": "SOId", "type": "INTEGER", "description": "Foreign key to SalesOrders table"},
                        {"name": "LineNumber", "type": "INTEGER", "description": "Line number within the SO"},
                        {"name": "ItemId", "type": "INTEGER", "description": "Foreign key to Items table"},
                        {"name": "ItemCode", "type": "TEXT", "description": "Item code being sold"},
                        {"name": "Description", "type": "TEXT", "description": "Item description"},
                        {"name": "Quantity", "type": "DECIMAL(18,4)", "description": "Quantity sold"},
                        {"name": "UnitPrice", "type": "DECIMAL(18,4)", "description": "Unit price"}
                    ]
                },
                {
                    "name": "AssetTransactions",
                    "description": "Asset movement/adjustment/disposal history",
                    "columns": [
                        {"name": "AssetTxnId", "type": "INTEGER", "description": "Primary key, unique transaction identifier"},
                        {"name": "AssetId", "type": "INTEGER", "description": "Foreign key to Assets table"},
                        {"name": "FromLocationId", "type": "INTEGER", "description": "Foreign key to Locations table (source)"},
                        {"name": "ToLocationId", "type": "INTEGER", "description": "Foreign key to Locations table (destination)"},
                        {"name": "TxnType", "type": "VARCHAR(30)", "description": "Transaction type (Move, Adjust, Dispose, Create)"},
                        {"name": "Quantity", "type": "INTEGER", "description": "Quantity moved/adjusted"},
                        {"name": "TxnDate", "type": "DATETIME", "description": "Transaction date"},
                        {"name": "Note", "type": "TEXT", "description": "Transaction notes"}
                    ]
                }
            ]
        }
          # Convert to DatabaseSchema object
        tables = []
        for table_data in schema_data["tables"]:
            table = DatabaseTable(
                name=table_data["name"],
                description=table_data["description"],
                columns=table_data["columns"]
            )
            tables.append(table)
        
        # Define relationships between tables
        relationships = [
            {"from_table": "Assets", "to_table": "AssetCategories", "foreign_key": "CategoryId"},
            {"from_table": "Assets", "to_table": "Sites", "foreign_key": "SiteId"},
            {"from_table": "Assets", "to_table": "Vendors", "foreign_key": "VendorId"},
            {"from_table": "Assets", "to_table": "PurchaseOrders", "foreign_key": "PurchaseOrderId"},
            {"from_table": "PurchaseOrders", "to_table": "Vendors", "foreign_key": "VendorId"},
            {"from_table": "SalesOrders", "to_table": "Customers", "foreign_key": "CustomerId"},
            {"from_table": "AssetCategories", "to_table": "AssetCategories", "foreign_key": "ParentCategoryId"}        ]
        
        return DatabaseSchema(tables=tables, relationships=relationships)

    async def _understand_goal_and_select_tables(self, user_query: str) -> Tuple[str, List[str], Dict[str, int]]:
        """
        Step 1: Understand the user's goal and select relevant tables, returns tokens used
        """
        # Create schema summary for LLM
        schema_summary = ""
        for table in self.database_schema.tables:
            schema_summary += f"\nTable: {table.name}\n"
            schema_summary += f"Description: {table.description}\n"
            column_list = ', '.join([f"{col['name']} ({col['type']})" for col in table.columns])
            schema_summary += f"Columns: {column_list}\n"

        prompt = f"""You are an expert database analyst. Based on the user's query and database schema, you need to:
1. Understand the user's goal/intent
2. Select the most relevant tables needed to answer the query

Database Schema:
{schema_summary}

User Query: "{user_query}"

Please analyze the query and respond with JSON in this exact format:
{{
    "goal": "Clear description of what the user wants to achieve",
    "relevant_tables": ["Table1", "Table2", "Table3"],
    "reasoning": "Explanation of why these tables were selected"
}}

Focus on selecting only the tables that are directly needed to answer the query. Consider relationships between tables when necessary.
"""

        try:
            response, goal_tokens = await openai_service.generate_response(prompt, max_tokens=500)
            
            # Extract JSON from response
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                json_str = json_match.group()
                parsed_response = json.loads(json_str)
                
                goal = parsed_response.get("goal", "Analyze database query")
                relevant_tables = parsed_response.get("relevant_tables", [])
                  # Validate table names exist in schema
                valid_table_names = [table.name for table in self.database_schema.tables]
                relevant_tables = [t for t in relevant_tables if t in valid_table_names]
                
                if not relevant_tables:
                    # Fallback: select all tables if none were identified
                    relevant_tables = valid_table_names[:3]  # Limit to first 3 tables
                
                logger.info(f"Goal understanding: {goal}")
                logger.info(f"Selected tables: {relevant_tables}")
                
                return goal, relevant_tables, goal_tokens
            else:
                raise ValueError("Could not parse JSON response from LLM")
                
        except Exception as e:
            logger.error(f"Error in goal understanding step: {e}")
            # Fallback: use Assets table as it's the main table
            return "Retrieve asset information", ["Assets"], {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}

    async def _generate_sql_query(self, goal: str, relevant_tables: List[str], user_query: str, attempt: int = 1) -> Tuple[str, bool, Dict[str, int]]:
        """
        Step 2: Generate SQL query based on goal and selected tables
        """
        # Get detailed schema for selected tables
        detailed_schema = ""
        for table in self.database_schema.tables:
            if table.name in relevant_tables:
                detailed_schema += f"\nTable: {table.name}\n"
                detailed_schema += f"Description: {table.description}\n"
                detailed_schema += "Columns:\n"
                for col in table.columns:
                    detailed_schema += f"  - {col['name']} ({col['type']}): {col['description']}\n"        # Include SQLite-specific example queries to improve generation quality
        example_queries = """
Example Queries (SQLite Syntax):
1. "Show all active assets at New York site":
   SELECT a.AssetTag, a.AssetName, a.Status, s.SiteName 
   FROM Assets a 
   JOIN Sites s ON a.SiteId = s.SiteId 
   WHERE a.Status = 'Active' AND s.City = 'New York';

2. "What is the total value of assets by category":
   SELECT Category, COUNT(*) as AssetCount, SUM(Cost) as TotalValue
   FROM Assets 
   GROUP BY Category;

3. "Show recent purchase orders with vendor details":
   SELECT po.PONumber, po.PODate, v.VendorName, po.Status
   FROM PurchaseOrders po 
   JOIN Vendors v ON po.VendorId = v.VendorId 
   ORDER BY po.PODate DESC 
   LIMIT 10;

4. "Find orders from last month" (SQLite date functions):
   SELECT COUNT(*) as OrderCount
   FROM SalesOrders 
   WHERE DATE(SODate) >= DATE('now', 'start of month', '-1 month')
   AND DATE(SODate) < DATE('now', 'start of month');

5. "Get data from specific date range":
   SELECT * FROM Assets 
   WHERE DATE(PurchaseDate) BETWEEN '2024-01-01' AND '2024-12-31';

6. "How many sales orders for each customer last month":
   SELECT c.CustomerName, COUNT(so.SOId) as OrderCount
   FROM Customers c
   LEFT JOIN SalesOrders so ON c.CustomerId = so.CustomerId 
   AND DATE(so.SODate) >= DATE('now', 'start of month', '-1 month')
   AND DATE(so.SODate) < DATE('now', 'start of month')
   GROUP BY c.CustomerId, c.CustomerName
   ORDER BY OrderCount DESC;
"""

        prompt = f"""You are an expert SQL developer. Generate a SQL query based on the following:

Goal: {goal}
User Query: "{user_query}"
Attempt: {attempt}/3

Relevant Tables Schema:
{detailed_schema}

{example_queries}

IMPORTANT SQLite Requirements:
1. Use SQLite date/time functions, NOT MySQL/PostgreSQL syntax
2. For date calculations, use: DATE('now', 'start of month', '-1 month') instead of INTERVAL
3. For extracting parts: strftime('%m', date_column) instead of MONTH(date_column)
4. For current date: DATE('now') instead of CURRENT_DATE
5. Use DATE() function to compare dates: DATE(column) = 'YYYY-MM-DD'
6. Use standard SQL syntax compatible with SQLite

Requirements:
1. Generate a single, well-formatted SQL query
2. Use proper JOINs when accessing multiple tables
3. Include relevant WHERE clauses to filter data appropriately
4. Use meaningful column aliases for better readability
5. Add ORDER BY and LIMIT clauses when appropriate
6. Only SELECT data - no INSERT, UPDATE, DELETE, DROP operations
7. Use SQLite-compatible syntax (see examples above)
8. When queries involve "given customer", "each customer", or "per customer", show data for ALL customers using GROUP BY and meaningful customer identifiers like CustomerName
9. Avoid hardcoded customer codes - instead use realistic approaches that show actual data

Respond with only the SQL query, no additional text or formatting:
"""

        try:
            response, sql_tokens = await openai_service.generate_response(prompt, max_tokens=800)
            
            # Clean up the response to extract just the SQL query
            sql_query = response.strip()
            
            # Remove any markdown formatting
            if sql_query.startswith('```sql'):
                sql_query = sql_query[6:]
            if sql_query.startswith('```'):
                sql_query = sql_query[3:]
            if sql_query.endswith('```'):
                sql_query = sql_query[:-3]
            
            sql_query = sql_query.strip()
              # Validate the generated query
            is_valid = self._validate_sql_query(sql_query, relevant_tables)
            
            logger.info(f"Generated SQL (attempt {attempt}): {sql_query}")
            logger.info(f"Query validation: {'PASSED' if is_valid else 'FAILED'}")
            
            return sql_query, is_valid, sql_tokens
            
        except Exception as e:
            logger.error(f"Error generating SQL query (attempt {attempt}): {e}")
            return f"-- Error generating SQL query: {str(e)}", False, {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}

    def _validate_sql_query(self, sql_query: str, expected_tables: List[str]) -> bool:
        """
        Validate the generated SQL query for safety and correctness by executing it against the SQLite database
        """
        try:
            # Convert to uppercase for checking
            query_upper = sql_query.upper()
            
            # Check 1: Only allow SELECT statements
            if not query_upper.strip().startswith('SELECT'):
                logger.warning("Query validation failed: Not a SELECT statement")
                return False
            
            # Check 2: Prevent destructive operations
            forbidden_keywords = [
                'DROP', 'DELETE', 'INSERT', 'UPDATE', 'ALTER', 'CREATE', 
                'TRUNCATE', 'REPLACE', 'MERGE', 'EXEC', 'EXECUTE', 'SP_'
            ]
            
            for keyword in forbidden_keywords:
                if keyword in query_upper:
                    logger.warning(f"Query validation failed: Contains forbidden keyword '{keyword}'")
                    return False
            
            # Check 3: Verify expected tables are referenced
            tables_in_query = []
            for table in expected_tables:
                if table.upper() in query_upper:
                    tables_in_query.append(table)
            
            if not tables_in_query:
                logger.warning("Query validation failed: Expected tables not found in query")
                return False
            
            # Check 4: Basic SQL syntax validation (simple checks)
            if query_upper.count('(') != query_upper.count(')'):
                logger.warning("Query validation failed: Mismatched parentheses")
                return False
            
            # Check 5: Execute query against SQLite database to validate syntax
            try:
                result = database_service.execute_query(sql_query)
                if not result['success']:
                    logger.warning(f"Query validation failed: Database execution error: {result['error']}")
                    return False                
                logger.info(f"✅ SQLITE DATABASE VALIDATION PASSED: Query executed successfully against SQLite database with {result['row_count']} rows returned")
                logger.info(f"Query validation passed. Tables found: {tables_in_query}, Database execution successful")
                return True
                
            except Exception as db_error:
                logger.warning(f"Query validation failed: Database execution error: {db_error}")
                return False
            
        except Exception as e:
            logger.error(f"Error during query validation: {e}")
            return False

    async def _explain_query_results(self, user_query: str, sql_query: str, goal: str, query_results: Dict[str, Any] = None) -> Tuple[str, Dict[str, int]]:
        """
        Generate a natural language answer to the user's question based on actual query results
        """
        prompt = f"""You are a business analyst providing answers based on database query results. The user asked a specific question and you have the actual data to answer it.

User's Question: "{user_query}"
Goal: {goal}"""
        
        # Include actual query results if available
        if query_results and query_results.get('success') and query_results.get('results'):
            results_data = query_results['results']
            row_count = query_results['row_count']
            columns = query_results['columns']
            
            prompt += f"""

ACTUAL DATA FROM DATABASE ({row_count} records found):
Columns: {', '.join(columns)}

Data:"""
            # Include all results in the prompt for better analysis
            for i, row in enumerate(results_data, 1):
                row_values = [f"{k}: {v}" for k, v in row.items()]
                prompt += f"\nRecord {i}: {', '.join(row_values)}"
            
            prompt += f"""

INSTRUCTIONS:
- Answer the user's question directly using this actual data
- Present the findings in a clear, business-friendly format
- Do NOT explain the SQL query or technical process
- Focus on the insights and answers the data provides
- Use specific numbers and categories from the results
- If it's a breakdown or summary, present it clearly

Example for breakdown questions: "Based on your data, here's the breakdown by category: Equipment has 18 assets, Computers has 18 assets, and Office Supplies has 12 assets."
"""
        else:
            prompt += f"""

No query results were available. Please provide a helpful response acknowledging this limitation.
"""
        
        try:
            explanation, explain_tokens = await openai_service.generate_response(prompt, max_tokens=400)
            logger.info(f"🎯 Generated direct answer based on query results: {explanation[:100]}...")
            return explanation.strip(), explain_tokens
        except Exception as e:
            logger.error(f"Error generating explanation: {e}")
            if query_results and query_results.get('success') and query_results.get('results'):
                # Provide a fallback response with the actual data
                results_data = query_results['results']
                if results_data and len(results_data) > 0:
                    # Create a simple breakdown from the results
                    if len(results_data[0]) == 2:  # Assuming category and count format
                        breakdown_parts = []
                        for row in results_data:
                            values = list(row.values())
                            breakdown_parts.append(f"{values[0]} has {values[1]} items")
                        return f"Based on your query '{user_query}', here's what I found: {', '.join(breakdown_parts)}.", {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
                return f"Based on your question '{user_query}', I found {len(results_data)} results in the database.", {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
            else:
                return f"I was unable to retrieve data for your question: '{user_query}'. Please check if the query parameters are correct.", {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}

    async def process_sql_query(self, request: SqlQueryRequest) -> SqlQueryResponse:
        """
        Main method to process SQL query requests with the two-step workflow
        """
        start_time = datetime.now()
        session_id = request.session_id
        user_query = request.message
        
        # Initialize session if it doesn't exist
        if session_id not in self.sessions:
            self.sessions[session_id] = []
          # Track validation attempts and token usage
        validation_attempts = []
        final_sql_query = ""
        final_explanation = ""
        goal = ""
        relevant_tables = []
        total_tokens = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
        
        try:
            logger.info(f"Processing SQL query for session {session_id}: {user_query}")            # Step 1: Understand goal and select tables
            goal, relevant_tables, goal_tokens = await self._understand_goal_and_select_tables(user_query)
            total_tokens["prompt_tokens"] += goal_tokens.get("prompt_tokens", 0)
            total_tokens["completion_tokens"] += goal_tokens.get("completion_tokens", 0)
            total_tokens["total_tokens"] += goal_tokens.get("total_tokens", 0)
              # Step 2: Generate SQL query with retry mechanism
            max_attempts = 3
            sql_query_generated = False
            
            for attempt in range(1, max_attempts + 1):
                logger.info(f"SQL generation attempt {attempt}/{max_attempts}")
                
                sql_query, is_valid, sql_tokens = await self._generate_sql_query(
                    goal, relevant_tables, user_query, attempt
                )                # Track tokens from SQL generation
                total_tokens["prompt_tokens"] += sql_tokens.get("prompt_tokens", 0)
                total_tokens["completion_tokens"] += sql_tokens.get("completion_tokens", 0)
                total_tokens["total_tokens"] += sql_tokens.get("total_tokens", 0)
                
                validation_attempts.append({
                    "attempt": attempt,
                    "sql_query": sql_query,
                    "is_valid": is_valid,
                    "timestamp": datetime.now().isoformat()
                })
                
                if is_valid:
                    final_sql_query = sql_query
                    sql_query_generated = True
                    break
                
                logger.warning(f"SQL validation failed on attempt {attempt}")
            
            # If all attempts failed, use the last generated query anyway
            if not sql_query_generated:
                final_sql_query = validation_attempts[-1]["sql_query"] if validation_attempts else "-- Unable to generate valid SQL query"
            
            # Step 3: Execute the final SQL query to get actual results
            query_results = None
            if sql_query_generated and final_sql_query and not final_sql_query.startswith('--'):
                try:
                    logger.info(f"🔍 Executing validated SQL query: {final_sql_query}")
                    query_results = database_service.execute_query(final_sql_query)
                    if query_results['success']:
                        logger.info(f"✅ QUERY EXECUTION SUCCESS: {query_results['row_count']} rows returned from SQLite database")
                        logger.info(f"📊 Query result columns: {query_results.get('columns', [])}")
                    else:
                        logger.warning(f"❌ Query execution failed: {query_results['error']}")
                except Exception as e:
                    logger.error(f"❌ Error executing SQL query: {e}")
                    query_results = {
                        'success': False,
                        'results': [],
                        'columns': [],
                        'row_count': 0,
                        'error': str(e)
                    }
            else:
                logger.warning("⚠️ Skipping query execution - no valid SQL query generated")
              # Step 4: Generate natural language explanation with actual results
            logger.info(f"🤖 Generating natural language explanation with results data...")
            final_explanation, explain_tokens = await self._explain_query_results(user_query, final_sql_query, goal, query_results)            # Track tokens from explanation generation
            total_tokens["prompt_tokens"] += explain_tokens.get("prompt_tokens", 0)
            total_tokens["completion_tokens"] += explain_tokens.get("completion_tokens", 0)
            total_tokens["total_tokens"] += explain_tokens.get("total_tokens", 0)
              # Add to session history
            self.sessions[session_id].append({
                "user_query": user_query,
                "goal": goal,
                "relevant_tables": relevant_tables,
                "sql_query": final_sql_query,
                "explanation": final_explanation,
                "validation_attempts": len(validation_attempts),
                "query_results": query_results,
                "timestamp": datetime.now().isoformat()
            })
              # Calculate latency and prepare response
            end_time = datetime.now()
            latency_ms = int((end_time - start_time).total_seconds() * 1000)
            
            # Get provider and model from environment
            provider = os.getenv('PROVIDER', 'openai')
            model = os.getenv('MODEL_NAME', 'gpt-4o')            # Use actual tracked token usage instead of estimation
            token_usage = total_tokens
            
            # Prepare table info for response (as list of strings)
            table_info = []
            for table_name in relevant_tables:
                table_info.append(table_name)  # Just the table name as string
            
            # Debug logging for status determination
            logger.info(f"🔍 STATUS DEBUG: sql_query_generated={sql_query_generated}, query_results_exists={query_results is not None}, query_results_success={query_results.get('success') if query_results else False}")
            final_status = "success" if (sql_query_generated and query_results and query_results.get('success')) else "warning"
            logger.info(f"🎯 FINAL STATUS: {final_status}")
            
            return SqlQueryResponse(
                natural_language_answer=final_explanation,
                sql_query=final_sql_query,
                token_usage=token_usage,
                latency_ms=latency_ms,
                provider=provider,
                model=model,
                status=final_status,
                # Internal fields for debugging/logging
                session_id=session_id,
                query_results=query_results['results'] if query_results and query_results.get('success') else None,  # Pass only the results list
                table_info=table_info,
                validation_attempts=len(validation_attempts),
                timestamp=end_time
            )
            
        except Exception as e:
            logger.error(f"Error processing SQL query: {e}")
            end_time = datetime.now()
            latency_ms = int((end_time - start_time).total_seconds() * 1000)
            
            provider = os.getenv('PROVIDER', 'openai')
            model = os.getenv('MODEL_NAME', 'gpt-4o')
            
            return SqlQueryResponse(
                natural_language_answer=f"I apologize, but I encountered an error while processing your query: {str(e)}",
                sql_query="-- Error generating SQL query",
                token_usage={"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
                latency_ms=latency_ms,
                provider=provider,
                model=model,
                status="error",
                # Internal fields
                session_id=session_id,
                query_results=None,
                table_info=[],
                validation_attempts=1,
                timestamp=end_time
            )
    
    def clear_session(self, session_id: str) -> bool:
        """Clear a specific session"""
        if session_id in self.sessions:
            del self.sessions[session_id]
            return True
        return False
    
    def get_session_history(self, session_id: str) -> List[Dict]:
        """Get conversation history for a session"""
        return self.sessions.get(session_id, [])

# Global instance
sql_chatbot_service = SqlChatbotService()
