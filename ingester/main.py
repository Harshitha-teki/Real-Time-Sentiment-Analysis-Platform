import os
import redis
import asyncio
from ingester import DataIngester

async def main():
    # Load config from .env (passed via docker-compose)
    redis_host = os.getenv('REDIS_HOST', 'redis')
    redis_port = int(os.getenv('REDIS_PORT', 6379))
    stream_name = os.getenv('REDIS_STREAM_NAME', 'social_posts_stream')
    
    # Connect to Redis
    r = redis.Redis(
        host=redis_host, 
        port=redis_port, 
        decode_responses=True
    )
    
    # Initialize and start
    ingester = DataIngester(r, stream_name, posts_per_minute=30)
    await ingester.start()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Stopping ingester...")