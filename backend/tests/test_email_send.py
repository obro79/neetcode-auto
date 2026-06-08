from datetime import date, datetime
from unittest.mock import AsyncMock

import pytest
from sqlalchemy import select

from app.core.timezone import vancouver_tz
from app.models.email_log import EmailLog


@pytest.mark.asyncio
async def test_send_skips_before_scheduled_slot(client, api_headers, monkeypatch) -> None:
    set_date = date(2026, 6, 7)
    monkeypatch.setattr("app.services.email_dispatch.today_vancouver", lambda: set_date)
    monkeypatch.setattr(
        "app.services.email_dispatch.now_vancouver",
        lambda: datetime(2026, 6, 7, 6, 0, tzinfo=vancouver_tz()),
    )

    response = await client.post("/daily-sets/today/send", headers=api_headers)
    assert response.status_code == 200
    payload = response.json()
    assert payload["sent"] is False
    assert "Not yet time" in payload["message"]


@pytest.mark.asyncio
async def test_send_at_slot_records_email_log(
    client,
    session,
    api_headers,
    monkeypatch,
) -> None:
    set_date = date(2026, 6, 7)
    monkeypatch.setattr("app.services.email_dispatch.today_vancouver", lambda: set_date)
    monkeypatch.setattr(
        "app.services.email_dispatch.now_vancouver",
        lambda: datetime(2026, 6, 7, 7, 5, tzinfo=vancouver_tz()),
    )
    monkeypatch.setattr(
        "app.services.email_dispatch.send_daily_email",
        AsyncMock(return_value="test-resend-id"),
    )

    response = await client.post("/daily-sets/today/send", headers=api_headers)
    assert response.status_code == 200
    payload = response.json()
    assert payload["sent"] is True
    assert payload["attempt"] == 1

    log = (await session.execute(select(EmailLog))).scalar_one()
    assert log.success is True
    assert log.resend_id == "test-resend-id"
    assert log.attempt == 1


@pytest.mark.asyncio
async def test_send_skips_after_successful_send_today(
    client,
    session,
    api_headers,
    monkeypatch,
) -> None:
    set_date = date(2026, 6, 7)
    now = datetime(2026, 6, 7, 7, 5, tzinfo=vancouver_tz())
    monkeypatch.setattr("app.services.email_dispatch.today_vancouver", lambda: set_date)
    monkeypatch.setattr("app.services.email_dispatch.now_vancouver", lambda: now)
    monkeypatch.setattr(
        "app.services.email_dispatch.send_daily_email",
        AsyncMock(return_value="first-id"),
    )

    first = await client.post("/daily-sets/today/send", headers=api_headers)
    assert first.json()["sent"] is True

    second = await client.post("/daily-sets/today/send", headers=api_headers)
    assert second.json()["sent"] is False
    assert "already sent" in second.json()["message"].lower()
