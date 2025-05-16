from typing import Dict, Any
from .session_service import SessionService
from .summary_service import SummaryService
import json
import logging
import time
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger('WikiService')

class WikiService:
    def __init__(self):
        self.session_service = SessionService()
        self.summary_service = SummaryService(session_service=self.session_service)
        logger.info("WikiService initialized")

    def _extract_content_from_response(self, response: list) -> str:
        """
        Extract content from the assistant's response based on content type.
        
        Args:
            response: The agent's response list
            
        Returns:
            Extracted content as string
        """
        logger.debug("Starting content extraction from response")
        if not isinstance(response, list):
            logger.error(f"Invalid response format: {type(response)}")
            logger.error(f"Response content: {response}")
            raise Exception("Invalid response format: expected list")

        # Get the last response from the assistant
        for event in reversed(response):
            if not isinstance(event, dict):
                logger.warning(f"Invalid event format: {type(event)}")
                continue
                
            if (event.get("author") == "assistant" and
                    isinstance(event.get("content"), dict) and
                    isinstance(event["content"].get("parts"), list)):
                
                for part in event["content"]["parts"]:
                    if not isinstance(part, dict):
                        logger.warning(f"Invalid part format: {type(part)}")
                        continue

                    if "text" in part and isinstance(part["text"], str):
                        text = part["text"]
                        # Clean up the text
                        cleaned_text = text.replace("```html", "").replace("```", "").strip()
                        if cleaned_text:
                            logger.debug("Successfully extracted content")
                            return cleaned_text
                        else:
                            logger.warning("Extracted text was empty after cleaning")

        logger.error("Could not find valid content in response")
        logger.error(f"Full response: {response}")
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
                f"Please return only title, page_id, version, content in JSON format with key 'page_title', 'page_id' ,'version', 'content'"
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
                                json_response = json.loads(part["text"].replace("```json", "").replace("```", ""))
                                if not isinstance(json_response, dict):
                                    raise Exception("Response is not a JSON object")

                                # Validate required fields
                                if "page_title" not in json_response or "content" not in json_response or "page_id" not in json_response or "version" not in json_response:
                                    raise Exception("Missing required fields in JSON response")

                                return {
                                    "page_title": json_response["page_title"],
                                    "page_id": json_response["page_id"],
                                    "content": json_response["content"],
                                    "version": json_response["version"]
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
            page_title: str,
            page_id: str
    ) -> dict[str:str]:
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
            Please update the wiki page: {wiki_url} with the following content. The wiki page id: {page_id}
            Important instructions:
            1. Keep the title as: {page_title}
            2. Keep all existing metadata and structure
            3. Should return version, title, page ID as json format with key 'page_title', 'page_id' ,'version'
            
            Content to update:
            ---
            {merged_content}
            ---
            """
            
            response = await self.session_service.query_agent(update_message)
            if not response:
                raise Exception("No response received from agent for update")

            # Extract and parse the JSON response
            for event in reversed(response):
                if (event.get("author") == "assistant" and
                        "content" in event and
                        "parts" in event["content"]):
                    for part in event["content"]["parts"]:
                        if "text" in part:
                            try:
                                # Parse the JSON response
                                json_response = json.loads(part["text"].replace("```json", "").replace("```", ""))
                                if not isinstance(json_response, dict):
                                    raise Exception("Response is not a JSON object")

                                # Validate required fields
                                if "page_title" not in json_response or "page_id" not in json_response or "version" not in json_response:
                                    raise Exception("Missing required fields in JSON response")

                                return {
                                    "page_title": json_response["page_title"],
                                    "page_id": json_response["page_id"],
                                    "version": json_response["version"]
                                }
                            except json.JSONDecodeError as e:
                                raise Exception(f"Failed to parse JSON response: {str(e)}")

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
        process_start_time = time.time()
        logger.info(f"Starting wiki processing workflow for URL: {wiki_url}")
        logger.info(f"Thread Slack URL: {thread_slack_url}")
        logger.info(f"Created date: {created_date}")

        max_tries = 3
        merged_content = ""
        summary_content = ""

        try:
            # Create a session if needed
            await self.session_service.create_session()
            logger.info("Session created/verified")

            for attempt in range(max_tries):
                attempt_start_time = time.time()
                logger.info(f"Starting attempt {attempt + 1} of {max_tries}")

                try:
                    # Step 1: Summarize the conversation
                    logger.info("Step 1: Starting conversation summarization")
                    step_start_time = time.time()
                    
                    summary_content = await self.summary_service.summarize_content(conversation)
                    if not summary_content:
                        logger.error("Summary content is empty")
                        raise Exception("Failed to generate summary content")
                    
                    step_duration = time.time() - step_start_time
                    logger.info(f"Step 1: Summary generation completed in {step_duration:.2f} seconds")
                    logger.debug(f"Generated summary: {summary_content[:200]}...")  # Log first 200 chars

                    # Step 2: Get wiki content
                    logger.info("Step 2: Retrieving wiki content")
                    step_start_time = time.time()
                    
                    wiki_data = await self.get_wiki_content(wiki_url)
                    if not wiki_data or "content" not in wiki_data or "page_title" not in wiki_data:
                        logger.error("Invalid wiki data received")
                        logger.error(f"Wiki data: {wiki_data}")
                        raise Exception("Failed to get wiki content or missing required fields")

                    page_title = wiki_data["page_title"]
                    page_id = wiki_data["page_id"]
                    version = wiki_data["version"]
                    page_content = wiki_data["content"]
                    
                    step_duration = time.time() - step_start_time
                    logger.info(f"Step 2: Wiki content retrieved in {step_duration:.2f} seconds")
                    logger.info(f"Page details - Title: {page_title}, ID: {page_id}, Version: {version}")
                    logger.debug(f"Page content length: {len(page_content)} characters")

                    # Step 3: Merge the summary into wiki content
                    logger.info("Step 3: Starting content merge")
                    step_start_time = time.time()
                    
                    merged_content = await self.merge_wiki_content(
                        page_content,
                        summary_content,
                        thread_slack_url,
                        created_date
                    )
                    
                    step_duration = time.time() - step_start_time
                    logger.info(f"Step 3: Content merge completed in {step_duration:.2f} seconds")
                    logger.debug(f"Merged content length: {len(merged_content)} characters")

                    # Step 4: Update the wiki page
                    logger.info("Step 4: Starting wiki page update")
                    step_start_time = time.time()
                    
                    result = await self.update_wiki_with_merged_content(
                        wiki_url,
                        merged_content,
                        page_title,
                        page_id
                    )

                    updated_page_title = result["page_title"]
                    updated_page_id = result["page_id"]
                    updated_version = result["version"]
                    
                    step_duration = time.time() - step_start_time
                    logger.info(f"Step 4: Wiki update completed in {step_duration:.2f} seconds")
                    logger.info(f"Updated page details - Title: {updated_page_title}, ID: {updated_page_id}, Version: {updated_version}")

                    attempt_duration = time.time() - attempt_start_time
                    logger.info(f"Attempt {attempt + 1} completed in {attempt_duration:.2f} seconds")

                    if int(updated_version) > int(version):
                        total_duration = time.time() - process_start_time
                        logger.info(f"Wiki update successful! Total process duration: {total_duration:.2f} seconds")
                        return {
                            "result": "SUCCESSFUL TO UPDATE",
                            "merged_content": merged_content,
                            "summary_content": summary_content
                        }

                    logger.warning(f"Version did not increment. Old: {version}, New: {updated_version}")
                    if attempt < max_tries - 1:
                        logger.info("Retrying process...")
                        continue

                    logger.error("All attempts completed but version did not increment")
                    return {
                        "result": "FAILED TO UPDATE",
                        "merged_content": merged_content,
                        "summary_content": summary_content,
                        "error": "Version did not increment after all attempts"
                    }

                except Exception as e:
                    attempt_duration = time.time() - attempt_start_time
                    logger.error(f"Attempt {attempt + 1} failed after {attempt_duration:.2f} seconds")
                    logger.error(f"Error details: {str(e)}")
                    
                    if attempt < max_tries - 1:
                        logger.info("Retrying process...")
                        continue
                    
                    raise

        except Exception as e:
            total_duration = time.time() - process_start_time
            logger.error(f"Wiki processing failed after {total_duration:.2f} seconds")
            logger.error(f"Final error: {str(e)}")
            raise Exception(f"Failed to process conversation to wiki: {str(e)}")
