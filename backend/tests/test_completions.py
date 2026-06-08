import pytest
from sqlalchemy import select

from app.enums import Confidence, ReviewStage
from app.models.problem import Problem
from app.models.user_progress import UserProgress


@pytest.mark.asyncio
async def test_completion_resolves_slug_alias(client, seeded_session, api_headers) -> None:
    response = await client.post(
        "/completions",
        headers=api_headers,
        json={"slug": "two-sum", "source": "leetcode", "confidence": "solid"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["slug"] == "two-integer-sum"
    assert data["review_stage"] == "1d"

    progress = (
        await seeded_session.execute(
            select(UserProgress).join(Problem).where(Problem.slug == "two-integer-sum")
        )
    ).scalar_one()
    assert progress.solved is True
    assert progress.review_stage == ReviewStage.ONE_DAY
    assert progress.confidence == Confidence.SOLID


@pytest.mark.asyncio
async def test_completion_unknown_slug_returns_404(client, api_headers) -> None:
    response = await client.post(
        "/completions",
        headers=api_headers,
        json={"slug": "does-not-exist", "source": "leetcode"},
    )
    assert response.status_code == 404
