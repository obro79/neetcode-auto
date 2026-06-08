"""Send the daily NeetCode email. Invoked by Railway cron every 15 minutes."""

from __future__ import annotations

import asyncio

from app.database.session import AsyncSessionLocal
from app.services.email_dispatch import send_daily_set_email


async def run() -> int:
    async with AsyncSessionLocal() as session:
        result = await send_daily_set_email(session)
        print(result.message)
        if result.sent:
            return 0
        if "already sent" in result.message.lower():
            return 0
        if "not yet time" in result.message.lower():
            return 0
        return 1


def main() -> None:
    raise SystemExit(asyncio.run(run()))


if __name__ == "__main__":
    main()
