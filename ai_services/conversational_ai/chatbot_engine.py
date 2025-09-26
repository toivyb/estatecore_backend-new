#!/usr/bin/env python3
"""
AI-Powered Conversational Assistant for EstateCore Phase 7B
Advanced chatbot with natural language understanding and task automation
"""

import os
import json
import logging
import re
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import sqlite3
import threading
import queue
import uuid

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Intent(Enum):
    # Property Management Intents
    GET_PROPERTY_INFO = "get_property_info"
    GET_OCCUPANCY_RATE = "get_occupancy_rate"
    GET_RENTAL_INCOME = "get_rental_income"
    GET_MAINTENANCE_STATUS = "get_maintenance_status"
    
    # Tenant Management Intents
    GET_TENANT_INFO = "get_tenant_info"
    PROCESS_RENT_PAYMENT = "process_rent_payment"
    HANDLE_TENANT_COMPLAINT = "handle_tenant_complaint"
    
    # Maintenance Intents
    SCHEDULE_MAINTENANCE = "schedule_maintenance"
    GET_MAINTENANCE_HISTORY = "get_maintenance_history"
    EMERGENCY_MAINTENANCE = "emergency_maintenance"
    
    # Financial Intents
    GET_FINANCIAL_REPORT = "get_financial_report"
    CALCULATE_ROI = "calculate_roi"
    GET_EXPENSES = "get_expenses"
    
    # Market Intelligence Intents
    GET_MARKET_DATA = "get_market_data"
    GET_INVESTMENT_OPPORTUNITIES = "get_investment_opportunities"
    GET_COMPETITIVE_ANALYSIS = "get_competitive_analysis"
    
    # General Intents
    GREETING = "greeting"
    GOODBYE = "goodbye"
    HELP = "help"
    UNCLEAR = "unclear"

class EntityType(Enum):
    PROPERTY_ID = "property_id"
    PROPERTY_ADDRESS = "property_address"
    TENANT_NAME = "tenant_name"
    TENANT_ID = "tenant_id"
    DATE = "date"
    AMOUNT = "amount"
    MAINTENANCE_TYPE = "maintenance_type"
    LOCATION = "location"
    TIME_PERIOD = "time_period"

@dataclass
class Entity:
    """Extracted entity from user message"""
    type: EntityType
    value: str
    confidence: float
    start_pos: int
    end_pos: int

@dataclass
class ConversationContext:
    """Context for maintaining conversation state"""
    user_id: str
    session_id: str
    last_intent: Optional[Intent]
    entities: Dict[str, Any]
    conversation_history: List[Dict[str, Any]]
    pending_actions: List[Dict[str, Any]]
    user_preferences: Dict[str, Any]
    created_at: datetime
    last_activity: datetime

@dataclass
class ChatResponse:
    """Response from the chatbot"""
    message: str
    intent: Intent
    confidence: float
    entities: List[Entity]
    suggested_actions: List[Dict[str, Any]]
    requires_followup: bool
    context_updated: bool
    response_type: str  # "text", "action", "clarification", "error"
    metadata: Dict[str, Any] = None

class IntentClassifier:
    """Natural language intent classification"""
    
    def __init__(self):
        self.intent_patterns = {
            Intent.GET_PROPERTY_INFO: [
                r'property\s+(info|information|details)',
                r'tell me about property',
                r'(what|show).*(property|building)',
                r'property\s+(\d+|[a-zA-Z\s]+)',
            ],
            Intent.GET_OCCUPANCY_RATE: [
                r'occupancy\s+rate',
                r'how many.*(occupied|vacant)',
                r'(full|empty).*(units|apartments)',
                r'vacancy.*(rate|percentage)',
            ],
            Intent.GET_RENTAL_INCOME: [
                r'rental\s+income',
                r'how much.*(rent|revenue)',
                r'monthly\s+(income|revenue)',
                r'total.*(rent|income)',
            ],
            Intent.SCHEDULE_MAINTENANCE: [
                r'schedule\s+(maintenance|repair)',
                r'book\s+(maintenance|repair)',
                r'need.*(maintenance|repair|fix)',
                r'maintenance\s+for\s+(\d+|[a-zA-Z\s]+)',
            ],
            Intent.GET_MARKET_DATA: [
                r'market\s+(data|information|prices)',
                r'property\s+(values|prices)',
                r'market\s+(trends|analysis)',
                r'(what|how).*(market|prices)',
            ],
            Intent.GREETING: [
                r'^(hi|hello|hey|good\s+(morning|afternoon|evening))',
                r'how\s+are\s+you',
                r'what\'s\s+up',
            ],
            Intent.HELP: [
                r'help',
                r'what\s+can\s+you\s+do',
                r'(show|tell)\s+me\s+(commands|options)',
                r'how\s+do\s+i',
            ],
        }
        
        logger.info("IntentClassifier initialized")
    
    def classify(self, message: str) -> Tuple[Intent, float]:
        """Classify user intent from message"""
        message_lower = message.lower().strip()
        
        best_intent = Intent.UNCLEAR
        best_confidence = 0.0
        
        for intent, patterns in self.intent_patterns.items():
            for pattern in patterns:
                match = re.search(pattern, message_lower)
                if match:
                    # Calculate confidence based on match quality
                    match_length = len(match.group(0))
                    message_length = len(message_lower)
                    confidence = min(0.95, match_length / message_length + 0.3)
                    
                    if confidence > best_confidence:
                        best_intent = intent
                        best_confidence = confidence
        
        # Apply context-based confidence adjustments
        if best_confidence < 0.3:
            best_intent = Intent.UNCLEAR
            best_confidence = 0.2
        
        return best_intent, best_confidence

class EntityExtractor:
    """Extract entities from user messages"""
    
    def __init__(self):
        self.entity_patterns = {
            EntityType.PROPERTY_ID: [
                r'property\s+(\d+)',
                r'unit\s+(\d+)',
                r'building\s+(\d+)',
            ],
            EntityType.PROPERTY_ADDRESS: [
                r'(\d+\s+[a-zA-Z\s]+(?:street|st|avenue|ave|road|rd|lane|ln|drive|dr|boulevard|blvd))',
                r'([a-zA-Z\s]+(?:street|st|avenue|ave|road|rd|lane|ln|drive|dr|boulevard|blvd)\s+\d+)',
            ],
            EntityType.TENANT_NAME: [
                r'tenant\s+([a-zA-Z\s]+)',
                r'renter\s+([a-zA-Z\s]+)',
                r'resident\s+([a-zA-Z\s]+)',
            ],
            EntityType.DATE: [
                r'(\d{1,2}[\/\-]\d{1,2}[\/\-]\d{2,4})',
                r'(today|tomorrow|yesterday)',
                r'(next|last)\s+(week|month|year)',
                r'(monday|tuesday|wednesday|thursday|friday|saturday|sunday)',
            ],
            EntityType.AMOUNT: [
                r'\$?([\d,]+\.?\d*)',
                r'(\d+)\s*(dollars?|bucks?)',
            ],
            EntityType.MAINTENANCE_TYPE: [
                r'(hvac|heating|cooling|air\s+conditioning)',
                r'(plumbing|water|leak|pipe)',
                r'(electrical|electric|wiring|power)',
                r'(paint|painting|wall)',
                r'(roof|roofing|ceiling)',
                r'(appliance|refrigerator|dishwasher|washer|dryer)',
            ],
            EntityType.LOCATION: [
                r'(new\s+york|los\s+angeles|chicago|houston|phoenix|philadelphia)',
                r'([a-zA-Z\s]+,\s*[a-zA-Z]{2})',
            ],
            EntityType.TIME_PERIOD: [
                r'(last|past|previous)\s+(week|month|quarter|year)',
                r'(next|coming|upcoming)\s+(week|month|quarter|year)',
                r'(this|current)\s+(week|month|quarter|year)',
            ],
        }
        
        logger.info("EntityExtractor initialized")
    
    def extract(self, message: str) -> List[Entity]:
        """Extract entities from message"""
        entities = []
        message_lower = message.lower()
        
        for entity_type, patterns in self.entity_patterns.items():
            for pattern in patterns:
                matches = re.finditer(pattern, message_lower)
                for match in matches:
                    entity = Entity(
                        type=entity_type,
                        value=match.group(1) if match.groups() else match.group(0),
                        confidence=0.8,  # Could be improved with ML model
                        start_pos=match.start(),
                        end_pos=match.end()
                    )
                    entities.append(entity)
        
        return entities

class ResponseGenerator:
    """Generate natural language responses"""
    
    def __init__(self):
        self.response_templates = {
            Intent.GREETING: [
                "Hello! I'm your EstateCore AI assistant. How can I help you manage your properties today?",
                "Hi there! I'm here to help with your property management needs. What would you like to know?",
                "Good day! I'm your AI property management assistant. How may I assist you?",
            ],
            Intent.HELP: [
                "I can help you with:\n• Property information and occupancy rates\n• Rental income and financial reports\n• Maintenance scheduling and history\n• Market data and investment opportunities\n• Tenant management\n\nWhat would you like to know about?",
                "Here's what I can do for you:\n📊 Property analytics and reports\n🔧 Maintenance management\n💰 Financial tracking\n🏠 Market intelligence\n👥 Tenant services\n\nJust ask me anything!",
            ],
            Intent.GET_PROPERTY_INFO: [
                "I'd be happy to get that property information for you. Let me look that up...",
                "Sure! I'll retrieve the property details for you right away.",
            ],
            Intent.GET_OCCUPANCY_RATE: [
                "Let me check the current occupancy rates for your properties...",
                "I'll get you the latest occupancy information.",
            ],
            Intent.SCHEDULE_MAINTENANCE: [
                "I'll help you schedule that maintenance. Let me get the details organized...",
                "Sure! I can schedule maintenance for you. Let me process this request...",
            ],
            Intent.UNCLEAR: [
                "I'm not sure I understood that correctly. Could you please rephrase your question?",
                "I want to make sure I help you with the right information. Could you be more specific?",
                "I didn't quite catch that. Could you tell me more about what you're looking for?",
            ],
        }
        
        self.action_responses = {
            "property_lookup": "Here's the information for {property}:",
            "maintenance_scheduled": "✅ Maintenance has been scheduled for {date} at {property}.",
            "financial_report": "📊 Here's your financial summary for {period}:",
            "market_data": "📈 Current market data for {location}:",
        }
        
        logger.info("ResponseGenerator initialized")
    
    def generate(self, intent: Intent, entities: List[Entity], 
                context: ConversationContext, action_result: Dict[str, Any] = None) -> str:
        """Generate appropriate response"""
        
        # If we have action results, format them
        if action_result:
            return self._format_action_response(intent, entities, action_result)
        
        # Get template responses for intent
        templates = self.response_templates.get(intent, ["I understand. Let me help you with that."])
        
        # For now, use the first template (could be randomized)
        response = templates[0]
        
        # Add entity-specific information
        if entities:
            entity_info = self._format_entities(entities)
            if entity_info:
                response += f" I see you mentioned: {entity_info}"
        
        return response
    
    def _format_action_response(self, intent: Intent, entities: List[Entity], 
                              action_result: Dict[str, Any]) -> str:
        """Format response with action results"""
        
        if intent == Intent.GET_PROPERTY_INFO and action_result.get('property_data'):
            data = action_result['property_data']
            return f"📍 Property Information:\n• Address: {data.get('address', 'N/A')}\n• Type: {data.get('type', 'N/A')}\n• Units: {data.get('units', 'N/A')}\n• Occupancy: {data.get('occupancy_rate', 'N/A')}%\n• Monthly Income: ${data.get('monthly_income', 0):,.2f}"
        
        elif intent == Intent.GET_OCCUPANCY_RATE and action_result.get('occupancy_data'):
            data = action_result['occupancy_data']
            return f"📊 Occupancy Summary:\n• Total Units: {data.get('total_units', 'N/A')}\n• Occupied: {data.get('occupied_units', 'N/A')}\n• Vacant: {data.get('vacant_units', 'N/A')}\n• Occupancy Rate: {data.get('occupancy_rate', 'N/A')}%"
        
        elif intent == Intent.GET_MARKET_DATA and action_result.get('market_data'):
            data = action_result['market_data']
            return f"📈 Market Data for {data.get('location', 'your area')}:\n• Median Price: ${data.get('median_price', 0):,.0f}\n• Average Rent: ${data.get('average_rent', 0):,.0f}\n• Price per SqFt: ${data.get('price_per_sqft', 0):,.0f}\n• Days on Market: {data.get('days_on_market', 'N/A')}"
        
        elif intent == Intent.SCHEDULE_MAINTENANCE and action_result.get('maintenance_scheduled'):
            return f"✅ Maintenance Scheduled Successfully!\n• Type: {action_result.get('maintenance_type', 'General')}\n• Property: {action_result.get('property', 'N/A')}\n• Date: {action_result.get('scheduled_date', 'N/A')}\n• Priority: {action_result.get('priority', 'Normal')}"
        
        return "I've processed your request. Is there anything else I can help you with?"
    
    def _format_entities(self, entities: List[Entity]) -> str:
        """Format entities for display"""
        entity_strings = []
        for entity in entities:
            if entity.type == EntityType.PROPERTY_ID:
                entity_strings.append(f"Property {entity.value}")
            elif entity.type == EntityType.DATE:
                entity_strings.append(f"Date: {entity.value}")
            elif entity.type == EntityType.AMOUNT:
                entity_strings.append(f"Amount: ${entity.value}")
            elif entity.type == EntityType.MAINTENANCE_TYPE:
                entity_strings.append(f"Maintenance: {entity.value}")
        
        return ", ".join(entity_strings)

class ConversationManager:
    """Manage conversation context and state"""
    
    def __init__(self, database_path: str = "conversations.db"):
        self.database_path = database_path
        self.active_contexts = {}
        self._initialize_database()
        
        logger.info("ConversationManager initialized")
    
    def _initialize_database(self):
        """Initialize conversation database"""
        conn = sqlite3.connect(self.database_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT UNIQUE NOT NULL,
                user_id TEXT NOT NULL,
                context_data TEXT NOT NULL,
                created_at TEXT NOT NULL,
                last_activity TEXT NOT NULL
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS conversation_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                message_type TEXT NOT NULL,
                content TEXT NOT NULL,
                intent TEXT,
                entities TEXT,
                timestamp TEXT NOT NULL,
                FOREIGN KEY (session_id) REFERENCES conversations (session_id)
            )
        """)
        
        conn.commit()
        conn.close()
    
    def get_or_create_context(self, user_id: str, session_id: str = None) -> ConversationContext:
        """Get existing context or create new one"""
        if not session_id:
            session_id = str(uuid.uuid4())
        
        # Check if context exists in memory
        if session_id in self.active_contexts:
            context = self.active_contexts[session_id]
            context.last_activity = datetime.now()
            return context
        
        # Try to load from database
        context = self._load_context_from_db(session_id)
        if context:
            self.active_contexts[session_id] = context
            context.last_activity = datetime.now()
            return context
        
        # Create new context
        context = ConversationContext(
            user_id=user_id,
            session_id=session_id,
            last_intent=None,
            entities={},
            conversation_history=[],
            pending_actions=[],
            user_preferences={},
            created_at=datetime.now(),
            last_activity=datetime.now()
        )
        
        self.active_contexts[session_id] = context
        self._save_context_to_db(context)
        
        return context
    
    def _load_context_from_db(self, session_id: str) -> Optional[ConversationContext]:
        """Load context from database"""
        try:
            conn = sqlite3.connect(self.database_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT user_id, context_data, created_at, last_activity 
                FROM conversations WHERE session_id = ?
            """, (session_id,))
            
            row = cursor.fetchone()
            if not row:
                return None
            
            user_id, context_data, created_at, last_activity = row
            data = json.loads(context_data)
            
            context = ConversationContext(
                user_id=user_id,
                session_id=session_id,
                last_intent=Intent(data['last_intent']) if data['last_intent'] else None,
                entities=data['entities'],
                conversation_history=data['conversation_history'],
                pending_actions=data['pending_actions'],
                user_preferences=data['user_preferences'],
                created_at=datetime.fromisoformat(created_at),
                last_activity=datetime.fromisoformat(last_activity)
            )
            
            conn.close()
            return context
            
        except Exception as e:
            logger.error(f"Error loading context: {e}")
            return None
    
    def _save_context_to_db(self, context: ConversationContext):
        """Save context to database"""
        try:
            conn = sqlite3.connect(self.database_path)
            cursor = conn.cursor()
            
            context_data = {
                'last_intent': context.last_intent.value if context.last_intent else None,
                'entities': context.entities,
                'conversation_history': context.conversation_history,
                'pending_actions': context.pending_actions,
                'user_preferences': context.user_preferences
            }
            
            cursor.execute("""
                INSERT OR REPLACE INTO conversations 
                (session_id, user_id, context_data, created_at, last_activity)
                VALUES (?, ?, ?, ?, ?)
            """, (
                context.session_id, context.user_id, json.dumps(context_data),
                context.created_at.isoformat(), context.last_activity.isoformat()
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Error saving context: {e}")
    
    def add_message_to_history(self, context: ConversationContext, 
                             message_type: str, content: str, 
                             intent: Intent = None, entities: List[Entity] = None):
        """Add message to conversation history"""
        # Convert entities to serializable format
        serializable_entities = []
        if entities:
            for entity in entities:
                serializable_entities.append({
                    'type': entity.type.value,
                    'value': entity.value,
                    'confidence': entity.confidence,
                    'start_pos': entity.start_pos,
                    'end_pos': entity.end_pos
                })
        
        message = {
            'type': message_type,
            'content': content,
            'intent': intent.value if intent else None,
            'entities': serializable_entities,
            'timestamp': datetime.now().isoformat()
        }
        
        context.conversation_history.append(message)
        
        # Keep only last 20 messages
        if len(context.conversation_history) > 20:
            context.conversation_history = context.conversation_history[-20:]
        
        # Save to database
        self._save_message_to_db(context.session_id, message)
        self._save_context_to_db(context)
    
    def _save_message_to_db(self, session_id: str, message: Dict[str, Any]):
        """Save message to database"""
        try:
            conn = sqlite3.connect(self.database_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO conversation_history 
                (session_id, message_type, content, intent, entities, timestamp)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                session_id, message['type'], message['content'],
                message['intent'], json.dumps(message['entities']),
                message['timestamp']
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Error saving message: {e}")

class EstateCoreChatbot:
    """Main chatbot engine integrating all components"""
    
    def __init__(self):
        self.intent_classifier = IntentClassifier()
        self.entity_extractor = EntityExtractor()
        self.response_generator = ResponseGenerator()
        self.conversation_manager = ConversationManager()
        
        logger.info("EstateCoreChatbot initialized")
    
    async def process_message(self, message: str, user_id: str, 
                            session_id: str = None) -> ChatResponse:
        """Process user message and generate response"""
        
        # Get or create conversation context
        context = self.conversation_manager.get_or_create_context(user_id, session_id)
        
        # Add user message to history
        self.conversation_manager.add_message_to_history(
            context, 'user', message
        )
        
        # Classify intent
        intent, intent_confidence = self.intent_classifier.classify(message)
        
        # Extract entities
        entities = self.entity_extractor.extract(message)
        
        # Update context
        context.last_intent = intent
        for entity in entities:
            context.entities[entity.type.value] = entity.value
        
        # Execute action if needed
        action_result = await self._execute_action(intent, entities, context)
        
        # Generate response
        response_text = self.response_generator.generate(
            intent, entities, context, action_result
        )
        
        # Add bot response to history
        self.conversation_manager.add_message_to_history(
            context, 'bot', response_text, intent, entities
        )
        
        # Determine suggested actions
        suggested_actions = self._generate_suggested_actions(intent, entities, context)
        
        # Create response
        response = ChatResponse(
            message=response_text,
            intent=intent,
            confidence=intent_confidence,
            entities=entities,
            suggested_actions=suggested_actions,
            requires_followup=self._requires_followup(intent, entities),
            context_updated=True,
            response_type=self._determine_response_type(intent, action_result),
            metadata={
                'session_id': context.session_id,
                'processing_time': 'fast',
                'action_executed': action_result is not None
            }
        )
        
        return response
    
    async def _execute_action(self, intent: Intent, entities: List[Entity], 
                            context: ConversationContext) -> Optional[Dict[str, Any]]:
        """Execute actions based on intent and entities"""
        
        try:
            if intent == Intent.GET_PROPERTY_INFO:
                return await self._get_property_info(entities, context)
            
            elif intent == Intent.GET_OCCUPANCY_RATE:
                return await self._get_occupancy_data(entities, context)
            
            elif intent == Intent.GET_MARKET_DATA:
                return await self._get_market_data(entities, context)
            
            elif intent == Intent.SCHEDULE_MAINTENANCE:
                return await self._schedule_maintenance(entities, context)
            
            # Add more actions as needed
            
        except Exception as e:
            logger.error(f"Error executing action for {intent}: {e}")
            return None
        
        return None
    
    async def _get_property_info(self, entities: List[Entity], 
                               context: ConversationContext) -> Dict[str, Any]:
        """Get property information"""
        # Simulate property data (in production, query real database)
        property_data = {
            'address': '123 Main Street, Anytown, NY',
            'type': 'Multifamily',
            'units': 24,
            'occupancy_rate': 92.5,
            'monthly_income': 28500.00
        }
        
        return {'property_data': property_data}
    
    async def _get_occupancy_data(self, entities: List[Entity], 
                                context: ConversationContext) -> Dict[str, Any]:
        """Get occupancy data"""
        # Simulate occupancy data
        occupancy_data = {
            'total_units': 24,
            'occupied_units': 22,
            'vacant_units': 2,
            'occupancy_rate': 91.7
        }
        
        return {'occupancy_data': occupancy_data}
    
    async def _get_market_data(self, entities: List[Entity], 
                             context: ConversationContext) -> Dict[str, Any]:
        """Get market data"""
        # Import market intelligence service
        from ai_services.market_intelligence.market_data_engine import get_current_market_data
        
        # Get location from entities or use default
        location = "New York, NY"
        for entity in entities:
            if entity.type == EntityType.LOCATION:
                location = entity.value
                break
        
        try:
            market_data = await get_current_market_data(location, "single_family")
            
            # Extract key metrics
            data = market_data.get('data', [])
            result = {'location': location}
            
            for item in data:
                if item['metric'] == 'median_price':
                    result['median_price'] = item['value']
                elif item['metric'] == 'average_rent':
                    result['average_rent'] = item['value']
                elif item['metric'] == 'price_per_sqft':
                    result['price_per_sqft'] = item['value']
                elif item['metric'] == 'days_on_market':
                    result['days_on_market'] = item['value']
            
            return {'market_data': result}
            
        except Exception as e:
            logger.error(f"Error getting market data: {e}")
            # Return simulated data as fallback
            return {
                'market_data': {
                    'location': location,
                    'median_price': 450000,
                    'average_rent': 2800,
                    'price_per_sqft': 280,
                    'days_on_market': 45
                }
            }
    
    async def _schedule_maintenance(self, entities: List[Entity], 
                                  context: ConversationContext) -> Dict[str, Any]:
        """Schedule maintenance"""
        # Extract maintenance details from entities
        maintenance_type = "General"
        property_ref = "Property 1"
        scheduled_date = "Next Available"
        
        for entity in entities:
            if entity.type == EntityType.MAINTENANCE_TYPE:
                maintenance_type = entity.value.title()
            elif entity.type == EntityType.PROPERTY_ID:
                property_ref = f"Property {entity.value}"
            elif entity.type == EntityType.DATE:
                scheduled_date = entity.value
        
        return {
            'maintenance_scheduled': True,
            'maintenance_type': maintenance_type,
            'property': property_ref,
            'scheduled_date': scheduled_date,
            'priority': 'Normal'
        }
    
    def _generate_suggested_actions(self, intent: Intent, entities: List[Entity], 
                                  context: ConversationContext) -> List[Dict[str, Any]]:
        """Generate suggested follow-up actions"""
        suggestions = []
        
        if intent == Intent.GET_PROPERTY_INFO:
            suggestions.extend([
                {'text': 'View maintenance history', 'action': 'get_maintenance_history'},
                {'text': 'Check occupancy rates', 'action': 'get_occupancy_rate'},
                {'text': 'Schedule maintenance', 'action': 'schedule_maintenance'}
            ])
        
        elif intent == Intent.GET_MARKET_DATA:
            suggestions.extend([
                {'text': 'View investment opportunities', 'action': 'get_investment_opportunities'},
                {'text': 'Get competitive analysis', 'action': 'get_competitive_analysis'},
                {'text': 'Market forecast', 'action': 'get_market_forecast'}
            ])
        
        elif intent == Intent.GREETING:
            suggestions.extend([
                {'text': 'Show property overview', 'action': 'get_property_info'},
                {'text': 'Check occupancy rates', 'action': 'get_occupancy_rate'},
                {'text': 'View market data', 'action': 'get_market_data'}
            ])
        
        return suggestions
    
    def _requires_followup(self, intent: Intent, entities: List[Entity]) -> bool:
        """Determine if response requires follow-up"""
        # Intents that typically need clarification
        clarification_intents = [Intent.UNCLEAR, Intent.SCHEDULE_MAINTENANCE]
        
        # If intent needs clarification or has missing entities
        if intent in clarification_intents:
            return True
        
        if intent == Intent.SCHEDULE_MAINTENANCE:
            # Check if we have required entities
            has_property = any(e.type in [EntityType.PROPERTY_ID, EntityType.PROPERTY_ADDRESS] for e in entities)
            has_maintenance_type = any(e.type == EntityType.MAINTENANCE_TYPE for e in entities)
            return not (has_property and has_maintenance_type)
        
        return False
    
    def _determine_response_type(self, intent: Intent, action_result: Dict[str, Any]) -> str:
        """Determine the type of response"""
        if intent == Intent.UNCLEAR:
            return "clarification"
        elif action_result:
            return "action"
        elif intent in [Intent.GREETING, Intent.HELP]:
            return "text"
        else:
            return "text"

# Global instance
_chatbot = None

def get_estatecore_chatbot() -> EstateCoreChatbot:
    """Get global chatbot instance"""
    global _chatbot
    if _chatbot is None:
        _chatbot = EstateCoreChatbot()
    return _chatbot

# API convenience functions
async def process_chat_message(message: str, user_id: str, session_id: str = None) -> Dict[str, Any]:
    """Process chat message and return response"""
    chatbot = get_estatecore_chatbot()
    response = await chatbot.process_message(message, user_id, session_id)
    
    return {
        'response': response.message,
        'intent': response.intent.value,
        'confidence': response.confidence,
        'entities': [asdict(e) for e in response.entities],
        'suggested_actions': response.suggested_actions,
        'requires_followup': response.requires_followup,
        'response_type': response.response_type,
        'session_id': response.metadata.get('session_id'),
        'timestamp': datetime.now().isoformat()
    }

if __name__ == "__main__":
    # Test the chatbot
    async def test_chatbot():
        chatbot = EstateCoreChatbot()
        
        test_messages = [
            "Hello!",
            "What's the occupancy rate for my properties?",
            "Can you get me market data for New York?",
            "Schedule HVAC maintenance for property 123",
            "Show me information about property 1",
            "Help"
        ]
        
        user_id = "test_user_1"
        session_id = None
        
        print("Testing EstateCore Chatbot")
        print("=" * 50)
        
        for message in test_messages:
            print(f"\nUser: {message}")
            response = await chatbot.process_message(message, user_id, session_id)
            session_id = response.metadata['session_id']  # Maintain session
            
            print(f"Bot: {response.message}")
            print(f"Intent: {response.intent.value} (confidence: {response.confidence:.2f})")
            
            if response.entities:
                entities_str = ", ".join([f"{e.type.value}: {e.value}" for e in response.entities])
                print(f"Entities: {entities_str}")
            
            if response.suggested_actions:
                actions_str = ", ".join([a['text'] for a in response.suggested_actions])
                print(f"Suggestions: {actions_str}")
    
    asyncio.run(test_chatbot())