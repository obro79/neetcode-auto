from fastapi import APIRouter
from sqlalchemy import text

from app.database.session import AsyncSessionLocal

router = APIRouter(prefix="/health", tags=["health"])


@router.get("")
async def health_check() -> dict[str, str]:
    try:
        async with AsyncSessionLocal() as session:
            await session.execute(text("SELECT 1"))
        return {"status": "ok", "database": "ok"}
    except Exception as exc:
        return {"status": "degraded", "database": f"error: {exc}"}
