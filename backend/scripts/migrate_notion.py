"""Optional one-off migration from exported Notion tracker JSON.

Expected input shape (array of objects):
{
  "slug": "two-sum",
  "solved": true,
  "review_stage": "7d",
  "next_review": "2026-06-10",
  "last_practiced": "2026-06-03",
  "confidence": "getting_there"
}
"""

from __future__ import annotations

import argparse
import asyncio
import json
from datetime import date
from pathlib import Path

from sqlalchemy import select

from app.database.session import AsyncSessionLocal
from app.enums import Confidence, ReviewStage
from app.models.problem import Problem
from app.models.user_progress import UserProgress


def _parse_date(value: str | None) -> date | None:
    if not value:
        return None
    return date.fromisoformat(value)


async def migrate(path: Path) -> None:
    rows = json.loads(path.read_text(encoding="utf-8"))
    async with AsyncSessionLocal() as session:
        for row in rows:
            stmt = select(Problem).where(Problem.slug == row["slug"])
            problem = (await session.execute(stmt)).scalar_one_or_none()
            if problem is None:
                print(f"Skipping unknown slug: {row['slug']}")
                continue

            progress_stmt = select(UserProgress).where(UserProgress.problem_id == problem.id)
            progress = (await session.execute(progress_stmt)).scalar_one()
            progress.solved = bool(row.get("solved", False))
            progress.review_stage = ReviewStage(row["review_stage"])
            progress.next_review = _parse_date(row.get("next_review"))
            progress.last_practiced = _parse_date(row.get("last_practiced"))
            confidence = row.get("confidence")
            progress.confidence = Confidence(confidence) if confidence else None

        await session.commit()
        print(f"Migrated {len(rows)} rows.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Migrate Notion tracker export")
    parser.add_argument("export_json", type=Path)
    args = parser.parse_args()
    asyncio.run(migrate(args.export_json))


if __name__ == "__main__":
    main()
