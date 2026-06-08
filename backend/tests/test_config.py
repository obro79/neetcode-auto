import pytest


@pytest.mark.asyncio
async def test_public_config_includes_slug_aliases(client) -> None:
    response = await client.get("/config/public")
    assert response.status_code == 200
    data = response.json()
    assert data["slug_aliases"]["two-sum"] == "two-integer-sum"
    assert "sync_only_daily_set" in data
