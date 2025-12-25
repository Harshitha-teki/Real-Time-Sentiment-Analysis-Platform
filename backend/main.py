from fastapi import FastAPI, Query, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, text
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
import json
import redis.asyncio as redis

# Use absolute imports to ensure package runs correctly inside container
from backend.database import get_db, engine
from backend.models import SocialMediaPost, SentimentAnalysis

app = FastAPI(title="Sentiment Analysis API")
# Connect to redis service defined in docker-compose
rd = redis.from_url("redis://redis:6379/0", decode_responses=True)

# Endpoint 1: Health Check (4.1.1)
@app.get("/api/health")
async def health_check(db: AsyncSession = Depends(get_db)):
    try:
        await db.execute(text("SELECT 1"))
        db_status = "connected"
    except Exception:
        db_status = "disconnected"
    
    try:
        await rd.ping()
        redis_status = "connected"
    except Exception:
        redis_status = "disconnected"
    
    status = "healthy" if db_status == "connected" and redis_status == "connected" else "unhealthy"
    return {
        "status": status,
        "timestamp": datetime.utcnow().isoformat(),
        "services": {"database": db_status, "redis": redis_status}
    }

# Endpoint 2: Get Posts (4.1.2)
@app.get("/api/posts")
async def get_posts(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    sentiment: Optional[str] = None,
    source: Optional[str] = None,
    start_ts: Optional[datetime] = None,
    end_ts: Optional[datetime] = None,
    db: AsyncSession = Depends(get_db)
):
    # Base query joining posts with their sentiment analysis
    query = select(SocialMediaPost, SentimentAnalysis).join(SentimentAnalysis)

    # Apply filters
    if sentiment:
        query = query.where(SentimentAnalysis.sentiment_label == sentiment)
    if source:
        query = query.where(SocialMediaPost.source == source)
    if start_ts:
        query = query.where(SocialMediaPost.created_at >= start_ts)
    if end_ts:
        query = query.where(SocialMediaPost.created_at <= end_ts)

    total_q = select(func.count()).select_from(SocialMediaPost).join(SentimentAnalysis)
    if sentiment:
        total_q = total_q.where(SentimentAnalysis.sentiment_label == sentiment)
    if source:
        total_q = total_q.where(SocialMediaPost.source == source)
    if start_ts:
        total_q = total_q.where(SocialMediaPost.created_at >= start_ts)
    if end_ts:
        total_q = total_q.where(SocialMediaPost.created_at <= end_ts)

    # paging and ordering
    query = query.order_by(SocialMediaPost.created_at.desc()).offset(offset).limit(limit)

    total_res = await db.execute(total_q)
    total_count = total_res.scalar_one()

    result = await db.execute(query)
    rows = result.all()

    posts: List[Dict[str, Any]] = []
    for row in rows:
        post_obj = row[0]
        analysis_obj = row[1]
        posts.append({
            "id": post_obj.id,
            "post_id": post_obj.post_id,
            "source": post_obj.source,
            "content": post_obj.content,
            "author": post_obj.author,
            "created_at": post_obj.created_at.isoformat() if post_obj.created_at else None,
            "sentiment": {
                "label": analysis_obj.sentiment_label,
                "confidence": analysis_obj.confidence_score,
                "emotion": analysis_obj.emotion,
                "model": analysis_obj.model_name
            }
        })

    return {"posts": posts, "limit": limit, "offset": offset, "total": total_count}

# Endpoint 4: Sentiment Distribution with Caching (4.1.4)
@app.get("/api/sentiment/distribution")
async def get_distribution(hours: int = Query(24, ge=1, le=168), db: AsyncSession = Depends(get_db)):
    cache_key = f"dist_{hours}"
    cached = await rd.get(cache_key)
    
    if cached:
        return {**json.loads(cached), "cached": True}
    # Compute time window
    start_ts = datetime.utcnow() - timedelta(hours=hours)

    q = select(SentimentAnalysis.sentiment_label, func.count().label("cnt")).join(SocialMediaPost).where(SocialMediaPost.created_at >= start_ts).group_by(SentimentAnalysis.sentiment_label)
    res = await db.execute(q)
    rows = res.all()

    dist = {"positive": 0, "negative": 0, "neutral": 0}
    total = 0
    for label, cnt in rows:
        if label in dist:
            dist[label] = cnt
        else:
            dist[label] = cnt
        total += cnt

    result_data = {
        "timeframe_hours": hours,
        "distribution": dist,
        "total": total,
        "cached": False,
        "cached_at": datetime.utcnow().isoformat()
    }

    # Cache for 60 seconds
    try:
        await rd.setex(cache_key, 60, json.dumps(result_data))
    except Exception:
        # don't fail the request if redis is unavailable
        pass

    return result_data



@app.get("/api/sentiment/aggregate")
async def sentiment_aggregate(hours: int = Query(24, ge=1, le=168), interval: str = Query("hour"), db: AsyncSession = Depends(get_db)):
    """Return time-bucketed sentiment counts over the past `hours`.
    interval: 'hour' or 'day'
    """
    if interval not in ("hour", "day"):
        raise HTTPException(status_code=400, detail="interval must be 'hour' or 'day'")

    start_ts = datetime.utcnow() - timedelta(hours=hours)

    # Use date_trunc via SQLAlchemy func
    bucket = func.date_trunc(interval, SocialMediaPost.created_at).label("bucket")
    q = select(bucket, SentimentAnalysis.sentiment_label, func.count().label("cnt")).join(SocialMediaPost).where(SocialMediaPost.created_at >= start_ts).group_by(bucket, SentimentAnalysis.sentiment_label).order_by(bucket)

    res = await db.execute(q)
    rows = res.all()

    # organize into {bucket: {label: count}}
    out: Dict[str, Dict[str, int]] = {}
    for bucket_val, label, cnt in rows:
        b = bucket_val.isoformat() if hasattr(bucket_val, 'isoformat') else str(bucket_val)
        if b not in out:
            out[b] = {"positive": 0, "negative": 0, "neutral": 0}
        out[b][label] = cnt

    return {"interval": interval, "hours": hours, "buckets": out}