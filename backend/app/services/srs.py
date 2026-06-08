from datetime import date, timedelta

from app.enums import (
    STAGE_INTERVALS,
    STAGE_PROGRESSION,
    Confidence,
    DailySlot,
    ReviewStage,
)


def advance_stage(current: ReviewStage) -> ReviewStage:
    try:
        index = STAGE_PROGRESSION.index(current)
    except ValueError:
        return ReviewStage.MASTERED
    if index >= len(STAGE_PROGRESSION) - 1:
        return ReviewStage.MASTERED
    return STAGE_PROGRESSION[index + 1]


def compute_next_review(stage: ReviewStage, today: date) -> date | None:
    interval = STAGE_INTERVALS.get(stage)
    if interval is None:
        return None
    return today + timedelta(days=interval)


def apply_completion(
    *,
    review_stage: ReviewStage,
    confidence: Confidence | None,
    new_confidence: Confidence | None,
    today: date,
) -> tuple[ReviewStage, date | None, Confidence | None]:
    resolved_confidence = new_confidence if new_confidence is not None else confidence
    new_stage = advance_stage(review_stage)
    next_review = compute_next_review(new_stage, today)

    if resolved_confidence == Confidence.STRUGGLING:
        next_review = today + timedelta(days=1)

    return new_stage, next_review, resolved_confidence


def completion_fields(today: date) -> dict:
    return {
        "solved": True,
        "last_practiced": today,
        "daily_slot": DailySlot.DONE,
    }
