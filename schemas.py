"""Request models for the JSON API."""
from pydantic import BaseModel, Field


class PromptRequest(BaseModel):
    prompt: str = Field(..., min_length=3, max_length=1000, examples=["A brave fox explores an enchanted forest."])
    character_name: str = Field("Hero", min_length=1, max_length=60)
    setting: str = Field("forest", min_length=1, max_length=80)
    tone: str = Field("dramatic", min_length=1, max_length=40)
    style: str = Field("comic book", min_length=1, max_length=40)
