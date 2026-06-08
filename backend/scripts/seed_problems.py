"""Seed problems and initial user_progress rows from the configured catalog JSON."""

from __future__ import annotations

import asyncio
import json

from sqlalchemy import select

from app.core.srs_config import get_srs_config
from app.database.session import AsyncSessionLocal
from app.enums import Difficulty, ReviewStage
from app.models.problem import Problem
from app.models.user_progress import UserProgress


def _normalize_difficulty(value: str) -> Difficulty:
    return Difficulty(value.lower())


def _full_neetcode_url(relative_url: str) -> str:
    if relative_url.startswith("http"):
        return relative_url
    path = relative_url.split("?", 1)[0]
    return f"https://neetcode.io{path}"


async def seed() -> None:
    config = get_srs_config()
    data_path = config.resolve_catalog_path()
    payload = json.loads(data_path.read_text(encoding="utf-8"))
    problems = payload["problems"]

    async with AsyncSessionLocal() as session:
        existing = (await session.execute(select(Problem.id).limit(1))).scalar_one_or_none()
        if existing is not None:
            print("Problems already seeded; skipping.")
            return

        for index, item in enumerate(problems, start=1):
            problem = Problem(
                slug=item["slug"],
                title=item["name"],
                pattern=item["category"],
                difficulty=_normalize_difficulty(item["difficulty"]),
                leetcode_url=item["leetcode_url"],
                neetcode_url=_full_neetcode_url(item["neetcode_url"]),
                sort_order=index,
            )
            session.add(problem)
            await session.flush()

            progress = UserProgress(
                problem_id=problem.id,
                solved=False,
                review_stage=ReviewStage.NEW,
            )
            session.add(progress)

        await session.commit()
        print(f"Seeded {len(problems)} problems from {data_path}.")


if __name__ == "__main__":
    asyncio.run(seed())
