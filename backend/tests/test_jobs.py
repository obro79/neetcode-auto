from __future__ import annotations

from app.core.jobs_config import FiltersConfig, JobsConfig, RankingConfig, SourceConfig, UserProfile
from app.services.jobs.filter import passes_filters
from app.services.jobs.ingest import ListingRecord
from app.services.jobs.rank import rank_listings


def _listing(**overrides) -> ListingRecord:
    base = {
        "id": "abc-123",
        "company_name": "Stripe",
        "title": "Backend Intern - Python API",
        "locations": ["San Francisco, CA"],
        "terms": ["Spring 2026"],
        "url": "https://example.com/apply",
        "category": "Software",
        "date_posted": 1_700_000_000,
        "active": True,
        "sponsorship": "Other",
        "is_visible": True,
    }
    base.update(overrides)
    return ListingRecord(**base)


def test_filter_accepts_backend_swe_listing():
    config = JobsConfig(
        source=SourceConfig(
            listings_url="https://example.com/listings.json",
        ),
        filters=FiltersConfig(
            terms=["Spring 2026"],
            categories=["software_engineering"],
            exclude_categories=["product_management"],
        ),
    )
    assert passes_filters(_listing(), config=config)


def test_filter_rejects_product_manager():
    config = JobsConfig(
        source=SourceConfig(listings_url="https://example.com/listings.json"),
        filters=FiltersConfig(
            terms=["Spring 2026"],
            categories=["software_engineering"],
            exclude_title_patterns=["Product Manager"],
        ),
    )
    listing = _listing(title="Product Manager Intern", category="Product")
    assert not passes_filters(listing, config=config)


def test_filter_rejects_non_north_america_by_default():
    config = JobsConfig(
        source=SourceConfig(listings_url="https://example.com/listings.json"),
        filters=FiltersConfig(terms=["Spring 2026"], locations=[]),
    )
    listing = _listing(locations=["London, UK"])
    assert not passes_filters(listing, config=config)


def test_rank_prefers_preferred_company_and_python():
    config = JobsConfig(
        source=SourceConfig(listings_url="https://example.com/listings.json"),
        ranking=RankingConfig(
            top_n=5,
            preferred_companies=["Stripe"],
            backend_keywords=["backend"],
            python_keywords=["python"],
        ),
    )
    profile = UserProfile(
        skills=["Python", "backend", "API"],
        preferred_roles=["backend intern"],
        preferred_companies=["Stripe"],
        notes="Python backend API",
    )
    listings = [
        _listing(id="1", company_name="Stripe", title="Backend Intern - Python API"),
        _listing(id="2", company_name="Other Co", title="Frontend Intern"),
    ]
    ranked = rank_listings(listings, config=config, profile=profile)
    assert ranked[0].listing.company_name == "Stripe"
    assert ranked[0].score >= ranked[1].score
