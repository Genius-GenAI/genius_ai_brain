from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict
from .services.wiki_service import WikiService
from .services.summary_service import SummaryService
from typing import Optional
import datetime

app = FastAPI()
wiki_service = WikiService()
summary_service = SummaryService()


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


#
# @app.get("/wiki/content")
# async def get_wiki_content(page_id: str, space_key: str) -> Dict[str, str]:
#     """
#     Get wiki page content
#     """
#     try:
#         content = await wiki_service.get_wiki_content(page_id, space_key)
#         return {"content": content}
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))


# @app.post("/wiki/merge-content")
# async def merge_wiki_content(request: MergeContentRequest) -> Dict[str, str]:
#     """
#     Merge new content into wiki page
#     """
#     content = await wiki_service.get_wiki_content(request.page_id, request.space_key)
#     current_date = datetime.datetime.now()
#     try:
#         merge_wiki_content = await wiki_service.merge_wiki_content(
#             content,
#             request.specification_content,
#             request.thread_slack_url,
#             current_date.strftime("%B %d %Y")
#
#         )
#
#         updated_content = await wiki_service.update_wiki_with_merged_content(
#             request.page_id,
#             request.space_key,
#             merge_wiki_content
#         )
#
#         return {"content": updated_content}
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))

#
# @app.post("/slack/summarize")
# async def summarize_content(request: SummaryRequest):
#     """
#     Summarize the provided content
#     """
#     try:
#         summary = await summary_service.summarize_content(request.content, request.max_length)
#         return {"summary": summary}
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))


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
