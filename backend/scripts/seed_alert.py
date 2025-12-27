#!/usr/bin/env python3
"""Seed the database with negative posts to trigger alert persistence.

Run this inside the backend container:
  docker-compose exec backend python /app/scripts/seed_alert.py
"""
import os
import uuid
import datetime
import psycopg2
from urllib.parse import urlparse

DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://sentiment_user:secure_pass_123@db:5432/sentiment_db')

# psycopg2 needs a DSN without the asyncpg prefix
if DATABASE_URL.startswith('postgresql+asyncpg://'):
    DATABASE_URL = DATABASE_URL.replace('postgresql+asyncpg://', 'postgresql://', 1)

p = urlparse(DATABASE_URL)
conn = psycopg2.connect(dbname=p.path.lstrip('/'), user=p.username, password=p.password, host=p.hostname, port=p.port)
cur = conn.cursor()

now = datetime.datetime.utcnow()

print('Inserting 6 negative posts and analyses...')
for i in range(6):
    post_id = str(uuid.uuid4())
    content = f'Test negative post {i} - trigger alert'
    author = 'seed-script'
    source = 'test'
    created_at = now - datetime.timedelta(seconds=(5 - i))

    cur.execute(
        "INSERT INTO social_media_posts (post_id, source, content, author, created_at) VALUES (%s,%s,%s,%s,%s) RETURNING id",
        (post_id, source, content, author, created_at)
    )
    post_db_id = cur.fetchone()[0]

    # Insert analysis; note: avoid 'created_at' column if not present in DB schema
    cur.execute(
        "INSERT INTO sentiment_analysis (post_id, sentiment_label, confidence_score, emotion, model_name) VALUES (%s,%s,%s,%s,%s)",
        (post_db_id, 'negative', 0.95, 'anger', 'seed-model')
    )
    conn.commit()
    print(f'Inserted post {i+1}/6 (id={post_db_id})')

cur.close()
conn.close()
print('Done. Alert monitor should detect this within its next run (max 60s).')
