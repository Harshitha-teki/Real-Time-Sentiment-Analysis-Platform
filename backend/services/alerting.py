from sqlalchemy import select, func
from datetime import datetime, timedelta
from database import AsyncSessionLocal
from models import SentimentAnalysis

async def check_sentiment_alerts(manager):
    """Checks for negative sentiment spikes and broadcasts alerts."""
    async with AsyncSessionLocal() as session:
        # Check the last 2 minutes
        threshold_time = datetime.utcnow() - timedelta(minutes=2)
        
        # Query for negative sentiment count
        query = select(func.count()).select_from(SentimentAnalysis).where(
            SentimentAnalysis.sentiment_label == 'negative',
            SentimentAnalysis.created_at >= threshold_time
        )
        
        result = await session.execute(query)
        count = result.scalar()
        
        # Trigger an alert if more than 5 negative posts appear
        if count > 5:
            await manager.broadcast_json({
                "type": "alert",
                "text": f"CRITICAL: {count} negative posts detected in the last 2 minutes!"
            })