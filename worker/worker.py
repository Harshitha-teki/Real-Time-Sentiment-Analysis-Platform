import os
import time
import json
import redis
from processor import SentimentProcessor # We will create this next

class SentimentWorker:
    def __init__(self):
        self.redis_client = redis.Redis(
            host=os.getenv('REDIS_HOST', 'redis'),
            port=6379,
            decode_responses=True
        )
        self.stream = os.getenv('REDIS_STREAM_NAME', 'social_posts_stream')
        self.group = os.getenv('REDIS_CONSUMER_GROUP', 'sentiment_workers')
        self.worker_name = f"worker_{os.uname().nodename}"
        self.processor = SentimentProcessor()
        
        # Ensure Consumer Group exists
        try:
            self.redis_client.xgroup_create(self.stream, self.group, id='0', mkstream=True)
        except redis.exceptions.ResponseError:
            pass # Group already exists

    def run(self):
        print(f"Worker {self.worker_name} started...")
        while True:
            try:
                # Mandatory: XREADGROUP
                messages = self.redis_client.xreadgroup(
                    self.group, self.worker_name, {self.stream: '>'}, count=1, block=5000
                )

                for stream, msg_list in messages:
                    for msg_id, data in msg_list:
                        print(f"Processing post: {data['post_id']}")
                        
                        # Run AI Analysis
                        self.processor.process(data)
                        
                        # Mandatory: XACK (Acknowledge)
                        self.redis_client.xack(self.stream, self.group, msg_id)
            except Exception as e:
                print(f"Worker Error: {e}")
                time.sleep(2)

if __name__ == "__main__":
    worker = SentimentWorker()
    worker.run()