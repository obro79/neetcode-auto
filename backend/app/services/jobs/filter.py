from __future__ import annotations

from app.core.jobs_config import (
    FiltersConfig,
    JobsConfig,
    UserProfile,
    get_jobs_config,
    get_profile,
)
from app.services.jobs.categories import (
    infer_category_key,
    is_north_america_location,
    title_has_no_sponsorship,
    title_requires_us_citizen,
)
from app.services.jobs.ingest import ListingRecord


def _location_matches(filters: FiltersConfig, locations: list[str]) -> bool:
    if filters.locations:
        lowered_targets = {loc.lower() for loc in filters.locations}
        for location in locations:
            loc_lower = location.lower()
            if any(target in loc_lower or loc_lower in target for target in lowered_targets):
                return True
        return False

    if filters.location_default == "north_america":
        return any(is_north_america_location(location) for location in locations)
    return True


def _term_matches(filters: FiltersConfig, terms: list[str]) -> bool:
    if not filters.terms:
        return True
    allowed = {term.lower() for term in filters.terms}
    return any(term.lower() in allowed for term in terms)


def _category_matches(filters: FiltersConfig, category: str) -> bool:
    category_key = infer_category_key(category)
    if category_key is None:
        return bool(filters.categories)
    excluded = {key.lower() for key in filters.exclude_categories}
    if category_key.lower() in excluded:
        return False
    if not filters.categories:
        return True
    allowed = {key.lower() for key in filters.categories}
    return category_key.lower() in allowed


def _title_excluded(filters: FiltersConfig, title: str) -> bool:
    lowered = title.lower()
    return any(pattern.lower() in lowered for pattern in filters.exclude_title_patterns)


def passes_filters(
    listing: ListingRecord,
    config: JobsConfig | None = None,
    profile: UserProfile | None = None,
) -> bool:
    cfg = config or get_jobs_config()
    prof = profile or get_profile()
    filters = cfg.filters

    if not listing.active or not listing.is_visible:
        return False
    if prof.blacklisted_companies and listing.company_name in prof.blacklisted_companies:
        return False
    if _title_excluded(filters, listing.title):
        return False
    if filters.require_sponsorship and title_has_no_sponsorship(listing.title):
        return False
    if not filters.require_us_citizen and title_requires_us_citizen(listing.title):
        return False
    if not _term_matches(filters, listing.terms):
        return False
    if not _location_matches(filters, listing.locations):
        return False
    if not _category_matches(filters, listing.category):
        return False
    return True


def filter_listings(
    listings: list[ListingRecord],
    config: JobsConfig | None = None,
    profile: UserProfile | None = None,
) -> list[ListingRecord]:
    return [listing for listing in listings if passes_filters(listing, config, profile)]
