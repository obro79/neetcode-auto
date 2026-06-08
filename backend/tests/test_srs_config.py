from pathlib import Path

from app.core.srs_config import SrsConfig, default_config_path, load_srs_config, repo_root


def test_default_config_path_exists() -> None:
    path = default_config_path()
    assert path.exists(), f"Expected config at {path}"


def test_load_repo_config_has_daily_set_defaults() -> None:
    config = load_srs_config(default_config_path())
    assert config.daily_set.review_count == 4
    assert config.daily_set.focused_new_count == 2
    assert config.email.anchor_time == "07:00"
    assert config.email.backoff_minutes == [0, 30, 90, 210]


def test_resolve_slug_alias() -> None:
    config = load_srs_config(default_config_path())
    assert config.resolve_slug("two-sum") == "two-integer-sum"
    assert config.resolve_slug("two-integer-sum") == "two-integer-sum"


def test_resolve_catalog_path_from_repo_root() -> None:
    config = load_srs_config(default_config_path())
    catalog = config.resolve_catalog_path()
    assert catalog.exists()
    assert catalog.name == "neetcode_250.json"


def test_load_missing_config_returns_defaults(tmp_path: Path) -> None:
    missing = tmp_path / "missing.yaml"
    config = load_srs_config(missing)
    assert isinstance(config, SrsConfig)
    assert config.daily_set.review_count == 4


def test_repo_root_points_at_catalog() -> None:
    root = repo_root()
    assert (root / "data" / "neetcode_250.json").exists() or (
        root / "backend" / "data" / "neetcode_250.json"
    ).exists()
