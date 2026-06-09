from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import yaml
from pydantic import BaseModel, Field

from app.core.srs_config import backend_dir, repo_root


def default_jobs_config_path() -> Path:
    backend = backend_dir()
    for base in (backend.parent, backend):
        candidate = base / "config" / "jobs.config.yaml"
        if candidate.exists():
            return candidate
    return backend / "config" / "jobs.config.yaml"


def default_profile_path() -> Path:
    backend = backend_dir()
    for base in (backend.parent, backend):
        candidate = base / "data" / "profile.json"
        if candidate.exists():
            return candidate
    return repo_root() / "data" / "profile.json"


class SourceConfig(BaseModel):
    listings_url: str
    branch: str = "dev"


class FiltersConfig(BaseModel):
    terms: list[str] = Field(default_factory=list)
    locations: list[str] = Field(default_factory=list)
    location_default: str = "north_america"
    categories: list[str] = Field(default_factory=list)
    exclude_categories: list[str] = Field(default_factory=list)
    exclude_title_patterns: list[str] = Field(default_factory=list)
    require_sponsorship: bool = True
    require_us_citizen: bool = False


class RankingWeights(BaseModel):
    bm25: float = 1.0
    company_tier: float = 0.3
    recency_days: float = 0.2
    backend_boost: float = 0.25
    python_boost: float = 0.15
    new_today_boost: float = 0.4


class RankingConfig(BaseModel):
    top_n: int = 10
    weights: RankingWeights = Field(default_factory=RankingWeights)
    backend_keywords: list[str] = Field(default_factory=list)
    python_keywords: list[str] = Field(default_factory=list)
    preferred_companies: list[str] = Field(default_factory=list)


class JobEmailConfig(BaseModel):
    to: str = "owenfisher46@gmail.com"
    from_address: str = Field(
        default="Internship Radar <onboarding@resend.dev>",
        alias="from",
    )
    anchor_times: list[str] = Field(default_factory=lambda: ["09:00", "12:00", "15:00"])
    send_only_if_new: bool = True
    include_full_list: bool = True


class JobsConfig(BaseModel):
    timezone: str = "America/Vancouver"
    source: SourceConfig
    filters: FiltersConfig = Field(default_factory=FiltersConfig)
    ranking: RankingConfig = Field(default_factory=RankingConfig)
    email: JobEmailConfig = Field(default_factory=JobEmailConfig)


class UserProfile(BaseModel):
    name: str = ""
    grad_year: int | None = None
    degree: str = ""
    work_authorization: str = ""
    skills: list[str] = Field(default_factory=list)
    preferred_roles: list[str] = Field(default_factory=list)
    preferred_companies: list[str] = Field(default_factory=list)
    blacklisted_companies: list[str] = Field(default_factory=list)
    notes: str = ""

    def bm25_query_text(self) -> str:
        parts = [
            " ".join(self.preferred_roles),
            " ".join(self.skills),
            self.notes,
        ]
        return " ".join(part for part in parts if part).strip()


def load_jobs_config(path: Path | None = None) -> JobsConfig:
    config_path = path or default_jobs_config_path()
    if not config_path.exists():
        raise FileNotFoundError(f"Jobs config not found: {config_path}")
    data = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    return JobsConfig.model_validate(data)


def load_profile(path: Path | None = None) -> UserProfile:
    profile_path = path or default_profile_path()
    if not profile_path.exists():
        return UserProfile()
    import json

    data = json.loads(profile_path.read_text(encoding="utf-8"))
    return UserProfile.model_validate(data)


@lru_cache
def get_jobs_config() -> JobsConfig:
    from app.core.config import get_settings

    settings = get_settings()
    if settings.jobs_config_path:
        return load_jobs_config(Path(settings.jobs_config_path))
    return load_jobs_config()


@lru_cache
def get_profile() -> UserProfile:
    from app.core.config import get_settings

    settings = get_settings()
    if settings.profile_path:
        return load_profile(Path(settings.profile_path))
    return load_profile()
