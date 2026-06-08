from datetime import date

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.timezone import now_vancouver
from app.enums import DailySlot
from app.models.daily_set import DailySet, DailySetItem
from app.models.problem import Problem
from app.models.user_progress import UserProgress
from app.schemas.daily_set import DailySetItemOut, DailySetOut
from app.services.selection import (
    ProblemCandidate,
    SelectedDailySet,
    build_daily_set,
    slot_for_candidate,
)


def _to_candidate(problem: Problem, progress: UserProgress) -> ProblemCandidate:
    return ProblemCandidate(
        problem_id=problem.id,
        slug=problem.slug,
        pattern=problem.pattern,
        difficulty=problem.difficulty,
        sort_order=problem.sort_order,
        solved=progress.solved,
        next_review=progress.next_review,
        last_practiced=progress.last_practiced,
        confidence=progress.confidence,
    )


async def load_candidates(session: AsyncSession) -> list[ProblemCandidate]:
    stmt = (
        select(Problem, UserProgress)
        .join(UserProgress, UserProgress.problem_id == Problem.id)
        .order_by(Problem.sort_order)
    )
    result = await session.execute(stmt)
    return [_to_candidate(problem, progress) for problem, progress in result.all()]


async def get_daily_set_for_date(session: AsyncSession, set_date: date) -> DailySet | None:
    stmt = (
        select(DailySet)
        .where(DailySet.set_date == set_date)
        .options(
            selectinload(DailySet.items)
            .selectinload(DailySetItem.problem)
            .selectinload(Problem.progress)
        )
    )
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def create_daily_set(
    session: AsyncSession,
    set_date: date,
    selected: SelectedDailySet,
) -> DailySet:
    daily_set = DailySet(
        set_date=set_date,
        focus_pattern=selected.focus_pattern,
        created_at=now_vancouver(),
    )
    session.add(daily_set)
    await session.flush()

    chosen = selected.review + selected.focused_new + selected.random_new
    for candidate in chosen:
        item = DailySetItem(
            daily_set_id=daily_set.id,
            problem_id=candidate.problem_id,
            slot=slot_for_candidate(candidate, selected),
        )
        session.add(item)

    progress_ids = [c.problem_id for c in chosen]
    stmt = select(UserProgress).where(UserProgress.problem_id.in_(progress_ids))
    result = await session.execute(stmt)
    progress_by_problem = {row.problem_id: row for row in result.scalars().all()}

    for candidate in chosen:
        progress = progress_by_problem[candidate.problem_id]
        progress.daily_slot = slot_for_candidate(candidate, selected)

    await session.commit()
    return await get_daily_set_for_date(session, set_date)  # type: ignore[return-value]


def _item_out(item: DailySetItem) -> DailySetItemOut:
    problem = item.problem
    return DailySetItemOut(
        slug=problem.slug,
        title=problem.title,
        pattern=problem.pattern,
        difficulty=problem.difficulty,
        leetcode_url=problem.leetcode_url,
        neetcode_url=problem.neetcode_url,
        slot=item.slot,
    )


def daily_set_to_schema(daily_set: DailySet) -> DailySetOut:
    review: list[DailySetItemOut] = []
    focused_new: list[DailySetItemOut] = []
    random_new: list[DailySetItemOut] = []

    for item in daily_set.items:
        out = _item_out(item)
        if item.slot == DailySlot.REVIEW:
            review.append(out)
        elif item.slot == DailySlot.FOCUSED_NEW:
            focused_new.append(out)
        else:
            random_new.append(out)

    return DailySetOut(
        set_date=daily_set.set_date.isoformat(),
        focus_pattern=daily_set.focus_pattern,
        review=review,
        focused_new=focused_new,
        random_new=random_new,
    )


async def get_or_create_today(session: AsyncSession, today: date) -> DailySetOut:
    existing = await get_daily_set_for_date(session, today)
    if existing:
        return daily_set_to_schema(existing)

    candidates = await load_candidates(session)
    selected = build_daily_set(candidates, today)
    created = await create_daily_set(session, today, selected)
    return daily_set_to_schema(created)
