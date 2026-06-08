from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import verify_api_key
from app.database.session import get_session
from app.schemas.completion import CompletionRequest, CompletionResponse
from app.services.completions import complete_problem

router = APIRouter(prefix="/completions", tags=["completions"])


@router.post("", response_model=CompletionResponse)
async def create_completion(
    payload: CompletionRequest,
    session: AsyncSession = Depends(get_session),
    _: None = Depends(verify_api_key),
) -> CompletionResponse:
    try:
        return await complete_problem(
            session,
            slug=payload.slug,
            confidence=payload.confidence,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
