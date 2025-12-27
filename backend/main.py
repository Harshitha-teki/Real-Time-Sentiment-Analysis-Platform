from fastapi import FastAPI, Query, Depends, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import datetime, timedelta
import json
import asyncio
import redis.asyncio as redis
from typing import List

# Ensure these match your database.py and updated models.py
from database import get_db, engine, AsyncSessionLocal
from models import Base, Post, SentimentAnalysis

app = FastAPI(title="Real-Time Sentiment Analysis API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Simplified for troubleshooting
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

rd = redis.from_url("redis://redis:6379/0", decode_responses=True)

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
    async def broadcast_json(self, message: dict):
        for ws in list(self.active_connections):
            try: await ws.send_json(message)
            except: self.disconnect(ws)

manager = ConnectionManager()

async def redis_listener():
    pubsub = rd.pubsub()
    await pubsub.subscribe("sentiment_updates")
    async for message in pubsub.listen():
        if message.get("type") == "message":
            try:
                data = json.loads(message["data"])
                await manager.broadcast_json({"type": "new_post", "data": data})
            except: pass

async def metrics_broadcaster():
    while True:
        try:
            async with AsyncSessionLocal() as session:
                # Aggregate counts from SentimentAnalysis
                q = select(SentimentAnalysis.sentiment_label, func.count()).group_by(SentimentAnalysis.sentiment_label)
                res = await session.execute(q)
                counts = {r[0]: r[1] for r in res.all()}
                await manager.broadcast_json({"type": "metrics_update", "data": {"last_24_hours": counts}})
        except: pass
        await asyncio.sleep(10)

@app.on_event("startup")
async def startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    asyncio.create_task(redis_listener())
    asyncio.create_task(metrics_broadcaster())

@app.get("/api/health")
async def health_check():
    return {"status": "healthy"}

@app.get("/api/posts")
async def get_posts(limit: int = 10, db: AsyncSession = Depends(get_db)):
    # Join posts with latest analysis entries and return the most recent ones
    query = (
        select(Post.content, SentimentAnalysis.sentiment_label, Post.post_id)
        .join(SentimentAnalysis, SentimentAnalysis.post_id == Post.id)
        .order_by(SentimentAnalysis.id.desc())
        .limit(limit)
    )
    res = await db.execute(query)
    rows = res.all()
    return {"posts": [{"content": r[0], "sentiment": r[1], "id": r[2]} for r in rows]}

@app.get("/api/sentiment/distribution")
async def get_sentiment_distribution(db: AsyncSession = Depends(get_db)):
    q = select(SentimentAnalysis.sentiment_label, func.count()).group_by(SentimentAnalysis.sentiment_label)
    res = await db.execute(q)
    dist = {r[0]: r[1] for r in res.all()}
    return {"distribution": dist or {"neutral": 0}, "total": sum(dist.values())}

@app.get("/api/sentiment/aggregate")
async def get_sentiment_aggregate(period: str = Query("hour"), db: AsyncSession = Depends(get_db)):
    bucket = func.date_trunc(period, SentimentAnalysis.created_at).label("ts")
    query = (
        select(bucket, SentimentAnalysis.sentiment_label, func.count())
        .group_by(bucket, SentimentAnalysis.sentiment_label)
        .order_by(bucket)
    )
    res = await db.execute(query)
    return {"data": [{"ts": r[0], "label": r[1], "count": r[2]} for r in res.all()]}

@app.websocket("/ws/sentiment")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True: await websocket.receive_text()
    except WebSocketDisconnect: manager.disconnect(websocket)


if __name__ == "__main__":
    # Run with Uvicorn when executing this module directly (used by docker-compose)
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, log_level="info")