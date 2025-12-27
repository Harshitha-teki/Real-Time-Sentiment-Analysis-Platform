import torch
from transformers import pipeline
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SentimentAnalyzer:
    def __init__(self, model_type='local'):
        logger.info("⏳ Loading AI models... (this may take a minute)")
        
        # Determine device (CPU for this setup)
        device = -1 # -1 means CPU
        logger.info(f"Device set to use CPU")

        try:
            # 1. Sentiment Pipeline (Positive/Negative)
            # Using safetensors=True to bypass the 2025 security vulnerability check
            self.sentiment_pipe = pipeline(
                "sentiment-analysis",
                model="distilbert-base-uncased-finetuned-sst-2-english",
                device=device,
            )

            # 2. Emotion Pipeline (Joy, Anger, Fear, etc.)
            self.emotion_pipe = pipeline(
                "text-classification",
                model="j-hartmann/emotion-english-distilroberta-base",
                device=device,
            )
            
            logger.info("✅ AI Models Loaded Successfully.")
        
        except Exception as e:
            logger.error(f"❌ Failed to load AI models: {e}")
            raise

    def analyze(self, text):
        """
        Analyzes text for both sentiment and emotion.
        """
        try:
            # Get Sentiment
            sentiment_result = self.sentiment_pipe(text)[0]
            
            # Get Emotion
            emotion_result = self.emotion_pipe(text)[0]
            
            return {
                "sentiment_label": sentiment_result['label'].lower(),
                "sentiment_score": float(sentiment_result['score']),
                "emotion": emotion_result['label'].lower(),
                "emotion_score": float(emotion_result['score'])
            }
        except Exception as e:
            logger.error(f"Error during analysis: {e}")
            return {
                "sentiment_label": "unknown",
                "sentiment_score": 0.0,
                "emotion": "neutral",
                "emotion_score": 0.0
            }