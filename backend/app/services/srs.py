from datetime import date, timedelta

from app.core.srs_config import SrsConfig, get_srs_config
from app.enums import Confidence, DailySlot, ReviewStage


def advance_stage(current: ReviewStage, config: SrsConfig | None = None) -> ReviewStage:
    progression = (config or get_srs_config()).srs.stage_progression()
    try:
        index = progression.index(current)
    except ValueError:
        return ReviewStage.MASTERED
    if index >= len(progression) - 1:
        return ReviewStage.MASTERED
    return progression[index + 1]


def compute_next_review(
    stage: ReviewStage,
    today: date,
    config: SrsConfig | None = None,
) -> date | None:
    intervals = (config or get_srs_config()).srs.stage_intervals()
    interval = intervals.get(stage)
    if interval is None:
        return None
    return today + timedelta(days=interval)


def apply_completion(
    *,
    review_stage: ReviewStage,
    confidence: Confidence | None,
    new_confidence: Confidence | None,
    today: date,
    config: SrsConfig | None = None,
) -> tuple[ReviewStage, date | None, Confidence | None]:
    cfg = config or get_srs_config()
    resolved_confidence = new_confidence if new_confidence is not None else confidence
    new_stage = advance_stage(review_stage, cfg)
    next_review = compute_next_review(new_stage, today, cfg)

    if resolved_confidence == Confidence.STRUGGLING:
        next_review = today + timedelta(days=cfg.srs.struggling_interval_days)

    return new_stage, next_review, resolved_confidence


def completion_fields(today: date) -> dict:
    return {
        "solved": True,
        "last_practiced": today,
        "daily_slot": DailySlot.DONE,
    }
