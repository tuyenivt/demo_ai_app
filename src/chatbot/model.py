from typing import List, Optional
from pydantic import BaseModel


class ChatRequest(BaseModel):
    user_id: str
    message: str


class ChatResponse(BaseModel):
    response: str
    history: Optional[List[dict]] = None


class UpsertResponse(BaseModel):
    success: bool
    doc_id: str
