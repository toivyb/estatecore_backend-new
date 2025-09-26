"""
Yardi Authentication Service

Handles authentication and connection management for various Yardi products
including OAuth2, API key authentication, and credential management.
"""

import os
import logging
import json
import secrets
import hashlib
import base64
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field, asdict
from enum import Enum
import asyncio
import aiohttp
import requests
from cryptography.fernet import Fernet
from urllib.parse import urlencode, urljoin
import jwt

from .models import (
    YardiProductType, YardiConnectionType, YardiAuthMethod,
    YardiConnection as YardiConnectionModel
)

logger = logging.getLogger(__name__)

class YardiConnectionStatus(Enum):
    """Connection status enumeration"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    EXPIRED = "expired"
    ERROR = "error"
    PENDING = "pending"

@dataclass
class YardiConnection:
    """Yardi connection data class"""
    connection_id: str
    organization_id: str
    connection_name: str
    yardi_product: YardiProductType
    connection_type: YardiConnectionType
    auth_method: YardiAuthMethod
    base_url: str
    company_info: Dict[str, Any] = field(default_factory=dict)
    is_active: bool = True
    is_sandbox: bool = False
    last_activity_at: Optional[datetime] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    rate_limit_per_minute: int = 60
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        data = asdict(self)
        # Convert enums to values
        data['yardi_product'] = self.yardi_product.value
        data['connection_type'] = self.connection_type.value
        data['auth_method'] = self.auth_method.value
        return data

@dataclass
class YardiCredentials:
    """Yardi connection credentials"""
    connection_id: str
    encrypted_credentials: str
    auth_method: YardiAuthMethod
    expires_at: Optional[datetime] = None
    refresh_token: Optional[str] = None
    scopes: List[str] = field(default_factory=list)

@dataclass
class YardiOAuthConfig:
    """OAuth configuration for Yardi products"""
    client_id: str
    client_secret: str
    authorization_url: str
    token_url: str
    redirect_uri: str
    scopes: List[str] = field(default_factory=list)

class YardiAuthService:
    """
    Yardi Authentication Service
    
    Manages authentication, connection credentials, and token lifecycle
    for various Yardi products.
    """
    
    def __init__(self):
        # Initialize encryption for credentials
        self.encryption_key = self._get_or_create_encryption_key()
        self.fernet = Fernet(self.encryption_key)
        
        # In-memory storage (in production, use database)
        self.connections: Dict[str, YardiConnection] = {}
        self.credentials: Dict[str, YardiCredentials] = {}
        self.oauth_configs: Dict[YardiProductType, YardiOAuthConfig] = {}
        
        # Load OAuth configurations
        self._load_oauth_configurations()
        
        logger.info("Yardi Authentication Service initialized")
    
    def _get_or_create_encryption_key(self) -> bytes:
        """Get or create encryption key for credentials"""
        key_path = os.environ.get('YARDI_ENCRYPTION_KEY_PATH', 'yardi_encryption.key')
        
        if os.path.exists(key_path):
            with open(key_path, 'rb') as f:
                return f.read()
        else:
            key = Fernet.generate_key()
            with open(key_path, 'wb') as f:
                f.write(key)
            logger.info(f"Generated new encryption key: {key_path}")
            return key
    
    def _load_oauth_configurations(self):
        """Load OAuth configurations for Yardi products"""
        # These would typically be loaded from environment variables or config
        self.oauth_configs = {
            YardiProductType.VOYAGER: YardiOAuthConfig(
                client_id=os.environ.get('YARDI_VOYAGER_CLIENT_ID', ''),
                client_secret=os.environ.get('YARDI_VOYAGER_CLIENT_SECRET', ''),
                authorization_url="https://auth.yardi.com/oauth2/authorize",
                token_url="https://auth.yardi.com/oauth2/token",
                redirect_uri=os.environ.get('YARDI_VOYAGER_REDIRECT_URI', ''),
                scopes=['read', 'write', 'admin']
            ),
            YardiProductType.BREEZE: YardiOAuthConfig(
                client_id=os.environ.get('YARDI_BREEZE_CLIENT_ID', ''),
                client_secret=os.environ.get('YARDI_BREEZE_CLIENT_SECRET', ''),
                authorization_url="https://api.rentcafe.com/oauth2/authorize",
                token_url="https://api.rentcafe.com/oauth2/token",
                redirect_uri=os.environ.get('YARDI_BREEZE_REDIRECT_URI', ''),
                scopes=['properties', 'residents', 'leases', 'payments']
            )
        }
    
    # =====================================================
    # CONNECTION MANAGEMENT
    # =====================================================
    
    def create_connection(self, organization_id: str, yardi_product: YardiProductType,
                         connection_type: YardiConnectionType, connection_params: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new Yardi connection"""
        try:
            connection_id = f"yardi_{organization_id}_{secrets.token_hex(8)}"
            
            # Validate connection parameters
            validation_result = self._validate_connection_params(
                yardi_product, connection_type, connection_params
            )
            if not validation_result['valid']:
                return {
                    "success": False,
                    "error": "Invalid connection parameters",
                    "validation_errors": validation_result['errors']
                }
            
            # Determine authentication method
            auth_method = connection_params.get('auth_method', YardiAuthMethod.API_KEY)
            if isinstance(auth_method, str):
                auth_method = YardiAuthMethod(auth_method)
            
            # Create connection object
            connection = YardiConnection(
                connection_id=connection_id,
                organization_id=organization_id,
                connection_name=connection_params.get('connection_name', f'Yardi {yardi_product.value}'),
                yardi_product=yardi_product,
                connection_type=connection_type,
                auth_method=auth_method,
                base_url=connection_params['base_url'],
                is_sandbox=connection_params.get('is_sandbox', False),
                rate_limit_per_minute=connection_params.get('rate_limit_per_minute', 60)
            )
            
            # Store encrypted credentials
            credentials_result = self._store_credentials(
                connection_id, auth_method, connection_params.get('credentials', {})
            )
            if not credentials_result['success']:
                return credentials_result
            
            # Store connection
            self.connections[connection_id] = connection
            
            logger.info(f"Created Yardi connection {connection_id} for organization {organization_id}")
            
            return {
                "success": True,
                "connection": connection,
                "connection_id": connection_id
            }
            
        except Exception as e:
            logger.error(f"Failed to create Yardi connection: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_connection(self, connection_id: str) -> Optional[YardiConnection]:
        """Get connection by ID"""
        return self.connections.get(connection_id)
    
    def get_organization_connections(self, organization_id: str) -> List[YardiConnection]:
        """Get all connections for an organization"""
        return [
            conn for conn in self.connections.values() 
            if conn.organization_id == organization_id
        ]
    
    def get_organization_connection(self, organization_id: str, 
                                  yardi_product: Optional[YardiProductType] = None) -> Optional[YardiConnection]:
        """Get primary connection for organization"""
        connections = self.get_organization_connections(organization_id)
        
        if yardi_product:
            connections = [conn for conn in connections if conn.yardi_product == yardi_product]
        
        # Return the most recently created active connection
        active_connections = [conn for conn in connections if conn.is_active]
        if active_connections:
            return max(active_connections, key=lambda c: c.created_at)
        
        return None
    
    def update_connection(self, connection_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Update connection configuration"""
        try:
            connection = self.connections.get(connection_id)
            if not connection:
                return {
                    "success": False,
                    "error": "Connection not found"
                }
            
            # Update allowed fields
            allowed_fields = [
                'connection_name', 'base_url', 'is_active', 'is_sandbox',
                'rate_limit_per_minute'
            ]
            
            for field, value in updates.items():
                if field in allowed_fields and hasattr(connection, field):
                    setattr(connection, field, value)
            
            # Update credentials if provided
            if 'credentials' in updates:
                credentials_result = self._store_credentials(
                    connection_id, connection.auth_method, updates['credentials']
                )
                if not credentials_result['success']:
                    return credentials_result
            
            logger.info(f"Updated Yardi connection {connection_id}")
            
            return {
                "success": True,
                "connection": connection
            }
            
        except Exception as e:
            logger.error(f"Failed to update connection: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def delete_connection(self, connection_id: str) -> Dict[str, Any]:
        """Delete a connection"""
        try:
            if connection_id not in self.connections:
                return {
                    "success": False,
                    "error": "Connection not found"
                }
            
            # Remove connection and credentials
            del self.connections[connection_id]
            if connection_id in self.credentials:
                del self.credentials[connection_id]
            
            logger.info(f"Deleted Yardi connection {connection_id}")
            
            return {
                "success": True,
                "message": "Connection deleted successfully"
            }
            
        except Exception as e:
            logger.error(f"Failed to delete connection: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def revoke_connection(self, connection_id: str) -> Dict[str, Any]:
        """Revoke connection and invalidate tokens"""
        try:
            connection = self.connections.get(connection_id)
            if not connection:
                return {
                    "success": False,
                    "error": "Connection not found"
                }
            
            # Mark as inactive
            connection.is_active = False
            
            # Revoke OAuth tokens if applicable
            if connection.auth_method == YardiAuthMethod.OAUTH2:
                credentials = self.credentials.get(connection_id)
                if credentials:
                    self._revoke_oauth_token(connection, credentials)
            
            logger.info(f"Revoked Yardi connection {connection_id}")
            
            return {
                "success": True,
                "message": "Connection revoked successfully"
            }
            
        except Exception as e:
            logger.error(f"Failed to revoke connection: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    # =====================================================
    # CREDENTIAL MANAGEMENT
    # =====================================================
    
    def _store_credentials(self, connection_id: str, auth_method: YardiAuthMethod,
                          credentials_data: Dict[str, Any]) -> Dict[str, Any]:
        """Store encrypted credentials"""
        try:
            # Validate credentials based on auth method
            validation_result = self._validate_credentials(auth_method, credentials_data)
            if not validation_result['valid']:
                return {
                    "success": False,
                    "error": "Invalid credentials",
                    "validation_errors": validation_result['errors']
                }
            
            # Encrypt credentials
            encrypted_data = self.fernet.encrypt(json.dumps(credentials_data).encode())
            
            # Store credentials
            self.credentials[connection_id] = YardiCredentials(
                connection_id=connection_id,
                encrypted_credentials=encrypted_data.decode(),
                auth_method=auth_method,
                expires_at=credentials_data.get('expires_at'),
                refresh_token=credentials_data.get('refresh_token'),
                scopes=credentials_data.get('scopes', [])
            )
            
            return {
                "success": True,
                "message": "Credentials stored successfully"
            }
            
        except Exception as e:
            logger.error(f"Failed to store credentials: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_decrypted_credentials(self, connection_id: str) -> Optional[Dict[str, Any]]:
        """Get decrypted credentials"""
        try:
            credentials = self.credentials.get(connection_id)
            if not credentials:
                return None
            
            # Decrypt credentials
            decrypted_data = self.fernet.decrypt(credentials.encrypted_credentials.encode())
            return json.loads(decrypted_data.decode())
            
        except Exception as e:
            logger.error(f"Failed to decrypt credentials: {e}")
            return None
    
    # =====================================================
    # OAUTH2 AUTHENTICATION
    # =====================================================
    
    def start_oauth_flow(self, organization_id: str, yardi_product: YardiProductType,
                        connection_params: Dict[str, Any]) -> Dict[str, Any]:
        """Start OAuth2 authentication flow"""
        try:
            oauth_config = self.oauth_configs.get(yardi_product)
            if not oauth_config:
                return {
                    "success": False,
                    "error": f"OAuth not supported for {yardi_product.value}"
                }
            
            # Generate state parameter for security
            state = secrets.token_urlsafe(32)
            
            # Store state and connection params temporarily
            state_key = f"oauth_state_{state}"
            # In production, store in Redis or database with expiration
            
            # Build authorization URL
            auth_params = {
                'client_id': oauth_config.client_id,
                'response_type': 'code',
                'redirect_uri': oauth_config.redirect_uri,
                'scope': ' '.join(oauth_config.scopes),
                'state': state
            }
            
            authorization_url = f"{oauth_config.authorization_url}?{urlencode(auth_params)}"
            
            return {
                "success": True,
                "authorization_url": authorization_url,
                "state": state,
                "instructions": f"Redirect user to authorization URL to complete {yardi_product.value} connection"
            }
            
        except Exception as e:
            logger.error(f"Failed to start OAuth flow: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def complete_oauth_flow(self, code: str, state: str, organization_id: str,
                          yardi_product: YardiProductType, connection_params: Dict[str, Any]) -> Dict[str, Any]:
        """Complete OAuth2 authentication flow"""
        try:
            oauth_config = self.oauth_configs.get(yardi_product)
            if not oauth_config:
                return {
                    "success": False,
                    "error": f"OAuth not supported for {yardi_product.value}"
                }
            
            # Exchange code for tokens
            token_result = self._exchange_oauth_code(oauth_config, code)
            if not token_result['success']:
                return token_result
            
            tokens = token_result['tokens']
            
            # Get user/company info
            user_info = self._get_oauth_user_info(oauth_config, tokens['access_token'])
            
            # Create connection with OAuth credentials
            connection_params.update({
                'auth_method': YardiAuthMethod.OAUTH2,
                'credentials': {
                    'access_token': tokens['access_token'],
                    'refresh_token': tokens.get('refresh_token'),
                    'token_type': tokens.get('token_type', 'Bearer'),
                    'expires_at': datetime.utcnow() + timedelta(seconds=tokens.get('expires_in', 3600)),
                    'scopes': tokens.get('scope', '').split()
                }
            })
            
            # Create connection
            connection_result = self.create_connection(
                organization_id=organization_id,
                yardi_product=yardi_product,
                connection_type=YardiConnectionType.API,
                connection_params=connection_params
            )
            
            if connection_result['success']:
                connection = connection_result['connection']
                connection.company_info = user_info
                
                return {
                    "success": True,
                    "connection": connection,
                    "user_info": user_info,
                    "message": f"Successfully connected to {yardi_product.value}"
                }
            else:
                return connection_result
                
        except Exception as e:
            logger.error(f"Failed to complete OAuth flow: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def refresh_oauth_token(self, connection_id: str) -> Dict[str, Any]:
        """Refresh OAuth2 access token"""
        try:
            connection = self.connections.get(connection_id)
            credentials = self.credentials.get(connection_id)
            
            if not connection or not credentials:
                return {
                    "success": False,
                    "error": "Connection or credentials not found"
                }
            
            if connection.auth_method != YardiAuthMethod.OAUTH2:
                return {
                    "success": False,
                    "error": "Connection does not use OAuth2"
                }
            
            oauth_config = self.oauth_configs.get(connection.yardi_product)
            if not oauth_config:
                return {
                    "success": False,
                    "error": "OAuth configuration not found"
                }
            
            # Get current credentials
            current_creds = self.get_decrypted_credentials(connection_id)
            if not current_creds or not current_creds.get('refresh_token'):
                return {
                    "success": False,
                    "error": "No refresh token available"
                }
            
            # Refresh token
            refresh_result = self._refresh_oauth_token(oauth_config, current_creds['refresh_token'])
            if not refresh_result['success']:
                return refresh_result
            
            tokens = refresh_result['tokens']
            
            # Update credentials
            current_creds.update({
                'access_token': tokens['access_token'],
                'expires_at': datetime.utcnow() + timedelta(seconds=tokens.get('expires_in', 3600))
            })
            
            if 'refresh_token' in tokens:
                current_creds['refresh_token'] = tokens['refresh_token']
            
            # Store updated credentials
            store_result = self._store_credentials(connection_id, YardiAuthMethod.OAUTH2, current_creds)
            
            return {
                "success": store_result['success'],
                "message": "Token refreshed successfully" if store_result['success'] else store_result.get('error')
            }
            
        except Exception as e:
            logger.error(f"Failed to refresh OAuth token: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def get_valid_token(self, connection_id: str) -> Optional[str]:
        """Get valid access token, refreshing if necessary"""
        try:
            credentials = self.credentials.get(connection_id)
            if not credentials:
                return None
            
            current_creds = self.get_decrypted_credentials(connection_id)
            if not current_creds:
                return None
            
            # Check if token is still valid
            expires_at = current_creds.get('expires_at')
            if expires_at:
                if isinstance(expires_at, str):
                    expires_at = datetime.fromisoformat(expires_at)
                
                # Refresh if expires within 5 minutes
                if expires_at <= datetime.utcnow() + timedelta(minutes=5):
                    refresh_result = await self.refresh_oauth_token(connection_id)
                    if refresh_result['success']:
                        current_creds = self.get_decrypted_credentials(connection_id)
            
            return current_creds.get('access_token') if current_creds else None
            
        except Exception as e:
            logger.error(f"Failed to get valid token: {e}")
            return None
    
    # =====================================================
    # PRIVATE HELPER METHODS
    # =====================================================
    
    def _validate_connection_params(self, yardi_product: YardiProductType,
                                  connection_type: YardiConnectionType,
                                  params: Dict[str, Any]) -> Dict[str, Any]:
        """Validate connection parameters"""
        errors = []
        
        if not params.get('base_url'):
            errors.append("Base URL is required")
        
        if not params.get('connection_name'):
            errors.append("Connection name is required")
        
        if connection_type == YardiConnectionType.API:
            if not params.get('credentials'):
                errors.append("API credentials are required")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors
        }
    
    def _validate_credentials(self, auth_method: YardiAuthMethod,
                            credentials: Dict[str, Any]) -> Dict[str, Any]:
        """Validate credentials based on authentication method"""
        errors = []
        
        if auth_method == YardiAuthMethod.API_KEY:
            if not credentials.get('api_key'):
                errors.append("API key is required")
        
        elif auth_method == YardiAuthMethod.USERNAME_PASSWORD:
            if not credentials.get('username'):
                errors.append("Username is required")
            if not credentials.get('password'):
                errors.append("Password is required")
        
        elif auth_method == YardiAuthMethod.OAUTH2:
            if not credentials.get('access_token'):
                errors.append("Access token is required")
        
        elif auth_method == YardiAuthMethod.TOKEN:
            if not credentials.get('token'):
                errors.append("Token is required")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors
        }
    
    def _exchange_oauth_code(self, oauth_config: YardiOAuthConfig, code: str) -> Dict[str, Any]:
        """Exchange authorization code for access token"""
        try:
            token_data = {
                'grant_type': 'authorization_code',
                'code': code,
                'client_id': oauth_config.client_id,
                'client_secret': oauth_config.client_secret,
                'redirect_uri': oauth_config.redirect_uri
            }
            
            response = requests.post(
                oauth_config.token_url,
                data=token_data,
                headers={'Content-Type': 'application/x-www-form-urlencoded'}
            )
            
            if response.status_code == 200:
                return {
                    "success": True,
                    "tokens": response.json()
                }
            else:
                return {
                    "success": False,
                    "error": f"Token exchange failed: {response.text}"
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def _refresh_oauth_token(self, oauth_config: YardiOAuthConfig, refresh_token: str) -> Dict[str, Any]:
        """Refresh OAuth access token"""
        try:
            token_data = {
                'grant_type': 'refresh_token',
                'refresh_token': refresh_token,
                'client_id': oauth_config.client_id,
                'client_secret': oauth_config.client_secret
            }
            
            response = requests.post(
                oauth_config.token_url,
                data=token_data,
                headers={'Content-Type': 'application/x-www-form-urlencoded'}
            )
            
            if response.status_code == 200:
                return {
                    "success": True,
                    "tokens": response.json()
                }
            else:
                return {
                    "success": False,
                    "error": f"Token refresh failed: {response.text}"
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def _revoke_oauth_token(self, connection: YardiConnection, credentials: YardiCredentials):
        """Revoke OAuth token"""
        try:
            oauth_config = self.oauth_configs.get(connection.yardi_product)
            if not oauth_config:
                return
            
            current_creds = self.get_decrypted_credentials(connection.connection_id)
            if not current_creds:
                return
            
            # Revoke token (if supported by provider)
            revoke_url = oauth_config.token_url.replace('/token', '/revoke')
            revoke_data = {
                'token': current_creds.get('access_token'),
                'client_id': oauth_config.client_id,
                'client_secret': oauth_config.client_secret
            }
            
            requests.post(revoke_url, data=revoke_data)
            
        except Exception as e:
            logger.error(f"Failed to revoke OAuth token: {e}")
    
    def _get_oauth_user_info(self, oauth_config: YardiOAuthConfig, access_token: str) -> Dict[str, Any]:
        """Get user/company information using access token"""
        try:
            # This would be product-specific
            user_info_url = oauth_config.authorization_url.replace('/authorize', '/userinfo')
            
            response = requests.get(
                user_info_url,
                headers={'Authorization': f'Bearer {access_token}'}
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                return {"name": "Unknown", "id": "unknown"}
                
        except Exception as e:
            logger.error(f"Failed to get user info: {e}")
            return {"name": "Unknown", "id": "unknown"}