from typing import List, Optional
from pydantic import BaseModel


class ChatRequest(BaseModel):
    user_id: str
    message: str


class ChatResponse(BaseModel):
    response: str
    history: Optional[List[dict]] = None


class UpsertDocumentRequest(BaseModel):
    text: str
    doc_id: Optional[str] = None


class UpsertDocumentResponse(BaseModel):
    success: bool
    doc_id: str
