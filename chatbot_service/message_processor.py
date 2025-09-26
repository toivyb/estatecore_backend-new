"""
Message Processing System for EstateCore Tenant Chatbot

Processes incoming messages through the AI pipeline including
NLP analysis, intent classification, entity extraction, and response generation.
"""

import logging
import asyncio
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from datetime import datetime

from ai_modules.chatbot import (
    NLPEngine, IntentClassifier, EntityExtractor, 
    ResponseGenerator, SentimentAnalyzer, ContextManager
)
from ai_modules.chatbot.conversation_manager import ConversationManager, EscalationReason
from ai_modules.chatbot.response_generator import ResponseContext, GeneratedResponse

@dataclass
class ProcessingResult:
    """Result of message processing"""
    intent: str
    confidence: float
    entities: Dict[str, Any]
    sentiment: Dict[str, Any]
    response: Dict[str, Any]
    escalated: bool = False
    requires_action: bool = False
    processing_time_ms: float = 0.0

class MessageProcessor:
    """
    Advanced message processing pipeline for tenant chatbot
    """
    
    def __init__(self, nlp_engine: NLPEngine, intent_classifier: IntentClassifier,
                 entity_extractor: EntityExtractor, sentiment_analyzer: SentimentAnalyzer):
        """
        Initialize Message Processor
        
        Args:
            nlp_engine: NLP processing engine
            intent_classifier: Intent classification system
            entity_extractor: Entity extraction system
            sentiment_analyzer: Sentiment analysis system
        """
        self.logger = logging.getLogger(__name__)
        
        self.nlp_engine = nlp_engine
        self.intent_classifier = intent_classifier
        self.entity_extractor = entity_extractor
        self.sentiment_analyzer = sentiment_analyzer
        
        # Will be injected by the API
        self.response_generator: Optional[ResponseGenerator] = None
        self.conversation_manager: Optional[ConversationManager] = None
        self.context_manager: Optional[ContextManager] = None
        self.data_integration = None
        
        # Processing configuration
        self.max_processing_time = 30.0  # seconds
        self.confidence_threshold = 0.6
        self.enable_async_processing = True
        
        self.logger.info("Message Processor initialized")
    
    def set_dependencies(self, response_generator: ResponseGenerator,
                        conversation_manager: ConversationManager,
                        context_manager: ContextManager,
                        data_integration):
        """Set dependency injection"""
        self.response_generator = response_generator
        self.conversation_manager = conversation_manager
        self.context_manager = context_manager
        self.data_integration = data_integration
    
    def process_message(self, user_id: str, conversation_id: str, 
                       message: str) -> ProcessingResult:
        """
        Process a user message through the complete AI pipeline
        
        Args:
            user_id: User identifier
            conversation_id: Conversation identifier
            message: User message text
            
        Returns:
            ProcessingResult with response and metadata
        """
        start_time = datetime.now()
        
        try:
            # Step 1: NLP Processing
            processed_text = self.nlp_engine.process_message(message)
            self.logger.debug(f"NLP processing completed for user {user_id}")
            
            # Step 2: Intent Classification
            intent_prediction = self.intent_classifier.predict(message, use_ensemble=True)
            self.logger.debug(f"Intent classified: {intent_prediction.intent} (confidence: {intent_prediction.confidence:.3f})")
            
            # Step 3: Entity Extraction
            extracted_entities = self.entity_extractor.extract_all(message)
            self.logger.debug(f"Entities extracted: {len(extracted_entities.entities)} entities")
            
            # Step 4: Sentiment Analysis
            sentiment_result = self.sentiment_analyzer.analyze(
                message, context=intent_prediction.intent
            )
            self.logger.debug(f"Sentiment analyzed: {sentiment_result.label} (polarity: {sentiment_result.polarity:.3f})")
            
            # Step 5: Context Management
            if self.context_manager:
                # Extract and update context from message
                context_items = self.context_manager.extract_context_from_message(
                    user_id, message, self._entities_to_dict(extracted_entities)
                )
                
                # Get relevant context for response
                relevant_context = self.context_manager.get_relevant_context(
                    user_id, intent_prediction.intent
                )
            else:
                relevant_context = {}
            
            # Step 6: Check for escalation
            should_escalate, escalation_reason = self._should_escalate(
                conversation_id, intent_prediction, sentiment_result, relevant_context
            )
            
            # Step 7: Generate Response
            response = self._generate_response(
                user_id, conversation_id, intent_prediction, 
                extracted_entities, sentiment_result, relevant_context
            )
            
            # Step 8: Handle escalation if needed
            if should_escalate:
                response = self._handle_escalation(
                    conversation_id, escalation_reason, response
                )
            
            # Step 9: Update interaction history
            if self.context_manager:
                self.context_manager.add_interaction_history(user_id, {
                    'message': message,
                    'intent': intent_prediction.intent,
                    'confidence': intent_prediction.confidence,
                    'sentiment': sentiment_result.label,
                    'response_type': response.response_type,
                    'escalated': should_escalate
                })
            
            # Calculate processing time
            processing_time = (datetime.now() - start_time).total_seconds() * 1000
            
            return ProcessingResult(
                intent=intent_prediction.intent,
                confidence=intent_prediction.confidence,
                entities=self._entities_to_dict(extracted_entities),
                sentiment={
                    'label': sentiment_result.label,
                    'polarity': sentiment_result.polarity,
                    'subjectivity': sentiment_result.subjectivity,
                    'emotions': sentiment_result.emotions,
                    'urgency_indicators': sentiment_result.urgency_indicators
                },
                response={
                    'text': response.text,
                    'type': response.response_type,
                    'quick_replies': response.quick_replies,
                    'data': response.data,
                    'requires_action': response.requires_action
                },
                escalated=should_escalate,
                requires_action=response.requires_action,
                processing_time_ms=processing_time
            )
            
        except Exception as e:
            self.logger.error(f"Error processing message: {e}")
            processing_time = (datetime.now() - start_time).total_seconds() * 1000
            
            # Return error response
            return ProcessingResult(
                intent='general_inquiry',
                confidence=0.0,
                entities={},
                sentiment={'label': 'neutral', 'polarity': 0.0, 'subjectivity': 0.0, 'emotions': {}, 'urgency_indicators': []},
                response={
                    'text': "I apologize, but I'm having trouble processing your request. Could you please try again or contact our office for assistance?",
                    'type': 'text',
                    'quick_replies': ['Contact office', 'Try again'],
                    'data': None,
                    'requires_action': False
                },
                escalated=True,
                requires_action=False,
                processing_time_ms=processing_time
            )
    
    def _should_escalate(self, conversation_id: str, intent_prediction,
                        sentiment_result, context: Dict) -> Tuple[bool, Optional[EscalationReason]]:
        """Determine if conversation should be escalated"""
        
        # Check sentiment-based escalation
        should_escalate_sentiment, reason = self.sentiment_analyzer.should_escalate_based_on_sentiment(
            sentiment_result
        )
        if should_escalate_sentiment:
            return True, EscalationReason.NEGATIVE_SENTIMENT
        
        # Check intent-based escalation
        if intent_prediction.intent == 'emergency':
            return True, EscalationReason.EMERGENCY
        
        if intent_prediction.intent == 'complaint':
            return True, EscalationReason.COMPLEX_QUERY
        
        # Check confidence threshold
        if intent_prediction.confidence < self.confidence_threshold:
            return True, EscalationReason.LOW_CONFIDENCE
        
        # Check conversation manager escalation logic
        if self.conversation_manager:
            should_escalate, escalation_reason = self.conversation_manager.should_escalate(
                conversation_id, intent_prediction, sentiment_result.__dict__
            )
            if should_escalate:
                return True, escalation_reason
        
        return False, None
    
    def _generate_response(self, user_id: str, conversation_id: str,
                          intent_prediction, extracted_entities, sentiment_result,
                          context: Dict) -> GeneratedResponse:
        """Generate response using response generator"""
        
        if not self.response_generator:
            return GeneratedResponse(
                text="I'm sorry, I'm not able to process your request right now. Please try again later.",
                response_type='text',
                escalate=True
            )
        
        # Get property and tenant data
        property_data = None
        tenant_data = None
        
        if self.data_integration:
            try:
                user_context = self.data_integration.get_user_context(user_id)
                property_data = self.data_integration.get_property_context(
                    user_context.get('property_id')
                ) if user_context.get('property_id') else None
                tenant_data = self.data_integration.get_tenant_context(user_id)
            except Exception as e:
                self.logger.error(f"Error getting integration data: {e}")
        
        # Create response context
        response_context = ResponseContext(
            intent=intent_prediction.intent,
            entities=intent_prediction.entities,
            user_context={
                'user_id': user_id,
                'conversation_id': conversation_id,
                'user_name': context.get('user_profile', {}).get('user_name'),
                'unit_number': context.get('tenant', {}).get('unit_number'),
                'original_text': context.get('conversation', {}).get('last_message', ''),
                **context
            },
            conversation_history=context.get('recent_interactions', []),
            property_data=property_data,
            tenant_data=tenant_data,
            confidence=intent_prediction.confidence
        )
        
        # Generate response
        response = self.response_generator.generate_response(response_context)
        
        # Add personality based on sentiment
        if sentiment_result:
            response.text = self.response_generator.add_personality(
                response.text, sentiment_result.label
            )
        
        return response
    
    def _handle_escalation(self, conversation_id: str, reason: EscalationReason,
                          response: GeneratedResponse) -> GeneratedResponse:
        """Handle conversation escalation"""
        
        escalation_messages = {
            EscalationReason.EMERGENCY: "I understand this is an emergency. I'm immediately connecting you with our emergency response team.",
            EscalationReason.NEGATIVE_SENTIMENT: "I can see you're frustrated, and I want to make sure you get the best help possible. Let me connect you with a team member who can assist you directly.",
            EscalationReason.COMPLEX_QUERY: "This seems like a complex situation that would benefit from personal attention. I'm connecting you with one of our specialists.",
            EscalationReason.LOW_CONFIDENCE: "I want to make sure you get accurate information. Let me connect you with a team member who can help you directly.",
            EscalationReason.USER_REQUEST: "Of course! I'm connecting you with a human agent right now.",
            EscalationReason.MULTIPLE_FAILURES: "I apologize that I haven't been able to help you effectively. Let me get you connected with someone who can assist you better."
        }
        
        escalation_text = escalation_messages.get(
            reason, 
            "I'm connecting you with a human agent for personalized assistance."
        )
        
        # Escalate through conversation manager
        if self.conversation_manager:
            self.conversation_manager.escalate_conversation(conversation_id, reason)
        
        # Modify response for escalation
        response.text = f"{escalation_text}\n\n{response.text}"
        response.escalate = True
        response.quick_replies = ['Wait for agent', 'Leave message', 'Call office']
        
        return response
    
    def _entities_to_dict(self, extracted_entities) -> Dict[str, Any]:
        """Convert extracted entities to dictionary format"""
        return {
            'spacy_entities': [
                {
                    'text': ent.text,
                    'label': ent.label,
                    'value': ent.value,
                    'confidence': ent.confidence
                } for ent in extracted_entities.entities
            ],
            'amounts': extracted_entities.amounts,
            'dates': extracted_entities.dates,
            'unit_numbers': extracted_entities.unit_numbers,
            'property_features': extracted_entities.property_features,
            'contact_info': extracted_entities.contact_info
        }
    
    def preprocess_message(self, message: str) -> str:
        """Preprocess message before processing"""
        # Basic preprocessing
        message = message.strip()
        
        # Remove excessive punctuation
        import re
        message = re.sub(r'[!]{3,}', '!!!', message)
        message = re.sub(r'[?]{3,}', '???', message)
        
        return message
    
    def validate_message(self, message: str) -> Tuple[bool, Optional[str]]:
        """Validate incoming message"""
        if not message or not message.strip():
            return False, "Empty message"
        
        if len(message) > 2000:
            return False, "Message too long"
        
        # Check for spam patterns (basic implementation)
        spam_patterns = [
            r'(.)\1{10,}',  # Repeated characters
            r'http[s]?://[^\s]+',  # URLs (might want to block)
        ]
        
        for pattern in spam_patterns:
            if re.search(pattern, message, re.IGNORECASE):
                return False, "Message contains suspicious content"
        
        return True, None
    
    async def process_message_async(self, user_id: str, conversation_id: str,
                                   message: str) -> ProcessingResult:
        """Asynchronous message processing for better performance"""
        if self.enable_async_processing:
            # Run processing in thread pool for CPU-intensive tasks
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None, self.process_message, user_id, conversation_id, message
            )
            return result
        else:
            return self.process_message(user_id, conversation_id, message)
    
    def get_processing_stats(self) -> Dict[str, Any]:
        """Get processing statistics"""
        # This would be implemented with actual metrics collection
        return {
            'total_messages_processed': 0,
            'average_processing_time_ms': 0.0,
            'intent_distribution': {},
            'escalation_rate': 0.0,
            'error_rate': 0.0
        }