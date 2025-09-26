"""
EstateCore AI-Powered Tenant Chatbot Service

Comprehensive chatbot service providing 24/7 automated tenant support
with AI/ML capabilities and property management system integration.
"""

from .chatbot_api import ChatbotAPI
from .websocket_handler import WebSocketHandler
from .message_processor import MessageProcessor
from .data_integration import DataIntegrationService
from .escalation_manager import EscalationManager

__all__ = [
    'ChatbotAPI',
    'WebSocketHandler', 
    'MessageProcessor',
    'DataIntegrationService',
    'EscalationManager'
]