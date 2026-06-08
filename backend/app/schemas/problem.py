from pydantic import BaseModel, ConfigDict

from app.enums import Confidence, DailySlot, Difficulty, ReviewStage


class ProblemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    slug: str
    title: str
    pattern: str
    difficulty: Difficulty
    leetcode_url: str
    neetcode_url: str
    sort_order: int


class ProgressOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    solved: bool
    review_stage: ReviewStage
    next_review: str | None
    last_practiced: str | None
    confidence: Confidence | None
    daily_slot: DailySlot | None


class ProblemWithProgressOut(ProblemOut):
    progress: ProgressOut | None = None
