from collections import Counter, defaultdict
from datetime import date

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.enums import Confidence, ReviewStage
from app.models.problem import Problem
from app.schemas.problem import ProblemWithProgressOut, ProgressOut
from app.schemas.stats import ConfidenceBreakdown, PatternStat, StatsSummaryOut
from app.services.daily_sets import load_candidates
from app.services.selection import ProblemCandidate, _review_sort_key


def _progress_out(problem: Problem) -> ProgressOut | None:
    progress = problem.progress
    if progress is None:
        return None
    return ProgressOut(
        solved=progress.solved,
        review_stage=progress.review_stage,
        next_review=progress.next_review.isoformat() if progress.next_review else None,
        last_practiced=progress.last_practiced.isoformat() if progress.last_practiced else None,
        confidence=progress.confidence,
        daily_slot=progress.daily_slot,
    )


def problem_with_progress_out(problem: Problem) -> ProblemWithProgressOut:
    return ProblemWithProgressOut(
        id=problem.id,
        slug=problem.slug,
        title=problem.title,
        pattern=problem.pattern,
        difficulty=problem.difficulty,
        leetcode_url=problem.leetcode_url,
        neetcode_url=problem.neetcode_url,
        sort_order=problem.sort_order,
        progress=_progress_out(problem),
    )


def _is_due(candidate: ProblemCandidate, today: date) -> bool:
    return (
        candidate.solved
        and candidate.next_review is not None
        and candidate.next_review <= today
    )


async def get_stats_summary(session: AsyncSession, today: date) -> StatsSummaryOut:
    candidates = await load_candidates(session)

    total = len(candidates)
    solved = sum(1 for candidate in candidates if candidate.solved)
    unsolved = total - solved

    confidence_counts = Counter(
        candidate.confidence.value if candidate.confidence else "unset"
        for candidate in candidates
    )
    by_confidence = ConfidenceBreakdown(
        struggling=confidence_counts.get(Confidence.STRUGGLING.value, 0),
        getting_there=confidence_counts.get(Confidence.GETTING_THERE.value, 0),
        solid=confidence_counts.get(Confidence.SOLID.value, 0),
        unset=confidence_counts.get("unset", 0),
    )

    stmt = select(Problem).options(selectinload(Problem.progress))
    result = await session.execute(stmt)
    problems = result.scalars().all()

    by_review_stage: dict[ReviewStage, int] = {stage: 0 for stage in ReviewStage}
    pattern_solved: dict[str, int] = defaultdict(int)
    pattern_total: dict[str, int] = defaultdict(int)
    mastered = 0

    for problem in problems:
        progress = problem.progress
        if progress is None:
            continue
        by_review_stage[progress.review_stage] += 1
        pattern_total[problem.pattern] += 1
        if progress.solved:
            pattern_solved[problem.pattern] += 1
        if progress.review_stage == ReviewStage.MASTERED:
            mastered += 1

    due_today = sum(
        1
        for candidate in candidates
        if _is_due(candidate, today) and candidate.next_review == today
    )
    due_overdue = sum(
        1
        for candidate in candidates
        if _is_due(candidate, today)
        and candidate.next_review is not None
        and candidate.next_review < today
    )

    by_pattern = [
        PatternStat(
            pattern=pattern,
            solved=pattern_solved[pattern],
            total=pattern_total[pattern],
        )
        for pattern in sorted(pattern_total)
    ]

    return StatsSummaryOut(
        total=total,
        solved=solved,
        unsolved=unsolved,
        by_confidence=by_confidence,
        by_review_stage=by_review_stage,
        by_pattern=by_pattern,
        due_today=due_today,
        due_overdue=due_overdue,
        mastered=mastered,
    )


async def get_due_reviews(
    session: AsyncSession,
    today: date,
    limit: int = 50,
) -> list[ProblemWithProgressOut]:
    candidates = await load_candidates(session)
    due = [candidate for candidate in candidates if _is_due(candidate, today)]
    due.sort(key=_review_sort_key)

    if not due:
        return []

    due_ids = [candidate.problem_id for candidate in due[:limit]]
    stmt = (
        select(Problem)
        .where(Problem.id.in_(due_ids))
        .options(selectinload(Problem.progress))
    )
    result = await session.execute(stmt)
    problems_by_id = {problem.id: problem for problem in result.scalars().all()}

    return [
        problem_with_progress_out(problems_by_id[candidate.problem_id])
        for candidate in due[:limit]
        if candidate.problem_id in problems_by_id
    ]
