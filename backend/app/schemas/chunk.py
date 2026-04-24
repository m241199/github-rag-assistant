from pydantic import BaseModel
from typing import Any


class ChunkResponse(BaseModel):
    id: str
    text: str
    metadata_json: dict[str, Any]