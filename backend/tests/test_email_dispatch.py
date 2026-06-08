from datetime import date

from app.core.srs_config import EmailConfig
from app.services.email_dispatch import _slot_ready, scheduled_send_times


def test_scheduled_send_times_from_anchor() -> None:
    config = EmailConfig(
        anchor_time="07:00",
        backoff_minutes=[0, 30, 90, 210],
    )
    set_date = date(2026, 6, 7)
    slots = scheduled_send_times(set_date, config)
    assert len(slots) == 4
    assert slots[0].hour == 7 and slots[0].minute == 0
    assert slots[1].hour == 7 and slots[1].minute == 30
    assert slots[2].hour == 8 and slots[2].minute == 30
    assert slots[3].hour == 10 and slots[3].minute == 30


def test_slot_ready_respects_backoff() -> None:
    config = EmailConfig(anchor_time="07:00", backoff_minutes=[0, 30])
    set_date = date(2026, 6, 7)
    slots = scheduled_send_times(set_date, config)

    assert _slot_ready(slots[0], set_date, config, 1) is True
    assert _slot_ready(slots[0], set_date, config, 2) is False
    assert _slot_ready(slots[1], set_date, config, 2) is True
