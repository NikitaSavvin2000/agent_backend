from typing import Optional

from pydantic import BaseModel


class HellowRequest(BaseModel):
    names: list[str]


class ChatRequest(BaseModel):
    session_id: str
    message: Optional[str] = None
    chat_id: Optional[str] = None
    data_json: Optional[list[dict]] = None
    filename: Optional[str] = None

class ChatDataRequest(BaseModel):
    session_id: str
    chat_id: str
