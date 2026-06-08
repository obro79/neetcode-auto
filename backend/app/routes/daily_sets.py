from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import verify_api_key
from app.core.timezone import today_vancouver
from app.database.session import get_session
from app.schemas.daily_set import DailySetOut, SendDailyResponse
from app.services.daily_sets import get_or_create_today
from app.services.email_dispatch import send_daily_set_email

router = APIRouter(prefix="/daily-sets", tags=["daily-sets"])


@router.get("/today", response_model=DailySetOut)
async def get_today_daily_set(
    session: AsyncSession = Depends(get_session),
    _: None = Depends(verify_api_key),
) -> DailySetOut:
    return await get_or_create_today(session, today_vancouver())


@router.post("/today/send", response_model=SendDailyResponse)
async def send_today_daily_set(
    attempt: int | None = None,
    session: AsyncSession = Depends(get_session),
    _: None = Depends(verify_api_key),
) -> SendDailyResponse:
    return await send_daily_set_email(session, attempt)
