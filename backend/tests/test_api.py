import pytest
from httpx import AsyncClient, ASGITransport
from main import app

@pytest.mark.asyncio
async def test_health_check():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/health")
    assert response.status_code == 200

@pytest.mark.asyncio
async def test_distribution_endpoint():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/sentiment/distribution")
    assert response.status_code == 200
    assert "distribution" in response.json()

@pytest.mark.asyncio
async def test_aggregate_endpoint():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/sentiment/aggregate?period=hour")
    assert response.status_code == 200
    assert "data" in response.json()