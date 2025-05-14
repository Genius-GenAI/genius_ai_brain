from .session_service import SessionService

class SummaryService:
    def __init__(self):
        self.session_service = SessionService()
        
    async def summarize_content(self, content: str, max_length: int = 500) -> str:
        """
        Call the agent to summarize the provided content
        """
        try:
            # Create a session if needed
            await self.session_service.create_session()
            
            # Prepare the summary request message
            message = f"Please summarize the following thread in {max_length} characters or fewer: {content}. Output only the core requirements as a software feature specification. Avoid explanations or phrases like 'This is a summary'. Format the output as concise bullet points if applicable."
            
            # Query the agent to summarize the content
            response = await self.session_service.query_agent(message)
            
            # Extract summary from the agent's response
            # Note: You'll need to adjust this based on your agent's actual response format
            if isinstance(response, list) and len(response) > 0:
                for event in response:
                    if "content" in event and "parts" in event["content"]:
                        for part in event["content"]["parts"]:
                            if "text" in part:
                                return part["text"].replace("```","")
            raise Exception("Could not extract summary from agent response")
            
        except Exception as e:
            raise Exception(f"Failed to summarize content: {str(e)}") 