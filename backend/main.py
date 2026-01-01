import asyncio
import json
from contextlib import asynccontextmanager
from typing import List

import redis.asyncio as redis
from fastapi import FastAPI, Query, Depends, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

# Internal imports - Ensure these files exist in your directory
from database import get_db, engine, AsyncSessionLocal
from models import Base, Post, SentimentAnalysis

# --- WebSocket Connection Manager ---
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
            try:
                await ws.send_json(message)
            except Exception:
                self.disconnect(ws)

manager = ConnectionManager()
# Redis connection using the service name defined in docker-compose
rd = redis.from_url("redis://redis:6379/0", decode_responses=True)

# --- Background Worker Tasks ---
async def redis_listener():
    """Subscribes to Redis and broadcasts new sentiment data to WebSockets."""
    pubsub = rd.pubsub()
    await pubsub.subscribe("sentiment_updates")
    try:
        async for message in pubsub.listen():
            if message.get("type") == "message":
                try:
                    data = json.loads(message["data"])
                    await manager.broadcast_json({"type": "new_post", "data": data})
                except Exception:
                    continue
    except asyncio.CancelledError:
        await pubsub.unsubscribe("sentiment_updates")
    finally:
        await pubsub.close()

async def metrics_broadcaster():
    """Periodically pushes aggregate sentiment stats to the frontend."""
    while True:
        try:
            # We use AsyncSessionLocal directly here because it's a background task, 
            # not a standard FastAPI request with Depends()
            async with AsyncSessionLocal() as session:
                q = select(
                    SentimentAnalysis.sentiment_label, 
                    func.count()
                ).group_by(SentimentAnalysis.sentiment_label)
                
                res = await session.execute(q)
                results = res.all()
                counts = {r[0]: r[1] for r in results}
                
                await manager.broadcast_json({
                    "type": "metrics_update", 
                    "data": {"last_24_hours": counts}
                })
        except Exception as e:
            print(f"Broadcaster error: {e}")
        
        await asyncio.sleep(10)

# --- Lifespan Management ---
# This manages the startup and shutdown, ensuring the Event Loop is shared correctly.
@asynccontextmanager
async def lifespan(app: FastAPI):
    # STARTUP: Setup DB tables and start background workers
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    listener_task = asyncio.create_task(redis_listener())
    broadcaster_task = asyncio.create_task(metrics_broadcaster())
    
    yield  # The app serves requests here
    
    # SHUTDOWN: Cleanup
    listener_task.cancel()
    broadcaster_task.cancel()
    try:
        await asyncio.gather(listener_task, broadcaster_task, return_exceptions=True)
    finally:
        await engine.dispose()
        await rd.close()

# --- FastAPI App Configuration ---
app = FastAPI(title="Real-Time Sentiment Analysis API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- API Endpoints ---

@app.get("/api/health")
async def health_check():
    return {"status": "healthy"}

@app.get("/api/posts")
async def get_posts(limit: int = 10, db: AsyncSession = Depends(get_db)):
    """Joins posts with analysis results for the main feed."""
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
    """Calculates distribution for the pie chart."""
    q = select(
        SentimentAnalysis.sentiment_label, 
        func.count()
    ).group_by(SentimentAnalysis.sentiment_label)
    
    res = await db.execute(q)
    dist = {r[0]: r[1] for r in res.all()}
    return {
        "distribution": dist if dist else {"neutral": 0}, 
        "total": sum(dist.values()) if dist else 0
    }

@app.get("/api/sentiment/aggregate")
async def get_sentiment_aggregate(period: str = Query("hour"), db: AsyncSession = Depends(get_db)):
    """Provides time-bucketed data for the trend line chart."""
    bucket = func.date_trunc(period, SentimentAnalysis.created_at).label("ts")
    query = (
        select(bucket, SentimentAnalysis.sentiment_label, func.count())
        .group_by(bucket, SentimentAnalysis.sentiment_label)
        .order_by(bucket)
    )
    res = await db.execute(query)
    return {"data": [{"ts": r[0], "label": r[1], "count": r[2]} for r in res.all()]}

# --- WebSocket Implementation ---
@app.websocket("/ws/sentiment")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # Keep connection alive; waiting for client heartbeat/text
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception:
        manager.disconnect(websocket)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, log_level="info", reload=True)