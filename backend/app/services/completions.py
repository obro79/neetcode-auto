from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.timezone import today_vancouver
from app.enums import Confidence
from app.models.problem import Problem
from app.schemas.completion import CompletionResponse
from app.services.srs import apply_completion, completion_fields


async def complete_problem(
    session: AsyncSession,
    *,
    slug: str,
    confidence: Confidence | None,
) -> CompletionResponse:
    today = today_vancouver()
    stmt = (
        select(Problem)
        .where(Problem.slug == slug)
        .options(selectinload(Problem.progress))
    )
    result = await session.execute(stmt)
    problem = result.scalar_one_or_none()
    if problem is None:
        raise ValueError(f"Unknown problem slug: {slug}")

    progress = problem.progress
    new_stage, next_review, resolved_confidence = apply_completion(
        review_stage=progress.review_stage,
        confidence=progress.confidence,
        new_confidence=confidence,
        today=today,
    )

    for field, value in completion_fields(today).items():
        setattr(progress, field, value)
    progress.review_stage = new_stage
    progress.next_review = next_review
    progress.confidence = resolved_confidence

    await session.commit()
    await session.refresh(progress)

    return CompletionResponse(
        slug=problem.slug,
        title=problem.title,
        review_stage=progress.review_stage.value,
        next_review=progress.next_review.isoformat() if progress.next_review else None,
        confidence=progress.confidence,
        daily_slot=progress.daily_slot.value if progress.daily_slot else "done",
    )
