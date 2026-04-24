from pydantic import BaseModel
from typing import Any


class ChatRequest(BaseModel):
    repo_id: str
    question: str


class ChatSource(BaseModel):
    file_path: str
    section_title: str | None = None
    symbol_name: str | None = None
    snippet: str


class ChatResponse(BaseModel):
    answer: str
    sources: list[ChatSource]