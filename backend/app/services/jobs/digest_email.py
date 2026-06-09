from __future__ import annotations

import asyncio
from datetime import UTC, date, datetime

import resend

from app.core.config import get_settings
from app.core.jobs_config import get_jobs_config
from app.services.jobs.rank import RankedListing


def _format_location(locations: list[str]) -> str:
    return ", ".join(locations) if locations else "Unknown"


def _format_terms(terms: list[str]) -> str:
    return ", ".join(terms) if terms else "N/A"


def _posted_label(date_posted: int | None) -> str:
    if date_posted is None:
        return "Unknown"
    posted = datetime.fromtimestamp(date_posted, tz=UTC).date()
    return posted.isoformat()


def _render_ranked_items(items: list[RankedListing], numbered: bool = True) -> str:
    if not items:
        return "<p><em>None</em></p>"
    tag = "ol" if numbered else "ul"
    lines = [f"<{tag}>"]
    for item in items:
        listing = item.listing
        new_marker = " <strong>[NEW]</strong>" if item.is_new else ""
        lines.append(
            "<li>"
            f"<strong>{listing.company_name}</strong> — {listing.title}{new_marker}<br>"
            f"Locations: {_format_location(listing.locations)} | "
            f"Terms: {_format_terms(listing.terms)} | "
            f"Posted: {_posted_label(listing.date_posted)} | "
            f"Score: {item.score:.2f}<br>"
            f'<a href="{listing.url}">Apply</a>'
            "</li>"
        )
    lines.append(f"</{tag}>")
    return "\n".join(lines)


def _render_ranked_items_text(items: list[RankedListing], numbered: bool = True) -> str:
    if not items:
        return "None\n"
    lines: list[str] = []
    for index, item in enumerate(items, start=1):
        listing = item.listing
        prefix = f"{index}." if numbered else "-"
        new_marker = " [NEW]" if item.is_new else ""
        lines.append(
            f"{prefix} {listing.company_name} — {listing.title}{new_marker}\n"
            f"   Locations: {_format_location(listing.locations)}\n"
            f"   Terms: {_format_terms(listing.terms)}\n"
            f"   Posted: {_posted_label(listing.date_posted)} | Score: {item.score:.2f}\n"
            f"   Apply: {listing.url}\n"
        )
    return "\n".join(lines)


def build_job_digest_html(
    *,
    digest_date: date,
    slot: int,
    highlights: list[RankedListing],
    new_listings: list[RankedListing],
    all_listings: list[RankedListing],
    include_full_list: bool,
) -> str:
    sections = [
        "<h1>Internship Radar</h1>",
        f"<p><strong>Date:</strong> {digest_date.isoformat()} | <strong>Slot:</strong> {slot}</p>",
        f"<h2>Top {len(highlights)} to apply to</h2>",
        _render_ranked_items(highlights, numbered=True),
        f"<h2>New since last email ({len(new_listings)})</h2>",
        _render_ranked_items(new_listings, numbered=False),
    ]
    if include_full_list:
        sections.extend(
            [
                f"<h2>All open matches ({len(all_listings)})</h2>",
                _render_ranked_items(all_listings, numbered=True),
            ]
        )
    return "\n".join(sections)


def build_job_digest_text(
    *,
    digest_date: date,
    slot: int,
    highlights: list[RankedListing],
    new_listings: list[RankedListing],
    all_listings: list[RankedListing],
    include_full_list: bool,
) -> str:
    lines = [
        "Internship Radar",
        f"Date: {digest_date.isoformat()} | Slot: {slot}",
        "",
        f"Top {len(highlights)} to apply to",
        _render_ranked_items_text(highlights, numbered=True),
        f"New since last email ({len(new_listings)})",
        _render_ranked_items_text(new_listings, numbered=False),
    ]
    if include_full_list:
        lines.extend(
            [
                f"All open matches ({len(all_listings)})",
                _render_ranked_items_text(all_listings, numbered=True),
            ]
        )
    return "\n".join(lines)


def _send_job_digest_sync(
    *,
    digest_date: date,
    slot: int,
    highlights: list[RankedListing],
    new_listings: list[RankedListing],
    all_listings: list[RankedListing],
    include_full_list: bool,
) -> str:
    settings = get_settings()
    jobs = get_jobs_config()
    resend.api_key = settings.resend_api_key

    subject = f"Internship Radar — {digest_date.isoformat()} (slot {slot})"
    response = resend.Emails.send(
        {
            "from": settings.email_from or jobs.email.from_address,
            "to": [settings.email_to or jobs.email.to],
            "subject": subject,
            "html": build_job_digest_html(
                digest_date=digest_date,
                slot=slot,
                highlights=highlights,
                new_listings=new_listings,
                all_listings=all_listings,
                include_full_list=include_full_list,
            ),
            "text": build_job_digest_text(
                digest_date=digest_date,
                slot=slot,
                highlights=highlights,
                new_listings=new_listings,
                all_listings=all_listings,
                include_full_list=include_full_list,
            ),
        }
    )
    return response.get("id", "sent")


async def send_job_digest_email(
    *,
    digest_date: date,
    slot: int,
    highlights: list[RankedListing],
    new_listings: list[RankedListing],
    all_listings: list[RankedListing],
    include_full_list: bool,
) -> str:
    return await asyncio.to_thread(
        _send_job_digest_sync,
        digest_date=digest_date,
        slot=slot,
        highlights=highlights,
        new_listings=new_listings,
        all_listings=all_listings,
        include_full_list=include_full_list,
    )
