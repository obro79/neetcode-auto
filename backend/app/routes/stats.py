from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import verify_api_key
from app.core.timezone import today_vancouver
from app.database.session import get_session
from app.schemas.stats import StatsSummaryOut
from app.services.stats import get_stats_summary

router = APIRouter(prefix="/stats", tags=["stats"])


@router.get("/summary", response_model=StatsSummaryOut)
async def stats_summary(
    session: AsyncSession = Depends(get_session),
    _: None = Depends(verify_api_key),
) -> StatsSummaryOut:
    return await get_stats_summary(session, today_vancouver())
