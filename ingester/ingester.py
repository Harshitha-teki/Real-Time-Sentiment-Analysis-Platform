import redis
import time
import random
import asyncio
from datetime import datetime

class DataIngester:
    """Publishes simulated social media posts to Redis Stream"""
    
    def __init__(self, redis_client, stream_name: str, posts_per_minute: int = 60):
        self.redis = redis_client
        self.stream_name = stream_name
        self.interval = 60.0 / posts_per_minute

    def generate_post(self) -> dict:
        """Requirement: 40% pos, 30% neu, 30% neg"""
        topics = ["iPhone 16", "Tesla Model 3", "ChatGPT", "Netflix"]
        authors = ["tech_fan", "user123", "critic_mode", "daily_buzz"]
        
        sentiment_roll = random.random()
        topic = random.choice(topics)
        
        if sentiment_roll < 0.40:
            content = f"I love the new {topic}! It's absolutely amazing."
        elif sentiment_roll < 0.70:
            content = f"Just started using {topic} today."
        else:
            content = f"I hate the new {topic} update. Very disappointed."

        return {
            'post_id': f"post_{int(time.time() * 1000)}",
            'source': random.choice(['twitter', 'reddit']),
            'content': content,
            'author': random.choice(authors),
            'created_at': datetime.utcnow().isoformat() + "Z"
        }

    async def publish_post(self, post_data: dict) -> bool:
        """Uses XADD to publish to the stream"""
        try:
            # We use * to let Redis generate the message ID
            self.redis.xadd(self.stream_name, post_data)
            return True
        except Exception as e:
            print(f"❌ Redis Error: {e}")
            return False

    async def start(self):
        print(f"🚀 Ingester active: {60/self.interval} posts/min")
        while True:
            post = self.generate_post()
            if await self.publish_post(post):
                print(f"📤 Sent: {post['post_id']} - {post['content'][:30]}...")
            await asyncio.sleep(self.interval)