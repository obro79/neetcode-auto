from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.auth import verify_api_key
from app.database.session import get_session
from app.models.problem import Problem
from app.schemas.problem import ProblemWithProgressOut, ProgressOut

router = APIRouter(prefix="/problems", tags=["problems"])


@router.get("", response_model=list[ProblemWithProgressOut])
async def list_problems(
    session: AsyncSession = Depends(get_session),
    _: None = Depends(verify_api_key),
) -> list[ProblemWithProgressOut]:
    stmt = select(Problem).options(selectinload(Problem.progress)).order_by(Problem.sort_order)
    result = await session.execute(stmt)
    problems = result.scalars().all()

    output: list[ProblemWithProgressOut] = []
    for problem in problems:
        progress = problem.progress
        progress_out = None
        if progress:
            progress_out = ProgressOut(
                solved=progress.solved,
                review_stage=progress.review_stage,
                next_review=progress.next_review.isoformat() if progress.next_review else None,
                last_practiced=(
                    progress.last_practiced.isoformat() if progress.last_practiced else None
                ),
                confidence=progress.confidence,
                daily_slot=progress.daily_slot,
            )
        output.append(
            ProblemWithProgressOut(
                id=problem.id,
                slug=problem.slug,
                title=problem.title,
                pattern=problem.pattern,
                difficulty=problem.difficulty,
                leetcode_url=problem.leetcode_url,
                neetcode_url=problem.neetcode_url,
                sort_order=problem.sort_order,
                progress=progress_out,
            )
        )
    return output
