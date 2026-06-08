from datetime import date

import pytest
from sqlalchemy import select

from app.enums import DailySlot, Difficulty, ReviewStage
from app.models.daily_set import DailySet
from app.models.problem import Problem
from app.models.user_progress import UserProgress


@pytest.mark.asyncio
async def test_get_today_daily_set_creates_set(client, session, api_headers, monkeypatch) -> None:
    for index, (slug, pattern) in enumerate(
        [
            ("review-1", "Greedy"),
            ("review-2", "Greedy"),
            ("review-3", "Greedy"),
            ("review-4", "Greedy"),
            ("new-1", "Advanced Graphs"),
            ("new-2", "Advanced Graphs"),
            ("new-3", "Tries"),
            ("new-4", "Tries"),
        ],
        start=1,
    ):
        problem = Problem(
            slug=slug,
            title=slug,
            pattern=pattern,
            difficulty=Difficulty.EASY,
            leetcode_url=f"https://leetcode.com/problems/{slug}/",
            neetcode_url=f"https://neetcode.io/problems/{slug}",
            sort_order=index,
        )
        session.add(problem)
        await session.flush()
        session.add(
            UserProgress(
                problem_id=problem.id,
                solved=slug.startswith("review"),
                review_stage=ReviewStage.ONE_DAY if slug.startswith("review") else ReviewStage.NEW,
                next_review=date(2026, 6, 7) if slug.startswith("review") else None,
            )
        )
    await session.commit()

    monkeypatch.setattr("app.core.timezone.today_vancouver", lambda: date(2026, 6, 7))
    monkeypatch.setattr("app.routes.daily_sets.today_vancouver", lambda: date(2026, 6, 7))

    response = await client.get("/daily-sets/today", headers=api_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["set_date"] == "2026-06-07"
    assert len(data["review"]) == 4
    assert data["focus_pattern"] == "Advanced Graphs"
    assert len(data["focused_new"]) == 2

    daily_set = (await session.execute(select(DailySet))).scalar_one()
    assert daily_set.set_date == date(2026, 6, 7)

    done_count = (
        (
            await session.execute(
                select(UserProgress).where(UserProgress.daily_slot != DailySlot.DONE)
            )
        )
        .scalars()
        .all()
    )
    assert len(done_count) == 8
