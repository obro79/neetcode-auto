from fastapi import APIRouter, Depends

from app.core.auth import verify_api_key
from app.core.config import get_settings
from app.schemas.auth import AuthVerifyOut

router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("/verify", response_model=AuthVerifyOut)
async def verify_auth(_: None = Depends(verify_api_key)) -> AuthVerifyOut:
    settings = get_settings()
    return AuthVerifyOut(ok=True, app_name=settings.app_name)
