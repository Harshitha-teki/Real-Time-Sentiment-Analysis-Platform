import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

# Use asyncpg for Phase 4 performance requirements
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://sentiment_user:secure_pass_123@db:5432/sentiment_db")

engine = create_async_engine(DATABASE_URL, echo=True)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session