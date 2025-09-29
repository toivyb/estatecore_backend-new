#!/usr/bin/env python3
"""
Real-time Team Messaging System for EstateCore Phase 8B
Slack-like team communication with channels, direct messages, and file sharing
"""

import os
import json
import asyncio
import logging
import sqlite3
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass, asdict
from enum import Enum
import uuid
import hashlib
import base64
from collections import defaultdict, deque

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MessageType(Enum):
    TEXT = "text"
    FILE = "file"
    IMAGE = "image"
    SYSTEM = "system"
    THREAD_REPLY = "thread_reply"
    EMOJI_REACTION = "emoji_reaction"
    CODE_SNIPPET = "code_snippet"
    POLL = "poll"

class ChannelType(Enum):
    PUBLIC = "public"
    PRIVATE = "private"
    DIRECT_MESSAGE = "direct_message"
    PROPERTY_CHANNEL = "property_channel"
    PROJECT_CHANNEL = "project_channel"

class UserStatus(Enum):
    ONLINE = "online"
    AWAY = "away"
    BUSY = "busy"
    OFFLINE = "offline"

class NotificationType(Enum):
    MENTION = "mention"
    DIRECT_MESSAGE = "direct_message"
    CHANNEL_MESSAGE = "channel_message"
    FILE_SHARED = "file_shared"
    THREAD_REPLY = "thread_reply"

@dataclass
class User:
    """Team user information"""
    user_id: str
    username: str
    display_name: str
    email: str
    avatar_url: str
    status: UserStatus
    role: str
    department: str
    timezone: str
    last_seen: datetime
    is_admin: bool
    preferences: Dict[str, Any]

@dataclass
class Channel:
    """Communication channel"""
    channel_id: str
    name: str
    description: str
    type: ChannelType
    created_by: str
    created_at: datetime
    members: List[str]
    admins: List[str]
    is_archived: bool
    topic: str
    purpose: str
    settings: Dict[str, Any]
    property_id: Optional[str]
    project_id: Optional[str]

@dataclass
class Message:
    """Chat message"""
    message_id: str
    channel_id: str
    user_id: str
    content: str
    message_type: MessageType
    timestamp: datetime
    edited_at: Optional[datetime]
    thread_id: Optional[str]
    parent_message_id: Optional[str]
    attachments: List[Dict[str, Any]]
    reactions: Dict[str, List[str]]  # emoji -> list of user_ids
    mentions: List[str]
    metadata: Dict[str, Any]
    is_pinned: bool
    is_deleted: bool

@dataclass
class FileAttachment:
    """File attachment"""
    file_id: str
    filename: str
    file_type: str
    file_size: int
    upload_url: str
    thumbnail_url: Optional[str]
    uploaded_by: str
    uploaded_at: datetime
    mime_type: str
    checksum: str

@dataclass
class Notification:
    """User notification"""
    notification_id: str
    user_id: str
    type: NotificationType
    title: str
    message: str
    channel_id: Optional[str]
    message_id: Optional[str]
    from_user_id: Optional[str]
    created_at: datetime
    read_at: Optional[datetime]
    metadata: Dict[str, Any]

class TeamMessagingService:
    """Real-time team messaging service"""
    
    def __init__(self, database_path: str = "team_messaging.db"):
        self.database_path = database_path
        self.active_connections: Dict[str, Set[Any]] = defaultdict(set)  # user_id -> websocket connections
        self.user_sessions: Dict[str, Dict[str, Any]] = {}  # user_id -> session data
        self.typing_indicators: Dict[str, Dict[str, datetime]] = defaultdict(dict)  # channel_id -> {user_id: timestamp}
        self.message_cache: Dict[str, deque] = defaultdict(lambda: deque(maxlen=100))  # channel_id -> recent messages
        
        # Initialize database
        self._initialize_database()
        
        # Load default channels and users
        self._load_default_data()
        
        logger.info("Team Messaging Service initialized")
    
    def _initialize_database(self):
        """Initialize messaging database"""
        conn = sqlite3.connect(self.database_path)
        cursor = conn.cursor()
        
        # Users table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id TEXT PRIMARY KEY,
                username TEXT UNIQUE NOT NULL,
                display_name TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                avatar_url TEXT,
                status TEXT DEFAULT 'offline',
                role TEXT,
                department TEXT,
                timezone TEXT DEFAULT 'UTC',
                last_seen TEXT,
                is_admin BOOLEAN DEFAULT 0,
                preferences TEXT,
                created_at TEXT NOT NULL
            )
        """)
        
        # Channels table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS channels (
                channel_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT,
                type TEXT NOT NULL,
                created_by TEXT NOT NULL,
                created_at TEXT NOT NULL,
                members TEXT,
                admins TEXT,
                is_archived BOOLEAN DEFAULT 0,
                topic TEXT,
                purpose TEXT,
                settings TEXT,
                property_id TEXT,
                project_id TEXT,
                FOREIGN KEY (created_by) REFERENCES users (user_id)
            )
        """)
        
        # Messages table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                message_id TEXT PRIMARY KEY,
                channel_id TEXT NOT NULL,
                user_id TEXT NOT NULL,
                content TEXT NOT NULL,
                message_type TEXT DEFAULT 'text',
                timestamp TEXT NOT NULL,
                edited_at TEXT,
                thread_id TEXT,
                parent_message_id TEXT,
                attachments TEXT,
                reactions TEXT,
                mentions TEXT,
                metadata TEXT,
                is_pinned BOOLEAN DEFAULT 0,
                is_deleted BOOLEAN DEFAULT 0,
                FOREIGN KEY (channel_id) REFERENCES channels (channel_id),
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        """)
        
        # File attachments table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS file_attachments (
                file_id TEXT PRIMARY KEY,
                filename TEXT NOT NULL,
                file_type TEXT,
                file_size INTEGER,
                upload_url TEXT NOT NULL,
                thumbnail_url TEXT,
                uploaded_by TEXT NOT NULL,
                uploaded_at TEXT NOT NULL,
                mime_type TEXT,
                checksum TEXT,
                FOREIGN KEY (uploaded_by) REFERENCES users (user_id)
            )
        """)
        
        # Notifications table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS notifications (
                notification_id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                type TEXT NOT NULL,
                title TEXT NOT NULL,
                message TEXT NOT NULL,
                channel_id TEXT,
                message_id TEXT,
                from_user_id TEXT,
                created_at TEXT NOT NULL,
                read_at TEXT,
                metadata TEXT,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        """)
        
        # Create indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_messages_channel_timestamp ON messages (channel_id, timestamp)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_messages_thread ON messages (thread_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_notifications_user ON notifications (user_id, created_at)")
        
        conn.commit()
        conn.close()
    
    def _load_default_data(self):
        """Load default users and channels"""
        # Create default users
        default_users = [
            User(
                user_id="admin_001",
                username="admin",
                display_name="System Administrator",
                email="admin@estatecore.com",
                avatar_url="/avatars/admin.png",
                status=UserStatus.ONLINE,
                role="administrator",
                department="IT",
                timezone="UTC",
                last_seen=datetime.now(),
                is_admin=True,
                preferences={"notifications": True, "theme": "light"}
            ),
            User(
                user_id="manager_001",
                username="pmanager",
                display_name="Property Manager",
                email="manager@estatecore.com",
                avatar_url="/avatars/manager.png",
                status=UserStatus.ONLINE,
                role="property_manager",
                department="Operations",
                timezone="UTC",
                last_seen=datetime.now(),
                is_admin=False,
                preferences={"notifications": True, "theme": "light"}
            )
        ]
        
        # Create default channels
        default_channels = [
            Channel(
                channel_id="general",
                name="general",
                description="General team discussions",
                type=ChannelType.PUBLIC,
                created_by="admin_001",
                created_at=datetime.now(),
                members=["admin_001", "manager_001"],
                admins=["admin_001"],
                is_archived=False,
                topic="Welcome to EstateCore team chat!",
                purpose="General team communication",
                settings={"allow_threads": True, "allow_reactions": True},
                property_id=None,
                project_id=None
            ),
            Channel(
                channel_id="maintenance",
                name="maintenance",
                description="Maintenance team coordination",
                type=ChannelType.PUBLIC,
                created_by="admin_001",
                created_at=datetime.now(),
                members=["admin_001", "manager_001"],
                admins=["admin_001"],
                is_archived=False,
                topic="Maintenance requests and updates",
                purpose="Coordinate maintenance activities",
                settings={"allow_threads": True, "allow_reactions": True},
                property_id=None,
                project_id=None
            )
        ]
        
        # Save to database
        for user in default_users:
            self._save_user(user)
        
        for channel in default_channels:
            self._save_channel(channel)
    
    async def send_message(self, channel_id: str, user_id: str, content: str, 
                          message_type: MessageType = MessageType.TEXT,
                          thread_id: Optional[str] = None,
                          attachments: List[Dict[str, Any]] = None) -> Message:
        """Send message to channel"""
        try:
            message_id = str(uuid.uuid4())
            timestamp = datetime.now()
            
            # Extract mentions
            mentions = self._extract_mentions(content)
            
            # Create message
            message = Message(
                message_id=message_id,
                channel_id=channel_id,
                user_id=user_id,
                content=content,
                message_type=message_type,
                timestamp=timestamp,
                edited_at=None,
                thread_id=thread_id,
                parent_message_id=None,
                attachments=attachments or [],
                reactions={},
                mentions=mentions,
                metadata={},
                is_pinned=False,
                is_deleted=False
            )
            
            # Save to database
            await self._save_message(message)
            
            # Add to cache
            self.message_cache[channel_id].append(message)
            
            # Send real-time notifications
            await self._broadcast_message(message)
            
            # Create notifications for mentions
            if mentions:
                await self._create_mention_notifications(message, mentions)
            
            logger.info(f"Message sent: {message_id} in channel {channel_id}")
            return message
            
        except Exception as e:
            logger.error(f"Failed to send message: {e}")
            raise
    
    async def edit_message(self, message_id: str, user_id: str, new_content: str) -> Message:
        """Edit existing message"""
        try:
            # Get existing message
            message = await self._get_message(message_id)
            if not message:
                raise ValueError("Message not found")
            
            if message.user_id != user_id:
                raise ValueError("Can only edit your own messages")
            
            # Update message
            message.content = new_content
            message.edited_at = datetime.now()
            message.mentions = self._extract_mentions(new_content)
            
            # Save to database
            await self._save_message(message)
            
            # Broadcast update
            await self._broadcast_message_update(message)
            
            return message
            
        except Exception as e:
            logger.error(f"Failed to edit message: {e}")
            raise
    
    async def add_reaction(self, message_id: str, user_id: str, emoji: str) -> Message:
        """Add emoji reaction to message"""
        try:
            message = await self._get_message(message_id)
            if not message:
                raise ValueError("Message not found")
            
            # Add reaction
            if emoji not in message.reactions:
                message.reactions[emoji] = []
            
            if user_id not in message.reactions[emoji]:
                message.reactions[emoji].append(user_id)
            
            # Save to database
            await self._save_message(message)
            
            # Broadcast reaction update
            await self._broadcast_reaction_update(message, emoji, user_id, "add")
            
            return message
            
        except Exception as e:
            logger.error(f"Failed to add reaction: {e}")
            raise
    
    async def create_channel(self, name: str, description: str, channel_type: ChannelType,
                           created_by: str, members: List[str] = None,
                           property_id: Optional[str] = None,
                           project_id: Optional[str] = None) -> Channel:
        """Create new channel"""
        try:
            channel_id = str(uuid.uuid4())
            
            channel = Channel(
                channel_id=channel_id,
                name=name,
                description=description,
                type=channel_type,
                created_by=created_by,
                created_at=datetime.now(),
                members=members or [created_by],
                admins=[created_by],
                is_archived=False,
                topic="",
                purpose=description,
                settings={"allow_threads": True, "allow_reactions": True},
                property_id=property_id,
                project_id=project_id
            )
            
            # Save to database
            await self._save_channel(channel)
            
            # Send system message
            await self.send_message(
                channel_id=channel_id,
                user_id="system",
                content=f"Channel '{name}' created by {created_by}",
                message_type=MessageType.SYSTEM
            )
            
            # Notify members
            await self._notify_channel_created(channel)
            
            logger.info(f"Channel created: {channel_id}")
            return channel
            
        except Exception as e:
            logger.error(f"Failed to create channel: {e}")
            raise
    
    async def join_channel(self, channel_id: str, user_id: str) -> bool:
        """Join user to channel"""
        try:
            channel = await self._get_channel(channel_id)
            if not channel:
                raise ValueError("Channel not found")
            
            if user_id not in channel.members:
                channel.members.append(user_id)
                await self._save_channel(channel)
                
                # Send system message
                user = await self._get_user(user_id)
                await self.send_message(
                    channel_id=channel_id,
                    user_id="system",
                    content=f"{user.display_name if user else user_id} joined the channel",
                    message_type=MessageType.SYSTEM
                )
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to join channel: {e}")
            return False
    
    async def get_channel_messages(self, channel_id: str, limit: int = 50, 
                                 before: Optional[str] = None) -> List[Message]:
        """Get messages from channel"""
        try:
            # Check cache first for recent messages
            if not before and channel_id in self.message_cache:
                cached_messages = list(self.message_cache[channel_id])
                if len(cached_messages) >= limit:
                    return cached_messages[-limit:]
            
            # Query database
            conn = sqlite3.connect(self.database_path)
            cursor = conn.cursor()
            
            query = """
                SELECT * FROM messages 
                WHERE channel_id = ? AND is_deleted = 0
                ORDER BY timestamp DESC
                LIMIT ?
            """
            params = [channel_id, limit]
            
            if before:
                query = query.replace("ORDER BY", "AND timestamp < ? ORDER BY")
                params.insert(-1, before)
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            conn.close()
            
            messages = []
            for row in rows:
                message = Message(
                    message_id=row[0],
                    channel_id=row[1],
                    user_id=row[2],
                    content=row[3],
                    message_type=MessageType(row[4]),
                    timestamp=datetime.fromisoformat(row[5]),
                    edited_at=datetime.fromisoformat(row[6]) if row[6] else None,
                    thread_id=row[7],
                    parent_message_id=row[8],
                    attachments=json.loads(row[9]) if row[9] else [],
                    reactions=json.loads(row[10]) if row[10] else {},
                    mentions=json.loads(row[11]) if row[11] else [],
                    metadata=json.loads(row[12]) if row[12] else {},
                    is_pinned=bool(row[13]),
                    is_deleted=bool(row[14])
                )
                messages.append(message)
            
            return list(reversed(messages))  # Return in chronological order
            
        except Exception as e:
            logger.error(f"Failed to get channel messages: {e}")
            return []
    
    async def get_user_channels(self, user_id: str) -> List[Channel]:
        """Get channels for user"""
        try:
            conn = sqlite3.connect(self.database_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT * FROM channels 
                WHERE members LIKE ? AND is_archived = 0
                ORDER BY name
            """, [f'%{user_id}%'])
            
            rows = cursor.fetchall()
            conn.close()
            
            channels = []
            for row in rows:
                channel = Channel(
                    channel_id=row[0],
                    name=row[1],
                    description=row[2],
                    type=ChannelType(row[3]),
                    created_by=row[4],
                    created_at=datetime.fromisoformat(row[5]),
                    members=json.loads(row[6]) if row[6] else [],
                    admins=json.loads(row[7]) if row[7] else [],
                    is_archived=bool(row[8]),
                    topic=row[9] or "",
                    purpose=row[10] or "",
                    settings=json.loads(row[11]) if row[11] else {},
                    property_id=row[12],
                    project_id=row[13]
                )
                # Verify user is actually a member
                if user_id in channel.members:
                    channels.append(channel)
            
            return channels
            
        except Exception as e:
            logger.error(f"Failed to get user channels: {e}")
            return []
    
    async def update_user_status(self, user_id: str, status: UserStatus):
        """Update user online status"""
        try:
            user = await self._get_user(user_id)
            if user:
                user.status = status
                user.last_seen = datetime.now()
                await self._save_user(user)
                
                # Broadcast status update
                await self._broadcast_user_status_update(user)
            
        except Exception as e:
            logger.error(f"Failed to update user status: {e}")
    
    async def start_typing(self, channel_id: str, user_id: str):
        """Start typing indicator"""
        self.typing_indicators[channel_id][user_id] = datetime.now()
        await self._broadcast_typing_indicator(channel_id, user_id, True)
    
    async def stop_typing(self, channel_id: str, user_id: str):
        """Stop typing indicator"""
        if channel_id in self.typing_indicators:
            self.typing_indicators[channel_id].pop(user_id, None)
        await self._broadcast_typing_indicator(channel_id, user_id, False)
    
    def _extract_mentions(self, content: str) -> List[str]:
        """Extract user mentions from message content"""
        import re
        mention_pattern = r'@(\w+)'
        matches = re.findall(mention_pattern, content)
        return matches
    
    async def _save_message(self, message: Message):
        """Save message to database"""
        conn = sqlite3.connect(self.database_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT OR REPLACE INTO messages 
            (message_id, channel_id, user_id, content, message_type, timestamp,
             edited_at, thread_id, parent_message_id, attachments, reactions,
             mentions, metadata, is_pinned, is_deleted)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            message.message_id, message.channel_id, message.user_id, message.content,
            message.message_type.value, message.timestamp.isoformat(),
            message.edited_at.isoformat() if message.edited_at else None,
            message.thread_id, message.parent_message_id,
            json.dumps(message.attachments), json.dumps(message.reactions),
            json.dumps(message.mentions), json.dumps(message.metadata),
            message.is_pinned, message.is_deleted
        ))
        
        conn.commit()
        conn.close()
    
    async def _save_channel(self, channel: Channel):
        """Save channel to database"""
        conn = sqlite3.connect(self.database_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT OR REPLACE INTO channels 
            (channel_id, name, description, type, created_by, created_at,
             members, admins, is_archived, topic, purpose, settings,
             property_id, project_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            channel.channel_id, channel.name, channel.description, channel.type.value,
            channel.created_by, channel.created_at.isoformat(),
            json.dumps(channel.members), json.dumps(channel.admins),
            channel.is_archived, channel.topic, channel.purpose,
            json.dumps(channel.settings), channel.property_id, channel.project_id
        ))
        
        conn.commit()
        conn.close()
    
    def _save_channel(self, channel: Channel):
        """Save channel to database (sync version for initialization)"""
        conn = sqlite3.connect(self.database_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT OR REPLACE INTO channels 
            (channel_id, name, description, type, created_by, created_at,
             members, admins, is_archived, topic, purpose, settings,
             property_id, project_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            channel.channel_id, channel.name, channel.description, channel.type.value,
            channel.created_by, channel.created_at.isoformat(),
            json.dumps(channel.members), json.dumps(channel.admins),
            channel.is_archived, channel.topic, channel.purpose,
            json.dumps(channel.settings), channel.property_id, channel.project_id
        ))
        
        conn.commit()
        conn.close()
    
    async def _save_user(self, user: User):
        """Save user to database"""
        conn = sqlite3.connect(self.database_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT OR REPLACE INTO users 
            (user_id, username, display_name, email, avatar_url, status,
             role, department, timezone, last_seen, is_admin, preferences, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            user.user_id, user.username, user.display_name, user.email,
            user.avatar_url, user.status.value, user.role, user.department,
            user.timezone, user.last_seen.isoformat(), user.is_admin,
            json.dumps(user.preferences), datetime.now().isoformat()
        ))
        
        conn.commit()
        conn.close()
    
    def _save_user(self, user: User):
        """Save user to database (sync version for initialization)"""
        conn = sqlite3.connect(self.database_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT OR REPLACE INTO users 
            (user_id, username, display_name, email, avatar_url, status,
             role, department, timezone, last_seen, is_admin, preferences, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            user.user_id, user.username, user.display_name, user.email,
            user.avatar_url, user.status.value, user.role, user.department,
            user.timezone, user.last_seen.isoformat(), user.is_admin,
            json.dumps(user.preferences), datetime.now().isoformat()
        ))
        
        conn.commit()
        conn.close()
    
    async def _broadcast_message(self, message: Message):
        """Broadcast message to channel members"""
        # In a real implementation, this would use WebSockets
        # For now, just log the broadcast
        logger.info(f"Broadcasting message {message.message_id} to channel {message.channel_id}")
    
    async def _broadcast_message_update(self, message: Message):
        """Broadcast message update"""
        logger.info(f"Broadcasting message update {message.message_id}")
    
    async def _broadcast_reaction_update(self, message: Message, emoji: str, user_id: str, action: str):
        """Broadcast reaction update"""
        logger.info(f"Broadcasting reaction {action}: {emoji} on {message.message_id} by {user_id}")
    
    async def _broadcast_user_status_update(self, user: User):
        """Broadcast user status update"""
        logger.info(f"Broadcasting status update for {user.user_id}: {user.status.value}")
    
    async def _broadcast_typing_indicator(self, channel_id: str, user_id: str, is_typing: bool):
        """Broadcast typing indicator"""
        logger.info(f"Broadcasting typing indicator: {user_id} {'is' if is_typing else 'stopped'} typing in {channel_id}")

# Global instance
_messaging_service = None

def get_messaging_service() -> TeamMessagingService:
    """Get global messaging service instance"""
    global _messaging_service
    if _messaging_service is None:
        _messaging_service = TeamMessagingService()
    return _messaging_service

# API convenience functions
async def send_team_message_api(message_data: Dict[str, Any]) -> Dict[str, Any]:
    """Send team message for API"""
    service = get_messaging_service()
    
    message = await service.send_message(
        channel_id=message_data["channel_id"],
        user_id=message_data["user_id"],
        content=message_data["content"],
        message_type=MessageType(message_data.get("message_type", "text")),
        thread_id=message_data.get("thread_id"),
        attachments=message_data.get("attachments", [])
    )
    
    return asdict(message)

async def get_channel_messages_api(channel_id: str, limit: int = 50, before: str = None) -> Dict[str, Any]:
    """Get channel messages for API"""
    service = get_messaging_service()
    
    messages = await service.get_channel_messages(channel_id, limit, before)
    
    return {
        "channel_id": channel_id,
        "messages": [asdict(msg) for msg in messages],
        "count": len(messages)
    }

async def get_user_channels_api(user_id: str) -> Dict[str, Any]:
    """Get user channels for API"""
    service = get_messaging_service()
    
    channels = await service.get_user_channels(user_id)
    
    return {
        "user_id": user_id,
        "channels": [asdict(channel) for channel in channels],
        "count": len(channels)
    }

if __name__ == "__main__":
    # Test the messaging service
    async def test_messaging():
        service = TeamMessagingService()
        
        print("Testing Team Messaging Service")
        print("=" * 50)
        
        # Test sending a message
        message = await service.send_message(
            channel_id="general",
            user_id="admin_001",
            content="Hello team! Welcome to our new messaging system.",
            message_type=MessageType.TEXT
        )
        print(f"Sent message: {message.message_id}")
        
        # Test getting messages
        messages = await service.get_channel_messages("general")
        print(f"Retrieved {len(messages)} messages from general channel")
        
        # Test user channels
        channels = await service.get_user_channels("admin_001")
        print(f"User has access to {len(channels)} channels")
        
        print("\nTeam Messaging Test Complete!")
    
    asyncio.run(test_messaging())