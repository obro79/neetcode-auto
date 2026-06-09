from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import verify_api_key
from app.core.timezone import today_vancouver
from app.database.session import get_session
from app.schemas.problem import ProblemWithProgressOut
from app.services.stats import get_due_reviews

router = APIRouter(prefix="/reviews", tags=["reviews"])


@router.get("/due", response_model=list[ProblemWithProgressOut])
async def due_reviews(
    limit: int = Query(default=50, ge=1, le=500),
    session: AsyncSession = Depends(get_session),
    _: None = Depends(verify_api_key),
) -> list[ProblemWithProgressOut]:
    return await get_due_reviews(session, today_vancouver(), limit=limit)
