import markdown
import json
from typing import Dict, Any
from .session_service import SessionService


class WikiService:
    def __init__(self):
        self.session_service = SessionService()

    def _extract_wiki_content(self, response: list) -> str:
        """
        Extract wiki content from the final assistant's response
        """
        if not isinstance(response, list):
            raise Exception("Invalid response format")

        # Get the last response from the assistant
        for event in reversed(response):
            if (event.get("author") == "assistant" and
                    "content" in event and
                    "parts" in event["content"]):

                for part in event["content"]["parts"]:
                    if "text" in part:
                        text = part["text"]

                        return text.replace("```html", "").replace("```", "")

        raise Exception("Could not find wiki content in assistant response")

    def _extract_merged_content(self, response: list) -> str:
        """
        Extract merged content from the agent's response for /wiki/merge-content endpoint
        """
        if not isinstance(response, list):
            raise Exception("Invalid response format")

        # Get the last response from the assistant
        for event in reversed(response):
            if (event.get("author") == "assistant" and
                    "content" in event and
                    "parts" in event["content"]):

                for part in event["content"]["parts"]:
                    if "text" in part:
                        text = part["text"]
                        return text.replace("```html", "").replace("```", "")

        raise Exception("Could not find merged content in assistant response")

    def _extract_updated_content(self, response: list) -> str:
        """
        Extract updated wiki content from the final assistant's response
        """
        if not isinstance(response, list):
            raise Exception("Invalid response format")
        for event in reversed(response):
            if (event.get("author") == "assistant" and
                    "content" in event and
                    "parts" in event["content"]):
                for part in event["content"]["parts"]:
                    if "text" in part:
                        return part["text"]
        raise Exception("Could not find updated content in assistant response")

    def _extract_page_name(self, response: list) -> str:
        """
        Extract wiki page name from the assistant's response by looking for the first heading
        """
        if not isinstance(response, list):
            raise Exception("Invalid response format")

        # Get the last response from the assistant
        for event in reversed(response):
            if (event.get("author") == "assistant" and
                    "content" in event and
                    "parts" in event["content"]):
                for part in event["content"]["parts"]:
                    if "text" in part:
                        text = part["text"]
                        # Try to find the first heading (h1) in the content
                        lines = text.split('\n')
                        for line in lines:
                            # Look for markdown h1 heading (# Title)
                            if line.strip().startswith('# '):
                                return line.strip()[2:].strip()
                            # Look for HTML h1 heading (<h1>Title</h1>)
                            elif line.strip().startswith('<h1>'):
                                return line.strip()[4:-5].strip()

        # If no heading found, try to get the first non-empty line
        for event in reversed(response):
            if (event.get("author") == "assistant" and
                    "content" in event and
                    "parts" in event["content"]):
                for part in event["content"]["parts"]:
                    if "text" in part:
                        text = part["text"]
                        lines = text.split('\n')
                        for line in lines:
                            if line.strip():
                                return line.strip()

        raise Exception("Could not find page name in assistant response")

    async def get_wiki_content(self, page_id: str, space_key: str) -> str:
        """
        Call the agent to get wiki page content and return only the content in markdown format
        """
        try:
            # Create a session if needed
            await self.session_service.create_session()

            # Query the agent to get wiki content
            message = (
                f"Please help retrieve the content and page title of the wiki page {page_id} in the space {space_key}. "
                f"Do not summarize the wiki content and please do not convert content to markdown. "
                f"convert_to_markdown should be False. "
                f"Should not include metadata in result. "
                f"include_metadata should be False"
                f"Please do not include any your description, explanation"
            )
            response = await self.session_service.query_agent(message)

            print("******")
            print(response)
            print("******")

            # Extract and return only the wiki content
            return self._extract_wiki_content(response)

        except Exception as e:
            raise Exception(f"Failed to get wiki content: {str(e)}")

    async def update_wiki_content(
            self,
            page_id: str,
            space_key: str,
            wiki_content: str,
            summary_content: str,
            thread_slack_url: str,
            created_date: str
    ) -> Dict[str, Any]:
        """
        Update wiki page with new content
        """
        try:
            # Create a session if needed
            await self.session_service.create_session()

            # Prepare the update message
            update_message = f"""
            Please update the following origin wiki content by appending a new row to the "Update Specification" table under the "Update Specification" section.

            The new row must include:
            
            - **Item**: A brief summary of the new feature or requirement
            - **Specification**: The detailed description provided below
            - **Created Date**: Use the provided creation date
            - **Thread Slack URL**: Use the provided Slack thread URL
            - **Category**: Select one of the following: "Login & Setup", "Home", or "Shopping Cart" — choose the most relevant
            
            Please make sure to **retain the original format** of the table (Markdown-style), and place the new row **after any existing rows** in the "Update Specification" table. Do not modify any other parts of the wiki content.
            You must output the original wiki content in Markdown format.Please do not include any your description, explanation such as : 'Here's the update content in Markdown format'. I only need the final content in your output
            
            ---
            ### Origin wiki content 
            {wiki_content}
            
            ### New Specification
            {summary_content}
            
            ### Created Date
            {created_date}
      
            ###  Thread Slack URL 
            {thread_slack_url}
            ---
            """

            # Query the agent to update the content
            response = await self.session_service.query_agent(update_message)

            # Return the agent's response
            return response

        except Exception as e:
            raise Exception(f"Failed to update wiki content: {str(e)}")

    async def merge_wiki_content(
            self,
            wiki_content: str,
            summary_content: str,
            thread_slack_url: str,
            created_date: str
    ) -> str:
        """
        Merge new content into the wiki page and return only the merged content
        """
        try:
            # Create a session if needed
            await self.session_service.create_session()

            # Prepare the update message
            update_message = f"""
            Please update the following origin wiki content by appending a new row to the table under the "Update Specification" section .

            The new row must include:
            
            - **Item**: A brief summary of the new specification
            - **Specification**: The detailed description of the new specification provided below.
            - **Created Date**: Use the provided creation date
            - **Thread Slack URL**: Use the provided Slack thread URL
            - **Category**: Select one of the following: "Login & Setup", "Home", or "Shopping Cart" — choose the most relevant
            
            Please make sure to **retain the original format** of the table, and place the new row **after any existing rows** in the table under the "Update Specification" section. Do not modify any other parts of the wiki content.
            Please do not include any your description, explanation. I only need the final content in your output
        
            ---
            ### Origin Content
            {wiki_content}
            
            ### New Specification
            {summary_content}
            
            ### Created Date
            {created_date}
      
            ###  Thread Slack URL 
            {thread_slack_url}
            ---
            """

            # Query the agent to update the content
            response = await self.session_service.query_agent(update_message)

            # Extract and return only the merged content
            return self._extract_merged_content(response)

        except Exception as e:
            raise Exception(f"Failed to merge wiki content: {str(e)}")

    async def update_wiki_with_merged_content(
            self,
            page_id: str,
            space_key: str,
            merged_content: str
    ) -> str:
        """
        Update wiki page with the merged content from /wiki/merge-content and return only the updated content
        """
        try:
            await self.session_service.create_session()
            update_message = f"""
            Please update the wiki page {page_id} in space {space_key} with the following content. You should keep the wiki page title
            ---
            {merged_content}
            ---
            """
            response = await self.session_service.query_agent(update_message)
            return self._extract_updated_content(response)
        except Exception as e:
            raise Exception(f"Failed to update wiki with merged content: {str(e)}")
