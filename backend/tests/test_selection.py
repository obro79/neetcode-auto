from datetime import date

from app.enums import Confidence, Difficulty
from app.services.selection import ProblemCandidate, build_daily_set, select_reviews


def _candidate(
    problem_id: int,
    *,
    pattern: str = "Arrays & Hashing",
    difficulty: Difficulty = Difficulty.EASY,
    sort_order: int = 0,
    solved: bool = False,
    next_review: date | None = None,
    last_practiced: date | None = None,
    confidence: Confidence | None = None,
) -> ProblemCandidate:
    return ProblemCandidate(
        problem_id=problem_id,
        slug=f"problem-{problem_id}",
        pattern=pattern,
        difficulty=difficulty,
        sort_order=sort_order,
        solved=solved,
        next_review=next_review,
        last_practiced=last_practiced,
        confidence=confidence,
    )


def test_review_sorting_prioritizes_struggling() -> None:
    today = date(2026, 6, 7)
    candidates = [
        _candidate(1, solved=True, next_review=today, confidence=Confidence.SOLID),
        _candidate(
            2,
            solved=True,
            next_review=today,
            confidence=Confidence.STRUGGLING,
        ),
    ]
    selected = select_reviews(candidates, today, count=2)
    assert selected[0].problem_id == 2


def test_focus_pattern_prefers_advanced_graphs() -> None:
    today = date(2026, 6, 7)
    candidates = [
        _candidate(1, pattern="Greedy", sort_order=1),
        _candidate(2, pattern="Advanced Graphs", sort_order=2),
        _candidate(3, pattern="Arrays & Hashing", sort_order=3),
    ]
    selected = build_daily_set(candidates, today)
    assert selected.focus_pattern == "Advanced Graphs"
    assert all(item.pattern == "Advanced Graphs" for item in selected.focused_new)


def test_excludes_linked_list_and_2d_dp() -> None:
    today = date(2026, 6, 7)
    candidates = [
        _candidate(1, pattern="Linked List", sort_order=1),
        _candidate(2, pattern="2-D Dynamic Programming", sort_order=2),
        _candidate(3, pattern="Greedy", sort_order=3),
        _candidate(4, pattern="Tries", sort_order=4),
    ]
    selected = build_daily_set(candidates, today)
    chosen_patterns = {
        item.pattern
        for item in selected.focused_new + selected.random_new
    }
    assert "Linked List" not in chosen_patterns
    assert "2-D Dynamic Programming" not in chosen_patterns
