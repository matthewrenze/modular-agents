from __future__ import annotations
from pydantic import BaseModel

class Review(BaseModel):
    steps: dict[str, str] = {}
    loops: str = ""
    summary: str = ""
    category: str = ""
    advice: str = ""