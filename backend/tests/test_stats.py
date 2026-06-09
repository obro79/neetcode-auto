from datetime import date

import pytest

from app.enums import Confidence, Difficulty, ReviewStage


@pytest.mark.asyncio
async def test_stats_summary_requires_api_key(client) -> None:
    response = await client.get("/stats/summary")
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_stats_summary_aggregates(client, session, api_headers, monkeypatch) -> None:
    today = date(2026, 6, 9)
    monkeypatch.setattr("app.routes.stats.today_vancouver", lambda: today)
    monkeypatch.setattr("app.routes.reviews.today_vancouver", lambda: today)

    fixtures = [
        (
            "due-today",
            "Arrays & Hashing",
            True,
            ReviewStage.ONE_DAY,
            today,
            Confidence.STRUGGLING,
        ),
        (
            "due-overdue",
            "Two Pointers",
            True,
            ReviewStage.THREE_DAY,
            date(2026, 6, 7),
            Confidence.GETTING_THERE,
        ),
        ("mastered", "Sliding Window", True, ReviewStage.MASTERED, None, Confidence.SOLID),
        ("unsolved", "Stack", False, ReviewStage.NEW, None, None),
        ("unsolved-2", "Arrays & Hashing", False, ReviewStage.NEW, None, None),
    ]
    for index, (slug, pattern, solved, stage, next_review, confidence) in enumerate(
        fixtures, start=1
    ):
        from app.models.problem import Problem
        from app.models.user_progress import UserProgress

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
                solved=solved,
                review_stage=stage,
                next_review=next_review,
                confidence=confidence,
            )
        )
    await session.commit()

    response = await client.get("/stats/summary", headers=api_headers)
    assert response.status_code == 200
    data = response.json()

    assert data["total"] == 5
    assert data["solved"] == 3
    assert data["unsolved"] == 2
    assert data["by_confidence"] == {
        "struggling": 1,
        "getting_there": 1,
        "solid": 1,
        "unset": 2,
    }
    assert data["by_review_stage"]["new"] == 2
    assert data["by_review_stage"]["1d"] == 1
    assert data["by_review_stage"]["3d"] == 1
    assert data["by_review_stage"]["mastered"] == 1
    assert data["due_today"] == 1
    assert data["due_overdue"] == 1
    assert data["mastered"] == 1

    patterns = {row["pattern"]: row for row in data["by_pattern"]}
    assert patterns["Arrays & Hashing"] == {"pattern": "Arrays & Hashing", "solved": 1, "total": 2}
    assert patterns["Stack"] == {"pattern": "Stack", "solved": 0, "total": 1}


@pytest.mark.asyncio
async def test_due_reviews_sorted_and_limited(client, session, api_headers, monkeypatch) -> None:
    today = date(2026, 6, 9)
    monkeypatch.setattr("app.routes.stats.today_vancouver", lambda: today)
    monkeypatch.setattr("app.routes.reviews.today_vancouver", lambda: today)

    fixtures = [
        ("older-review", date(2026, 6, 1), Confidence.SOLID, 1),
        ("today-review", today, Confidence.STRUGGLING, 2),
        ("today-solid", today, Confidence.SOLID, 3),
        ("not-due", date(2026, 6, 15), Confidence.STRUGGLING, 4),
    ]
    for slug, next_review, confidence, sort_order in fixtures:
        from app.models.problem import Problem
        from app.models.user_progress import UserProgress

        problem = Problem(
            slug=slug,
            title=slug,
            pattern="Greedy",
            difficulty=Difficulty.MEDIUM,
            leetcode_url=f"https://leetcode.com/problems/{slug}/",
            neetcode_url=f"https://neetcode.io/problems/{slug}",
            sort_order=sort_order,
        )
        session.add(problem)
        await session.flush()
        session.add(
            UserProgress(
                problem_id=problem.id,
                solved=True,
                review_stage=ReviewStage.ONE_DAY,
                next_review=next_review,
                confidence=confidence,
            )
        )
    await session.commit()

    response = await client.get("/reviews/due?limit=2", headers=api_headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["slug"] == "older-review"
    assert data[1]["slug"] == "today-review"
    assert all(item["progress"]["solved"] for item in data)


@pytest.mark.asyncio
async def test_auth_verify(client, api_headers) -> None:
    response = await client.get("/auth/verify", headers=api_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["ok"] is True
    assert data["app_name"] == "NeetCode SRS"
