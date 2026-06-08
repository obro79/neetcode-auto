from fastapi import FastAPI

from app.core.config import get_settings
from app.routes import completions, config, daily_sets, health, problems


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title=settings.app_name)
    app.include_router(health.router)
    app.include_router(config.router)
    app.include_router(daily_sets.router)
    app.include_router(completions.router)
    app.include_router(problems.router)
    return app


app = create_app()
