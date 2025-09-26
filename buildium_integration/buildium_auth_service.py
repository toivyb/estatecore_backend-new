"""
Buildium Authentication Service

Handles authentication and authorization for Buildium API integration
with support for OAuth 2.0, API keys, and secure credential management.
Optimized for small property managers with simplified authentication flows.
"""

import os
import logging
import json
import base64
import secrets
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict, field
from enum import Enum
import asyncio
import aiohttp
from cryptography.fernet import Fernet
from urllib.parse import urlencode, parse_qs

from .models import BuildiumProductType, BuildiumIntegrationConfig

logger = logging.getLogger(__name__)


class AuthMethod(Enum):
    """Supported authentication methods"""
    API_KEY = "api_key"
    OAUTH2 = "oauth2"
    BASIC_AUTH = "basic_auth"


class ConnectionStatus(Enum):
    """Connection status types"""
    NOT_CONNECTED = "not_connected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    EXPIRED = "expired"
    ERROR = "error"
    REFRESHING = "refreshing"


@dataclass
class BuildiumCredentials:
    """Buildium API credentials"""
    api_key: str
    api_secret: str
    auth_method: AuthMethod = AuthMethod.API_KEY
    base_url: str = "https://api.buildium.com"
    environment: str = "production"
    encrypted: bool = False
    created_at: datetime = field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None


@dataclass
class OAuth2Credentials:
    """OAuth 2.0 specific credentials"""
    client_id: str
    client_secret: str
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None
    token_type: str = "Bearer"
    expires_at: Optional[datetime] = None
    scope: List[str] = field(default_factory=list)
    redirect_uri: Optional[str] = None
    state: Optional[str] = None


@dataclass
class BuildiumConnection:
    """Buildium connection information"""
    connection_id: str
    organization_id: str
    connection_name: str
    credentials: BuildiumCredentials
    oauth2_credentials: Optional[OAuth2Credentials] = None
    status: ConnectionStatus = ConnectionStatus.NOT_CONNECTED
    last_authenticated: Optional[datetime] = None
    last_error: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3
    products: List[BuildiumProductType] = field(default_factory=list)
    permissions: List[str] = field(default_factory=list)
    rate_limit_info: Dict[str, Any] = field(default_factory=dict)
    is_sandbox: bool = False
    small_portfolio_mode: bool = False
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)


class BuildiumAuthService:
    """
    Buildium Authentication Service
    
    Manages authentication, credential storage, and session management
    for Buildium API integration with enhanced security and support
    for small property manager workflows.
    """
    
    def __init__(self, encryption_key: Optional[str] = None):
        self.encryption_key = encryption_key or os.getenv('BUILDIUM_ENCRYPTION_KEY')
        if not self.encryption_key:
            self.encryption_key = Fernet.generate_key().decode()
            logger.warning("Generated new encryption key. Store securely!")
        
        self.fernet = Fernet(self.encryption_key.encode() if isinstance(self.encryption_key, str) else self.encryption_key)
        self.connections: Dict[str, BuildiumConnection] = {}
        
        # OAuth 2.0 configuration
        self.oauth_config = {
            'authorization_url': 'https://signin.buildium.com/oauth/authorize',
            'token_url': 'https://api.buildium.com/oauth/token',
            'scope': [
                'property:read', 'property:write',
                'tenant:read', 'tenant:write',
                'lease:read', 'lease:write',
                'payment:read', 'payment:write',
                'maintenance:read', 'maintenance:write',
                'accounting:read', 'accounting:write',
                'document:read', 'document:write'
            ]
        }
        
        # Small portfolio optimized scopes
        self.small_portfolio_scopes = [
            'property:read', 'property:write',
            'tenant:read', 'tenant:write',
            'lease:read', 'lease:write',
            'payment:read', 'payment:write',
            'maintenance:read', 'maintenance:write'
        ]
    
    async def create_connection(
        self,
        organization_id: str,
        connection_name: str,
        credentials: BuildiumCredentials,
        oauth2_credentials: Optional[OAuth2Credentials] = None,
        small_portfolio_mode: bool = False
    ) -> BuildiumConnection:
        """Create a new Buildium connection"""
        try:
            connection_id = f"buildium_{organization_id}_{secrets.token_hex(8)}"
            
            # Encrypt sensitive credentials
            encrypted_credentials = await self._encrypt_credentials(credentials)
            encrypted_oauth2 = None
            if oauth2_credentials:
                encrypted_oauth2 = await self._encrypt_oauth2_credentials(oauth2_credentials)
            
            connection = BuildiumConnection(
                connection_id=connection_id,
                organization_id=organization_id,
                connection_name=connection_name,
                credentials=encrypted_credentials,
                oauth2_credentials=encrypted_oauth2,
                small_portfolio_mode=small_portfolio_mode
            )
            
            self.connections[connection_id] = connection
            
            logger.info(f"Created Buildium connection {connection_id} for organization {organization_id}")
            return connection
            
        except Exception as e:
            logger.error(f"Failed to create connection: {e}")
            raise
    
    async def connect_with_api_key(
        self,
        organization_id: str,
        api_key: str,
        api_secret: str,
        connection_name: str = "Buildium API Key Connection",
        small_portfolio_mode: bool = False,
        environment: str = "production"
    ) -> Tuple[bool, BuildiumConnection]:
        """Connect using API key authentication"""
        try:
            credentials = BuildiumCredentials(
                api_key=api_key,
                api_secret=api_secret,
                auth_method=AuthMethod.API_KEY,
                environment=environment
            )
            
            connection = await self.create_connection(
                organization_id=organization_id,
                connection_name=connection_name,
                credentials=credentials,
                small_portfolio_mode=small_portfolio_mode
            )
            
            # Validate the API key
            is_valid = await self._validate_api_key(connection)
            
            if is_valid:
                connection.status = ConnectionStatus.CONNECTED
                connection.last_authenticated = datetime.utcnow()
                
                # Get available products and permissions
                await self._get_connection_capabilities(connection)
                
                logger.info(f"Successfully connected to Buildium with API key for {organization_id}")
                return True, connection
            else:
                connection.status = ConnectionStatus.ERROR
                connection.last_error = "Invalid API key or secret"
                logger.error(f"Invalid API credentials for {organization_id}")
                return False, connection
                
        except Exception as e:
            logger.error(f"Failed to connect with API key: {e}")
            raise
    
    async def start_oauth_flow(
        self,
        organization_id: str,
        client_id: str,
        client_secret: str,
        redirect_uri: str,
        connection_name: str = "Buildium OAuth Connection",
        small_portfolio_mode: bool = False,
        custom_scopes: Optional[List[str]] = None
    ) -> Tuple[str, str]:
        """Start OAuth 2.0 authorization flow"""
        try:
            # Generate state for CSRF protection
            state = secrets.token_urlsafe(32)
            
            # Use appropriate scopes based on portfolio mode
            scopes = custom_scopes or (
                self.small_portfolio_scopes if small_portfolio_mode 
                else self.oauth_config['scope']
            )
            
            oauth2_credentials = OAuth2Credentials(
                client_id=client_id,
                client_secret=client_secret,
                redirect_uri=redirect_uri,
                state=state,
                scope=scopes
            )
            
            credentials = BuildiumCredentials(
                api_key="",  # Will be populated after OAuth
                api_secret="",
                auth_method=AuthMethod.OAUTH2
            )
            
            connection = await self.create_connection(
                organization_id=organization_id,
                connection_name=connection_name,
                credentials=credentials,
                oauth2_credentials=oauth2_credentials,
                small_portfolio_mode=small_portfolio_mode
            )
            
            connection.status = ConnectionStatus.CONNECTING
            
            # Build authorization URL
            auth_params = {
                'response_type': 'code',
                'client_id': client_id,
                'redirect_uri': redirect_uri,
                'scope': ' '.join(scopes),
                'state': state
            }
            
            auth_url = f"{self.oauth_config['authorization_url']}?{urlencode(auth_params)}"
            
            logger.info(f"Started OAuth flow for {organization_id}")
            return auth_url, state
            
        except Exception as e:
            logger.error(f"Failed to start OAuth flow: {e}")
            raise
    
    async def complete_oauth_flow(
        self,
        organization_id: str,
        authorization_code: str,
        state: str
    ) -> Tuple[bool, Optional[BuildiumConnection]]:
        """Complete OAuth 2.0 authorization flow"""
        try:
            # Find connection by state
            connection = None
            for conn in self.connections.values():
                if (conn.organization_id == organization_id and 
                    conn.oauth2_credentials and 
                    conn.oauth2_credentials.state == state):
                    connection = conn
                    break
            
            if not connection:
                logger.error(f"No matching OAuth flow found for state {state}")
                return False, None
            
            oauth2_creds = connection.oauth2_credentials
            if not oauth2_creds:
                logger.error("No OAuth2 credentials found")
                return False, None
            
            # Exchange authorization code for access token
            token_data = {
                'grant_type': 'authorization_code',
                'code': authorization_code,
                'redirect_uri': oauth2_creds.redirect_uri,
                'client_id': oauth2_creds.client_id,
                'client_secret': oauth2_creds.client_secret
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.oauth_config['token_url'],
                    data=token_data,
                    headers={'Content-Type': 'application/x-www-form-urlencoded'}
                ) as response:
                    if response.status == 200:
                        token_response = await response.json()
                        
                        # Update OAuth credentials
                        oauth2_creds.access_token = token_response['access_token']
                        oauth2_creds.refresh_token = token_response.get('refresh_token')
                        oauth2_creds.token_type = token_response.get('token_type', 'Bearer')
                        
                        # Calculate expiration
                        expires_in = token_response.get('expires_in', 3600)
                        oauth2_creds.expires_at = datetime.utcnow() + timedelta(seconds=expires_in)
                        
                        # Update connection status
                        connection.status = ConnectionStatus.CONNECTED
                        connection.last_authenticated = datetime.utcnow()
                        
                        # Get connection capabilities
                        await self._get_connection_capabilities(connection)
                        
                        logger.info(f"Successfully completed OAuth flow for {organization_id}")
                        return True, connection
                    else:
                        error_data = await response.json()
                        connection.status = ConnectionStatus.ERROR
                        connection.last_error = error_data.get('error_description', 'OAuth token exchange failed')
                        logger.error(f"OAuth token exchange failed: {error_data}")
                        return False, connection
            
        except Exception as e:
            logger.error(f"Failed to complete OAuth flow: {e}")
            if connection:
                connection.status = ConnectionStatus.ERROR
                connection.last_error = str(e)
            return False, connection
    
    async def refresh_access_token(self, connection_id: str) -> bool:
        """Refresh OAuth 2.0 access token"""
        try:
            connection = self.connections.get(connection_id)
            if not connection or not connection.oauth2_credentials:
                logger.error(f"Connection {connection_id} not found or not OAuth")
                return False
            
            oauth2_creds = connection.oauth2_credentials
            if not oauth2_creds.refresh_token:
                logger.error(f"No refresh token available for {connection_id}")
                return False
            
            connection.status = ConnectionStatus.REFRESHING
            
            token_data = {
                'grant_type': 'refresh_token',
                'refresh_token': oauth2_creds.refresh_token,
                'client_id': oauth2_creds.client_id,
                'client_secret': oauth2_creds.client_secret
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.oauth_config['token_url'],
                    data=token_data,
                    headers={'Content-Type': 'application/x-www-form-urlencoded'}
                ) as response:
                    if response.status == 200:
                        token_response = await response.json()
                        
                        # Update tokens
                        oauth2_creds.access_token = token_response['access_token']
                        if 'refresh_token' in token_response:
                            oauth2_creds.refresh_token = token_response['refresh_token']
                        
                        expires_in = token_response.get('expires_in', 3600)
                        oauth2_creds.expires_at = datetime.utcnow() + timedelta(seconds=expires_in)
                        
                        connection.status = ConnectionStatus.CONNECTED
                        connection.last_authenticated = datetime.utcnow()
                        
                        logger.info(f"Successfully refreshed token for {connection_id}")
                        return True
                    else:
                        connection.status = ConnectionStatus.ERROR
                        connection.last_error = "Token refresh failed"
                        logger.error(f"Token refresh failed for {connection_id}")
                        return False
            
        except Exception as e:
            logger.error(f"Failed to refresh token: {e}")
            if connection:
                connection.status = ConnectionStatus.ERROR
                connection.last_error = str(e)
            return False
    
    async def validate_connection(self, connection_id: str) -> Dict[str, Any]:
        """Validate connection status and credentials"""
        try:
            connection = self.connections.get(connection_id)
            if not connection:
                return {
                    'valid': False,
                    'error': 'Connection not found',
                    'status': 'not_found'
                }
            
            # Check if OAuth token is expired
            if (connection.credentials.auth_method == AuthMethod.OAUTH2 and 
                connection.oauth2_credentials and 
                connection.oauth2_credentials.expires_at and
                connection.oauth2_credentials.expires_at <= datetime.utcnow()):
                
                # Try to refresh token
                refreshed = await self.refresh_access_token(connection_id)
                if not refreshed:
                    return {
                        'valid': False,
                        'error': 'Token expired and refresh failed',
                        'status': 'expired'
                    }
            
            # Test API connectivity
            is_valid = await self._test_api_connectivity(connection)
            
            return {
                'valid': is_valid,
                'status': connection.status.value,
                'last_authenticated': connection.last_authenticated.isoformat() if connection.last_authenticated else None,
                'products': [p.value for p in connection.products],
                'permissions': connection.permissions,
                'rate_limit_info': connection.rate_limit_info
            }
            
        except Exception as e:
            logger.error(f"Failed to validate connection: {e}")
            return {
                'valid': False,
                'error': str(e),
                'status': 'error'
            }
    
    async def disconnect(self, connection_id: str) -> bool:
        """Disconnect and clean up connection"""
        try:
            connection = self.connections.get(connection_id)
            if not connection:
                return False
            
            # Revoke OAuth token if applicable
            if (connection.credentials.auth_method == AuthMethod.OAUTH2 and 
                connection.oauth2_credentials and 
                connection.oauth2_credentials.access_token):
                await self._revoke_oauth_token(connection)
            
            # Remove connection
            del self.connections[connection_id]
            
            logger.info(f"Disconnected Buildium connection {connection_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to disconnect: {e}")
            return False
    
    def get_connection(self, connection_id: str) -> Optional[BuildiumConnection]:
        """Get connection by ID"""
        return self.connections.get(connection_id)
    
    def get_organization_connections(self, organization_id: str) -> List[BuildiumConnection]:
        """Get all connections for an organization"""
        return [
            conn for conn in self.connections.values()
            if conn.organization_id == organization_id
        ]
    
    async def get_auth_header(self, connection_id: str) -> Optional[Dict[str, str]]:
        """Get authentication header for API requests"""
        try:
            connection = self.connections.get(connection_id)
            if not connection:
                return None
            
            if connection.credentials.auth_method == AuthMethod.API_KEY:
                # Decrypt credentials
                decrypted_creds = await self._decrypt_credentials(connection.credentials)
                auth_string = f"{decrypted_creds.api_key}:{decrypted_creds.api_secret}"
                encoded_auth = base64.b64encode(auth_string.encode()).decode()
                return {'Authorization': f'Basic {encoded_auth}'}
            
            elif connection.credentials.auth_method == AuthMethod.OAUTH2:
                if not connection.oauth2_credentials or not connection.oauth2_credentials.access_token:
                    return None
                
                return {
                    'Authorization': f'{connection.oauth2_credentials.token_type} {connection.oauth2_credentials.access_token}'
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get auth header: {e}")
            return None
    
    # Private helper methods
    
    async def _encrypt_credentials(self, credentials: BuildiumCredentials) -> BuildiumCredentials:
        """Encrypt sensitive credential data"""
        encrypted_creds = BuildiumCredentials(
            api_key=self.fernet.encrypt(credentials.api_key.encode()).decode(),
            api_secret=self.fernet.encrypt(credentials.api_secret.encode()).decode(),
            auth_method=credentials.auth_method,
            base_url=credentials.base_url,
            environment=credentials.environment,
            encrypted=True,
            created_at=credentials.created_at,
            expires_at=credentials.expires_at
        )
        return encrypted_creds
    
    async def _decrypt_credentials(self, credentials: BuildiumCredentials) -> BuildiumCredentials:
        """Decrypt credential data"""
        if not credentials.encrypted:
            return credentials
        
        decrypted_creds = BuildiumCredentials(
            api_key=self.fernet.decrypt(credentials.api_key.encode()).decode(),
            api_secret=self.fernet.decrypt(credentials.api_secret.encode()).decode(),
            auth_method=credentials.auth_method,
            base_url=credentials.base_url,
            environment=credentials.environment,
            encrypted=False,
            created_at=credentials.created_at,
            expires_at=credentials.expires_at
        )
        return decrypted_creds
    
    async def _encrypt_oauth2_credentials(self, oauth2_creds: OAuth2Credentials) -> OAuth2Credentials:
        """Encrypt OAuth2 credentials"""
        encrypted_oauth2 = OAuth2Credentials(
            client_id=oauth2_creds.client_id,
            client_secret=self.fernet.encrypt(oauth2_creds.client_secret.encode()).decode(),
            access_token=self.fernet.encrypt(oauth2_creds.access_token.encode()).decode() if oauth2_creds.access_token else None,
            refresh_token=self.fernet.encrypt(oauth2_creds.refresh_token.encode()).decode() if oauth2_creds.refresh_token else None,
            token_type=oauth2_creds.token_type,
            expires_at=oauth2_creds.expires_at,
            scope=oauth2_creds.scope,
            redirect_uri=oauth2_creds.redirect_uri,
            state=oauth2_creds.state
        )
        return encrypted_oauth2
    
    async def _validate_api_key(self, connection: BuildiumConnection) -> bool:
        """Validate API key by making a test request"""
        try:
            auth_header = await self.get_auth_header(connection.connection_id)
            if not auth_header:
                return False
            
            # Test endpoint - get account info
            test_url = f"{connection.credentials.base_url}/v1/account"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(test_url, headers=auth_header) as response:
                    return response.status == 200
            
        except Exception as e:
            logger.error(f"API key validation failed: {e}")
            return False
    
    async def _test_api_connectivity(self, connection: BuildiumConnection) -> bool:
        """Test API connectivity"""
        try:
            auth_header = await self.get_auth_header(connection.connection_id)
            if not auth_header:
                return False
            
            test_url = f"{connection.credentials.base_url}/v1/account"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(test_url, headers=auth_header) as response:
                    if response.status == 200:
                        # Update rate limit info
                        rate_limit_headers = {
                            'limit': response.headers.get('X-RateLimit-Limit'),
                            'remaining': response.headers.get('X-RateLimit-Remaining'),
                            'reset': response.headers.get('X-RateLimit-Reset')
                        }
                        connection.rate_limit_info.update(rate_limit_headers)
                        return True
                    return False
            
        except Exception as e:
            logger.error(f"API connectivity test failed: {e}")
            return False
    
    async def _get_connection_capabilities(self, connection: BuildiumConnection) -> None:
        """Get available products and permissions for connection"""
        try:
            auth_header = await self.get_auth_header(connection.connection_id)
            if not auth_header:
                return
            
            # Get account info to determine capabilities
            account_url = f"{connection.credentials.base_url}/v1/account"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(account_url, headers=auth_header) as response:
                    if response.status == 200:
                        account_data = await response.json()
                        
                        # Map account features to products
                        features = account_data.get('Features', [])
                        connection.products = self._map_features_to_products(features)
                        connection.permissions = account_data.get('Permissions', [])
            
        except Exception as e:
            logger.error(f"Failed to get connection capabilities: {e}")
    
    def _map_features_to_products(self, features: List[str]) -> List[BuildiumProductType]:
        """Map Buildium account features to product types"""
        product_mapping = {
            'PropertyManagement': BuildiumProductType.PROPERTY_MANAGEMENT,
            'RentCollection': BuildiumProductType.RENT_COLLECTION,
            'Maintenance': BuildiumProductType.MAINTENANCE,
            'TenantScreening': BuildiumProductType.TENANT_SCREENING,
            'Accounting': BuildiumProductType.ACCOUNTING,
            'OwnerReporting': BuildiumProductType.OWNER_REPORTING,
            'VendorManagement': BuildiumProductType.VENDOR_MANAGEMENT,
            'DocumentManagement': BuildiumProductType.DOCUMENT_MANAGEMENT
        }
        
        return [product_mapping[feature] for feature in features if feature in product_mapping]
    
    async def _revoke_oauth_token(self, connection: BuildiumConnection) -> None:
        """Revoke OAuth token"""
        try:
            if not connection.oauth2_credentials or not connection.oauth2_credentials.access_token:
                return
            
            revoke_url = "https://api.buildium.com/oauth/revoke"
            token_data = {
                'token': connection.oauth2_credentials.access_token,
                'client_id': connection.oauth2_credentials.client_id,
                'client_secret': connection.oauth2_credentials.client_secret
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(revoke_url, data=token_data) as response:
                    if response.status == 200:
                        logger.info(f"Successfully revoked OAuth token for {connection.connection_id}")
                    else:
                        logger.warning(f"Failed to revoke OAuth token: {response.status}")
            
        except Exception as e:
            logger.error(f"Failed to revoke OAuth token: {e}")