from typing import Dict
from .session_service import SessionService
import logging
import time

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
        logger.info("WikiService initialized with session and summary services")

    async def _process(
            self,
            conversation: str,
            wiki_url: str,
            thread_slack_url: str,
            created_date: str
    ) -> dict[str:str]:
        """
        Update wiki page with the merged content from /wiki/merge-content and return only the updated content
        """

        try:
            # Ensure we have a valid session
            if not hasattr(self.session_service, 'session_id'):
                logger.info("No active session found, creating new session")
                await self.session_service.create_session()

            update_message = f"""
            Please summarize the below conversation into a new technical specification, formatted as a clear and concise set of requirements. The specification should cover all decisions made regarding [**main topic of the conversation**].
            ### Conversation: [{conversation}]
            ### Additional Context:
                 * **Related [slack_url]:** [{thread_slack_url}]
                 * **Conversation Date:** [{created_date}] 
            After generating the new specification, please get wiki page content from the following wiki page: [{wiki_url}] Then please help include the new specification to the origin wiki page content. Then please update the updated content to the wiki page.
            """

            logger.info("Sending update request to agent")
            response = await self.session_service.query_agent(update_message)

            if not response:
                logger.error("No response received from agent")
                raise ValueError("No response received from agent for update")

            # Extract and parse the JSON response
            logger.info("Processing agent response")
            for event in reversed(response):
                if (event.get("author") == "atlassian_agent" and
                        "content" in event and
                        "parts" in event["content"]):
                    for part in event["content"]["parts"]:
                        if "text" in part:
                            text = part["text"]
                            return {
                                "content": text
                            }

        except Exception as e:
            logger.error(f"Error in wiki processing: {str(e)}", exc_info=True)
            raise

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
        logger.info(f"Starting wiki processing workflow for URL: {wiki_url}")
        logger.info(f"Thread Slack URL: {thread_slack_url}")
        logger.info(f"Created date: {created_date}")

        max_tries = 3
        attempt = 0

        try:
            # Create a session if needed
            await self.session_service.create_session()

            while attempt < max_tries:
                attempt_start_time = time.time()
                attempt += 1
                logger.info(f"Starting attempt {attempt} of {max_tries}")

                try:
                    # Process the wiki update
                    logger.info("Starting wiki processing")

                    result = await self._process(
                        conversation,
                        wiki_url,
                        thread_slack_url,
                        created_date
                    )

                    attempt_end_time = time.time() - attempt_start_time

                    if result:
                        logger.info(
                            f"Wiki update successful! Attempt time: {attempt_end_time} seconds")

                        return {
                            "result": result["content"]
                        }

                    if attempt < max_tries:
                        logger.info("Retrying process...")
                        continue

                    logger.error("All attempts completed but no successful update")
                    return {
                        "result": "FAILED TO UPDATE"
                    }

                except Exception as e:
                    logger.error(f"Error details: {str(e)}", exc_info=True)

                    if attempt < max_tries:
                        logger.info("Retrying process...")
                        continue

                    raise

        except Exception as e:
            logger.error(f"Final error: {str(e)}", exc_info=True)
            raise ValueError(f"Failed to process conversation to wiki: {str(e)}")
