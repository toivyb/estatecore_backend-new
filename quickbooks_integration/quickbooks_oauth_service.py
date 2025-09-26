"""
QuickBooks Online OAuth 2.0 Authentication Service

Provides secure OAuth 2.0 authentication flow for QuickBooks Online integration
with proper token management, refresh handling, and enterprise security features.
"""

import os
import json
import uuid
import base64
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Dict, Optional, Any, List
from dataclasses import dataclass, asdict
from urllib.parse import urlencode, parse_qs
import requests
from cryptography.fernet import Fernet
import logging

logger = logging.getLogger(__name__)

@dataclass
class QuickBooksConnection:
    """Represents a QuickBooks Online connection for an organization"""
    connection_id: str
    organization_id: str
    company_id: str  # QuickBooks Company ID
    access_token: str
    refresh_token: str
    token_expires_at: datetime
    scope: List[str]
    base_url: str  # QuickBooks API base URL
    company_info: Dict[str, Any]
    created_at: datetime
    updated_at: datetime
    is_active: bool = True
    last_sync_at: Optional[datetime] = None
    
    def is_token_expired(self) -> bool:
        """Check if access token is expired"""
        return datetime.now() >= self.token_expires_at - timedelta(minutes=5)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage"""
        data = asdict(self)
        data['token_expires_at'] = self.token_expires_at.isoformat()
        data['created_at'] = self.created_at.isoformat()
        data['updated_at'] = self.updated_at.isoformat()
        if self.last_sync_at:
            data['last_sync_at'] = self.last_sync_at.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'QuickBooksConnection':
        """Create from dictionary"""
        data['token_expires_at'] = datetime.fromisoformat(data['token_expires_at'])
        data['created_at'] = datetime.fromisoformat(data['created_at'])
        data['updated_at'] = datetime.fromisoformat(data['updated_at'])
        if data.get('last_sync_at'):
            data['last_sync_at'] = datetime.fromisoformat(data['last_sync_at'])
        return cls(**data)

@dataclass
class OAuthConfig:
    """OAuth configuration for QuickBooks Online"""
    client_id: str
    client_secret: str
    redirect_uri: str
    scope: List[str]
    discovery_document_url: str = "https://appcenter.intuit.com/api/v1/OpenID_sandbox"
    base_url: str = "https://sandbox-quickbooks.api.intuit.com"  # Change for production
    
class QuickBooksOAuthService:
    """
    Handles OAuth 2.0 authentication flow for QuickBooks Online
    """
    
    def __init__(self, config: Optional[OAuthConfig] = None):
        self.config = config or self._load_config()
        self.connections: Dict[str, QuickBooksConnection] = {}
        
        # Initialize encryption for token storage
        self.encryption_key = self._get_encryption_key()
        self.cipher = Fernet(self.encryption_key)
        
        # OAuth endpoints
        self.auth_url = "https://appcenter.intuit.com/connect/oauth2"
        self.token_url = "https://oauth.platform.intuit.com/oauth2/v1/tokens/bearer"
        self.discovery_url = "https://appcenter.intuit.com/api/v1/OpenID_sandbox"
        
        # Load existing connections
        self._load_connections()
    
    def _load_config(self) -> OAuthConfig:
        """Load OAuth configuration from environment or config"""
        return OAuthConfig(
            client_id=os.getenv('QUICKBOOKS_CLIENT_ID', ''),
            client_secret=os.getenv('QUICKBOOKS_CLIENT_SECRET', ''),
            redirect_uri=os.getenv('QUICKBOOKS_REDIRECT_URI', 'http://localhost:5000/api/quickbooks/oauth/callback'),
            scope=['com.intuit.quickbooks.accounting'],
            discovery_document_url=os.getenv('QUICKBOOKS_DISCOVERY_URL', 
                                           "https://appcenter.intuit.com/api/v1/OpenID_sandbox"),
            base_url=os.getenv('QUICKBOOKS_BASE_URL', 
                             "https://sandbox-quickbooks.api.intuit.com")
        )
    
    def _get_encryption_key(self) -> bytes:
        """Get or generate encryption key for token storage"""
        key_env = os.getenv('QUICKBOOKS_ENCRYPTION_KEY')
        if key_env:
            return base64.urlsafe_b64decode(key_env.encode())
        
        # Generate new key for development
        key = Fernet.generate_key()
        logger.warning("Generated new encryption key. Set QUICKBOOKS_ENCRYPTION_KEY in production!")
        logger.info(f"QUICKBOOKS_ENCRYPTION_KEY={base64.urlsafe_b64encode(key).decode()}")
        return key
    
    def _load_connections(self):
        """Load existing connections from storage"""
        # In production, this would load from database
        connections_file = "instance/quickbooks_connections.json"
        if os.path.exists(connections_file):
            try:
                with open(connections_file, 'r') as f:
                    data = json.load(f)
                    for conn_data in data.get('connections', []):
                        # Decrypt tokens
                        conn_data['access_token'] = self._decrypt_token(conn_data['access_token'])
                        conn_data['refresh_token'] = self._decrypt_token(conn_data['refresh_token'])
                        
                        connection = QuickBooksConnection.from_dict(conn_data)
                        self.connections[connection.connection_id] = connection
            except Exception as e:
                logger.error(f"Failed to load connections: {e}")
    
    def _save_connections(self):
        """Save connections to storage"""
        # In production, this would save to database
        os.makedirs("instance", exist_ok=True)
        connections_file = "instance/quickbooks_connections.json"
        
        try:
            connections_data = []
            for connection in self.connections.values():
                conn_data = connection.to_dict()
                # Encrypt tokens before storage
                conn_data['access_token'] = self._encrypt_token(connection.access_token)
                conn_data['refresh_token'] = self._encrypt_token(connection.refresh_token)
                connections_data.append(conn_data)
            
            with open(connections_file, 'w') as f:
                json.dump({'connections': connections_data}, f, indent=2)
                
        except Exception as e:
            logger.error(f"Failed to save connections: {e}")
    
    def _encrypt_token(self, token: str) -> str:
        """Encrypt token for storage"""
        return self.cipher.encrypt(token.encode()).decode()
    
    def _decrypt_token(self, encrypted_token: str) -> str:
        """Decrypt token from storage"""
        return self.cipher.decrypt(encrypted_token.encode()).decode()
    
    def generate_authorization_url(self, organization_id: str, state: Optional[str] = None) -> tuple[str, str]:
        """
        Generate authorization URL for OAuth flow
        
        Returns:
            tuple: (authorization_url, state)
        """
        if not state:
            state = secrets.token_urlsafe(32)
        
        # Store state for validation
        self._store_oauth_state(state, organization_id)
        
        params = {
            'client_id': self.config.client_id,
            'scope': ' '.join(self.config.scope),
            'redirect_uri': self.config.redirect_uri,
            'response_type': 'code',
            'access_type': 'offline',
            'state': state
        }
        
        auth_url = f"{self.auth_url}?{urlencode(params)}"
        
        logger.info(f"Generated authorization URL for organization {organization_id}")
        return auth_url, state
    
    def _store_oauth_state(self, state: str, organization_id: str):
        """Store OAuth state for validation"""
        # In production, store in Redis or database with expiration
        states_file = "instance/oauth_states.json"
        states = {}
        
        if os.path.exists(states_file):
            try:
                with open(states_file, 'r') as f:
                    states = json.load(f)
            except:
                pass
        
        states[state] = {
            'organization_id': organization_id,
            'created_at': datetime.now().isoformat(),
            'expires_at': (datetime.now() + timedelta(minutes=10)).isoformat()
        }
        
        os.makedirs("instance", exist_ok=True)
        with open(states_file, 'w') as f:
            json.dump(states, f)
    
    def _validate_oauth_state(self, state: str) -> Optional[str]:
        """Validate OAuth state and return organization_id"""
        states_file = "instance/oauth_states.json"
        if not os.path.exists(states_file):
            return None
        
        try:
            with open(states_file, 'r') as f:
                states = json.load(f)
            
            state_data = states.get(state)
            if not state_data:
                return None
            
            # Check expiration
            expires_at = datetime.fromisoformat(state_data['expires_at'])
            if datetime.now() > expires_at:
                return None
            
            # Remove used state
            del states[state]
            with open(states_file, 'w') as f:
                json.dump(states, f)
            
            return state_data['organization_id']
            
        except Exception as e:
            logger.error(f"Failed to validate OAuth state: {e}")
            return None
    
    def exchange_code_for_tokens(self, code: str, state: str, realm_id: str) -> QuickBooksConnection:
        """
        Exchange authorization code for access tokens
        
        Args:
            code: Authorization code from callback
            state: OAuth state parameter
            realm_id: QuickBooks Company ID
            
        Returns:
            QuickBooksConnection: The established connection
        """
        # Validate state
        organization_id = self._validate_oauth_state(state)
        if not organization_id:
            raise ValueError("Invalid or expired OAuth state")
        
        # Prepare token exchange request
        headers = {
            'Authorization': f'Basic {self._get_basic_auth_header()}',
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        
        data = {
            'grant_type': 'authorization_code',
            'code': code,
            'redirect_uri': self.config.redirect_uri
        }
        
        # Exchange code for tokens
        response = requests.post(self.token_url, headers=headers, data=data)
        
        if not response.ok:
            logger.error(f"Token exchange failed: {response.text}")
            raise Exception(f"Token exchange failed: {response.status_code}")
        
        token_data = response.json()
        
        # Get company information
        company_info = self._get_company_info(token_data['access_token'], realm_id)
        
        # Create connection
        connection = QuickBooksConnection(
            connection_id=str(uuid.uuid4()),
            organization_id=organization_id,
            company_id=realm_id,
            access_token=token_data['access_token'],
            refresh_token=token_data['refresh_token'],
            token_expires_at=datetime.now() + timedelta(seconds=token_data['expires_in']),
            scope=token_data.get('scope', '').split(' '),
            base_url=self.config.base_url,
            company_info=company_info,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        # Store connection
        self.connections[connection.connection_id] = connection
        self._save_connections()
        
        logger.info(f"Successfully created QuickBooks connection for organization {organization_id}")
        return connection
    
    def _get_basic_auth_header(self) -> str:
        """Generate Basic Auth header for API requests"""
        credentials = f"{self.config.client_id}:{self.config.client_secret}"
        encoded = base64.b64encode(credentials.encode()).decode()
        return encoded
    
    def _get_company_info(self, access_token: str, company_id: str) -> Dict[str, Any]:
        """Get company information from QuickBooks"""
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Accept': 'application/json'
        }
        
        url = f"{self.config.base_url}/v3/company/{company_id}/companyinfo/{company_id}"
        
        try:
            response = requests.get(url, headers=headers)
            if response.ok:
                data = response.json()
                return data.get('QueryResponse', {}).get('CompanyInfo', [{}])[0]
            else:
                logger.warning(f"Failed to get company info: {response.status_code}")
                return {}
        except Exception as e:
            logger.error(f"Error getting company info: {e}")
            return {}
    
    def refresh_access_token(self, connection_id: str) -> bool:
        """
        Refresh access token for a connection
        
        Args:
            connection_id: ID of the connection to refresh
            
        Returns:
            bool: True if successful, False otherwise
        """
        connection = self.connections.get(connection_id)
        if not connection:
            logger.error(f"Connection {connection_id} not found")
            return False
        
        headers = {
            'Authorization': f'Basic {self._get_basic_auth_header()}',
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        
        data = {
            'grant_type': 'refresh_token',
            'refresh_token': connection.refresh_token
        }
        
        try:
            response = requests.post(self.token_url, headers=headers, data=data)
            
            if not response.ok:
                logger.error(f"Token refresh failed for {connection_id}: {response.text}")
                return False
            
            token_data = response.json()
            
            # Update connection with new tokens
            connection.access_token = token_data['access_token']
            if 'refresh_token' in token_data:
                connection.refresh_token = token_data['refresh_token']
            connection.token_expires_at = datetime.now() + timedelta(seconds=token_data['expires_in'])
            connection.updated_at = datetime.now()
            
            # Save updated connection
            self._save_connections()
            
            logger.info(f"Successfully refreshed token for connection {connection_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error refreshing token for {connection_id}: {e}")
            return False
    
    def get_connection(self, connection_id: str) -> Optional[QuickBooksConnection]:
        """Get a connection by ID"""
        return self.connections.get(connection_id)
    
    def get_organization_connection(self, organization_id: str) -> Optional[QuickBooksConnection]:
        """Get active connection for an organization"""
        for connection in self.connections.values():
            if connection.organization_id == organization_id and connection.is_active:
                return connection
        return None
    
    def list_connections(self, organization_id: Optional[str] = None) -> List[QuickBooksConnection]:
        """List all connections, optionally filtered by organization"""
        connections = list(self.connections.values())
        if organization_id:
            connections = [c for c in connections if c.organization_id == organization_id]
        return connections
    
    def revoke_connection(self, connection_id: str) -> bool:
        """
        Revoke a connection and its tokens
        
        Args:
            connection_id: ID of connection to revoke
            
        Returns:
            bool: True if successful
        """
        connection = self.connections.get(connection_id)
        if not connection:
            return False
        
        # Revoke tokens with QuickBooks
        try:
            headers = {
                'Authorization': f'Basic {self._get_basic_auth_header()}',
                'Content-Type': 'application/x-www-form-urlencoded'
            }
            
            data = {
                'token': connection.refresh_token
            }
            
            revoke_url = "https://developer.api.intuit.com/v2/oauth2/tokens/revoke"
            response = requests.post(revoke_url, headers=headers, data=data)
            
            if not response.ok:
                logger.warning(f"Failed to revoke tokens with QuickBooks: {response.status_code}")
            
        except Exception as e:
            logger.error(f"Error revoking tokens: {e}")
        
        # Mark connection as inactive
        connection.is_active = False
        connection.updated_at = datetime.now()
        self._save_connections()
        
        logger.info(f"Revoked connection {connection_id}")
        return True
    
    def ensure_valid_token(self, connection_id: str) -> Optional[str]:
        """
        Ensure connection has valid access token, refresh if needed
        
        Args:
            connection_id: ID of connection
            
        Returns:
            str: Valid access token or None if failed
        """
        connection = self.connections.get(connection_id)
        if not connection or not connection.is_active:
            return None
        
        # Check if token needs refresh
        if connection.is_token_expired():
            if not self.refresh_access_token(connection_id):
                logger.error(f"Failed to refresh token for connection {connection_id}")
                return None
            # Get updated connection
            connection = self.connections.get(connection_id)
        
        return connection.access_token if connection else None
    
    def get_connection_status(self, connection_id: str) -> Dict[str, Any]:
        """Get detailed status of a connection"""
        connection = self.connections.get(connection_id)
        if not connection:
            return {'status': 'not_found'}
        
        return {
            'status': 'active' if connection.is_active else 'inactive',
            'organization_id': connection.organization_id,
            'company_id': connection.company_id,
            'company_name': connection.company_info.get('Name', 'Unknown'),
            'token_expires_at': connection.token_expires_at.isoformat(),
            'token_expired': connection.is_token_expired(),
            'last_sync_at': connection.last_sync_at.isoformat() if connection.last_sync_at else None,
            'created_at': connection.created_at.isoformat(),
            'scope': connection.scope
        }

# Service instance
_oauth_service = None

def get_quickbooks_oauth_service() -> QuickBooksOAuthService:
    """Get singleton OAuth service instance"""
    global _oauth_service
    if _oauth_service is None:
        _oauth_service = QuickBooksOAuthService()
    return _oauth_service