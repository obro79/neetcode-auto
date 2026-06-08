
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.timezone import now_vancouver, today_vancouver
from app.models.email_log import EmailLog
from app.schemas.daily_set import SendDailyResponse
from app.services.daily_sets import get_or_create_today
from app.services.email import send_daily_email


async def send_daily_set_email(session: AsyncSession, attempt: int) -> SendDailyResponse:
    today = today_vancouver()

    if attempt not in (1, 2):
        return SendDailyResponse(
            set_date=today.isoformat(),
            attempt=attempt,
            sent=False,
            message="Attempt must be 1 or 2",
        )

    existing_stmt = select(EmailLog).where(
        EmailLog.set_date == today,
        EmailLog.attempt == attempt,
    )
    existing = (await session.execute(existing_stmt)).scalar_one_or_none()
    if existing:
        return SendDailyResponse(
            set_date=today.isoformat(),
            attempt=attempt,
            sent=False,
            message=f"Email already sent for attempt {attempt}",
        )

    count_stmt = select(EmailLog).where(EmailLog.set_date == today)
    sent_today = len((await session.execute(count_stmt)).scalars().all())
    if sent_today >= 2:
        return SendDailyResponse(
            set_date=today.isoformat(),
            attempt=attempt,
            sent=False,
            message="Daily email cap reached (2 per day)",
        )

    daily_set = await get_or_create_today(session, today)
    email_id = send_daily_email(daily_set)

    log = EmailLog(
        set_date=today,
        sent_at=now_vancouver(),
        attempt=attempt,
    )
    session.add(log)
    await session.commit()

    return SendDailyResponse(
        set_date=today.isoformat(),
        attempt=attempt,
        sent=True,
        message=f"Email sent (id={email_id})",
    )
