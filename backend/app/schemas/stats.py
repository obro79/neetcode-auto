from pydantic import BaseModel

from app.enums import ReviewStage


class ConfidenceBreakdown(BaseModel):
    struggling: int
    getting_there: int
    solid: int
    unset: int


class PatternStat(BaseModel):
    pattern: str
    solved: int
    total: int


class StatsSummaryOut(BaseModel):
    total: int
    solved: int
    unsolved: int
    by_confidence: ConfidenceBreakdown
    by_review_stage: dict[ReviewStage, int]
    by_pattern: list[PatternStat]
    due_today: int
    due_overdue: int
    mastered: int
