import os
from transformers import pipeline
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
# Import your models (we'll ensure these are shared or accessible)
# from models import SocialMediaPost, SentimentAnalysis 

class SentimentProcessor:
    def __init__(self):
        # Load local Hugging Face models
        print("Loading AI models... this may take a minute...")
        self.sentiment_pipe = pipeline("sentiment-analysis", model=os.getenv('HUGGINGFACE_MODEL'))
        self.emotion_pipe = pipeline("text-classification", model=os.getenv('EMOTION_MODEL'))
        
        # Database Setup
        engine = create_engine(os.getenv('DATABASE_URL'))
        self.Session = sessionmaker(bind=engine)

    def process(self, data):
        content = data['content']
        
        # 1. Local Sentiment Analysis
        sentiment_result = self.sentiment_pipe(content)[0]
        
        # 2. Local Emotion Detection
        emotion_result = self.emotion_pipe(content)[0]
        
        print(f"Result: {sentiment_result['label']} | Emotion: {emotion_result['label']}")
        
        # 3. TODO: Save to Database (We'll add the DB save logic next)