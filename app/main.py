from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict
from .services.wiki_service import WikiService
from typing import Optional
import datetime

app = FastAPI()
wiki_service = WikiService()


class WikiContentRequest(BaseModel):
    page_id: str
    space_key: str


class MergeContentRequest(BaseModel):
    page_id: str
    space_key: str
    specification_content: str
    thread_slack_url: str


class UpdateWikiRequest(BaseModel):
    page_id: str
    space_key: str
    merged_content: str


class SummaryRequest(BaseModel):
    content: str
    max_length: Optional[int] = 500


class ConversationToWikiRequest(BaseModel):
    conversation: str
    wiki_url: str
    thread_slack_url: str


@app.post("/wiki/process-conversation")
async def process_conversation_to_wiki(request: ConversationToWikiRequest) -> Dict[str, str]:
    """
    Process a complete workflow in one API call:
    1. Summarize conversation into a software feature specification
    2. Get wiki content
    3. Merge summary into wiki content
    4. Update wiki page
    """
    try:
        current_date = datetime.datetime.now()

        result = await wiki_service.process_conversation_to_wiki(
            request.conversation,
            request.wiki_url,
            request.thread_slack_url,
            current_date.strftime("%B %d %Y")
        )

        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
