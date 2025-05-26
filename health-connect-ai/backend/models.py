from pydantic import BaseModel


class ChatInput(BaseModel):
    sender_id: str
    message: str
