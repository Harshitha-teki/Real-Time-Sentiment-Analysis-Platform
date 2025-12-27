import redis
import json
import time

# Connect to your local Redis
r = redis.Redis(host='localhost', port=6379, decode_responses=True)

print("Injecting 6 negative posts to trigger an alert...")

for i in range(6):
    mock_post = {
        "text": f"This is a test negative message #{i}",
        "sentiment": "negative",
        "confidence": 0.99
    }
    # We publish to the same channel the worker uses
    r.publish('sentiment_updates', json.dumps(mock_post))
    print(f"Sent post {i+1}/6")
    time.sleep(0.5)

print("\nDone! Wait up to 60 seconds for the 'alert_monitor' task in the backend to detect these in the database and send the Red Alert to your dashboard.")