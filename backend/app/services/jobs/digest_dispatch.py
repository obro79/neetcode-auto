from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time
from zoneinfo import ZoneInfo

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.jobs_config import JobEmailConfig, JobsConfig, get_jobs_config
from app.models.job_digest_log import JobDigestLog
from app.models.job_listing import JobListing
from app.services.jobs.digest_email import send_job_digest_email
from app.services.jobs.filter import filter_listings
from app.services.jobs.ingest import fetch_listings, ingest_listings
from app.services.jobs.rank import rank_listings


@dataclass(frozen=True)
class JobDigestResult:
    digest_date: str
    slot: int
    sent: bool
    message: str
    filtered_count: int = 0
    new_count: int = 0
    top_count: int = 0


def jobs_tz(config: JobsConfig | None = None) -> ZoneInfo:
    cfg = config or get_jobs_config()
    return ZoneInfo(cfg.timezone)


def today_jobs(config: JobsConfig | None = None) -> date:
    return datetime.now(jobs_tz(config)).date()


def now_jobs(config: JobsConfig | None = None) -> datetime:
    return datetime.now(jobs_tz(config))


def _parse_anchor_time(value: str) -> time:
    hour_str, minute_str = value.split(":", 1)
    return time(int(hour_str), int(minute_str))


def scheduled_slot_times(
    digest_date: date,
    email_config: JobEmailConfig,
    tz: ZoneInfo,
) -> list[datetime]:
    slots: list[datetime] = []
    for anchor in email_config.anchor_times:
        anchor_time = _parse_anchor_time(anchor)
        slots.append(datetime.combine(digest_date, anchor_time, tzinfo=tz))
    return slots


async def resolve_due_slot(
    session: AsyncSession,
    now: datetime,
    digest_date: date,
    email_config: JobEmailConfig,
    tz: ZoneInfo,
) -> int | None:
    slots = scheduled_slot_times(digest_date, email_config, tz)
    for index, slot_time in enumerate(slots, start=1):
        if now < slot_time:
            continue
        if await _successful_slot_today(session, digest_date, index):
            continue
        return index
    return None


async def _successful_slot_today(
    session: AsyncSession,
    digest_date: date,
    slot: int,
) -> bool:
    stmt = select(JobDigestLog).where(
        JobDigestLog.digest_date == digest_date,
        JobDigestLog.slot == slot,
        JobDigestLog.success.is_(True),
    )
    return (await session.execute(stmt)).scalar_one_or_none() is not None


async def _last_successful_digest(session: AsyncSession) -> JobDigestLog | None:
    stmt = (
        select(JobDigestLog)
        .where(JobDigestLog.success.is_(True))
        .order_by(JobDigestLog.sent_at.desc())
        .limit(1)
    )
    return (await session.execute(stmt)).scalar_one_or_none()


async def _new_listing_ids_since(
    session: AsyncSession,
    filtered_ids: set[str],
    since: datetime | None,
) -> set[str]:
    if not filtered_ids:
        return set()
    stmt = select(JobListing).where(JobListing.id.in_(filtered_ids))
    rows = list((await session.execute(stmt)).scalars().all())
    if since is None:
        return {row.id for row in rows}
    return {row.id for row in rows if row.first_seen_at > since}


async def send_job_digest(
    session: AsyncSession,
    *,
    dry_run: bool = False,
    force_slot: int | None = None,
) -> JobDigestResult:
    config = get_jobs_config()
    email_config = config.email
    tz = jobs_tz(config)
    today = today_jobs(config)
    now = now_jobs(config)

    inserted, updated, newly_seen = (0, 0, set())
    listings = await fetch_listings(config)
    if not dry_run:
        inserted, updated, newly_seen = await ingest_listings(session, listings)
    filtered = filter_listings(listings, config)
    ranked = rank_listings(filtered, newly_seen_ids=newly_seen, config=config)
    filtered_ids = {item.listing.id for item in ranked}

    due_slot = force_slot
    if due_slot is None:
        if dry_run:
            slots = scheduled_slot_times(today, email_config, tz)
            due_slot = next(
                (index for index, slot_time in enumerate(slots, start=1) if now >= slot_time),
                None,
            )
        else:
            due_slot = await resolve_due_slot(session, now, today, email_config, tz)
    if due_slot is None:
        return JobDigestResult(
            digest_date=today.isoformat(),
            slot=0,
            sent=False,
            message="No digest slot due yet",
            filtered_count=len(filtered),
            new_count=len(newly_seen & filtered_ids),
            top_count=min(len(ranked), config.ranking.top_n),
        )

    slot_already_sent = (
        not dry_run
        and force_slot is None
        and await _successful_slot_today(session, today, due_slot)
    )
    if slot_already_sent:
        return JobDigestResult(
            digest_date=today.isoformat(),
            slot=due_slot,
            sent=False,
            message=f"Digest already sent for slot {due_slot} today",
            filtered_count=len(filtered),
            new_count=0,
            top_count=min(len(ranked), config.ranking.top_n),
        )

    last_digest = None if dry_run else await _last_successful_digest(session)
    since = last_digest.sent_at if last_digest else None
    if dry_run:
        new_ids = {listing.id for listing in filtered if listing.id in newly_seen}
    else:
        new_ids = await _new_listing_ids_since(session, filtered_ids, since)

    if email_config.send_only_if_new and not new_ids and not dry_run:
        if not dry_run:
            log = JobDigestLog(
                digest_date=today,
                slot=due_slot,
                sent_at=now,
                success=True,
                listing_ids=sorted(filtered_ids),
                new_listing_ids=[],
                message="skipped: no new listings",
            )
            session.add(log)
            await session.commit()
        return JobDigestResult(
            digest_date=today.isoformat(),
            slot=due_slot,
            sent=False,
            message="skipped: no new listings",
            filtered_count=len(filtered),
            new_count=0,
            top_count=min(len(ranked), config.ranking.top_n),
        )

    top_n = config.ranking.top_n
    highlights = ranked[:top_n]
    new_ranked = [item for item in ranked if item.listing.id in new_ids]

    if dry_run:
        return JobDigestResult(
            digest_date=today.isoformat(),
            slot=due_slot,
            sent=True,
            message=(
                f"dry-run: would send digest slot {due_slot} "
                f"({len(new_ids)} new, {len(filtered)} filtered)"
            ),
            filtered_count=len(filtered),
            new_count=len(new_ids),
            top_count=len(highlights),
        )

    try:
        resend_id = await send_job_digest_email(
            digest_date=today,
            slot=due_slot,
            highlights=highlights,
            new_listings=new_ranked,
            all_listings=ranked if email_config.include_full_list else highlights,
            include_full_list=email_config.include_full_list,
        )
        success = True
        message = f"Digest sent (id={resend_id})"
    except Exception as exc:
        resend_id = None
        success = False
        message = f"Digest send failed: {exc}"

    log = JobDigestLog(
        digest_date=today,
        slot=due_slot,
        sent_at=now,
        success=success,
        resend_id=resend_id,
        listing_ids=sorted(filtered_ids),
        new_listing_ids=sorted(new_ids),
        message=message,
    )
    session.add(log)
    await session.commit()

    return JobDigestResult(
        digest_date=today.isoformat(),
        slot=due_slot,
        sent=success,
        message=message,
        filtered_count=len(filtered),
        new_count=len(new_ids),
        top_count=len(highlights),
    )
