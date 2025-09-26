"""
Sentiment Analysis System for EstateCore Tenant Chatbot

Analyzes emotional tone and sentiment in tenant messages to improve
response quality and identify escalation triggers.
"""

import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from textblob import TextBlob
import re
from datetime import datetime

@dataclass
class SentimentResult:
    """Container for sentiment analysis results"""
    polarity: float  # -1 (negative) to 1 (positive)
    subjectivity: float  # 0 (objective) to 1 (subjective)
    label: str  # 'positive', 'negative', 'neutral'
    confidence: float
    emotions: Dict[str, float]
    urgency_indicators: List[str]

class SentimentAnalyzer:
    """
    Advanced sentiment analysis for tenant chatbot messages
    """
    
    def __init__(self):
        """Initialize Sentiment Analyzer"""
        self.logger = logging.getLogger(__name__)
        
        # Emotion keywords and weights
        self.emotion_patterns = {
            'anger': {
                'keywords': ['angry', 'mad', 'furious', 'annoyed', 'frustrated', 'outraged', 
                           'livid', 'irritated', 'upset', 'hate', 'terrible', 'awful'],
                'weight': 1.5
            },
            'fear': {
                'keywords': ['scared', 'afraid', 'worried', 'anxious', 'nervous', 'panic',
                           'frightened', 'terrified', 'concerned', 'stress'],
                'weight': 1.3
            },
            'sadness': {
                'keywords': ['sad', 'depressed', 'disappointed', 'upset', 'miserable',
                           'unhappy', 'devastated', 'heartbroken', 'down'],
                'weight': 1.2
            },
            'joy': {
                'keywords': ['happy', 'excited', 'great', 'awesome', 'wonderful', 'amazing',
                           'fantastic', 'excellent', 'perfect', 'love', 'pleased'],
                'weight': 1.0
            },
            'surprise': {
                'keywords': ['surprised', 'shocked', 'amazed', 'astonished', 'unexpected'],
                'weight': 1.1
            },
            'disgust': {
                'keywords': ['disgusting', 'gross', 'sick', 'revolting', 'appalling'],
                'weight': 1.4
            }
        }
        
        # Urgency and escalation indicators
        self.urgency_patterns = {
            'emergency': ['emergency', 'urgent', 'immediately', 'right now', 'asap', 'help'],
            'dissatisfaction': ['unacceptable', 'ridiculous', 'pathetic', 'worst', 'horrible'],
            'threat': ['lawyer', 'sue', 'legal action', 'complaint', 'report'],
            'escalation_request': ['manager', 'supervisor', 'human', 'person', 'someone else']
        }
        
        # Property management specific sentiment modifiers
        self.context_modifiers = {
            'maintenance': {
                'positive_boost': ['fixed', 'repaired', 'working', 'resolved'],
                'negative_boost': ['broken', 'leaking', 'not working', 'still broken']
            },
            'payment': {
                'positive_boost': ['paid', 'processed', 'received'],
                'negative_boost': ['overdue', 'late fee', 'penalty', 'declined']
            },
            'service': {
                'positive_boost': ['helpful', 'professional', 'quick', 'efficient'],
                'negative_boost': ['rude', 'unprofessional', 'slow', 'ignored']
            }
        }
        
        self.logger.info("Sentiment Analyzer initialized")
    
    def analyze(self, text: str, context: Optional[str] = None) -> SentimentResult:
        """
        Perform comprehensive sentiment analysis
        
        Args:
            text: Input text to analyze
            context: Optional context (e.g., 'maintenance', 'payment')
            
        Returns:
            SentimentResult object
        """
        if not text or not text.strip():
            return SentimentResult(0.0, 0.0, 'neutral', 0.5, {}, [])
        
        # Basic sentiment analysis using TextBlob
        blob = TextBlob(text)
        polarity = blob.sentiment.polarity
        subjectivity = blob.sentiment.subjectivity
        
        # Apply context-specific modifications
        if context:
            polarity = self._apply_context_modifiers(text, polarity, context)
        
        # Analyze emotions
        emotions = self._analyze_emotions(text)
        
        # Detect urgency indicators
        urgency_indicators = self._detect_urgency(text)
        
        # Calculate confidence based on subjectivity and text length
        confidence = self._calculate_confidence(text, subjectivity)
        
        # Determine sentiment label
        label = self._get_sentiment_label(polarity)
        
        return SentimentResult(
            polarity=polarity,
            subjectivity=subjectivity,
            label=label,
            confidence=confidence,
            emotions=emotions,
            urgency_indicators=urgency_indicators
        )
    
    def _apply_context_modifiers(self, text: str, polarity: float, context: str) -> float:
        """Apply context-specific sentiment modifications"""
        text_lower = text.lower()
        modifier = 0.0
        
        if context in self.context_modifiers:
            modifiers = self.context_modifiers[context]
            
            # Check for positive boost keywords
            for keyword in modifiers.get('positive_boost', []):
                if keyword in text_lower:
                    modifier += 0.2
            
            # Check for negative boost keywords  
            for keyword in modifiers.get('negative_boost', []):
                if keyword in text_lower:
                    modifier -= 0.3
        
        # Apply modifier but keep within bounds
        new_polarity = polarity + modifier
        return max(-1.0, min(1.0, new_polarity))
    
    def _analyze_emotions(self, text: str) -> Dict[str, float]:
        """Analyze emotional content of text"""
        text_lower = text.lower()
        emotions = {}
        
        for emotion, data in self.emotion_patterns.items():
            score = 0.0
            keywords = data['keywords']
            weight = data['weight']
            
            for keyword in keywords:
                if keyword in text_lower:
                    # Count occurrences and apply weight
                    count = text_lower.count(keyword)
                    score += count * weight
            
            # Normalize by text length
            if len(text_lower.split()) > 0:
                score = score / len(text_lower.split())
            
            emotions[emotion] = min(score, 1.0)  # Cap at 1.0
        
        return emotions
    
    def _detect_urgency(self, text: str) -> List[str]:
        """Detect urgency and escalation indicators"""
        text_lower = text.lower()
        indicators = []
        
        for category, keywords in self.urgency_patterns.items():
            for keyword in keywords:
                if keyword in text_lower:
                    indicators.append(f"{category}:{keyword}")
        
        # Check for repeated exclamation marks or capitals
        if '!!!' in text or text.isupper():
            indicators.append('emphasis:formatting')
        
        return indicators
    
    def _calculate_confidence(self, text: str, subjectivity: float) -> float:
        """Calculate confidence score for sentiment analysis"""
        base_confidence = 0.5
        
        # Higher confidence for more subjective text
        subjectivity_boost = subjectivity * 0.3
        
        # Higher confidence for longer text
        length_boost = min(len(text.split()) / 20.0, 0.2)
        
        # Check for clear sentiment indicators
        clear_indicators = 0
        positive_words = ['great', 'excellent', 'amazing', 'perfect', 'love']
        negative_words = ['terrible', 'awful', 'hate', 'worst', 'horrible']
        
        text_lower = text.lower()
        for word in positive_words + negative_words:
            if word in text_lower:
                clear_indicators += 1
        
        indicator_boost = min(clear_indicators * 0.1, 0.2)
        
        confidence = base_confidence + subjectivity_boost + length_boost + indicator_boost
        return min(confidence, 1.0)
    
    def _get_sentiment_label(self, polarity: float) -> str:
        """Convert polarity score to sentiment label"""
        if polarity > 0.1:
            return 'positive'
        elif polarity < -0.1:
            return 'negative'
        else:
            return 'neutral'
    
    def should_escalate_based_on_sentiment(self, sentiment: SentimentResult) -> Tuple[bool, str]:
        """
        Determine if conversation should be escalated based on sentiment
        
        Args:
            sentiment: SentimentResult object
            
        Returns:
            Tuple of (should_escalate, reason)
        """
        # Check for very negative sentiment
        if sentiment.polarity < -0.6 and sentiment.confidence > 0.7:
            return True, "Very negative sentiment detected"
        
        # Check for high anger emotion
        if sentiment.emotions.get('anger', 0) > 0.7:
            return True, "High anger level detected"
        
        # Check for urgency indicators
        urgent_indicators = ['emergency', 'threat', 'escalation_request']
        for indicator in sentiment.urgency_indicators:
            if any(urgent in indicator for urgent in urgent_indicators):
                return True, f"Urgency indicator: {indicator}"
        
        # Check for dissatisfaction patterns
        dissatisfaction_indicators = [ind for ind in sentiment.urgency_indicators 
                                    if 'dissatisfaction' in ind]
        if len(dissatisfaction_indicators) > 1:
            return True, "Multiple dissatisfaction indicators"
        
        return False, ""
    
    def get_response_tone_suggestion(self, sentiment: SentimentResult) -> Dict[str, str]:
        """
        Suggest appropriate response tone based on sentiment analysis
        
        Args:
            sentiment: SentimentResult object
            
        Returns:
            Dictionary with tone suggestions
        """
        suggestions = {}
        
        if sentiment.label == 'negative':
            suggestions['tone'] = 'empathetic'
            suggestions['approach'] = 'apologetic_helpful'
            suggestions['urgency'] = 'high' if sentiment.polarity < -0.5 else 'medium'
        elif sentiment.label == 'positive':
            suggestions['tone'] = 'friendly'
            suggestions['approach'] = 'enthusiastic_helpful'
            suggestions['urgency'] = 'low'
        else:
            suggestions['tone'] = 'professional'
            suggestions['approach'] = 'informative_helpful'
            suggestions['urgency'] = 'medium'
        
        # Adjust based on emotions
        dominant_emotion = max(sentiment.emotions.items(), key=lambda x: x[1])
        if dominant_emotion[1] > 0.5:
            emotion, score = dominant_emotion
            if emotion == 'anger':
                suggestions['tone'] = 'calm_reassuring'
                suggestions['priority'] = 'high'
            elif emotion == 'fear':
                suggestions['tone'] = 'supportive_reassuring'
                suggestions['priority'] = 'medium'
            elif emotion == 'joy':
                suggestions['tone'] = 'enthusiastic'
                suggestions['priority'] = 'low'
        
        return suggestions
    
    def analyze_conversation_sentiment_trend(self, messages: List[str]) -> Dict[str, any]:
        """
        Analyze sentiment trend across multiple messages in a conversation
        
        Args:
            messages: List of message texts
            
        Returns:
            Dictionary with trend analysis
        """
        if not messages:
            return {'trend': 'neutral', 'change': 0, 'recommendation': 'continue'}
        
        sentiments = [self.analyze(msg) for msg in messages]
        polarities = [s.polarity for s in sentiments]
        
        # Calculate trend
        if len(polarities) < 2:
            trend = 'stable'
            change = 0
        else:
            recent_avg = sum(polarities[-3:]) / len(polarities[-3:])
            early_avg = sum(polarities[:3]) / min(len(polarities[:3]), 3)
            change = recent_avg - early_avg
            
            if change > 0.2:
                trend = 'improving'
            elif change < -0.2:
                trend = 'deteriorating'
            else:
                trend = 'stable'
        
        # Recommendation based on trend
        if trend == 'deteriorating':
            recommendation = 'escalate'
        elif trend == 'improving':
            recommendation = 'continue_positive'
        else:
            recommendation = 'maintain'
        
        # Overall conversation sentiment
        overall_polarity = sum(polarities) / len(polarities)
        overall_label = self._get_sentiment_label(overall_polarity)
        
        return {
            'trend': trend,
            'change': change,
            'recommendation': recommendation,
            'overall_sentiment': overall_label,
            'overall_polarity': overall_polarity,
            'message_count': len(messages),
            'sentiment_scores': polarities
        }
    
    def get_sentiment_summary(self, sentiment: SentimentResult) -> str:
        """
        Get a human-readable summary of sentiment analysis
        
        Args:
            sentiment: SentimentResult object
            
        Returns:
            Summary string
        """
        summary_parts = []
        
        # Main sentiment
        summary_parts.append(f"Sentiment: {sentiment.label.title()} (score: {sentiment.polarity:.2f})")
        
        # Dominant emotion
        if sentiment.emotions:
            dominant_emotion = max(sentiment.emotions.items(), key=lambda x: x[1])
            if dominant_emotion[1] > 0.3:
                summary_parts.append(f"Dominant emotion: {dominant_emotion[0]} ({dominant_emotion[1]:.2f})")
        
        # Urgency indicators
        if sentiment.urgency_indicators:
            summary_parts.append(f"Urgency indicators: {len(sentiment.urgency_indicators)}")
        
        # Confidence
        summary_parts.append(f"Confidence: {sentiment.confidence:.2f}")
        
        return " | ".join(summary_parts)