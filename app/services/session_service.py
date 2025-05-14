import requests
import uuid
from typing import Dict, Any
from ..config import settings

class SessionService:
    def __init__(self):
        self.agent_base_url = settings.AGENT_BASE_URL
        self.app_name = settings.APP_NAME
        self.user_id = settings.DEFAULT_USER_ID
        
    def _generate_session_id(self) -> str:
        """
        Generate a unique session ID
        """
        return f"s_{uuid.uuid4().hex[:8]}"
        
    async def create_session(self, state: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Create a new session with the agent using a unique session ID
        """
        try:
            if state is None:
                state = {}
            
            # Generate a new session ID for each request
            session_id = self._generate_session_id()
                
            response = requests.post(
                f"{self.agent_base_url}/apps/{self.app_name}/users/{self.user_id}/sessions/{session_id}",
                json={"state": state}
            )
            response.raise_for_status()
            
            # Store the session ID for the query
            self.session_id = session_id
            return response.json()
        except requests.exceptions.RequestException as e:
            raise Exception(f"Failed to create session: {str(e)}")
            
    async def query_agent(self, message: str) -> Dict[str, Any]:
        """
        Send a query to the agent using the current session
        """
        try:
            if not hasattr(self, 'session_id'):
                raise Exception("No active session. Please create a session first.")
                
            response = requests.post(
                f"{self.agent_base_url}/run",
                json={
                    "app_name": self.app_name,
                    "user_id": self.user_id,
                    "session_id": self.session_id,
                    "new_message": {
                        "role": "user",
                        "parts": [{
                            "text": message
                        }]
                    }
                }
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise Exception(f"Failed to query agent: {str(e)}")
            
    def set_user_id(self, user_id: str):
        """
        Update user ID if needed
        """
        self.user_id = user_id 