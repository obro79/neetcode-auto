from fastapi import APIRouter

from app.core.srs_config import get_srs_config
from app.schemas.config import PublicConfigOut

router = APIRouter(prefix="/config", tags=["config"])


@router.get("/public", response_model=PublicConfigOut)
async def get_public_config() -> PublicConfigOut:
    config = get_srs_config()
    return PublicConfigOut(
        slug_aliases=config.slug_aliases,
        sync_only_daily_set=config.extension.sync_only_daily_set,
    )
