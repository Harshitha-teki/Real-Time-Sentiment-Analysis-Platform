from sqlalchemy import Column, Integer, String, Text, DateTime, Float, ForeignKey
from sqlalchemy.orm import declarative_base, relationship
import datetime

Base = declarative_base()

class SocialMediaPost(Base):
    __tablename__ = "social_media_posts"
    id = Column(Integer, primary_key=True)
    post_id = Column(String, unique=True, nullable=False)
    source = Column(String)
    content = Column(Text)
    author = Column(String)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    analysis = relationship("SentimentAnalysis", back_populates="post", uselist=False)

class SentimentAnalysis(Base):
    __tablename__ = "sentiment_analysis"
    id = Column(Integer, primary_key=True)
    post_id = Column(Integer, ForeignKey("social_media_posts.id"))
    sentiment_label = Column(String)  # 'positive', 'negative', 'neutral'
    confidence_score = Column(Float)
    emotion = Column(String)  # 'joy', 'sadness', etc.
    model_name = Column(String)
    
    post = relationship("SocialMediaPost", back_populates="analysis")