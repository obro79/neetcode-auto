from datetime import date, datetime
from zoneinfo import ZoneInfo

VANCOUVER_TZ = ZoneInfo("America/Vancouver")


def today_vancouver() -> date:
    return datetime.now(VANCOUVER_TZ).date()


def now_vancouver() -> datetime:
    return datetime.now(VANCOUVER_TZ)
