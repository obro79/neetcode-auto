from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.core.config import get_settings
from app.routes import auth, completions, config, daily_sets, health, problems, reviews, stats


def _dashboard_dist() -> Path | None:
    backend_root = Path(__file__).resolve().parent.parent
    candidates = [
        backend_root / "dashboard_dist",
        backend_root.parent / "dashboard" / "dist",
    ]
    for path in candidates:
        if path.is_dir() and (path / "index.html").is_file():
            return path
    return None


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title=settings.app_name)
    app.include_router(health.router)
    app.include_router(config.router)
    app.include_router(daily_sets.router)
    app.include_router(completions.router)
    app.include_router(problems.router)
    app.include_router(stats.router)
    app.include_router(reviews.router)
    app.include_router(auth.router)

    dashboard_dist = _dashboard_dist()
    if dashboard_dist is not None:
        app.mount(
            "/dashboard",
            StaticFiles(directory=dashboard_dist, html=True),
            name="dashboard",
        )
    return app


app = create_app()
