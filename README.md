# Wiki Agent API

This FastAPI application provides endpoints to interact with Atlassian wiki pages through an ADK agent. It supports getting wiki content, summarizing content, and updating wiki pages with summaries.

## Setup

1. Create a virtual environment and activate it:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Create a `.env` file in the root directory with the following variables:
```
AGENT_BASE_URL=http://0.0.0.0:8000  # Your ADK agent server URL
API_PORT=8081                        # Port for this API application
```

## Running the Application

1. First, ensure your ADK agent server is running. You can start it using:
```bash
adk api_server  # This will run on port 8000
```

2. Then start this API application:
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8081 --reload
```

The API will be available at `http://localhost:8081`

## API Endpoints

### 1. Get Wiki Content
- **Endpoint**: POST `/wiki/content`
- **Request Body**:
```json
{
    "page_id": "your-page-id",
    "space_key": "your-space-key"
}
```
- **Response**: Returns the wiki content in markdown format
- **Note**: This endpoint creates a session with the ADK agent and sends a query to get the wiki content

### 2. Summarize Content
- **Endpoint**: POST `/wiki/summarize`
- **Request Body**:
```json
{
    "content": "content to summarize",
    "max_length": 500  // optional
}
```
- **Response**: Returns the summarized content
- **Note**: This endpoint creates a session with the ADK agent and sends a query to summarize the content

### 3. Update Wiki Content
- **Endpoint**: POST `/wiki/update`
- **Request Body**:
```json
{
    "page_id": "your-page-id",
    "space_key": "your-space-key",
    "summary_content": "summary to add"
}
```
- **Response**: Returns confirmation of the update
- **Note**: This endpoint creates a session with the ADK agent and sends a query to update the wiki content

## Session Management

The application uses the ADK agent's session management system. By default, it uses:
- App name: "agents"
- User ID: "u_123"
- Session ID: "s_123"

These can be modified by updating the `SessionService` class if needed.

## API Documentation

Once the application is running, you can access the interactive API documentation at:
- Swagger UI: `http://localhost:8081/docs`
- ReDoc: `http://localhost:8081/redoc`

## ADK Agent Integration

This application integrates with the Google Agent Development Kit (ADK) agent. The agent handles:
- Wiki content retrieval
- Content summarization
- Wiki content updates

Make sure your ADK agent is properly configured to handle these operations through natural language queries. 