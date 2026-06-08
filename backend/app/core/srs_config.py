from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import yaml
from pydantic import BaseModel, Field

from app.enums import ReviewStage


def backend_dir() -> Path:
    return Path(__file__).resolve().parents[2]


def repo_root() -> Path:
    backend = backend_dir()
    monorepo_root = backend.parent
    if (monorepo_root / "data" / "neetcode_250.json").exists():
        return monorepo_root
    return backend


def default_config_path() -> Path:
    backend = backend_dir()
    for base in (backend.parent, backend):
        candidate = base / "config" / "srs.config.yaml"
        if candidate.exists():
            return candidate
    return backend.parent / "config" / "srs.config.yaml"


class CatalogConfig(BaseModel):
    path: str = "data/neetcode_250.json"


class DailySetConfig(BaseModel):
    review_count: int = 4
    focused_new_count: int = 2
    random_new_count: int = 2
    excluded_patterns: list[str] = Field(
        default_factory=lambda: ["Linked List", "2-D Dynamic Programming"]
    )
    focus_pattern_order: list[str] = Field(
        default_factory=lambda: [
            "Advanced Graphs",
            "Math & Geometry",
            "Greedy",
            "Tries",
        ]
    )


class SrsStagesConfig(BaseModel):
    stages: list[str] = Field(
        default_factory=lambda: ["new", "1d", "3d", "7d", "14d", "30d", "mastered"]
    )
    intervals_days: dict[str, int] = Field(
        default_factory=lambda: {
            "1d": 1,
            "3d": 3,
            "7d": 7,
            "14d": 14,
            "30d": 30,
        }
    )
    struggling_interval_days: int = 1

    def stage_progression(self) -> list[ReviewStage]:
        return [ReviewStage(s) for s in self.stages]

    def stage_intervals(self) -> dict[ReviewStage, int | None]:
        intervals: dict[ReviewStage, int | None] = {}
        for stage in self.stage_progression():
            if stage == ReviewStage.MASTERED:
                intervals[stage] = None
            else:
                intervals[stage] = self.intervals_days.get(stage.value)
        return intervals


class EmailConfig(BaseModel):
    to: str = "owenfisher46@gmail.com"
    from_address: str = Field(
        default="NeetCode SRS <onboarding@resend.dev>",
        alias="from",
    )
    anchor_time: str = "07:00"
    backoff_minutes: list[int] = Field(default_factory=lambda: [0, 30, 90, 210])
    max_attempts_per_day: int = 4


class ExtensionConfig(BaseModel):
    sync_only_daily_set: bool = False


class SrsConfig(BaseModel):
    timezone: str = "America/Vancouver"
    catalog: CatalogConfig = Field(default_factory=CatalogConfig)
    daily_set: DailySetConfig = Field(default_factory=DailySetConfig)
    srs: SrsStagesConfig = Field(default_factory=SrsStagesConfig)
    email: EmailConfig = Field(default_factory=EmailConfig)
    extension: ExtensionConfig = Field(default_factory=ExtensionConfig)
    slug_aliases: dict[str, str] = Field(default_factory=dict)

    def resolve_catalog_path(self) -> Path:
        path = Path(self.catalog.path)
        if path.is_absolute():
            return path
        return repo_root() / path

    def resolve_slug(self, slug: str) -> str:
        return self.slug_aliases.get(slug, slug)

    @property
    def excluded_patterns(self) -> set[str]:
        return set(self.daily_set.excluded_patterns)


def load_srs_config(path: Path | None = None) -> SrsConfig:
    config_path = path or default_config_path()
    if not config_path.exists():
        return SrsConfig()
    data = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    return SrsConfig.model_validate(data)


@lru_cache
def get_srs_config() -> SrsConfig:
    from app.core.config import get_settings

    settings = get_settings()
    if settings.srs_config_path:
        return load_srs_config(Path(settings.srs_config_path))
    return load_srs_config()
