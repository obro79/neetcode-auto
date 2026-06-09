from __future__ import annotations

from datetime import UTC, datetime

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.jobs_config import JobsConfig, get_jobs_config
from app.models.job_listing import JobListing
from app.services.jobs.categories import ListingRecord, normalize_category


def parse_listing(raw: dict) -> ListingRecord:
    return ListingRecord(
        id=str(raw["id"]),
        company_name=str(raw.get("company_name") or "").strip(),
        title=str(raw.get("title") or "").strip(),
        locations=[str(loc) for loc in (raw.get("locations") or [])],
        terms=[str(term) for term in (raw.get("terms") or [])],
        url=str(raw.get("url") or "").strip(),
        category=normalize_category(str(raw.get("category") or "Unknown")),
        date_posted=raw.get("date_posted"),
        active=bool(raw.get("active", False)),
        sponsorship=raw.get("sponsorship"),
        is_visible=bool(raw.get("is_visible", True)),
    )


async def fetch_listings(config: JobsConfig | None = None) -> list[ListingRecord]:
    cfg = config or get_jobs_config()
    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.get(cfg.source.listings_url)
        response.raise_for_status()
        payload = response.json()
    if not isinstance(payload, list):
        raise ValueError("Expected listings.json to be a list")
    return [parse_listing(item) for item in payload]


async def ingest_listings(
    session: AsyncSession,
    listings: list[ListingRecord] | None = None,
) -> tuple[int, int, set[str]]:
    """Upsert listings. Returns (inserted, updated, newly_seen_ids)."""
    records = listings if listings is not None else await fetch_listings()
    now = datetime.now(UTC)
    inserted = 0
    updated = 0
    newly_seen: set[str] = set()

    existing_ids: set[str] = set()
    result = await session.execute(select(JobListing.id))
    for row in result.scalars().all():
        existing_ids.add(row)

    for record in records:
        if not record.id:
            continue
        existing = await session.get(JobListing, record.id)
        if existing is None:
            session.add(
                JobListing(
                    id=record.id,
                    company_name=record.company_name,
                    title=record.title,
                    locations=record.locations,
                    terms=record.terms,
                    url=record.url,
                    category=record.category,
                    date_posted=record.date_posted,
                    active=record.active,
                    sponsorship=record.sponsorship,
                    first_seen_at=now,
                    last_seen_at=now,
                )
            )
            inserted += 1
            newly_seen.add(record.id)
        else:
            existing.company_name = record.company_name
            existing.title = record.title
            existing.locations = record.locations
            existing.terms = record.terms
            existing.url = record.url
            existing.category = record.category
            existing.date_posted = record.date_posted
            existing.active = record.active
            existing.sponsorship = record.sponsorship
            existing.last_seen_at = now
            updated += 1

    await session.commit()
    return inserted, updated, newly_seen
