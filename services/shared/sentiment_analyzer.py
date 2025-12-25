"""
Sentiment Analysis Module
Analyzes customer sentiment in real-time and flags negative interactions
"""
from typing import Dict, Optional
import re

class SentimentAnalyzer:
    """
    Simple rule-based sentiment analyzer for customer service.
    In production, use transformers-based models like:
    - cardiffnlp/twitter-roberta-base-sentiment
    - distilbert-base-uncased-finetuned-sst-2-english
    """
    
    def __init__(self):
        # Negative sentiment indicators
        self.negative_keywords = {
            'angry', 'terrible', 'worst', 'horrible', 'awful', 'frustrated',
            'disappointed', 'useless', 'pathetic', 'disgusted', 'hate',
            'angry', 'furious', 'upset', 'mad', 'annoyed', 'irritated',
            'poor', 'bad', 'never', 'waste', 'scam', 'fraud', 'lie',
            'cancel', 'refund', 'complaint', 'unacceptable', 'ridiculous'
        }
        
        # Positive sentiment indicators
        self.positive_keywords = {
            'great', 'excellent', 'amazing', 'wonderful', 'fantastic',
            'perfect', 'love', 'awesome', 'brilliant', 'helpful',
            'appreciate', 'thank', 'thanks', 'impressed', 'satisfied',
            'happy', 'pleased', 'good', 'best', 'nice'
        }
        
        # Escalation triggers
        self.escalation_keywords = {
            'lawyer', 'legal', 'sue', 'court', 'attorney', 'lawsuit',
            'manager', 'supervisor', 'complaint', 'report', 'bbb',
            'scam', 'fraud', 'stolen', 'police'
        }
        
        # Urgency indicators
        self.urgency_keywords = {
            'urgent', 'asap', 'immediately', 'emergency', 'now',
            'critical', 'important', 'deadline', 'today'
        }
    
    def analyze(self, text: str) -> Dict:
        """
        Analyze sentiment of customer message
        
        Returns:
            {
                'sentiment': 'positive' | 'negative' | 'neutral',
                'score': float (-1.0 to 1.0),
                'confidence': float (0.0 to 1.0),
                'needs_escalation': bool,
                'is_urgent': bool,
                'flags': List[str]
            }
        """
        text_lower = text.lower()
        words = re.findall(r'\b\w+\b', text_lower)
        
        # Count sentiment indicators
        negative_count = sum(1 for word in words if word in self.negative_keywords)
        positive_count = sum(1 for word in words if word in self.positive_keywords)
        
        # Check escalation and urgency
        needs_escalation = any(word in text_lower for word in self.escalation_keywords)
        is_urgent = any(word in text_lower for word in self.urgency_keywords)
        
        # Detect excessive capitalization (shouting)
        caps_ratio = sum(1 for c in text if c.isupper()) / max(len(text), 1)
        is_shouting = caps_ratio > 0.5 and len(text) > 10
        
        # Detect multiple exclamation/question marks
        excessive_punctuation = '!!!' in text or '???' in text
        
        # Calculate sentiment
        total_sentiment_words = negative_count + positive_count
        
        if total_sentiment_words == 0:
            sentiment = 'neutral'
            score = 0.0
            confidence = 0.3
        else:
            score = (positive_count - negative_count) / total_sentiment_words
            
            if score > 0.3:
                sentiment = 'positive'
                confidence = min(0.8, 0.5 + (score * 0.3))
            elif score < -0.3:
                sentiment = 'negative'
                confidence = min(0.8, 0.5 + (abs(score) * 0.3))
            else:
                sentiment = 'neutral'
                confidence = 0.5
        
        # Collect flags
        flags = []
        if is_shouting:
            flags.append('shouting')
            sentiment = 'negative'  # Override to negative
            score = min(score, -0.5)
        
        if excessive_punctuation:
            flags.append('excessive_punctuation')
        
        if needs_escalation:
            flags.append('escalation_keywords')
        
        if is_urgent:
            flags.append('urgent')
        
        if negative_count >= 3:
            flags.append('high_negative_sentiment')
        
        return {
            'sentiment': sentiment,
            'score': score,
            'confidence': confidence,
            'needs_escalation': needs_escalation or len(flags) >= 2,
            'is_urgent': is_urgent,
            'flags': flags,
            'metrics': {
                'positive_words': positive_count,
                'negative_words': negative_count,
                'caps_ratio': round(caps_ratio, 2)
            }
        }
    
    def get_response_tone(self, sentiment_result: Dict) -> str:
        """Get recommended tone for response based on sentiment"""
        if sentiment_result['needs_escalation']:
            return 'apologetic_professional'
        elif sentiment_result['sentiment'] == 'negative':
            return 'empathetic_supportive'
        elif sentiment_result['is_urgent']:
            return 'prompt_helpful'
        else:
            return 'friendly_helpful'


# Advanced sentiment analyzer using transformers (optional)
class TransformerSentimentAnalyzer:
    """
    Advanced sentiment analysis using pre-trained transformers.
    Requires: pip install transformers torch
    """
    
    def __init__(self, model_name: str = "distilbert-base-uncased-finetuned-sst-2-english"):
        try:
            from transformers import pipeline
            self.classifier = pipeline(
                "sentiment-analysis",
                model=model_name,
                device=-1  # CPU, use 0 for GPU
            )
            self.available = True
        except ImportError:
            print("⚠️  Transformers not available. Using rule-based sentiment analysis.")
            self.available = False
            self.fallback = SentimentAnalyzer()
    
    def analyze(self, text: str) -> Dict:
        """Analyze sentiment using transformer model"""
        if not self.available:
            return self.fallback.analyze(text)
        
        try:
            result = self.classifier(text[:512])[0]  # Limit to 512 chars
            
            # Convert to our format
            label = result['label'].lower()
            score = result['score']
            
            # Map labels
            if label == 'positive':
                sentiment = 'positive'
                sentiment_score = score
            elif label == 'negative':
                sentiment = 'negative'
                sentiment_score = -score
            else:
                sentiment = 'neutral'
                sentiment_score = 0.0
            
            # Still check for escalation keywords
            fallback_check = self.fallback.analyze(text)
            
            return {
                'sentiment': sentiment,
                'score': sentiment_score,
                'confidence': score,
                'needs_escalation': fallback_check['needs_escalation'],
                'is_urgent': fallback_check['is_urgent'],
                'flags': fallback_check['flags'],
                'model': 'transformer'
            }
        
        except Exception as e:
            print(f"Transformer analysis failed: {e}")
            return self.fallback.analyze(text)


# Factory function
def get_sentiment_analyzer(use_transformer: bool = False) -> SentimentAnalyzer:
    """Get appropriate sentiment analyzer"""
    if use_transformer:
        return TransformerSentimentAnalyzer()
    return SentimentAnalyzer()
