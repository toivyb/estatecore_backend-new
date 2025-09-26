"""
Conversation Management System for EstateCore Tenant Chatbot

Manages conversation context, state, and multi-turn dialog handling
with intelligent conversation flow control and escalation logic.
"""

import logging
import json
import time
import uuid
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from enum import Enum
import redis
from .nlp_engine import ProcessedText
from .intent_classifier import IntentPrediction

class ConversationState(Enum):
    """Possible conversation states"""
    ACTIVE = "active"
    WAITING_FOR_INPUT = "waiting_for_input"
    ESCALATED = "escalated"
    RESOLVED = "resolved"
    ABANDONED = "abandoned"

class EscalationReason(Enum):
    """Reasons for escalating to human agent"""
    COMPLEX_QUERY = "complex_query"
    LOW_CONFIDENCE = "low_confidence"
    USER_REQUEST = "user_request"
    EMERGENCY = "emergency"
    MULTIPLE_FAILURES = "multiple_failures"
    NEGATIVE_SENTIMENT = "negative_sentiment"

@dataclass
class Message:
    """Individual message in conversation"""
    id: str
    sender: str  # 'user' or 'bot'
    content: str
    timestamp: datetime
    intent: Optional[str] = None
    entities: Optional[Dict] = None
    confidence: Optional[float] = None
    processed_data: Optional[Dict] = None

@dataclass
class ConversationContext:
    """Context information for conversation"""
    user_id: str
    tenant_id: Optional[str] = None
    property_id: Optional[str] = None
    unit_number: Optional[str] = None
    user_name: Optional[str] = None
    preferred_language: str = "en"
    previous_queries: List[str] = None
    current_topic: Optional[str] = None
    extracted_entities: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.previous_queries is None:
            self.previous_queries = []
        if self.extracted_entities is None:
            self.extracted_entities = {}

@dataclass
class Conversation:
    """Complete conversation object"""
    id: str
    user_id: str
    context: ConversationContext
    messages: List[Message]
    state: ConversationState
    created_at: datetime
    updated_at: datetime
    escalation_reason: Optional[EscalationReason] = None
    escalated_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    satisfaction_score: Optional[int] = None
    tags: List[str] = None
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = []

class ConversationManager:
    """
    Advanced conversation management system for the tenant chatbot
    """
    
    def __init__(self, redis_client: Optional[redis.Redis] = None):
        """
        Initialize Conversation Manager
        
        Args:
            redis_client: Redis client for session storage
        """
        self.logger = logging.getLogger(__name__)
        
        # Redis for session storage
        if redis_client:
            self.redis = redis_client
        else:
            try:
                self.redis = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
                # Test connection
                self.redis.ping()
            except Exception as e:
                self.logger.warning(f"Redis not available, using memory storage: {e}")
                self.redis = None
        
        # In-memory fallback storage
        self.conversations: Dict[str, Conversation] = {}
        
        # Configuration
        self.max_conversation_age = timedelta(hours=24)
        self.max_messages_per_conversation = 100
        self.escalation_confidence_threshold = 0.6
        self.max_failed_attempts = 3
        self.session_timeout = timedelta(minutes=30)
        
        self.logger.info("Conversation Manager initialized")
    
    def start_conversation(self, user_id: str, context: ConversationContext) -> str:
        """
        Start a new conversation
        
        Args:
            user_id: User identifier
            context: Conversation context
            
        Returns:
            Conversation ID
        """
        conversation_id = str(uuid.uuid4())
        
        conversation = Conversation(
            id=conversation_id,
            user_id=user_id,
            context=context,
            messages=[],
            state=ConversationState.ACTIVE,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        # Store conversation
        self._store_conversation(conversation)
        
        self.logger.info(f"Started conversation {conversation_id} for user {user_id}")
        return conversation_id
    
    def add_message(self, conversation_id: str, sender: str, content: str,
                   intent: Optional[str] = None, entities: Optional[Dict] = None,
                   confidence: Optional[float] = None) -> Message:
        """
        Add a message to the conversation
        
        Args:
            conversation_id: Conversation ID
            sender: Message sender ('user' or 'bot')
            content: Message content
            intent: Detected intent (optional)
            entities: Extracted entities (optional)
            confidence: Intent confidence (optional)
            
        Returns:
            Created Message object
        """
        conversation = self.get_conversation(conversation_id)
        if not conversation:
            raise ValueError(f"Conversation {conversation_id} not found")
        
        # Create message
        message = Message(
            id=str(uuid.uuid4()),
            sender=sender,
            content=content,
            timestamp=datetime.now(),
            intent=intent,
            entities=entities,
            confidence=confidence
        )
        
        # Add to conversation
        conversation.messages.append(message)
        conversation.updated_at = datetime.now()
        
        # Update conversation state based on message
        self._update_conversation_state(conversation, message)
        
        # Store updated conversation
        self._store_conversation(conversation)
        
        return message
    
    def get_conversation(self, conversation_id: str) -> Optional[Conversation]:
        """
        Retrieve a conversation by ID
        
        Args:
            conversation_id: Conversation ID
            
        Returns:
            Conversation object or None if not found
        """
        if self.redis:
            try:
                data = self.redis.get(f"conversation:{conversation_id}")
                if data:
                    return self._deserialize_conversation(json.loads(data))
            except Exception as e:
                self.logger.error(f"Error retrieving conversation from Redis: {e}")
        
        return self.conversations.get(conversation_id)
    
    def get_user_conversations(self, user_id: str, limit: int = 10) -> List[Conversation]:
        """
        Get conversations for a specific user
        
        Args:
            user_id: User ID
            limit: Maximum number of conversations to return
            
        Returns:
            List of user's conversations
        """
        conversations = []
        
        if self.redis:
            try:
                # Get conversation IDs for user
                conv_ids = self.redis.smembers(f"user_conversations:{user_id}")
                for conv_id in list(conv_ids)[:limit]:
                    conv = self.get_conversation(conv_id)
                    if conv:
                        conversations.append(conv)
            except Exception as e:
                self.logger.error(f"Error retrieving user conversations: {e}")
        else:
            # Search in-memory conversations
            user_convs = [conv for conv in self.conversations.values() 
                         if conv.user_id == user_id]
            conversations = sorted(user_convs, 
                                 key=lambda x: x.updated_at, reverse=True)[:limit]
        
        return conversations
    
    def update_context(self, conversation_id: str, context_updates: Dict[str, Any]) -> bool:
        """
        Update conversation context
        
        Args:
            conversation_id: Conversation ID
            context_updates: Dictionary of context updates
            
        Returns:
            True if successful, False otherwise
        """
        conversation = self.get_conversation(conversation_id)
        if not conversation:
            return False
        
        # Update context fields
        for key, value in context_updates.items():
            if hasattr(conversation.context, key):
                setattr(conversation.context, key, value)
            else:
                # Add to extracted_entities if not a direct field
                conversation.context.extracted_entities[key] = value
        
        conversation.updated_at = datetime.now()
        self._store_conversation(conversation)
        
        return True
    
    def should_escalate(self, conversation_id: str, 
                       intent_prediction: IntentPrediction,
                       sentiment: Optional[Dict] = None) -> Tuple[bool, Optional[EscalationReason]]:
        """
        Determine if conversation should be escalated to human agent
        
        Args:
            conversation_id: Conversation ID
            intent_prediction: Latest intent prediction
            sentiment: Sentiment analysis results
            
        Returns:
            Tuple of (should_escalate, escalation_reason)
        """
        conversation = self.get_conversation(conversation_id)
        if not conversation:
            return False, None
        
        # Check for emergency intent
        if intent_prediction.intent == 'emergency':
            return True, EscalationReason.EMERGENCY
        
        # Check confidence threshold
        if intent_prediction.confidence < self.escalation_confidence_threshold:
            return True, EscalationReason.LOW_CONFIDENCE
        
        # Check for negative sentiment
        if sentiment and sentiment.get('polarity', 0) < -0.5:
            return True, EscalationReason.NEGATIVE_SENTIMENT
        
        # Check for repeated failed attempts
        failed_attempts = self._count_failed_attempts(conversation)
        if failed_attempts >= self.max_failed_attempts:
            return True, EscalationReason.MULTIPLE_FAILURES
        
        # Check for explicit user request for human agent
        last_message = conversation.messages[-1] if conversation.messages else None
        if last_message and self._contains_human_request(last_message.content):
            return True, EscalationReason.USER_REQUEST
        
        # Check for complex queries (multiple intents with low confidence)
        if (len(intent_prediction.alternative_intents) > 2 and 
            intent_prediction.confidence < 0.8):
            return True, EscalationReason.COMPLEX_QUERY
        
        return False, None
    
    def escalate_conversation(self, conversation_id: str, 
                            reason: EscalationReason) -> bool:
        """
        Escalate conversation to human agent
        
        Args:
            conversation_id: Conversation ID
            reason: Reason for escalation
            
        Returns:
            True if successful, False otherwise
        """
        conversation = self.get_conversation(conversation_id)
        if not conversation:
            return False
        
        conversation.state = ConversationState.ESCALATED
        conversation.escalation_reason = reason
        conversation.escalated_at = datetime.now()
        conversation.updated_at = datetime.now()
        
        # Add escalation tag
        if 'escalated' not in conversation.tags:
            conversation.tags.append('escalated')
            conversation.tags.append(f'escalation:{reason.value}')
        
        self._store_conversation(conversation)
        
        # Log escalation
        self.logger.info(f"Escalated conversation {conversation_id} - Reason: {reason.value}")
        
        return True
    
    def resolve_conversation(self, conversation_id: str, 
                           satisfaction_score: Optional[int] = None) -> bool:
        """
        Mark conversation as resolved
        
        Args:
            conversation_id: Conversation ID
            satisfaction_score: User satisfaction score (1-5)
            
        Returns:
            True if successful, False otherwise
        """
        conversation = self.get_conversation(conversation_id)
        if not conversation:
            return False
        
        conversation.state = ConversationState.RESOLVED
        conversation.resolved_at = datetime.now()
        conversation.updated_at = datetime.now()
        
        if satisfaction_score:
            conversation.satisfaction_score = satisfaction_score
        
        if 'resolved' not in conversation.tags:
            conversation.tags.append('resolved')
        
        self._store_conversation(conversation)
        
        self.logger.info(f"Resolved conversation {conversation_id}")
        return True
    
    def get_conversation_summary(self, conversation_id: str) -> Dict[str, Any]:
        """
        Get conversation summary and analytics
        
        Args:
            conversation_id: Conversation ID
            
        Returns:
            Dictionary with conversation summary
        """
        conversation = self.get_conversation(conversation_id)
        if not conversation:
            return {}
        
        # Calculate metrics
        user_messages = [m for m in conversation.messages if m.sender == 'user']
        bot_messages = [m for m in conversation.messages if m.sender == 'bot']
        
        duration = conversation.updated_at - conversation.created_at
        
        # Extract intents
        intents = [m.intent for m in conversation.messages if m.intent]
        unique_intents = list(set(intents))
        
        return {
            'conversation_id': conversation.id,
            'user_id': conversation.user_id,
            'state': conversation.state.value,
            'duration_minutes': duration.total_seconds() / 60,
            'total_messages': len(conversation.messages),
            'user_messages': len(user_messages),
            'bot_messages': len(bot_messages),
            'unique_intents': unique_intents,
            'escalated': conversation.state == ConversationState.ESCALATED,
            'escalation_reason': conversation.escalation_reason.value if conversation.escalation_reason else None,
            'satisfaction_score': conversation.satisfaction_score,
            'tags': conversation.tags,
            'created_at': conversation.created_at.isoformat(),
            'updated_at': conversation.updated_at.isoformat()
        }
    
    def cleanup_old_conversations(self) -> int:
        """
        Clean up old conversations
        
        Returns:
            Number of conversations cleaned up
        """
        cleaned_count = 0
        cutoff_time = datetime.now() - self.max_conversation_age
        
        if self.redis:
            # Redis cleanup would require scanning all keys
            # This is a simplified version
            pass
        else:
            # Clean up in-memory conversations
            to_remove = []
            for conv_id, conv in self.conversations.items():
                if conv.updated_at < cutoff_time:
                    to_remove.append(conv_id)
            
            for conv_id in to_remove:
                del self.conversations[conv_id]
                cleaned_count += 1
        
        if cleaned_count > 0:
            self.logger.info(f"Cleaned up {cleaned_count} old conversations")
        
        return cleaned_count
    
    def get_context_for_response(self, conversation_id: str) -> Dict[str, Any]:
        """
        Get conversation context for response generation
        
        Args:
            conversation_id: Conversation ID
            
        Returns:
            Context dictionary for response generation
        """
        conversation = self.get_conversation(conversation_id)
        if not conversation:
            return {}
        
        # Get recent messages for context
        recent_messages = conversation.messages[-5:] if conversation.messages else []
        
        # Extract key information
        context = {
            'user_id': conversation.user_id,
            'tenant_id': conversation.context.tenant_id,
            'property_id': conversation.context.property_id,
            'unit_number': conversation.context.unit_number,
            'user_name': conversation.context.user_name,
            'preferred_language': conversation.context.preferred_language,
            'current_topic': conversation.context.current_topic,
            'recent_messages': [
                {
                    'sender': msg.sender,
                    'content': msg.content,
                    'intent': msg.intent,
                    'timestamp': msg.timestamp.isoformat()
                }
                for msg in recent_messages
            ],
            'extracted_entities': conversation.context.extracted_entities,
            'conversation_state': conversation.state.value
        }
        
        return context
    
    def _store_conversation(self, conversation: Conversation) -> None:
        """Store conversation in Redis or memory"""
        if self.redis:
            try:
                # Store conversation
                conv_data = json.dumps(self._serialize_conversation(conversation), default=str)
                self.redis.setex(f"conversation:{conversation.id}", 
                               int(self.session_timeout.total_seconds()), conv_data)
                
                # Add to user's conversation list
                self.redis.sadd(f"user_conversations:{conversation.user_id}", 
                              conversation.id)
                self.redis.expire(f"user_conversations:{conversation.user_id}",
                                int(self.max_conversation_age.total_seconds()))
                
            except Exception as e:
                self.logger.error(f"Error storing conversation in Redis: {e}")
                # Fallback to memory
                self.conversations[conversation.id] = conversation
        else:
            self.conversations[conversation.id] = conversation
    
    def _serialize_conversation(self, conversation: Conversation) -> Dict:
        """Serialize conversation for storage"""
        return {
            'id': conversation.id,
            'user_id': conversation.user_id,
            'context': asdict(conversation.context),
            'messages': [asdict(msg) for msg in conversation.messages],
            'state': conversation.state.value,
            'created_at': conversation.created_at.isoformat(),
            'updated_at': conversation.updated_at.isoformat(),
            'escalation_reason': conversation.escalation_reason.value if conversation.escalation_reason else None,
            'escalated_at': conversation.escalated_at.isoformat() if conversation.escalated_at else None,
            'resolved_at': conversation.resolved_at.isoformat() if conversation.resolved_at else None,
            'satisfaction_score': conversation.satisfaction_score,
            'tags': conversation.tags
        }
    
    def _deserialize_conversation(self, data: Dict) -> Conversation:
        """Deserialize conversation from storage"""
        # Parse dates
        created_at = datetime.fromisoformat(data['created_at'])
        updated_at = datetime.fromisoformat(data['updated_at'])
        escalated_at = datetime.fromisoformat(data['escalated_at']) if data.get('escalated_at') else None
        resolved_at = datetime.fromisoformat(data['resolved_at']) if data.get('resolved_at') else None
        
        # Parse messages
        messages = []
        for msg_data in data['messages']:
            msg_data['timestamp'] = datetime.fromisoformat(msg_data['timestamp'])
            messages.append(Message(**msg_data))
        
        # Parse context
        context = ConversationContext(**data['context'])
        
        # Parse state and escalation reason
        state = ConversationState(data['state'])
        escalation_reason = EscalationReason(data['escalation_reason']) if data.get('escalation_reason') else None
        
        return Conversation(
            id=data['id'],
            user_id=data['user_id'],
            context=context,
            messages=messages,
            state=state,
            created_at=created_at,
            updated_at=updated_at,
            escalation_reason=escalation_reason,
            escalated_at=escalated_at,
            resolved_at=resolved_at,
            satisfaction_score=data.get('satisfaction_score'),
            tags=data.get('tags', [])
        )
    
    def _update_conversation_state(self, conversation: Conversation, message: Message) -> None:
        """Update conversation state based on new message"""
        if message.sender == 'user':
            if conversation.state == ConversationState.WAITING_FOR_INPUT:
                conversation.state = ConversationState.ACTIVE
            
            # Update current topic based on intent
            if message.intent:
                conversation.context.current_topic = message.intent
    
    def _count_failed_attempts(self, conversation: Conversation) -> int:
        """Count consecutive failed bot responses"""
        failed_count = 0
        
        # Look at recent bot messages for failure indicators
        bot_messages = [m for m in conversation.messages[-10:] if m.sender == 'bot']
        
        for message in reversed(bot_messages):
            if any(phrase in message.content.lower() for phrase in 
                   ['sorry', 'understand', 'help', 'unclear']):
                failed_count += 1
            else:
                break
        
        return failed_count
    
    def _contains_human_request(self, text: str) -> bool:
        """Check if text contains request for human agent"""
        human_phrases = [
            'speak to human', 'talk to person', 'human agent', 
            'real person', 'customer service', 'representative'
        ]
        
        text_lower = text.lower()
        return any(phrase in text_lower for phrase in human_phrases)