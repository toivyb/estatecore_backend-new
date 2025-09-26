"""
Context Management System for EstateCore Tenant Chatbot

Manages conversation context, user state, and contextual information
for intelligent, personalized chatbot interactions.
"""

import logging
import json
import time
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from enum import Enum

class ContextType(Enum):
    """Types of context information"""
    USER_PROFILE = "user_profile"
    CONVERSATION = "conversation"
    PROPERTY = "property"
    TENANT = "tenant"
    SYSTEM = "system"

@dataclass
class ContextItem:
    """Individual context item"""
    key: str
    value: Any
    context_type: ContextType
    timestamp: datetime
    ttl: Optional[int] = None  # Time to live in seconds
    confidence: float = 1.0
    source: str = "system"

@dataclass
class UserContext:
    """Complete user context"""
    user_id: str
    session_id: str
    profile: Dict[str, Any]
    preferences: Dict[str, Any]
    current_conversation: Dict[str, Any]
    property_context: Dict[str, Any]
    tenant_context: Dict[str, Any]
    interaction_history: List[Dict[str, Any]]
    last_updated: datetime

class ContextManager:
    """
    Advanced context management for tenant chatbot conversations
    """
    
    def __init__(self):
        """Initialize Context Manager"""
        self.logger = logging.getLogger(__name__)
        
        # In-memory context storage (in production, use Redis or database)
        self.contexts: Dict[str, UserContext] = {}
        self.context_items: Dict[str, List[ContextItem]] = {}
        
        # Configuration
        self.default_ttl = 3600  # 1 hour
        self.max_history_items = 50
        self.context_cleanup_interval = 300  # 5 minutes
        
        # Context extraction rules
        self.extraction_rules = {
            'unit_number': {
                'patterns': [r'unit\s*#?(\d+[a-z]?)', r'apartment\s*#?(\d+[a-z]?)', r'apt\.?\s*#?(\d+[a-z]?)'],
                'type': ContextType.TENANT,
                'confidence': 0.9
            },
            'payment_amount': {
                'patterns': [r'\$[\d,]+\.?\d*', r'[\d,]+\.?\d*\s*dollars?'],
                'type': ContextType.CONVERSATION,
                'confidence': 0.8
            },
            'maintenance_type': {
                'keywords': {
                    'plumbing': ['leak', 'water', 'toilet', 'sink', 'faucet', 'pipe'],
                    'hvac': ['heat', 'air', 'ac', 'cooling', 'heating', 'temperature'],
                    'electrical': ['light', 'outlet', 'power', 'electricity', 'electrical'],
                    'appliance': ['dishwasher', 'refrigerator', 'stove', 'oven', 'washer', 'dryer']
                },
                'type': ContextType.CONVERSATION,
                'confidence': 0.7
            }
        }
        
        self.logger.info("Context Manager initialized")
    
    def create_user_context(self, user_id: str, session_id: str, 
                           initial_data: Optional[Dict[str, Any]] = None) -> UserContext:
        """
        Create a new user context
        
        Args:
            user_id: User identifier
            session_id: Session identifier
            initial_data: Optional initial context data
            
        Returns:
            UserContext object
        """
        context = UserContext(
            user_id=user_id,
            session_id=session_id,
            profile=initial_data.get('profile', {}) if initial_data else {},
            preferences=initial_data.get('preferences', {}) if initial_data else {},
            current_conversation={},
            property_context=initial_data.get('property', {}) if initial_data else {},
            tenant_context=initial_data.get('tenant', {}) if initial_data else {},
            interaction_history=[],
            last_updated=datetime.now()
        )
        
        self.contexts[user_id] = context
        self.context_items[user_id] = []
        
        self.logger.info(f"Created context for user {user_id}")
        return context
    
    def get_user_context(self, user_id: str) -> Optional[UserContext]:
        """
        Get user context by ID
        
        Args:
            user_id: User identifier
            
        Returns:
            UserContext object or None
        """
        return self.contexts.get(user_id)
    
    def update_context_item(self, user_id: str, key: str, value: Any,
                           context_type: ContextType, confidence: float = 1.0,
                           source: str = "system", ttl: Optional[int] = None) -> bool:
        """
        Update a context item
        
        Args:
            user_id: User identifier
            key: Context key
            value: Context value
            context_type: Type of context
            confidence: Confidence score
            source: Source of the context
            ttl: Time to live in seconds
            
        Returns:
            True if successful, False otherwise
        """
        if user_id not in self.contexts:
            return False
        
        # Remove existing item with same key
        if user_id in self.context_items:
            self.context_items[user_id] = [
                item for item in self.context_items[user_id] if item.key != key
            ]
        else:
            self.context_items[user_id] = []
        
        # Add new context item
        item = ContextItem(
            key=key,
            value=value,
            context_type=context_type,
            timestamp=datetime.now(),
            ttl=ttl or self.default_ttl,
            confidence=confidence,
            source=source
        )
        
        self.context_items[user_id].append(item)
        
        # Update appropriate context section
        context = self.contexts[user_id]
        if context_type == ContextType.USER_PROFILE:
            context.profile[key] = value
        elif context_type == ContextType.CONVERSATION:
            context.current_conversation[key] = value
        elif context_type == ContextType.PROPERTY:
            context.property_context[key] = value
        elif context_type == ContextType.TENANT:
            context.tenant_context[key] = value
        
        context.last_updated = datetime.now()
        
        return True
    
    def extract_context_from_message(self, user_id: str, message: str,
                                   entities: Optional[Dict] = None) -> List[ContextItem]:
        """
        Extract context information from a message
        
        Args:
            user_id: User identifier
            message: Message text
            entities: Optional extracted entities
            
        Returns:
            List of extracted context items
        """
        extracted_items = []
        message_lower = message.lower()
        
        # Extract using predefined rules
        for context_key, rule in self.extraction_rules.items():
            
            # Pattern-based extraction
            if 'patterns' in rule:
                import re
                for pattern in rule['patterns']:
                    matches = re.finditer(pattern, message, re.IGNORECASE)
                    for match in matches:
                        value = match.group(1) if match.groups() else match.group()
                        item = ContextItem(
                            key=context_key,
                            value=value,
                            context_type=rule['type'],
                            timestamp=datetime.now(),
                            confidence=rule['confidence'],
                            source="message_extraction"
                        )
                        extracted_items.append(item)
            
            # Keyword-based extraction
            if 'keywords' in rule:
                for category, keywords in rule['keywords'].items():
                    for keyword in keywords:
                        if keyword in message_lower:
                            item = ContextItem(
                                key=context_key,
                                value=category,
                                context_type=rule['type'],
                                timestamp=datetime.now(),
                                confidence=rule['confidence'],
                                source="keyword_extraction"
                            )
                            extracted_items.append(item)
                            break  # Only first match per category
        
        # Extract from entities if provided
        if entities:
            for entity_key, entity_value in entities.items():
                if entity_key == 'unit_numbers' and entity_value:
                    item = ContextItem(
                        key='unit_number',
                        value=entity_value[0],  # Take first unit number
                        context_type=ContextType.TENANT,
                        timestamp=datetime.now(),
                        confidence=0.9,
                        source="entity_extraction"
                    )
                    extracted_items.append(item)
                
                elif entity_key == 'amounts' and entity_value:
                    item = ContextItem(
                        key='mentioned_amount',
                        value=entity_value[0]['value'],
                        context_type=ContextType.CONVERSATION,
                        timestamp=datetime.now(),
                        confidence=0.8,
                        source="entity_extraction"
                    )
                    extracted_items.append(item)
        
        # Update context with extracted items
        for item in extracted_items:
            self.update_context_item(
                user_id, item.key, item.value, item.context_type,
                item.confidence, item.source, item.ttl
            )
        
        return extracted_items
    
    def get_relevant_context(self, user_id: str, intent: str,
                           max_items: int = 10) -> Dict[str, Any]:
        """
        Get relevant context for a specific intent
        
        Args:
            user_id: User identifier
            intent: Current intent
            max_items: Maximum context items to return
            
        Returns:
            Dictionary of relevant context
        """
        context = self.get_user_context(user_id)
        if not context:
            return {}
        
        relevant_context = {
            'user_profile': context.profile,
            'conversation': context.current_conversation,
            'property': context.property_context,
            'tenant': context.tenant_context
        }
        
        # Add intent-specific context
        intent_context = self._get_intent_specific_context(user_id, intent)
        if intent_context:
            relevant_context['intent_specific'] = intent_context
        
        # Add recent interaction history
        recent_history = context.interaction_history[-5:]
        if recent_history:
            relevant_context['recent_interactions'] = recent_history
        
        # Clean expired items
        self._clean_expired_context(user_id)
        
        return relevant_context
    
    def _get_intent_specific_context(self, user_id: str, intent: str) -> Dict[str, Any]:
        """Get context items relevant to specific intent"""
        if user_id not in self.context_items:
            return {}
        
        intent_relevant = {}
        
        # Define relevance mapping
        relevance_map = {
            'rent_payment': ['payment_amount', 'mentioned_amount', 'account_balance', 'due_date'],
            'maintenance_request': ['maintenance_type', 'unit_number', 'urgency_level'],
            'lease_inquiry': ['unit_number', 'lease_end_date', 'renewal_interest'],
            'amenities_info': ['requested_amenity', 'property_features'],
            'account_balance': ['account_balance', 'last_payment', 'due_amount']
        }
        
        relevant_keys = relevance_map.get(intent, [])
        
        for item in self.context_items[user_id]:
            if item.key in relevant_keys and not self._is_expired(item):
                intent_relevant[item.key] = {
                    'value': item.value,
                    'confidence': item.confidence,
                    'timestamp': item.timestamp.isoformat(),
                    'source': item.source
                }
        
        return intent_relevant
    
    def add_interaction_history(self, user_id: str, interaction: Dict[str, Any]) -> None:
        """
        Add interaction to history
        
        Args:
            user_id: User identifier
            interaction: Interaction data
        """
        context = self.get_user_context(user_id)
        if not context:
            return
        
        interaction['timestamp'] = datetime.now().isoformat()
        context.interaction_history.append(interaction)
        
        # Keep only recent interactions
        if len(context.interaction_history) > self.max_history_items:
            context.interaction_history = context.interaction_history[-self.max_history_items:]
        
        context.last_updated = datetime.now()
    
    def get_conversation_context_summary(self, user_id: str) -> Dict[str, Any]:
        """
        Get a summary of conversation context
        
        Args:
            user_id: User identifier
            
        Returns:
            Context summary dictionary
        """
        context = self.get_user_context(user_id)
        if not context:
            return {}
        
        # Count context items by type
        type_counts = {}
        if user_id in self.context_items:
            for item in self.context_items[user_id]:
                if not self._is_expired(item):
                    type_name = item.context_type.value
                    type_counts[type_name] = type_counts.get(type_name, 0) + 1
        
        # Get key context values
        key_context = {}
        important_keys = ['unit_number', 'current_topic', 'maintenance_type', 'user_name']
        
        all_context = {**context.profile, **context.current_conversation, 
                      **context.property_context, **context.tenant_context}
        
        for key in important_keys:
            if key in all_context:
                key_context[key] = all_context[key]
        
        return {
            'user_id': user_id,
            'session_id': context.session_id,
            'context_item_counts': type_counts,
            'key_context': key_context,
            'interaction_count': len(context.interaction_history),
            'last_updated': context.last_updated.isoformat(),
            'session_duration_minutes': (datetime.now() - context.last_updated).total_seconds() / 60
        }
    
    def merge_external_context(self, user_id: str, external_context: Dict[str, Any],
                              source: str = "external") -> bool:
        """
        Merge context from external sources (e.g., property management system)
        
        Args:
            user_id: User identifier
            external_context: External context data
            source: Source identifier
            
        Returns:
            True if successful, False otherwise
        """
        context = self.get_user_context(user_id)
        if not context:
            return False
        
        # Map external data to context types
        mapping = {
            'tenant_info': ContextType.TENANT,
            'property_info': ContextType.PROPERTY,
            'user_profile': ContextType.USER_PROFILE,
            'account_info': ContextType.TENANT
        }
        
        for data_type, data_values in external_context.items():
            if data_type in mapping and isinstance(data_values, dict):
                context_type = mapping[data_type]
                
                for key, value in data_values.items():
                    self.update_context_item(
                        user_id, key, value, context_type,
                        confidence=0.95, source=source
                    )
        
        return True
    
    def predict_user_intent_from_context(self, user_id: str) -> List[Tuple[str, float]]:
        """
        Predict likely user intents based on context
        
        Args:
            user_id: User identifier
            
        Returns:
            List of (intent, probability) tuples
        """
        context = self.get_user_context(user_id)
        if not context:
            return []
        
        intent_scores = {}
        
        # Analyze recent interactions
        recent_intents = []
        for interaction in context.interaction_history[-5:]:
            if 'intent' in interaction:
                recent_intents.append(interaction['intent'])
        
        # Score based on recent activity
        if recent_intents:
            for intent in set(recent_intents):
                count = recent_intents.count(intent)
                intent_scores[intent] = count / len(recent_intents) * 0.3
        
        # Score based on context items
        if user_id in self.context_items:
            for item in self.context_items[user_id]:
                if self._is_expired(item):
                    continue
                
                # Map context to likely intents
                if item.key == 'maintenance_type':
                    intent_scores['maintenance_request'] = intent_scores.get('maintenance_request', 0) + 0.4
                elif item.key in ['payment_amount', 'mentioned_amount']:
                    intent_scores['rent_payment'] = intent_scores.get('rent_payment', 0) + 0.3
                elif item.key == 'account_balance':
                    intent_scores['account_balance'] = intent_scores.get('account_balance', 0) + 0.3
        
        # Convert to sorted list
        sorted_intents = sorted(intent_scores.items(), key=lambda x: x[1], reverse=True)
        return sorted_intents[:5]  # Top 5 predictions
    
    def _is_expired(self, item: ContextItem) -> bool:
        """Check if context item is expired"""
        if item.ttl is None:
            return False
        
        age = (datetime.now() - item.timestamp).total_seconds()
        return age > item.ttl
    
    def _clean_expired_context(self, user_id: str) -> int:
        """Clean expired context items"""
        if user_id not in self.context_items:
            return 0
        
        original_count = len(self.context_items[user_id])
        self.context_items[user_id] = [
            item for item in self.context_items[user_id]
            if not self._is_expired(item)
        ]
        
        cleaned_count = original_count - len(self.context_items[user_id])
        
        if cleaned_count > 0:
            self.logger.debug(f"Cleaned {cleaned_count} expired context items for user {user_id}")
        
        return cleaned_count
    
    def cleanup_all_expired_context(self) -> int:
        """Clean up expired context for all users"""
        total_cleaned = 0
        
        for user_id in list(self.context_items.keys()):
            total_cleaned += self._clean_expired_context(user_id)
        
        # Clean up empty context entries
        empty_users = [user_id for user_id, items in self.context_items.items() if not items]
        for user_id in empty_users:
            if user_id in self.contexts and \
               (datetime.now() - self.contexts[user_id].last_updated).total_seconds() > 3600:
                del self.contexts[user_id]
                del self.context_items[user_id]
                total_cleaned += 1
        
        if total_cleaned > 0:
            self.logger.info(f"Cleaned up {total_cleaned} expired context items")
        
        return total_cleaned
    
    def export_context(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Export user context for analysis or backup
        
        Args:
            user_id: User identifier
            
        Returns:
            Serializable context dictionary
        """
        context = self.get_user_context(user_id)
        if not context:
            return None
        
        context_items = []
        if user_id in self.context_items:
            for item in self.context_items[user_id]:
                if not self._is_expired(item):
                    context_items.append({
                        'key': item.key,
                        'value': item.value,
                        'type': item.context_type.value,
                        'timestamp': item.timestamp.isoformat(),
                        'confidence': item.confidence,
                        'source': item.source
                    })
        
        return {
            'user_id': user_id,
            'session_id': context.session_id,
            'profile': context.profile,
            'preferences': context.preferences,
            'current_conversation': context.current_conversation,
            'property_context': context.property_context,
            'tenant_context': context.tenant_context,
            'interaction_history': context.interaction_history,
            'context_items': context_items,
            'last_updated': context.last_updated.isoformat()
        }