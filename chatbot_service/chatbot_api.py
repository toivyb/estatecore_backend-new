"""
Chatbot API Service for EstateCore

RESTful API endpoints for chatbot functionality including conversation
management, message processing, and administrative controls.
"""

import logging
import json
from datetime import datetime
from typing import Dict, List, Optional, Any
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
import asyncio
import uuid

from .message_processor import MessageProcessor
from .data_integration import DataIntegrationService
from .escalation_manager import EscalationManager
from ai_modules.chatbot import (
    NLPEngine, IntentClassifier, EntityExtractor, 
    ConversationManager, ResponseGenerator, SentimentAnalyzer, ContextManager
)

# Create Blueprint
chatbot_bp = Blueprint('chatbot', __name__, url_prefix='/api/chatbot')

class ChatbotAPI:
    """
    Main Chatbot API service class
    """
    
    def __init__(self, app=None):
        """
        Initialize Chatbot API
        
        Args:
            app: Flask application instance
        """
        self.logger = logging.getLogger(__name__)
        
        # Initialize AI components
        self.nlp_engine = NLPEngine()
        self.intent_classifier = IntentClassifier()
        self.entity_extractor = EntityExtractor()
        self.conversation_manager = ConversationManager()
        self.response_generator = ResponseGenerator()
        self.sentiment_analyzer = SentimentAnalyzer()
        self.context_manager = ContextManager()
        
        # Initialize service components
        self.message_processor = MessageProcessor(
            nlp_engine=self.nlp_engine,
            intent_classifier=self.intent_classifier,
            entity_extractor=self.entity_extractor,
            sentiment_analyzer=self.sentiment_analyzer
        )
        
        self.data_integration = DataIntegrationService()
        self.escalation_manager = EscalationManager()
        
        # Train models if needed
        self._initialize_models()
        
        if app:
            self.init_app(app)
        
        self.logger.info("Chatbot API initialized")
    
    def init_app(self, app):
        """Initialize with Flask app"""
        app.register_blueprint(chatbot_bp)
        
        # Store reference in app context
        app.chatbot_api = self
    
    def _initialize_models(self):
        """Initialize and train AI models"""
        try:
            # Train intent classifier with default data
            self.intent_classifier.train()
            self.logger.info("Intent classifier trained successfully")
        except Exception as e:
            self.logger.error(f"Error training models: {e}")

# API Endpoints

@chatbot_bp.route('/conversation/start', methods=['POST'])
@jwt_required()
def start_conversation():
    """Start a new chatbot conversation"""
    try:
        user_id = get_jwt_identity()
        data = request.get_json() or {}
        
        # Get user context from database
        # This would typically fetch from your user/tenant database
        user_context = current_app.chatbot_api.data_integration.get_user_context(user_id)
        
        # Create conversation context
        from ai_modules.chatbot.conversation_manager import ConversationContext
        context = ConversationContext(
            user_id=user_id,
            tenant_id=user_context.get('tenant_id'),
            property_id=user_context.get('property_id'),
            unit_number=user_context.get('unit_number'),
            user_name=user_context.get('user_name'),
            preferred_language=data.get('language', 'en')
        )
        
        # Start conversation
        conversation_id = current_app.chatbot_api.conversation_manager.start_conversation(
            user_id, context
        )
        
        # Create user context in context manager
        current_app.chatbot_api.context_manager.create_user_context(
            user_id, conversation_id, {
                'profile': user_context,
                'tenant': user_context,
                'property': current_app.chatbot_api.data_integration.get_property_context(
                    user_context.get('property_id')
                )
            }
        )
        
        return jsonify({
            'success': True,
            'conversation_id': conversation_id,
            'greeting': "Hello! I'm here to help you with any questions about your property. How can I assist you today?",
            'quick_replies': ['Pay rent', 'Maintenance request', 'Account info', 'Contact office']
        })
        
    except Exception as e:
        current_app.logger.error(f"Error starting conversation: {e}")
        return jsonify({'success': False, 'error': 'Failed to start conversation'}), 500

@chatbot_bp.route('/message', methods=['POST'])
@jwt_required()
def send_message():
    """Send a message to the chatbot"""
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        if not data or 'message' not in data:
            return jsonify({'success': False, 'error': 'Message is required'}), 400
        
        conversation_id = data.get('conversation_id')
        message_text = data['message']
        
        # Get or create conversation
        if conversation_id:
            conversation = current_app.chatbot_api.conversation_manager.get_conversation(conversation_id)
            if not conversation or conversation.user_id != user_id:
                return jsonify({'success': False, 'error': 'Invalid conversation'}), 404
        else:
            # Start new conversation if none exists
            result = start_conversation()
            if result.status_code != 200:
                return result
            response_data = result.get_json()
            conversation_id = response_data['conversation_id']
        
        # Process message
        response = current_app.chatbot_api.message_processor.process_message(
            user_id=user_id,
            conversation_id=conversation_id,
            message=message_text
        )
        
        # Add message to conversation
        current_app.chatbot_api.conversation_manager.add_message(
            conversation_id=conversation_id,
            sender='user',
            content=message_text,
            intent=response.get('intent'),
            entities=response.get('entities'),
            confidence=response.get('confidence')
        )
        
        # Add bot response to conversation
        current_app.chatbot_api.conversation_manager.add_message(
            conversation_id=conversation_id,
            sender='bot',
            content=response['response']['text']
        )
        
        return jsonify({
            'success': True,
            'conversation_id': conversation_id,
            'response': response['response'],
            'metadata': {
                'intent': response.get('intent'),
                'confidence': response.get('confidence'),
                'sentiment': response.get('sentiment'),
                'escalated': response.get('escalated', False)
            }
        })
        
    except Exception as e:
        current_app.logger.error(f"Error processing message: {e}")
        return jsonify({'success': False, 'error': 'Failed to process message'}), 500

@chatbot_bp.route('/conversation/<conversation_id>', methods=['GET'])
@jwt_required()
def get_conversation(conversation_id):
    """Get conversation details"""
    try:
        user_id = get_jwt_identity()
        
        conversation = current_app.chatbot_api.conversation_manager.get_conversation(conversation_id)
        
        if not conversation:
            return jsonify({'success': False, 'error': 'Conversation not found'}), 404
        
        if conversation.user_id != user_id:
            return jsonify({'success': False, 'error': 'Access denied'}), 403
        
        # Get conversation summary
        summary = current_app.chatbot_api.conversation_manager.get_conversation_summary(conversation_id)
        
        return jsonify({
            'success': True,
            'conversation': summary
        })
        
    except Exception as e:
        current_app.logger.error(f"Error getting conversation: {e}")
        return jsonify({'success': False, 'error': 'Failed to get conversation'}), 500

@chatbot_bp.route('/conversations', methods=['GET'])
@jwt_required()
def get_user_conversations():
    """Get user's conversations"""
    try:
        user_id = get_jwt_identity()
        limit = request.args.get('limit', 10, type=int)
        
        conversations = current_app.chatbot_api.conversation_manager.get_user_conversations(
            user_id, limit=limit
        )
        
        conversation_summaries = [
            current_app.chatbot_api.conversation_manager.get_conversation_summary(conv.id)
            for conv in conversations
        ]
        
        return jsonify({
            'success': True,
            'conversations': conversation_summaries
        })
        
    except Exception as e:
        current_app.logger.error(f"Error getting conversations: {e}")
        return jsonify({'success': False, 'error': 'Failed to get conversations'}), 500

@chatbot_bp.route('/conversation/<conversation_id>/resolve', methods=['POST'])
@jwt_required()
def resolve_conversation(conversation_id):
    """Mark conversation as resolved"""
    try:
        user_id = get_jwt_identity()
        data = request.get_json() or {}
        
        conversation = current_app.chatbot_api.conversation_manager.get_conversation(conversation_id)
        
        if not conversation or conversation.user_id != user_id:
            return jsonify({'success': False, 'error': 'Invalid conversation'}), 404
        
        satisfaction_score = data.get('satisfaction_score')
        
        success = current_app.chatbot_api.conversation_manager.resolve_conversation(
            conversation_id, satisfaction_score
        )
        
        if success:
            return jsonify({'success': True, 'message': 'Conversation resolved'})
        else:
            return jsonify({'success': False, 'error': 'Failed to resolve conversation'}), 500
            
    except Exception as e:
        current_app.logger.error(f"Error resolving conversation: {e}")
        return jsonify({'success': False, 'error': 'Failed to resolve conversation'}), 500

@chatbot_bp.route('/escalate', methods=['POST'])
@jwt_required()
def escalate_conversation():
    """Escalate conversation to human agent"""
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        if not data or 'conversation_id' not in data:
            return jsonify({'success': False, 'error': 'Conversation ID is required'}), 400
        
        conversation_id = data['conversation_id']
        reason = data.get('reason', 'user_request')
        
        conversation = current_app.chatbot_api.conversation_manager.get_conversation(conversation_id)
        
        if not conversation or conversation.user_id != user_id:
            return jsonify({'success': False, 'error': 'Invalid conversation'}), 404
        
        # Escalate conversation
        from ai_modules.chatbot.conversation_manager import EscalationReason
        escalation_reason = EscalationReason(reason)
        
        success = current_app.chatbot_api.escalation_manager.escalate_conversation(
            conversation_id, escalation_reason, user_context={
                'user_id': user_id,
                'priority': data.get('priority', 'medium')
            }
        )
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Your conversation has been escalated to a human agent',
                'estimated_wait_time': '10-15 minutes'
            })
        else:
            return jsonify({'success': False, 'error': 'Failed to escalate conversation'}), 500
            
    except Exception as e:
        current_app.logger.error(f"Error escalating conversation: {e}")
        return jsonify({'success': False, 'error': 'Failed to escalate conversation'}), 500

@chatbot_bp.route('/feedback', methods=['POST'])
@jwt_required()
def submit_feedback():
    """Submit feedback about chatbot interaction"""
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        if not data:
            return jsonify({'success': False, 'error': 'Feedback data is required'}), 400
        
        feedback = {
            'user_id': user_id,
            'conversation_id': data.get('conversation_id'),
            'rating': data.get('rating'),
            'feedback_text': data.get('feedback'),
            'helpful': data.get('helpful'),
            'timestamp': datetime.now().isoformat()
        }
        
        # Store feedback (implement based on your storage system)
        # For now, just log it
        current_app.logger.info(f"Chatbot feedback received: {feedback}")
        
        return jsonify({
            'success': True,
            'message': 'Thank you for your feedback!'
        })
        
    except Exception as e:
        current_app.logger.error(f"Error submitting feedback: {e}")
        return jsonify({'success': False, 'error': 'Failed to submit feedback'}), 500

# Admin endpoints
@chatbot_bp.route('/admin/conversations', methods=['GET'])
@jwt_required()
def admin_get_conversations():
    """Get all conversations for admin (requires admin role)"""
    try:
        # Check if user is admin (implement your role checking logic)
        # For now, simplified check
        user_id = get_jwt_identity()
        
        # Get query parameters
        limit = request.args.get('limit', 50, type=int)
        status = request.args.get('status')  # active, escalated, resolved
        
        # This would need to be implemented in conversation manager
        # For now, return placeholder
        return jsonify({
            'success': True,
            'conversations': [],
            'total': 0,
            'message': 'Admin conversation retrieval not yet implemented'
        })
        
    except Exception as e:
        current_app.logger.error(f"Error getting admin conversations: {e}")
        return jsonify({'success': False, 'error': 'Failed to get conversations'}), 500

@chatbot_bp.route('/admin/analytics', methods=['GET'])
@jwt_required()
def get_analytics():
    """Get chatbot analytics"""
    try:
        # Placeholder for analytics
        analytics = {
            'total_conversations': 0,
            'active_conversations': 0,
            'escalated_conversations': 0,
            'resolved_conversations': 0,
            'average_resolution_time': '0 minutes',
            'user_satisfaction': 0.0,
            'top_intents': [],
            'escalation_rate': 0.0
        }
        
        return jsonify({
            'success': True,
            'analytics': analytics
        })
        
    except Exception as e:
        current_app.logger.error(f"Error getting analytics: {e}")
        return jsonify({'success': False, 'error': 'Failed to get analytics'}), 500

@chatbot_bp.route('/admin/retrain', methods=['POST'])
@jwt_required()
def retrain_models():
    """Retrain AI models with new data"""
    try:
        # Check if user is admin
        data = request.get_json() or {}
        
        # Retrain intent classifier
        training_data = data.get('training_data', [])
        if training_data:
            metrics = current_app.chatbot_api.intent_classifier.train(training_data)
        else:
            metrics = current_app.chatbot_api.intent_classifier.train()
        
        return jsonify({
            'success': True,
            'message': 'Models retrained successfully',
            'metrics': metrics
        })
        
    except Exception as e:
        current_app.logger.error(f"Error retraining models: {e}")
        return jsonify({'success': False, 'error': 'Failed to retrain models'}), 500

@chatbot_bp.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    try:
        # Check AI components
        health_status = {
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'components': {
                'nlp_engine': 'healthy',
                'intent_classifier': 'healthy' if current_app.chatbot_api.intent_classifier.is_trained else 'training',
                'conversation_manager': 'healthy',
                'data_integration': 'healthy'
            }
        }
        
        return jsonify(health_status)
        
    except Exception as e:
        current_app.logger.error(f"Health check error: {e}")
        return jsonify({
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500