import asyncio
import json
import redis
import logging
from sentiment_analyzer import SentimentAnalyzer
from sqlalchemy import create_engine, Column, String, Float, Integer, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database Setup
Base = declarative_base()
class SentimentResult(Base):
    __tablename__ = 'sentiment_analysis'
    id = Column(Integer, primary_key=True)
    post_id = Column(String)
    content = Column(String)
    sentiment_label = Column(String)
    sentiment_score = Column(Float)
    emotion = Column(String)
    emotion_score = Column(Float)
    timestamp = Column(DateTime, default=datetime.utcnow)

engine = create_engine('postgresql://sentiment_user:sentiment_pass@db:5432/sentiment_db')
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)
db_session = Session()

async def start_worker():
    # Initialize Analyzer
    analyzer = SentimentAnalyzer()
    
    # Connect to Redis
    r = redis.Redis(host='redis', port=6379, decode_responses=True)
    logger.info("👷 Worker connected to social_posts_stream. Listening for posts...")

    while True:
        try:
            # Read from Redis Stream
            # ID '0' reads from the beginning, '$' reads only new posts
            streams = r.xread({'social_posts_stream': '0'}, count=1, block=5000)
            
            if streams:
                for stream_name, messages in streams:
                    for msg_id, data in messages:
                        content = data.get('content', '')
                        post_id = data.get('post_id', msg_id)
                        
                        # Perform AI Analysis
                        results = analyzer.analyze(content)
                        
                        # Save to Database
                        new_record = SentimentResult(
                            post_id=post_id,
                            content=content,
                            sentiment_label=results['sentiment_label'],
                            sentiment_score=results['sentiment_score'],
                            emotion=results['emotion'],
                            emotion_score=results['emotion_score']
                        )
                        db_session.add(new_record)
                        db_session.commit()
                        
                        # Delete from Redis after processing (optional)
                        r.xdel('social_posts_stream', msg_id)
                        
                        logger.info(f"✅ Processed: {post_id} | Label: {results['sentiment_label']} | Emotion: {results['emotion']}")

        except Exception as e:
            logger.error(f"Error in worker loop: {e}")
            await asyncio.sleep(2)

if __name__ == "__main__":
    asyncio.run(start_worker())