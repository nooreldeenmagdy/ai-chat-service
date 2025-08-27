# AI Chat Service

This project implements a minimal AI chat service using FastAPI and Streamlit, integrating with OpenAI services. It exposes a REST API for chat interactions and provides a web-based interface for users.

## Project Structure

```
ai-chat-service
├── src/
│   ├── __init__.py
│   ├── main.py
│   ├── api/
│   │   ├── __init__.py
│   │   └── routes.py
│   ├── services/
│   │   ├── __init__.py
│   │   ├── openai_service.py
│   │   └── forecasting_service.py
│   └── models/
│       ├── __init__.py
│       └── chat_models.py
├── streamlit_app/
│   ├── __init__.py
│   └── app.py
├── requirements.txt
├── .env.example
├── faq.json
├── Dockerfile
├── docker-compose.yml
├── start.bat
├── start.sh
└── README.md
```

## Setup Instructions

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd ai-chat-service
   ```

2. **Create a virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables:**
   Copy `.env.example` to `.env` and fill in the required values, such as your OpenAI API key.

## Running the Application

To start the FastAPI application, run:

```bash
uvicorn src.main:app --reload
```

To run the Streamlit application, execute:

```bash
streamlit run streamlit_app/app.py
```

## API Endpoints

- **POST /api/chat**: Send a message to the AI model and receive a response.
- **GET /api/health**: Check the health status of the service.

## Sample Usage

You can test the API using `curl` or Postman. Here’s an example using `curl`:

```bash
curl -X POST "http://localhost:8000/api/chat" -H "Content-Type: application/json" -d '{"message": "Hello, AI!"}'
```

## License

This project is licensed under the MIT License.