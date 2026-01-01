import asyncio
import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from models import Base, Post, SentimentAnalysis
from database import DATABASE_URL
from datetime import datetime

@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest_asyncio.fixture(scope="session", autouse=True)
async def setup_db():
    engine = create_async_engine(DATABASE_URL)
    async with engine.begin() as conn:
        # This creates the tables based on your models.py
        await conn.run_sync(Base.metadata.create_all)
    
    # Create an async session to seed data
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        # 1. Create a Post (this holds the 'content')
        test_post = Post(
            post_id="unique_123",
            source="test_source",
            content="This is a test post content",
            author="test_author"
        )
        session.add(test_post)
        await session.flush()  # Flush to get the test_post.id

        # 2. Create the Analysis linked to that post
        test_analysis = SentimentAnalysis(
            post_id=test_post.id,
            sentiment_label="POSITIVE",
            confidence_score=0.95,
            emotion="joy",
            model_name="v1-transformer"
        )
        session.add(test_analysis)
        await session.commit()
    
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()