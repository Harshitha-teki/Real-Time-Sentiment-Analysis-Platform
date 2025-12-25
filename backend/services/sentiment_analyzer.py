from transformers import pipeline
import torch

class SentimentAnalyzer:
    def __init__(self, model_type: str = 'local'):
        self.model_type = model_type
        if model_type == 'local':
            # Use GPU if available (Requirement 3.2)
            device = 0 if torch.cuda.is_available() else -1
            
            # Load the specific models mentioned in requirements
            self.sentiment_pipe = pipeline(
                "text-classification", 
                model="distilbert-base-uncased-finetuned-sst-2-english",
                device=device
            )
            self.emotion_pipe = pipeline(
                "text-classification", 
                model="j-hartmann/emotion-english-distilroberta-base",
                device=device
            )

    async def analyze_sentiment(self, text: str) -> dict:
        if not text:
            return {"sentiment_label": "neutral", "confidence_score": 0.0, "model_name": "none"}
            
        # Local model inference
        result = self.sentiment_pipe(text[:512])[0] # Limit to 512 tokens
        
        # Mapping model labels to standard labels (Requirement 3.2)
        label_map = {"POSITIVE": "positive", "NEGATIVE": "negative"}
        
        return {
            "sentiment_label": label_map.get(result['label'], "neutral"),
            "confidence_score": round(result['score'], 4),
            "model_name": "distilbert-sst2"
        }

    async def analyze_emotion(self, text: str) -> dict:
        if len(text) < 10:
            return {"emotion": "neutral", "confidence_score": 1.0, "model_name": "threshold"}
            
        result = self.emotion_pipe(text[:512])[0]
        return {
            "emotion": result['label'].lower(),
            "confidence_score": round(result['score'], 4),
            "model_name": "distilroberta-emotion"
        }