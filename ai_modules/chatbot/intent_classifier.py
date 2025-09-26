"""
Intent Classification System for EstateCore Tenant Chatbot

Classifies tenant messages into specific intents using machine learning
and rule-based approaches for property management scenarios.
"""

import json
import logging
import numpy as np
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.svm import SVC
from sklearn.pipeline import Pipeline
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score
from sentence_transformers import SentenceTransformer
import pickle
import os
import re

@dataclass
class IntentPrediction:
    """Container for intent prediction results"""
    intent: str
    confidence: float
    alternative_intents: List[Tuple[str, float]]
    entities: Dict[str, any]

class IntentClassifier:
    """
    Advanced intent classification system for tenant chatbot queries
    """
    
    # Predefined intents for property management
    INTENTS = {
        'rent_payment': {
            'description': 'Questions about rent payments, due dates, payment methods',
            'examples': [
                'when is my rent due',
                'how do i pay rent',
                'what payment methods do you accept',
                'i want to pay my rent online',
                'my rent payment failed'
            ]
        },
        'maintenance_request': {
            'description': 'Requests for maintenance or repair services',
            'examples': [
                'my air conditioning is broken',
                'there is a leak in my bathroom',
                'the elevator is not working',
                'i need maintenance in my unit',
                'can someone fix my dishwasher'
            ]
        },
        'lease_inquiry': {
            'description': 'Questions about lease terms, renewal, documents',
            'examples': [
                'when does my lease expire',
                'can i renew my lease',
                'where is my lease document',
                'what are the lease terms',
                'i want to break my lease'
            ]
        },
        'amenities_info': {
            'description': 'Questions about building amenities and facilities',
            'examples': [
                'what amenities are available',
                'when is the pool open',
                'how do i access the gym',
                'where is the laundry room',
                'what are the parking rules'
            ]
        },
        'contact_info': {
            'description': 'Requests for contact information or office hours',
            'examples': [
                'what are your office hours',
                'how do i contact the office',
                'who is my property manager',
                'what is the emergency number',
                'where is the leasing office'
            ]
        },
        'account_balance': {
            'description': 'Questions about account balance, charges, fees',
            'examples': [
                'what is my account balance',
                'what charges do i have',
                'why was i charged a fee',
                'show me my payment history',
                'what do i owe'
            ]
        },
        'move_in_out': {
            'description': 'Questions about move-in/move-out procedures',
            'examples': [
                'what do i need for move in',
                'when can i get my keys',
                'what is the move out process',
                'how do i schedule move out',
                'what about my security deposit'
            ]
        },
        'policies_rules': {
            'description': 'Questions about building policies and rules',
            'examples': [
                'what are the guest policies',
                'can i have pets',
                'what are the noise policies',
                'when is quiet hours',
                'what are the parking rules'
            ]
        },
        'emergency': {
            'description': 'Emergency situations requiring immediate attention',
            'examples': [
                'this is an emergency',
                'water is flooding my unit',
                'there is a fire',
                'gas leak in my apartment',
                'someone is locked out'
            ]
        },
        'complaint': {
            'description': 'Complaints about service, neighbors, or facilities',
            'examples': [
                'i want to file a complaint',
                'my neighbors are too loud',
                'the service is poor',
                'i am not satisfied',
                'this is unacceptable'
            ]
        },
        'general_inquiry': {
            'description': 'General questions or greetings',
            'examples': [
                'hello',
                'can you help me',
                'i have a question',
                'good morning',
                'thank you'
            ]
        }
    }
    
    def __init__(self, model_path: Optional[str] = None):
        """
        Initialize Intent Classifier
        
        Args:
            model_path: Path to saved model file
        """
        self.logger = logging.getLogger(__name__)
        self.model_path = model_path or 'ai_models/intent_classifier.pkl'
        self.sentence_model = None
        
        # Initialize components
        self.vectorizer = TfidfVectorizer(
            max_features=5000,
            ngram_range=(1, 3),
            stop_words='english',
            lowercase=True
        )
        
        self.classifier = SVC(
            kernel='rbf',
            probability=True,
            random_state=42
        )
        
        self.pipeline = Pipeline([
            ('vectorizer', self.vectorizer),
            ('classifier', self.classifier)
        ])
        
        self.is_trained = False
        self.intent_keywords = self._build_intent_keywords()
        
        # Load pre-trained model if available
        if os.path.exists(self.model_path):
            self.load_model()
        
        self.logger.info("Intent Classifier initialized")
    
    def _build_intent_keywords(self) -> Dict[str, List[str]]:
        """Build keyword mappings for rule-based classification"""
        keywords = {}
        
        for intent, data in self.INTENTS.items():
            keywords[intent] = []
            
            # Extract keywords from examples and descriptions
            text = ' '.join(data['examples']) + ' ' + data['description']
            words = re.findall(r'\w+', text.lower())
            
            # Filter relevant keywords (remove common words)
            common_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 
                          'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were'}
            
            keywords[intent] = [word for word in set(words) 
                              if len(word) > 2 and word not in common_words]
        
        return keywords
    
    def _rule_based_classify(self, text: str) -> Dict[str, float]:
        """
        Rule-based classification using keyword matching
        
        Args:
            text: Input text to classify
            
        Returns:
            Dictionary of intent scores
        """
        text_lower = text.lower()
        scores = {}
        
        for intent, keywords in self.intent_keywords.items():
            score = 0
            for keyword in keywords:
                if keyword in text_lower:
                    # Weight keywords differently based on importance
                    if keyword in ['emergency', 'urgent', 'fire', 'flood', 'leak']:
                        score += 5
                    elif keyword in ['rent', 'payment', 'maintenance', 'repair']:
                        score += 3
                    else:
                        score += 1
            
            # Normalize by number of keywords
            scores[intent] = score / max(len(keywords), 1)
        
        return scores
    
    def _prepare_training_data(self) -> Tuple[List[str], List[str]]:
        """
        Prepare training data from predefined intents
        
        Returns:
            Tuple of (texts, labels)
        """
        texts = []
        labels = []
        
        for intent, data in self.INTENTS.items():
            for example in data['examples']:
                texts.append(example)
                labels.append(intent)
        
        return texts, labels
    
    def train(self, additional_data: Optional[List[Tuple[str, str]]] = None) -> Dict[str, float]:
        """
        Train the intent classifier
        
        Args:
            additional_data: Optional additional training data as (text, intent) pairs
            
        Returns:
            Training metrics
        """
        self.logger.info("Training intent classifier...")
        
        # Prepare base training data
        texts, labels = self._prepare_training_data()
        
        # Add additional data if provided
        if additional_data:
            for text, intent in additional_data:
                texts.append(text)
                labels.append(intent)
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            texts, labels, test_size=0.2, random_state=42, stratify=labels
        )
        
        # Train pipeline
        self.pipeline.fit(X_train, y_train)
        
        # Evaluate
        y_pred = self.pipeline.predict(X_test)
        accuracy = accuracy_score(y_test, y_pred)
        
        self.is_trained = True
        self.logger.info(f"Intent classifier trained with accuracy: {accuracy:.3f}")
        
        # Save model
        self.save_model()
        
        return {
            'accuracy': accuracy,
            'classification_report': classification_report(y_test, y_pred, output_dict=True)
        }
    
    def predict(self, text: str, use_ensemble: bool = True) -> IntentPrediction:
        """
        Predict intent for given text
        
        Args:
            text: Input text to classify
            use_ensemble: Whether to use ensemble of ML and rule-based methods
            
        Returns:
            IntentPrediction object
        """
        if not text or not text.strip():
            return IntentPrediction('general_inquiry', 0.5, [], {})
        
        predictions = {}
        
        # Rule-based prediction (always available)
        rule_scores = self._rule_based_classify(text)
        
        # ML-based prediction (if model is trained)
        if self.is_trained:
            try:
                probabilities = self.pipeline.predict_proba([text])[0]
                classes = self.pipeline.classes_
                ml_scores = dict(zip(classes, probabilities))
            except Exception as e:
                self.logger.error(f"ML prediction failed: {e}")
                ml_scores = {}
        else:
            ml_scores = {}
        
        # Ensemble prediction
        if use_ensemble and ml_scores:
            # Weighted average (ML gets higher weight)
            for intent in self.INTENTS.keys():
                ml_score = ml_scores.get(intent, 0)
                rule_score = rule_scores.get(intent, 0)
                
                # Weighted combination (70% ML, 30% rules)
                predictions[intent] = 0.7 * ml_score + 0.3 * rule_score
        else:
            # Use rule-based only
            predictions = rule_scores
        
        # Handle empty predictions
        if not predictions:
            predictions = {'general_inquiry': 0.5}
        
        # Sort predictions by confidence
        sorted_predictions = sorted(predictions.items(), key=lambda x: x[1], reverse=True)
        
        # Get top prediction
        top_intent, top_confidence = sorted_predictions[0]
        
        # Get alternatives (top 3 excluding the main prediction)
        alternatives = sorted_predictions[1:4]
        
        # Extract entities based on intent
        entities = self._extract_intent_entities(text, top_intent)
        
        return IntentPrediction(
            intent=top_intent,
            confidence=float(top_confidence),
            alternative_intents=alternatives,
            entities=entities
        )
    
    def _extract_intent_entities(self, text: str, intent: str) -> Dict[str, any]:
        """
        Extract entities relevant to the predicted intent
        
        Args:
            text: Input text
            intent: Predicted intent
            
        Returns:
            Dictionary of extracted entities
        """
        entities = {}
        text_lower = text.lower()
        
        if intent == 'rent_payment':
            # Extract payment-related entities
            if 'online' in text_lower:
                entities['payment_method'] = 'online'
            if 'cash' in text_lower:
                entities['payment_method'] = 'cash'
            if 'check' in text_lower:
                entities['payment_method'] = 'check'
        
        elif intent == 'maintenance_request':
            # Extract maintenance categories
            if any(word in text_lower for word in ['ac', 'air conditioning', 'cooling']):
                entities['maintenance_type'] = 'hvac'
            elif any(word in text_lower for word in ['leak', 'water', 'plumbing']):
                entities['maintenance_type'] = 'plumbing'
            elif any(word in text_lower for word in ['electrical', 'outlet', 'light']):
                entities['maintenance_type'] = 'electrical'
            elif any(word in text_lower for word in ['appliance', 'dishwasher', 'refrigerator']):
                entities['maintenance_type'] = 'appliance'
        
        elif intent == 'emergency':
            # Extract emergency type
            if any(word in text_lower for word in ['fire', 'smoke']):
                entities['emergency_type'] = 'fire'
            elif any(word in text_lower for word in ['flood', 'water', 'leak']):
                entities['emergency_type'] = 'water'
            elif 'gas' in text_lower:
                entities['emergency_type'] = 'gas'
        
        return entities
    
    def add_training_example(self, text: str, intent: str) -> None:
        """
        Add a new training example (for continuous learning)
        
        Args:
            text: Example text
            intent: Intent label
        """
        if intent not in self.INTENTS:
            self.logger.warning(f"Unknown intent: {intent}")
            return
        
        # For now, just log the example
        # In a production system, you'd store this for retraining
        self.logger.info(f"Added training example: '{text}' -> {intent}")
    
    def get_intent_info(self, intent: str) -> Dict[str, any]:
        """
        Get information about a specific intent
        
        Args:
            intent: Intent name
            
        Returns:
            Intent information dictionary
        """
        return self.INTENTS.get(intent, {})
    
    def list_intents(self) -> List[str]:
        """
        Get list of all available intents
        
        Returns:
            List of intent names
        """
        return list(self.INTENTS.keys())
    
    def save_model(self) -> None:
        """Save the trained model to disk"""
        try:
            os.makedirs(os.path.dirname(self.model_path), exist_ok=True)
            
            model_data = {
                'pipeline': self.pipeline,
                'is_trained': self.is_trained,
                'intent_keywords': self.intent_keywords
            }
            
            with open(self.model_path, 'wb') as f:
                pickle.dump(model_data, f)
            
            self.logger.info(f"Model saved to {self.model_path}")
        except Exception as e:
            self.logger.error(f"Failed to save model: {e}")
    
    def load_model(self) -> None:
        """Load a trained model from disk"""
        try:
            with open(self.model_path, 'rb') as f:
                model_data = pickle.load(f)
            
            self.pipeline = model_data['pipeline']
            self.is_trained = model_data.get('is_trained', False)
            self.intent_keywords = model_data.get('intent_keywords', self.intent_keywords)
            
            self.logger.info(f"Model loaded from {self.model_path}")
        except Exception as e:
            self.logger.error(f"Failed to load model: {e}")
    
    def confidence_threshold_filter(self, prediction: IntentPrediction, 
                                  threshold: float = 0.6) -> IntentPrediction:
        """
        Apply confidence threshold filtering
        
        Args:
            prediction: Original prediction
            threshold: Confidence threshold
            
        Returns:
            Filtered prediction (may default to general_inquiry)
        """
        if prediction.confidence < threshold:
            return IntentPrediction(
                intent='general_inquiry',
                confidence=0.5,
                alternative_intents=[(prediction.intent, prediction.confidence)],
                entities={}
            )
        
        return prediction