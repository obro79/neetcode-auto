from pydantic import BaseModel, Field

from app.enums import Confidence


class CompletionRequest(BaseModel):
    slug: str
    confidence: Confidence | None = None
    source: str = Field(default="manual", description="leetcode, neetcode, or manual")


class CompletionResponse(BaseModel):
    slug: str
    title: str
    review_stage: str
    next_review: str | None
    confidence: Confidence | None
    daily_slot: str
