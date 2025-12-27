import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select, update
from sqlalchemy.dialects.postgresql import insert

# Import your models from the backend folder
# (Ensure your Docker volumes/paths allow the worker to see these)
from models import SocialMediaPost, SentimentAnalysis

DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_async_engine(DATABASE_URL)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def save_post_and_analysis(post_data: dict, sentiment_result: dict, emotion_result: dict):
    """
    Saves post and analysis results to database using an Upsert strategy.
    """
    async with AsyncSessionLocal() as session:
        async with session.begin():
            try:
                # 1. UPSERT the Post (Requirement 3.3: Update ingested_at if exists)
                # This ensures we don't get duplicate errors for the same post_id
                stmt = insert(SocialMediaPost).values(
                    post_id=post_data['post_id'],
                    source=post_data['source'],
                    content=post_data['content'],
                    author=post_data['author'],
                    created_at=post_data['created_at']
                )
                
                # If post_id exists, just update the content (or timestamp)
                do_update_stmt = stmt.on_conflict_do_update(
                    index_elements=['post_id'],
                    set_=dict(content=post_data['content'])
                )
                
                result = await session.execute(do_update_stmt)
                
                # Get the internal database ID for the post to link the analysis
                query = select(SocialMediaPost.id).where(SocialMediaPost.post_id == post_data['post_id'])
                post_record = await session.execute(query)
                internal_post_id = post_record.scalar_one()

                # 2. Insert Sentiment Analysis (Requirement 3.3)
                new_analysis = SentimentAnalysis(
                    post_id=internal_post_id,
                    sentiment_label=sentiment_result['sentiment_label'],
                    confidence_score=sentiment_result['confidence_score'],
                    emotion=emotion_result['emotion'],
                    model_name=sentiment_result['model_name']
                )
                
                session.add(new_analysis)
                
                # The 'async with session.begin()' handles the commit automatically
                return internal_post_id
                
            except Exception as e:
                await session.rollback()
                print(f"Database Error: {e}")
                raise e