import asyncio
import json
import os
import redis
import logging
from sentiment_analyzer import SentimentAnalyzer
from sqlalchemy import create_engine, text
from datetime import datetime

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database Setup (sync engine for worker)
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://sentiment_user:secure_pass_123@db:5432/sentiment_db')
# If an async URL was provided (e.g. postgresql+asyncpg://), convert it to a sync URL
if DATABASE_URL.startswith('postgresql+asyncpg://'):
    DATABASE_URL = DATABASE_URL.replace('postgresql+asyncpg://', 'postgresql://', 1)
engine = create_engine(DATABASE_URL)

async def start_worker():
    # Initialize Analyzer
    analyzer = SentimentAnalyzer()
    
    # Connect to Redis
    r = redis.Redis(host='redis', port=6379, decode_responses=True)
    logger.info("👷 Worker connected to social_posts_stream. Listening for posts...")

    while True:
        try:
            # Read from Redis Stream
            streams = r.xread({'social_posts_stream': '0'}, count=1, block=5000)
            
            if streams:
                for stream_name, messages in streams:
                    for msg_id, data in messages:
                        content = data.get('content', '')
                        post_id = data.get('post_id', msg_id)
                        
                        # Perform AI Analysis
                        results = analyzer.analyze(content)
                        
                        # Save to Database using SQL compatible with backend models
                        try:
                            with engine.begin() as conn:
                                # Upsert post into social_media_posts, return internal id
                                res = conn.execute(
                                    text("""
                                    INSERT INTO social_media_posts (post_id, source, content, author, created_at)
                                    VALUES (:post_id, :source, :content, :author, :created_at)
                                    ON CONFLICT (post_id) DO UPDATE SET content = EXCLUDED.content
                                    RETURNING id
                                    """),
                                    {
                                        "post_id": post_id,
                                        "source": "ingester",
                                        "content": content,
                                        "author": None,
                                        "created_at": datetime.utcnow()
                                    }
                                )
                                row = res.fetchone()
                                internal_id = row[0] if row is not None else None

                                # Insert sentiment_analysis row matching backend schema
                                conn.execute(
                                    text("""
                                    INSERT INTO sentiment_analysis (post_id, sentiment_label, confidence_score, emotion, model_name, created_at)
                                    VALUES (:post_id, :label, :confidence, :emotion, :model, :created_at)
                                    """),
                                    {
                                        "post_id": internal_id,
                                        "label": results.get('sentiment_label') or 'unknown',
                                        "confidence": results.get('sentiment_score') or results.get('confidence_score') or 0.0,
                                        "emotion": results.get('emotion') or 'neutral',
                                        "model": results.get('model_name') or 'worker-model',
                                        "created_at": datetime.utcnow()
                                    }
                                )
                        except Exception as e:
                            logger.error(f"DB write failed: {e}")
                        
                        # Publish a compact event to Redis pub/sub for realtime UI
                        try:
                            payload = json.dumps({
                                "post_id": post_id,
                                "content": content,
                                "sentiment": results['sentiment_label'],
                                "confidence": results.get('sentiment_score') or results.get('confidence_score'),
                                "emotion": results.get('emotion'),
                                "timestamp": datetime.utcnow().isoformat()
                            })
                            r.publish('sentiment_updates', payload)
                        except Exception as e:
                            logger.warning(f"Failed to publish to Redis pubsub: {e}")

                        # Delete from Redis after processing (optional)
                        r.xdel('social_posts_stream', msg_id)
                        
                        logger.info(f"✅ Processed: {post_id} | Label: {results['sentiment_label']} | Emotion: {results['emotion']}")

        except Exception as e:
            logger.error(f"Error in worker loop: {e}")
            await asyncio.sleep(2)

if __name__ == "__main__":
    asyncio.run(start_worker())