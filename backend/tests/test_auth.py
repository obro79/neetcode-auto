import pytest


@pytest.mark.asyncio
async def test_protected_route_requires_api_key(client) -> None:
    response = await client.get("/daily-sets/today")
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_invalid_api_key_returns_401(client, api_headers) -> None:
    response = await client.get(
        "/daily-sets/today",
        headers={"X-API-Key": "wrong-key"},
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid API key"


@pytest.mark.asyncio
async def test_valid_api_key_allows_access(client, api_headers) -> None:
    response = await client.get("/daily-sets/today", headers=api_headers)
    assert response.status_code == 200
