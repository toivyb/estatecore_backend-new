"""
WebSocket Handler for EstateCore Tenant Chatbot

Handles real-time WebSocket connections for the chatbot,
providing instant messaging capabilities and live conversation updates.
"""

import logging
import json
import asyncio
from datetime import datetime
from typing import Dict, List, Optional, Any, Set
from flask_socketio import SocketIO, emit, join_room, leave_room, rooms
from flask_jwt_extended import decode_token, get_jwt_identity
import uuid

from .message_processor import MessageProcessor, ProcessingResult

class WebSocketHandler:
    """
    WebSocket handler for real-time chatbot communication
    """
    
    def __init__(self, socketio: SocketIO, message_processor: MessageProcessor):
        """
        Initialize WebSocket Handler
        
        Args:
            socketio: Flask-SocketIO instance
            message_processor: Message processing system
        """
        self.logger = logging.getLogger(__name__)
        self.socketio = socketio
        self.message_processor = message_processor
        
        # Connection management
        self.active_connections: Dict[str, Dict] = {}  # session_id -> connection_info
        self.user_sessions: Dict[str, Set[str]] = {}  # user_id -> set of session_ids
        self.conversation_rooms: Dict[str, Set[str]] = {}  # conversation_id -> set of session_ids
        
        # Typing indicators
        self.typing_users: Dict[str, Dict] = {}  # conversation_id -> {user_id: timestamp}
        
        # Configuration
        self.max_connections_per_user = 3
        self.typing_timeout = 5.0  # seconds
        self.connection_timeout = 300.0  # 5 minutes
        
        # Register event handlers
        self._register_handlers()
        
        self.logger.info("WebSocket Handler initialized")
    
    def _register_handlers(self):
        """Register SocketIO event handlers"""
        
        @self.socketio.on('connect')
        def handle_connect(auth):
            """Handle client connection"""
            try:
                session_id = self._generate_session_id()
                
                # Authenticate user
                user_id = self._authenticate_connection(auth)
                if not user_id:
                    self.logger.warning("Unauthorized WebSocket connection attempt")
                    return False  # Reject connection
                
                # Store connection info
                connection_info = {
                    'user_id': user_id,
                    'session_id': session_id,
                    'connected_at': datetime.now(),
                    'last_activity': datetime.now(),
                    'conversation_id': None
                }
                
                self.active_connections[session_id] = connection_info
                
                # Add to user sessions
                if user_id not in self.user_sessions:
                    self.user_sessions[user_id] = set()
                self.user_sessions[user_id].add(session_id)
                
                # Check connection limits
                if len(self.user_sessions[user_id]) > self.max_connections_per_user:
                    # Remove oldest connection
                    oldest_session = min(
                        self.user_sessions[user_id],
                        key=lambda sid: self.active_connections.get(sid, {}).get('connected_at', datetime.now())
                    )
                    self._disconnect_session(oldest_session)
                
                self.logger.info(f"WebSocket connected: user_id={user_id}, session_id={session_id}")
                
                # Send connection confirmation
                emit('connected', {
                    'session_id': session_id,
                    'status': 'connected',
                    'message': 'Connected to EstateCore chatbot'
                })
                
            except Exception as e:
                self.logger.error(f"Error in connect handler: {e}")
                return False
        
        @self.socketio.on('disconnect')
        def handle_disconnect():
            """Handle client disconnection"""
            try:
                session_id = self._get_current_session_id()
                if session_id:
                    self._disconnect_session(session_id)
                    self.logger.info(f"WebSocket disconnected: session_id={session_id}")
                    
            except Exception as e:
                self.logger.error(f"Error in disconnect handler: {e}")
        
        @self.socketio.on('join_conversation')
        def handle_join_conversation(data):
            """Handle joining a conversation room"""
            try:
                session_id = self._get_current_session_id()
                connection = self.active_connections.get(session_id)
                
                if not connection:
                    emit('error', {'message': 'Invalid session'})
                    return
                
                conversation_id = data.get('conversation_id')
                if not conversation_id:
                    emit('error', {'message': 'Conversation ID required'})
                    return
                
                # Validate conversation access
                if not self._validate_conversation_access(connection['user_id'], conversation_id):
                    emit('error', {'message': 'Access denied to conversation'})
                    return
                
                # Leave previous conversation room
                if connection['conversation_id']:
                    leave_room(f"conv_{connection['conversation_id']}")
                    self._remove_from_conversation_room(connection['conversation_id'], session_id)
                
                # Join new conversation room
                room_name = f"conv_{conversation_id}"
                join_room(room_name)
                
                # Update connection info
                connection['conversation_id'] = conversation_id
                connection['last_activity'] = datetime.now()
                
                # Add to conversation room tracking
                if conversation_id not in self.conversation_rooms:
                    self.conversation_rooms[conversation_id] = set()
                self.conversation_rooms[conversation_id].add(session_id)
                
                emit('joined_conversation', {
                    'conversation_id': conversation_id,
                    'status': 'joined'
                })
                
                self.logger.debug(f"User joined conversation: user_id={connection['user_id']}, conversation_id={conversation_id}")
                
            except Exception as e:
                self.logger.error(f"Error in join_conversation handler: {e}")
                emit('error', {'message': 'Failed to join conversation'})
        
        @self.socketio.on('send_message')
        def handle_send_message(data):
            """Handle sending a message"""
            try:
                session_id = self._get_current_session_id()
                connection = self.active_connections.get(session_id)
                
                if not connection:
                    emit('error', {'message': 'Invalid session'})
                    return
                
                message_text = data.get('message', '').strip()
                if not message_text:
                    emit('error', {'message': 'Message cannot be empty'})
                    return
                
                conversation_id = connection['conversation_id']
                if not conversation_id:
                    emit('error', {'message': 'No active conversation'})
                    return
                
                # Update activity
                connection['last_activity'] = datetime.now()
                
                # Show typing indicator stopped
                self._stop_typing(conversation_id, connection['user_id'])
                
                # Echo message to conversation room
                self.socketio.emit('message', {
                    'message_id': str(uuid.uuid4()),
                    'conversation_id': conversation_id,
                    'sender': 'user',
                    'content': message_text,
                    'timestamp': datetime.now().isoformat(),
                    'user_id': connection['user_id']
                }, room=f"conv_{conversation_id}")
                
                # Process message asynchronously
                asyncio.create_task(self._process_message_async(
                    connection['user_id'], conversation_id, message_text, session_id
                ))
                
            except Exception as e:
                self.logger.error(f"Error in send_message handler: {e}")
                emit('error', {'message': 'Failed to send message'})
        
        @self.socketio.on('typing_start')
        def handle_typing_start(data):
            """Handle typing indicator start"""
            try:
                session_id = self._get_current_session_id()
                connection = self.active_connections.get(session_id)
                
                if not connection or not connection['conversation_id']:
                    return
                
                conversation_id = connection['conversation_id']
                user_id = connection['user_id']
                
                # Track typing
                if conversation_id not in self.typing_users:
                    self.typing_users[conversation_id] = {}
                
                self.typing_users[conversation_id][user_id] = datetime.now()
                
                # Broadcast typing indicator to conversation room
                self.socketio.emit('typing_indicator', {
                    'conversation_id': conversation_id,
                    'user_id': user_id,
                    'typing': True
                }, room=f"conv_{conversation_id}", include_self=False)
                
            except Exception as e:
                self.logger.error(f"Error in typing_start handler: {e}")
        
        @self.socketio.on('typing_stop')
        def handle_typing_stop(data):
            """Handle typing indicator stop"""
            try:
                session_id = self._get_current_session_id()
                connection = self.active_connections.get(session_id)
                
                if not connection or not connection['conversation_id']:
                    return
                
                conversation_id = connection['conversation_id']
                user_id = connection['user_id']
                
                self._stop_typing(conversation_id, user_id)
                
            except Exception as e:
                self.logger.error(f"Error in typing_stop handler: {e}")
        
        @self.socketio.on('get_status')
        def handle_get_status():
            """Handle status request"""
            try:
                session_id = self._get_current_session_id()
                connection = self.active_connections.get(session_id)
                
                if not connection:
                    emit('error', {'message': 'Invalid session'})
                    return
                
                status = {
                    'session_id': session_id,
                    'user_id': connection['user_id'],
                    'conversation_id': connection['conversation_id'],
                    'connected_at': connection['connected_at'].isoformat(),
                    'last_activity': connection['last_activity'].isoformat(),
                    'status': 'active'
                }
                
                emit('status', status)
                
            except Exception as e:
                self.logger.error(f"Error in get_status handler: {e}")
                emit('error', {'message': 'Failed to get status'})
    
    async def _process_message_async(self, user_id: str, conversation_id: str,
                                    message: str, session_id: str):
        """Process message asynchronously and send response"""
        try:
            # Show bot typing indicator
            self.socketio.emit('typing_indicator', {
                'conversation_id': conversation_id,
                'user_id': 'bot',
                'typing': True
            }, room=f"conv_{conversation_id}")
            
            # Process message
            result = await self.message_processor.process_message_async(
                user_id, conversation_id, message
            )
            
            # Stop bot typing indicator
            self.socketio.emit('typing_indicator', {
                'conversation_id': conversation_id,
                'user_id': 'bot',
                'typing': False
            }, room=f"conv_{conversation_id}")
            
            # Send bot response
            bot_response = {
                'message_id': str(uuid.uuid4()),
                'conversation_id': conversation_id,
                'sender': 'bot',
                'content': result.response['text'],
                'response_type': result.response['type'],
                'quick_replies': result.response.get('quick_replies'),
                'data': result.response.get('data'),
                'timestamp': datetime.now().isoformat(),
                'metadata': {
                    'intent': result.intent,
                    'confidence': result.confidence,
                    'sentiment': result.sentiment['label'],
                    'processing_time_ms': result.processing_time_ms,
                    'escalated': result.escalated
                }
            }
            
            self.socketio.emit('message', bot_response, room=f"conv_{conversation_id}")
            
            # Send escalation notification if needed
            if result.escalated:
                self.socketio.emit('escalation_notice', {
                    'conversation_id': conversation_id,
                    'message': 'Your conversation has been escalated to a human agent',
                    'estimated_wait_time': '10-15 minutes'
                }, room=f"conv_{conversation_id}")
            
        except Exception as e:
            self.logger.error(f"Error processing message asynchronously: {e}")
            
            # Send error response
            error_response = {
                'message_id': str(uuid.uuid4()),
                'conversation_id': conversation_id,
                'sender': 'bot',
                'content': 'I apologize, but I encountered an error processing your message. Please try again.',
                'response_type': 'text',
                'timestamp': datetime.now().isoformat(),
                'error': True
            }
            
            self.socketio.emit('message', error_response, room=f"conv_{conversation_id}")
    
    def _authenticate_connection(self, auth: Dict) -> Optional[str]:
        """Authenticate WebSocket connection"""
        try:
            if not auth or 'token' not in auth:
                return None
            
            token = auth['token']
            
            # Decode JWT token
            decoded_token = decode_token(token)
            user_id = decoded_token.get('sub')  # Subject contains user ID
            
            return user_id
            
        except Exception as e:
            self.logger.error(f"Authentication error: {e}")
            return None
    
    def _validate_conversation_access(self, user_id: str, conversation_id: str) -> bool:
        """Validate if user has access to conversation"""
        # This should check against your database/conversation manager
        # For now, simplified validation
        try:
            if hasattr(self.message_processor, 'conversation_manager'):
                conversation = self.message_processor.conversation_manager.get_conversation(conversation_id)
                return conversation and conversation.user_id == user_id
            return True  # Allow access if no conversation manager
        except:
            return False
    
    def _generate_session_id(self) -> str:
        """Generate unique session ID"""
        return str(uuid.uuid4())
    
    def _get_current_session_id(self) -> Optional[str]:
        """Get session ID for current request"""
        # This is a simplified approach - in production you'd track this properly
        for session_id, connection in self.active_connections.items():
            # You'd need to track which session is making the current request
            # For now, return any active session (this is not production-ready)
            pass
        return None
    
    def _disconnect_session(self, session_id: str):
        """Disconnect a specific session"""
        try:
            connection = self.active_connections.get(session_id)
            if not connection:
                return
            
            user_id = connection['user_id']
            conversation_id = connection['conversation_id']
            
            # Remove from conversation room
            if conversation_id:
                self._remove_from_conversation_room(conversation_id, session_id)
            
            # Remove from user sessions
            if user_id in self.user_sessions:
                self.user_sessions[user_id].discard(session_id)
                if not self.user_sessions[user_id]:
                    del self.user_sessions[user_id]
            
            # Remove connection
            del self.active_connections[session_id]
            
        except Exception as e:
            self.logger.error(f"Error disconnecting session {session_id}: {e}")
    
    def _remove_from_conversation_room(self, conversation_id: str, session_id: str):
        """Remove session from conversation room"""
        if conversation_id in self.conversation_rooms:
            self.conversation_rooms[conversation_id].discard(session_id)
            if not self.conversation_rooms[conversation_id]:
                del self.conversation_rooms[conversation_id]
    
    def _stop_typing(self, conversation_id: str, user_id: str):
        """Stop typing indicator for user"""
        if conversation_id in self.typing_users:
            if user_id in self.typing_users[conversation_id]:
                del self.typing_users[conversation_id][user_id]
            
            if not self.typing_users[conversation_id]:
                del self.typing_users[conversation_id]
        
        # Broadcast typing stopped
        self.socketio.emit('typing_indicator', {
            'conversation_id': conversation_id,
            'user_id': user_id,
            'typing': False
        }, room=f"conv_{conversation_id}", include_self=False)
    
    def cleanup_expired_typing(self):
        """Clean up expired typing indicators"""
        current_time = datetime.now()
        
        for conversation_id, users in list(self.typing_users.items()):
            for user_id, start_time in list(users.items()):
                if (current_time - start_time).total_seconds() > self.typing_timeout:
                    self._stop_typing(conversation_id, user_id)
    
    def cleanup_inactive_connections(self):
        """Clean up inactive connections"""
        current_time = datetime.now()
        
        for session_id, connection in list(self.active_connections.items()):
            time_since_activity = (current_time - connection['last_activity']).total_seconds()
            
            if time_since_activity > self.connection_timeout:
                self.logger.info(f"Cleaning up inactive connection: {session_id}")
                self._disconnect_session(session_id)
    
    def get_connection_stats(self) -> Dict[str, Any]:
        """Get WebSocket connection statistics"""
        return {
            'active_connections': len(self.active_connections),
            'active_users': len(self.user_sessions),
            'active_conversations': len(self.conversation_rooms),
            'typing_users': sum(len(users) for users in self.typing_users.values())
        }
    
    def broadcast_admin_message(self, message: str, conversation_id: Optional[str] = None):
        """Broadcast admin message to conversations"""
        try:
            admin_message = {
                'message_id': str(uuid.uuid4()),
                'sender': 'admin',
                'content': message,
                'response_type': 'announcement',
                'timestamp': datetime.now().isoformat()
            }
            
            if conversation_id:
                # Send to specific conversation
                admin_message['conversation_id'] = conversation_id
                self.socketio.emit('message', admin_message, room=f"conv_{conversation_id}")
            else:
                # Broadcast to all active conversations
                for conv_id in self.conversation_rooms.keys():
                    admin_message['conversation_id'] = conv_id
                    self.socketio.emit('message', admin_message, room=f"conv_{conv_id}")
            
            self.logger.info(f"Admin message broadcast: {message}")
            
        except Exception as e:
            self.logger.error(f"Error broadcasting admin message: {e}")