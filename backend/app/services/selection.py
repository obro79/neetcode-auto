from collections import Counter
from dataclasses import dataclass
from datetime import date

from app.enums import (
    CONFIDENCE_PRIORITY,
    DIFFICULTY_ORDER,
    EXCLUDED_PATTERNS,
    FOCUS_PATTERN_ORDER,
    Confidence,
    DailySlot,
    Difficulty,
)


@dataclass(frozen=True)
class ProblemCandidate:
    problem_id: int
    slug: str
    pattern: str
    difficulty: Difficulty
    sort_order: int
    solved: bool
    next_review: date | None
    last_practiced: date | None
    confidence: Confidence | None


@dataclass(frozen=True)
class SelectedDailySet:
    focus_pattern: str | None
    review: list[ProblemCandidate]
    focused_new: list[ProblemCandidate]
    random_new: list[ProblemCandidate]


def _confidence_sort_key(confidence: Confidence | None) -> int:
    if confidence is None:
        return len(CONFIDENCE_PRIORITY)
    return CONFIDENCE_PRIORITY[confidence]


def _review_sort_key(candidate: ProblemCandidate) -> tuple:
    return (
        candidate.next_review or date.min,
        _confidence_sort_key(candidate.confidence),
        candidate.last_practiced or date.min,
        candidate.sort_order,
    )


def _new_sort_key(candidate: ProblemCandidate) -> tuple:
    return (
        DIFFICULTY_ORDER[candidate.difficulty],
        candidate.sort_order,
    )


def select_reviews(
    candidates: list[ProblemCandidate],
    today: date,
    count: int = 4,
) -> list[ProblemCandidate]:
    due = [
        c
        for c in candidates
        if c.solved and c.next_review is not None and c.next_review <= today
    ]
    due.sort(key=_review_sort_key)
    return due[:count]


def _unsolved_by_pattern(candidates: list[ProblemCandidate]) -> Counter[str]:
    counts: Counter[str] = Counter()
    for candidate in candidates:
        if not candidate.solved and candidate.pattern not in EXCLUDED_PATTERNS:
            counts[candidate.pattern] += 1
    return counts


def _pick_focus_pattern(candidates: list[ProblemCandidate]) -> str | None:
    unsolved_counts = _unsolved_by_pattern(candidates)
    if not unsolved_counts:
        return None

    for pattern in FOCUS_PATTERN_ORDER:
        if unsolved_counts.get(pattern, 0) > 0:
            return pattern

    remaining = [
        pattern
        for pattern, count in unsolved_counts.items()
        if pattern != "Linked List" and count > 0
    ]
    if not remaining:
        return None
    return max(remaining, key=lambda pattern: unsolved_counts[pattern])


def select_focused_new(
    candidates: list[ProblemCandidate],
    focus_pattern: str,
    count: int = 2,
    *,
    exclude_ids: set[int] | None = None,
) -> list[ProblemCandidate]:
    exclude_ids = exclude_ids or set()
    pool = [
        c
        for c in candidates
        if not c.solved
        and c.pattern == focus_pattern
        and c.pattern not in EXCLUDED_PATTERNS
        and c.problem_id not in exclude_ids
    ]
    pool.sort(key=_new_sort_key)
    return pool[:count]


def select_random_new(
    candidates: list[ProblemCandidate],
    focus_pattern: str | None,
    count: int = 2,
    *,
    exclude_ids: set[int] | None = None,
) -> list[ProblemCandidate]:
    exclude_ids = exclude_ids or set()
    pool = [
        c
        for c in candidates
        if not c.solved
        and c.pattern not in EXCLUDED_PATTERNS
        and c.pattern != focus_pattern
        and c.problem_id not in exclude_ids
    ]
    pool.sort(key=_new_sort_key)

    mediums = [c for c in pool if c.difficulty == Difficulty.MEDIUM]
    if len(mediums) >= count:
        return mediums[:count]

    if pool and all(c.difficulty == Difficulty.HARD for c in pool[:count]):
        non_hard = [c for c in pool if c.difficulty != Difficulty.HARD]
        if non_hard:
            chosen = non_hard[:count]
            remaining = count - len(chosen)
            if remaining > 0:
                hard_pool = [c for c in pool if c.difficulty == Difficulty.HARD and c not in chosen]
                chosen.extend(hard_pool[:remaining])
            return chosen[:count]

    return pool[:count]


def build_daily_set(candidates: list[ProblemCandidate], today: date) -> SelectedDailySet:
    review = select_reviews(candidates, today)
    used_ids = {c.problem_id for c in review}

    focus_pattern = _pick_focus_pattern(candidates)
    focused_new: list[ProblemCandidate] = []
    if focus_pattern:
        focused_new = select_focused_new(candidates, focus_pattern, exclude_ids=used_ids)
        used_ids.update(c.problem_id for c in focused_new)

    random_new = select_random_new(candidates, focus_pattern, exclude_ids=used_ids)

    return SelectedDailySet(
        focus_pattern=focus_pattern,
        review=review,
        focused_new=focused_new,
        random_new=random_new,
    )


def slot_for_candidate(
    candidate: ProblemCandidate,
    selected: SelectedDailySet,
) -> DailySlot:
    if candidate in selected.review:
        return DailySlot.REVIEW
    if candidate in selected.focused_new:
        return DailySlot.FOCUSED_NEW
    return DailySlot.RANDOM_NEW
