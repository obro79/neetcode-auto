from datetime import date, datetime
from zoneinfo import ZoneInfo

from app.core.srs_config import get_srs_config


def vancouver_tz() -> ZoneInfo:
    return ZoneInfo(get_srs_config().timezone)


def today_vancouver() -> date:
    return datetime.now(vancouver_tz()).date()


def now_vancouver() -> datetime:
    return datetime.now(vancouver_tz())
