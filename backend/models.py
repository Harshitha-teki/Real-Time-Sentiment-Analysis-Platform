from sqlalchemy import Column, Integer, String, Text, DateTime, Float, ForeignKey
from sqlalchemy.orm import declarative_base, relationship
import datetime

Base = declarative_base()

class Post(Base):
    """
    Main table for storing raw social media posts.
    """
    __tablename__ = "social_media_posts"
    
    id = Column(Integer, primary_key=True)
    post_id = Column(String, unique=True, nullable=False)
    source = Column(String)
    content = Column(Text)
    author = Column(String)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    # Relationship to analysis results
    analysis = relationship("SentimentAnalysis", back_populates="post", uselist=False)

class SentimentAnalysis(Base):
    """
    Table for storing the results of the AI processing.
    """
    __tablename__ = "sentiment_analysis"
    
    id = Column(Integer, primary_key=True)
    post_id = Column(Integer, ForeignKey("social_media_posts.id"))
    sentiment_label = Column(String)  # e.g., 'positive', 'negative'
    confidence_score = Column(Float)
    emotion = Column(String)          # e.g., 'joy', 'anger'
    model_name = Column(String)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    post = relationship("Post", back_populates="analysis")


class SentimentAlert(Base):
    __tablename__ = "sentiment_alerts"
    id = Column(Integer, primary_key=True)
    alert_type = Column(String)
    threshold = Column(Float)
    actual_ratio = Column(Float)
    window_minutes = Column(Integer)
    positive_count = Column(Integer)
    negative_count = Column(Integer)
    neutral_count = Column(Integer)
    total_count = Column(Integer)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)