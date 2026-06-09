"""Send internship job digest emails. Invoked by Railway cron every 15 minutes."""

from __future__ import annotations

import argparse
import asyncio

from app.database.session import AsyncSessionLocal
from app.services.jobs.digest_dispatch import send_job_digest


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print what would happen without sending email or writing skip logs.",
    )
    parser.add_argument(
        "--force-slot",
        type=int,
        choices=[1, 2, 3],
        help="Force a digest slot (testing only).",
    )
    return parser.parse_args()


async def run(dry_run: bool = False, force_slot: int | None = None) -> int:
    async with AsyncSessionLocal() as session:
        result = await send_job_digest(
            session,
            dry_run=dry_run,
            force_slot=force_slot,
        )
        print(
            f"{result.digest_date} slot={result.slot} sent={result.sent} "
            f"filtered={result.filtered_count} new={result.new_count} "
            f"top={result.top_count} — {result.message}"
        )
        lowered = result.message.lower()
        if result.sent:
            return 0
        if "skipped" in lowered or "not yet" in lowered or "already sent" in lowered:
            return 0
        if dry_run:
            return 0
        return 1


def main() -> None:
    args = parse_args()
    raise SystemExit(asyncio.run(run(dry_run=args.dry_run, force_slot=args.force_slot)))


if __name__ == "__main__":
    main()
