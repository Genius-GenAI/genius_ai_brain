import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    AGENT_BASE_URL: str = os.getenv("AGENT_BASE_URL", "http://0.0.0.0:8000")
    API_PORT: int = int(os.getenv("API_PORT", "8081"))
    API_HOST: str = os.getenv("API_HOST", "0.0.0.0")
    
    # Session defaults
    APP_NAME: str = "agents"
    DEFAULT_USER_ID: str = "u_123"

settings = Settings() 