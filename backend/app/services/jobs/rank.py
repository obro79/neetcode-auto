from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime

from rank_bm25 import BM25Okapi

from app.core.jobs_config import JobsConfig, UserProfile, get_jobs_config, get_profile
from app.services.jobs.categories import listing_document_text
from app.services.jobs.ingest import ListingRecord


def _tokenize(text: str) -> list[str]:
    return [token for token in text.lower().replace("/", " ").split() if token]


@dataclass(frozen=True)
class RankedListing:
    listing: ListingRecord
    score: float
    bm25_score: float
    is_new: bool


def _recency_boost(date_posted: int | None, today: datetime) -> float:
    if date_posted is None:
        return 0.0
    posted = datetime.fromtimestamp(date_posted, tz=UTC).date()
    age_days = max((today.date() - posted).days, 0)
    if age_days == 0:
        return 1.0
    if age_days <= 7:
        return max(0.0, 1.0 - (age_days / 7.0))
    return 0.0


def _keyword_boost(title: str, keywords: list[str]) -> float:
    lowered = title.lower()
    return 1.0 if any(keyword.lower() in lowered for keyword in keywords) else 0.0


def rank_listings(
    listings: list[ListingRecord],
    *,
    newly_seen_ids: set[str] | None = None,
    config: JobsConfig | None = None,
    profile: UserProfile | None = None,
    now: datetime | None = None,
) -> list[RankedListing]:
    cfg = config or get_jobs_config()
    prof = profile or get_profile()
    weights = cfg.ranking.weights
    current_time = now or datetime.now(UTC)
    new_ids = newly_seen_ids or set()

    preferred_companies = {
        company.lower()
        for company in (
            list(cfg.ranking.preferred_companies) + list(prof.preferred_companies)
        )
    }

    if not listings:
        return []

    documents = [
        _tokenize(listing_document_text(item.company_name, item.title, item.locations))
        for item in listings
    ]
    query_tokens = _tokenize(prof.bm25_query_text())
    bm25 = BM25Okapi(documents)
    bm25_scores = bm25.get_scores(query_tokens) if query_tokens else [0.0] * len(listings)

    ranked: list[RankedListing] = []
    for index, listing in enumerate(listings):
        company_lower = listing.company_name.lower()
        if company_lower in {c.lower() for c in prof.blacklisted_companies}:
            continue

        bm25_score = float(bm25_scores[index])
        score = weights.bm25 * bm25_score

        if any(pref in company_lower or company_lower in pref for pref in preferred_companies):
            score += weights.company_tier

        score += weights.recency_days * _recency_boost(listing.date_posted, current_time)
        score += weights.backend_boost * _keyword_boost(
            listing.title, cfg.ranking.backend_keywords
        )
        score += weights.python_boost * _keyword_boost(
            listing.title, cfg.ranking.python_keywords
        )

        is_new = listing.id in new_ids
        if is_new:
            score += weights.new_today_boost

        ranked.append(
            RankedListing(
                listing=listing,
                score=score,
                bm25_score=bm25_score,
                is_new=is_new,
            )
        )

    ranked.sort(key=lambda item: (-item.score, item.listing.company_name, item.listing.title))
    return ranked
