
from typing import Dict, Any
from .session_service import SessionService
from .summary_service import SummaryService
import json


class WikiService:
    def __init__(self):
        self.session_service = SessionService()
        self.summary_service = SummaryService(session_service=self.session_service)

    def _extract_content_from_response(self, response: list) -> str:
        """
        Extract content from the assistant's response based on content type.
        
        Args:
            response: The agent's response list
            
        Returns:
            Extracted content as string
        """
        if not isinstance(response, list):
            print(f"Invalid response format: {type(response)}")
            print(f"Response content: {response}")
            raise Exception("Invalid response format: expected list")

        # Get the last response from the assistant
        for event in reversed(response):
            if not isinstance(event, dict):
                print(f"Invalid event format: {type(event)}")
                continue
                
            if (event.get("author") == "assistant" and
                    isinstance(event.get("content"), dict) and
                    isinstance(event["content"].get("parts"), list)):
                
                for part in event["content"]["parts"]:
                    if not isinstance(part, dict):
                        print(f"Invalid part format: {type(part)}")
                        continue

                    if "text" in part and isinstance(part["text"], str):
                        text = part["text"]
                        # Clean up the text
                        cleaned_text = text.replace("```html", "").replace("```", "").strip()
                        if cleaned_text:
                            return cleaned_text
                        else:
                            print("Extracted text was empty after cleaning")

        print("Could not find valid content in response")
        print(f"Full response: {response}")
        raise Exception("Could not find valid content in assistant response")

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

    async def get_wiki_content(self, wiki_url: str) -> Dict[str, str]:
        """
        Call the agent to get wiki page content and return a dictionary containing title and content
        """
        try:
            # Query the agent to get wiki content
            message = (
                f"Please help retrieve the content, the title of the wiki page {wiki_url} "
                f"Do not summarize the wiki content and please do not convert content to markdown. "
                f"convert_to_markdown should be False. "
                f"Please do not include any your description. "
                f"Please return only title, content in JSON format with key 'page_title','content'"
            )
            response = await self.session_service.query_agent(message)

            # Extract and parse the JSON response
            for event in reversed(response):
                if (event.get("author") == "assistant" and
                        "content" in event and
                        "parts" in event["content"]):
                    for part in event["content"]["parts"]:
                        if "text" in part:
                            try:
                                # Parse the JSON response
                                json_response = json.loads(part["text"])
                                if not isinstance(json_response, dict):
                                    raise Exception("Response is not a JSON object")

                                # Validate required fields
                                if "page_title" not in json_response or "content" not in json_response:
                                    raise Exception("Missing required fields in JSON response")

                                return {
                                    "page_title": json_response["page_title"],
                                    "content": json_response["content"]
                                }
                            except json.JSONDecodeError as e:
                                raise Exception(f"Failed to parse JSON response: {str(e)}")

            raise Exception("Could not find valid JSON response in assistant response")

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
            
            - **Item**: A brief summary of the new Specification
            - **Specification**: The detailed description of new Specification provided below
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

            # Prepare the update message
            update_message = f"""
            Please update the following origin wiki content by appending a new row to the table under the "Update Specification" section.

            The new row must include:
            - Item: A brief summary of the new specification
            - Specification: The detailed description provided below
            - Created Date: {created_date}
            - Thread Slack URL: {thread_slack_url}
            - Category: Select one of the following: "Login & Setup", "Home", or "Shopping Cart" — choose the most relevant

            Please make sure to **retain the original format** of the table, and place the new row **after any existing rows** in the table under the "Update Specification" section. Do not modify any other parts of the wiki content.
            Please do not include any your description, explanation. I only need the final content in your output

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

            # Extract and return only the merged content
            return self._extract_content_from_response(response)

        except Exception as e:
            raise Exception(f"Failed to merge wiki content: {str(e)}")

    async def update_wiki_with_merged_content(
            self,
            wiki_url: str,
            merged_content: str,
            page_title: str
    ) -> str:
        """
        Update wiki page with the merged content from /wiki/merge-content and return only the updated content
        """
        try:
            if not merged_content or not merged_content.strip():
                raise Exception("Merged content cannot be empty or whitespace only")

            if not page_title or not page_title.strip():
                raise Exception("Page title cannot be empty")

            # Ensure we have a valid session
            if not hasattr(self.session_service, 'session_id'):
                await self.session_service.create_session()

            update_message = f"""
            Please update the wiki page {wiki_url} with the following content.
            Important instructions:
            1. Keep the page title as: {page_title}
            2. Keep all existing metadata and structure
            3. Only update the content while preserving the page format
            4. Ensure the content is properly formatted in Confluence wiki markup
            5. Do not add any explanations or descriptions in your response
            6. Return only the final wiki content
            
            Content to update:
            ---
            {merged_content}
            ---
            """

            # Log the update message for debugging
            print(f"Update message for {wiki_url}:")
            print(update_message)
            
            response = await self.session_service.query_agent(update_message)
            if not response:
                raise Exception("No response received from agent for update")

            # Log the raw response for debugging
            print(f"Raw response from agent:")
            print(response)

            content = self._extract_content_from_response(response)
            if not content or not content.strip():
                raise Exception("Failed to extract valid content from update response")

            # Log the extracted content for debugging
            print(f"Extracted content:")
            print(content)

            return content

        except Exception as e:
            print(f"Error in update_wiki_with_merged_content: {str(e)}")
            raise Exception(f"Failed to update wiki with merged content: {str(e)}")

    async def process_conversation_to_wiki(
            self,
            conversation: str,
            wiki_url: str,
            thread_slack_url: str,
            created_date: str
    ) -> Dict[str, str]:
        """
        Process a complete workflow:
        1. Summarize conversation into a software feature specification
        2. Get wiki content
        3. Merge summary into wiki content
        4. Update wiki page
        """
        try:
            # Create a session if needed
            await self.session_service.create_session()

            # Step 1: Summarize the conversation
            summary_content = await self.summary_service.summarize_content(conversation)
            if not summary_content:
                raise Exception("Failed to generate summary content")

            # Step 2: Get wiki content
            wiki_data = await self.get_wiki_content(wiki_url)
            if not wiki_data or "content" not in wiki_data or "page_title" not in wiki_data:
                raise Exception("Failed to get wiki content or missing required fields")

            page_title = wiki_data["page_title"]
            page_content = wiki_data["page_title"]

            # Step 3: Merge the summary into wiki content
            merged_content = await self.merge_wiki_content(
                page_content,
                summary_content,
                thread_slack_url,
                created_date
            )

            print("Merged content:", merged_content)

            # Step 4: Update the wiki page
            final_content = await self.update_wiki_with_merged_content(
                wiki_url,
                merged_content,
                page_title
            )

            return {
                "update_content": final_content,
                "summary_content": summary_content
            }

        except Exception as e:
            raise Exception(f"Failed to process conversation to wiki: {str(e)}")
