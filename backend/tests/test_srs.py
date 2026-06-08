from datetime import date

import pytest

from app.enums import Confidence, ReviewStage
from app.services.srs import advance_stage, apply_completion, compute_next_review


def test_advance_stage_progression() -> None:
    assert advance_stage(ReviewStage.NEW) == ReviewStage.ONE_DAY
    assert advance_stage(ReviewStage.THIRTY_DAY) == ReviewStage.MASTERED
    assert advance_stage(ReviewStage.MASTERED) == ReviewStage.MASTERED


@pytest.mark.parametrize(
    ("stage", "expected"),
    [
        (ReviewStage.ONE_DAY, date(2026, 6, 8)),
        (ReviewStage.THREE_DAY, date(2026, 6, 10)),
        (ReviewStage.MASTERED, None),
    ],
)
def test_compute_next_review(stage: ReviewStage, expected: date | None) -> None:
    assert compute_next_review(stage, date(2026, 6, 7)) == expected


def test_struggling_forces_one_day_interval() -> None:
    stage, next_review, confidence = apply_completion(
        review_stage=ReviewStage.NEW,
        confidence=Confidence.GETTING_THERE,
        new_confidence=Confidence.STRUGGLING,
        today=date(2026, 6, 7),
    )
    assert stage == ReviewStage.ONE_DAY
    assert next_review == date(2026, 6, 8)
    assert confidence == Confidence.STRUGGLING


def test_preserve_confidence_when_not_provided() -> None:
    _, _, confidence = apply_completion(
        review_stage=ReviewStage.ONE_DAY,
        confidence=Confidence.SOLID,
        new_confidence=None,
        today=date(2026, 6, 7),
    )
    assert confidence == Confidence.SOLID
