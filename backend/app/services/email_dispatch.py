from __future__ import annotations

from datetime import date, datetime, time, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.srs_config import EmailConfig, get_srs_config
from app.core.timezone import now_vancouver, today_vancouver, vancouver_tz
from app.enums import DailySlot
from app.models.email_log import EmailLog
from app.models.user_progress import UserProgress
from app.schemas.daily_set import DailySetOut, SendDailyResponse
from app.services.daily_sets import get_or_create_today
from app.services.email import send_daily_email


def _parse_anchor_time(anchor_time: str) -> time:
    hour_str, minute_str = anchor_time.split(":", 1)
    return time(int(hour_str), int(minute_str))


def scheduled_send_times(set_date: date, email_config: EmailConfig) -> list[datetime]:
    anchor = _parse_anchor_time(email_config.anchor_time)
    base = datetime.combine(set_date, anchor, tzinfo=vancouver_tz())
    return [base + timedelta(minutes=offset) for offset in email_config.backoff_minutes]


def next_attempt_number(attempts_today: int) -> int:
    return attempts_today + 1


async def _successful_send_today(session: AsyncSession, today: date) -> bool:
    stmt = select(EmailLog).where(EmailLog.set_date == today)
    logs = (await session.execute(stmt)).scalars().all()
    return any(log.success for log in logs)


async def _attempts_today(session: AsyncSession, today: date) -> list[EmailLog]:
    stmt = select(EmailLog).where(EmailLog.set_date == today).order_by(EmailLog.attempt)
    return list((await session.execute(stmt)).scalars().all())


def _slot_ready(
    now: datetime,
    set_date: date,
    email_config: EmailConfig,
    attempt_number: int,
) -> bool:
    slots = scheduled_send_times(set_date, email_config)
    if attempt_number < 1 or attempt_number > len(slots):
        return False
    return now >= slots[attempt_number - 1]


async def _mark_completed_items(session: AsyncSession, daily_set: DailySetOut) -> DailySetOut:
    slugs = [
        item.slug
        for section in (daily_set.review, daily_set.focused_new, daily_set.random_new)
        for item in section
    ]
    if not slugs:
        return daily_set

    from app.models.problem import Problem

    stmt = (
        select(Problem.slug, UserProgress.daily_slot)
        .join(UserProgress, UserProgress.problem_id == Problem.id)
        .where(Problem.slug.in_(slugs))
    )
    rows = (await session.execute(stmt)).all()
    done_slugs = {slug for slug, slot in rows if slot == DailySlot.DONE}

    def mark_section(items: list):
        for item in items:
            item.completed = item.slug in done_slugs

    mark_section(daily_set.review)
    mark_section(daily_set.focused_new)
    mark_section(daily_set.random_new)
    return daily_set


async def send_daily_set_email(
    session: AsyncSession,
    attempt: int | None = None,
) -> SendDailyResponse:
    config = get_srs_config()
    email_config = config.email
    today = today_vancouver()
    now = now_vancouver()

    if await _successful_send_today(session, today):
        return SendDailyResponse(
            set_date=today.isoformat(),
            attempt=attempt or 0,
            sent=False,
            message="Email already sent successfully today",
        )

    logs = await _attempts_today(session, today)
    if len(logs) >= email_config.max_attempts_per_day:
        return SendDailyResponse(
            set_date=today.isoformat(),
            attempt=attempt or len(logs),
            sent=False,
            message=f"Daily email cap reached ({email_config.max_attempts_per_day} per day)",
        )

    resolved_attempt = attempt if attempt is not None else next_attempt_number(len(logs))

    if attempt is not None:
        existing = next((log for log in logs if log.attempt == attempt), None)
        if existing:
            return SendDailyResponse(
                set_date=today.isoformat(),
                attempt=attempt,
                sent=False,
                message=f"Email already attempted for slot {attempt}",
            )
    elif any(log.attempt == resolved_attempt for log in logs):
        return SendDailyResponse(
            set_date=today.isoformat(),
            attempt=resolved_attempt,
            sent=False,
            message=f"Email already attempted for slot {resolved_attempt}",
        )

    if not _slot_ready(now, today, email_config, resolved_attempt):
        slots = scheduled_send_times(today, email_config)
        next_slot = slots[resolved_attempt - 1] if resolved_attempt <= len(slots) else None
        return SendDailyResponse(
            set_date=today.isoformat(),
            attempt=resolved_attempt,
            sent=False,
            message=f"Not yet time for attempt {resolved_attempt}"
            + (f" (scheduled {next_slot.isoformat()})" if next_slot else ""),
        )

    daily_set = await get_or_create_today(session, today)
    daily_set = await _mark_completed_items(session, daily_set)

    try:
        email_id = await send_daily_email(daily_set)
        success = True
        message = f"Email sent (id={email_id})"
    except Exception as exc:
        email_id = None
        success = False
        message = f"Email send failed: {exc}"

    log = EmailLog(
        set_date=today,
        sent_at=now,
        attempt=resolved_attempt,
        success=success,
        resend_id=email_id,
    )
    session.add(log)
    await session.commit()

    return SendDailyResponse(
        set_date=today.isoformat(),
        attempt=resolved_attempt,
        sent=success,
        message=message,
    )
