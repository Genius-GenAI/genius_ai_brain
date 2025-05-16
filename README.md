# Wiki Agent API

This FastAPI application provides endpoints to interact with Atlassian wiki pages through an ADK agent. It supports getting wiki content, summarizing content, and updating wiki pages with summaries.

## Setup Options

You can run the application either using Docker or locally. Choose one of the following methods:

### Option 1: Docker Setup (Recommended)

1. Ensure you have Docker and Docker Compose installed on your system.

2. Create a `.env` file in the root directory with the following variables:
```
AGENT_BASE_URL=http://agent:8000  # Docker service name for agent
API_PORT=8081                     # Port for this API application
```

3. Build and start the services using Docker Compose:
```bash
# Build and start both services
docker-compose up --build

# Or run in detached mode
docker-compose up -d

# To stop the services
docker-compose down
```

The services will be available at:
- API Application: `http://localhost:8081`
- Agent Service: `http://localhost:8000`

### Option 2: Local Setup

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

4. Start the services:

   a. First, start the ADK agent server:
   ```bash
   adk api_server  # This will run on port 8000
   ```

   b. Then start the API application:
   ```bash
   uvicorn app.main:app --host 0.0.0.0 --port 8081 --reload
   ```

## Docker Configuration

The application uses two Docker containers:

1. **Agent Container** (`Dockerfile.agent`):
   - Runs the ADK agent service
   - Exposes port 8000
   - Mounts the `agents/` directory for development

2. **App Container** (`Dockerfile.app`):
   - Runs the FastAPI application
   - Exposes port 8081
   - Mounts the `app/` directory for development
   - Communicates with the agent container

The containers are configured to work together using Docker Compose, which:
- Sets up a bridge network for container communication
- Manages environment variables
- Handles volume mounting for development
- Ensures proper service startup order

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

## Development

### Docker Development
- The Docker setup uses volume mounts for both the agent and app code
- Changes to the code are reflected immediately without rebuilding
- Logs from both services can be viewed using:
  ```bash
  docker-compose logs -f
  ```

### Local Development
- Use the `--reload` flag with uvicorn for automatic reloading
- Monitor the agent and app logs separately
- Ensure both services are running on the correct ports

## Troubleshooting

### Docker Issues
1. If containers fail to start:
   ```bash
   # Check container logs
   docker-compose logs
   
   # Rebuild containers
   docker-compose up --build --force-recreate
   ```

2. If services can't communicate:
   - Verify the network exists: `docker network ls`
   - Check container status: `docker-compose ps`
   - Ensure environment variables are set correctly

### Local Setup Issues
1. Port conflicts:
   - Ensure ports 8000 and 8081 are available
   - Check if other services are using these ports

2. Agent connection issues:
   - Verify the agent is running
   - Check the AGENT_BASE_URL in .env
   - Ensure network connectivity

## ADK Agent Integration

This application integrates with the Google Agent Development Kit (ADK) agent. The agent handles:
- Wiki content retrieval
- Content summarization
- Wiki content updates

Make sure your ADK agent is properly configured to handle these operations through natural language queries. 