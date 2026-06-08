"""Send the daily NeetCode email. Invoked by Railway cron."""

from __future__ import annotations

import argparse
import asyncio

from app.database.session import AsyncSessionLocal
from app.services.email_dispatch import send_daily_set_email


async def run(attempt: int) -> int:
    async with AsyncSessionLocal() as session:
        result = await send_daily_set_email(session, attempt)
        print(result.message)
        return 0 if result.sent or "already sent" in result.message.lower() else 1


def main() -> None:
    parser = argparse.ArgumentParser(description="Send daily NeetCode email")
    parser.add_argument("--attempt", type=int, default=1, choices=[1, 2])
    args = parser.parse_args()
    raise SystemExit(asyncio.run(run(args.attempt)))


if __name__ == "__main__":
    main()
