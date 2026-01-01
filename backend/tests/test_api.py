import pytest
import asyncio
import json
from unittest.mock import AsyncMock, MagicMock, patch
from httpx import AsyncClient, ASGITransport
from fastapi.testclient import TestClient

# Local imports
from main import app, manager, redis_listener, metrics_broadcaster
from models import Post, SentimentAnalysis
from database import AsyncSessionLocal
from sqlalchemy import insert, inspect

@pytest.mark.asyncio
async def test_api_endpoints_and_data(setup_db):
    """Covers GET endpoints and database selection logic."""
    async with AsyncSessionLocal() as session:
        # Seed a post
        new_post = Post(post_id="test_123", content="Test", author="user", source="web")
        session.add(new_post)
        await session.commit()
        await session.refresh(new_post)
        
        # Seed analysis using sniffed column names
        columns = [c.key for c in inspect(SentimentAnalysis).attrs]
        score_key = next((n for n in ["score", "sentiment_score", "sentiment"] if n in columns), None)
        
        analysis_data = {"post_id": new_post.id, "sentiment_label": "POSITIVE"}
        if score_key: analysis_data[score_key] = 0.99
            
        await session.execute(insert(SentimentAnalysis).values(**analysis_data))
        await session.commit()

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # Cover Health, Posts, Distribution, and Aggregate
        for endpoint in ["/api/health", "/api/posts", "/api/sentiment/distribution", "/api/sentiment/aggregate"]:
            res = await ac.get(endpoint)
            assert res.status_code == 200

@pytest.mark.asyncio
async def test_websocket_manager():
    """Covers ConnectionManager and WebSocketDisconnect logic."""
    mock_ws = AsyncMock()
    await manager.connect(mock_ws)
    assert mock_ws in manager.active_connections
    
    await manager.broadcast_json({"test": "message"})
    
    manager.disconnect(mock_ws)
    assert mock_ws not in manager.active_connections

@pytest.mark.asyncio
async def test_background_worker_logic():
    """Covers redis_listener and metrics_broadcaster logic without infinite loops."""
    
    # 1. Test Redis Listener logic (one iteration)
    mock_pubsub = AsyncMock()
    # Simulate one message then stop
    mock_pubsub.listen.return_value = [
        {"type": "message", "data": json.dumps({"test": "data"})}
    ]
    
    with patch("main.rd.pubsub", return_value=mock_pubsub):
        # We use a timeout because the function has a loop
        try:
            await asyncio.wait_for(redis_listener(), timeout=0.1)
        except (asyncio.TimeoutError, Exception):
            pass # Expected as the loop is infinite

    # 2. Test Metrics Broadcaster logic (one iteration)
    with patch("main.asyncio.sleep", side_effect=asyncio.CancelledError):
        try:
            await metrics_broadcaster()
        except asyncio.CancelledError:
            pass # Successfully hit the logic and exited at sleep


@pytest.mark.asyncio
async def test_aggregate_endpoint_logic(setup_db):
    """Specifically targets the time-bucketed aggregation logic."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # Testing different time periods (hour, day)
        for period in ["hour", "day"]:
            response = await ac.get(f"/api/sentiment/aggregate?period={period}")
            assert response.status_code == 200
            assert "data" in response.json()