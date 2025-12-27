import os
import json
import asyncio
import redis.asyncio as redis
from datetime import datetime
from processor import save_post_and_analysis # Your DB function
from backend.services.sentiment_analyzer import SentimentAnalyzer

class SentimentWorker:
    def __init__(self):
        self.redis_url = f"redis://{os.getenv('REDIS_HOST', 'redis')}:6379"
        self.stream = "social_posts_stream"
        self.group = "sentiment_workers"
        self.analyzer = SentimentAnalyzer(model_type='local')

    async def process_message(self, redis_client, msg_id, data):
        try:
            # 1. AI Analysis
            sentiment = await self.analyzer.analyze_sentiment(data['content'])
            emotion = await self.analyzer.analyze_emotion(data['content'])

            # 2. Database Save (Atomic Transaction)
            await save_post_and_analysis(data, sentiment, emotion)

            # 3. Real-Time Broadcast (Requirement 4.2)
            payload = {
                "type": "new_post",
                "data": {
                    "post_id": data['post_id'],
                    "content": data['content'][:100] + "...",
                    "sentiment_label": sentiment['sentiment_label'],
                    "emotion": emotion['emotion'],
                    "timestamp": datetime.utcnow().isoformat()
                }
            }
            await redis_client.publish("sentiment_updates", json.dumps(payload))

            # 4. Acknowledge message only on success
            await redis_client.xack(self.stream, self.group, msg_id)
            return True
        except Exception as e:
            print(f"Error processing {msg_id}: {e}")
            return False

    async def run(self):
        client = redis.from_url(self.redis_url, decode_responses=True)
        try:
            await client.xgroup_create(self.stream, self.group, id='0', mkstream=True)
        except: pass

        while True:
            # Batch processing for throughput (Requirement 3.3)
            messages = await client.xreadgroup(self.group, "worker_1", {self.stream: ">"}, count=10, block=5000)
            if messages:
                tasks = [self.process_message(client, mid, data) for _, msg_list in messages for mid, data in msg_list]
                await asyncio.gather(*tasks)

if __name__ == "__main__":
    asyncio.run(SentimentWorker().run())