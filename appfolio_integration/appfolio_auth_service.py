"""
AppFolio Authentication Service

Handles OAuth 2.0 authentication and connection management for AppFolio's
property management platform including Property Manager, Investment Manager,
and related services.
"""

import os
import logging
import json
import uuid
import base64
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field, asdict
from enum import Enum
import requests
from urllib.parse import urlencode, parse_qs, urlparse
import jwt
from cryptography.fernet import Fernet

logger = logging.getLogger(__name__)

class AppFolioProductType(Enum):
    """AppFolio product types"""
    PROPERTY_MANAGER = "property_manager"
    INVESTMENT_MANAGER = "investment_manager"
    APM = "apm"  # AppFolio Property Manager
    MAINTENANCE = "maintenance"
    ACCOUNTING = "accounting"
    TENANT_PORTAL = "tenant_portal"
    VENDOR_MANAGEMENT = "vendor_management"
    SCREENING = "screening"
    MARKETING = "marketing"

class AppFolioEnvironment(Enum):
    """AppFolio environments"""
    PRODUCTION = "production"
    SANDBOX = "sandbox"
    STAGING = "staging"
    DEVELOPMENT = "development"

class ConnectionStatus(Enum):
    """Connection status types"""
    PENDING = "pending"
    ACTIVE = "active"
    EXPIRED = "expired"
    REVOKED = "revoked"
    ERROR = "error"
    SUSPENDED = "suspended"

@dataclass
class AppFolioCredentials:
    """AppFolio API credentials"""
    client_id: str
    client_secret: str
    redirect_uri: str
    environment: AppFolioEnvironment
    scopes: List[str] = field(default_factory=list)
    webhook_secret: Optional[str] = None
    encryption_key: Optional[str] = None

@dataclass
class AppFolioConnection:
    """AppFolio connection details"""
    connection_id: str
    organization_id: str
    client_id: str
    product_types: List[AppFolioProductType]
    access_token: str
    refresh_token: str
    token_expires_at: datetime
    refresh_expires_at: datetime
    scopes: List[str]
    company_info: Dict[str, Any]
    environment: AppFolioEnvironment
    status: ConnectionStatus
    created_at: datetime
    last_used_at: Optional[datetime] = None
    last_sync_at: Optional[datetime] = None
    webhook_url: Optional[str] = None
    webhook_secret: Optional[str] = None
    rate_limit_remaining: int = 1000
    rate_limit_reset: Optional[datetime] = None
    connection_metadata: Dict[str, Any] = field(default_factory=dict)
    portfolio_count: int = 0
    unit_count: int = 0
    tenant_count: int = 0

@dataclass
class OAuthState:
    """OAuth state management"""
    state: str
    organization_id: str
    product_types: List[AppFolioProductType]
    redirect_uri: str
    created_at: datetime
    expires_at: datetime
    code_verifier: Optional[str] = None  # For PKCE
    code_challenge: Optional[str] = None

class AppFolioAuthService:
    """
    AppFolio Authentication Service
    
    Manages OAuth 2.0 authentication flow, token management, and secure
    credential storage for AppFolio's property management platform.
    """
    
    def __init__(self):
        # Configuration
        self.client_id = os.environ.get('APPFOLIO_CLIENT_ID')
        self.client_secret = os.environ.get('APPFOLIO_CLIENT_SECRET')
        self.redirect_uri = os.environ.get('APPFOLIO_REDIRECT_URI')
        self.environment = AppFolioEnvironment(
            os.environ.get('APPFOLIO_ENVIRONMENT', 'sandbox')
        )
        self.webhook_secret = os.environ.get('APPFOLIO_WEBHOOK_SECRET')
        
        # Encryption for secure credential storage
        encryption_key = os.environ.get('APPFOLIO_ENCRYPTION_KEY')
        if not encryption_key:
            encryption_key = Fernet.generate_key().decode()
            logger.warning("Generated new encryption key. Store this securely: %s", encryption_key)
        self.cipher = Fernet(encryption_key.encode())
        
        # API endpoints by environment
        self.api_endpoints = {
            AppFolioEnvironment.PRODUCTION: {
                'auth_url': 'https://auth.appfolio.com/oauth/authorize',
                'token_url': 'https://auth.appfolio.com/oauth/token',
                'revoke_url': 'https://auth.appfolio.com/oauth/revoke',
                'userinfo_url': 'https://api.appfolio.com/v1/userinfo',
                'base_api_url': 'https://api.appfolio.com/v1'
            },
            AppFolioEnvironment.SANDBOX: {
                'auth_url': 'https://auth-sandbox.appfolio.com/oauth/authorize',
                'token_url': 'https://auth-sandbox.appfolio.com/oauth/token',
                'revoke_url': 'https://auth-sandbox.appfolio.com/oauth/revoke',
                'userinfo_url': 'https://api-sandbox.appfolio.com/v1/userinfo',
                'base_api_url': 'https://api-sandbox.appfolio.com/v1'
            }
        }
        
        # In-memory storage (in production, use database)
        self.active_connections: Dict[str, AppFolioConnection] = {}
        self.oauth_states: Dict[str, OAuthState] = {}
        self.organization_connections: Dict[str, str] = {}  # org_id -> connection_id
        
        # Product-specific scopes
        self.product_scopes = {
            AppFolioProductType.PROPERTY_MANAGER: [
                'properties:read', 'properties:write',
                'units:read', 'units:write',
                'tenants:read', 'tenants:write',
                'leases:read', 'leases:write',
                'rent_rolls:read', 'payments:read'
            ],
            AppFolioProductType.INVESTMENT_MANAGER: [
                'portfolios:read', 'portfolios:write',
                'investments:read', 'investments:write',
                'financial_reports:read', 'analytics:read'
            ],
            AppFolioProductType.APM: [
                'leasing:read', 'leasing:write',
                'applications:read', 'applications:write',
                'screening:read', 'marketing:read'
            ],
            AppFolioProductType.MAINTENANCE: [
                'work_orders:read', 'work_orders:write',
                'vendors:read', 'vendors:write',
                'maintenance_requests:read', 'maintenance_requests:write'
            ],
            AppFolioProductType.ACCOUNTING: [
                'accounting:read', 'accounting:write',
                'bank_reconciliation:read', 'financial_reports:read',
                'budgets:read', 'budgets:write'
            ],
            AppFolioProductType.TENANT_PORTAL: [
                'resident_portal:read', 'resident_portal:write',
                'communications:read', 'communications:write',
                'online_payments:read'
            ],
            AppFolioProductType.VENDOR_MANAGEMENT: [
                'vendors:read', 'vendors:write',
                'vendor_payments:read', 'vendor_payments:write',
                'purchase_orders:read', 'purchase_orders:write'
            ]
        }
        
        logger.info("AppFolio Authentication Service initialized")
    
    def generate_authorization_url(self, organization_id: str, 
                                 product_types: List[AppFolioProductType],
                                 custom_scopes: List[str] = None,
                                 use_pkce: bool = True) -> Tuple[str, str]:
        """
        Generate OAuth 2.0 authorization URL for AppFolio
        
        Args:
            organization_id: Organization identifier
            product_types: List of AppFolio products to authorize
            custom_scopes: Additional custom scopes
            use_pkce: Use PKCE for additional security
            
        Returns:
            Tuple of (authorization_url, state)
        """
        try:
            # Generate secure state
            state = secrets.token_urlsafe(32)
            
            # Collect scopes for requested products
            scopes = set(['openid', 'profile', 'email'])
            for product in product_types:
                if product in self.product_scopes:
                    scopes.update(self.product_scopes[product])
            
            if custom_scopes:
                scopes.update(custom_scopes)
            
            # PKCE parameters
            code_verifier = None
            code_challenge = None
            if use_pkce:
                code_verifier = base64.urlsafe_b64encode(
                    secrets.token_bytes(32)
                ).decode().rstrip('=')
                
                code_challenge = base64.urlsafe_b64encode(
                    hashlib.sha256(code_verifier.encode()).digest()
                ).decode().rstrip('=')
            
            # Store OAuth state
            oauth_state = OAuthState(
                state=state,
                organization_id=organization_id,
                product_types=product_types,
                redirect_uri=self.redirect_uri,
                created_at=datetime.utcnow(),
                expires_at=datetime.utcnow() + timedelta(minutes=10),
                code_verifier=code_verifier,
                code_challenge=code_challenge
            )
            self.oauth_states[state] = oauth_state
            
            # Build authorization URL
            params = {
                'response_type': 'code',
                'client_id': self.client_id,
                'redirect_uri': self.redirect_uri,
                'scope': ' '.join(scopes),
                'state': state,
                'access_type': 'offline',  # Request refresh token
                'prompt': 'consent'  # Force consent screen
            }
            
            if use_pkce:
                params.update({
                    'code_challenge': code_challenge,
                    'code_challenge_method': 'S256'
                })
            
            auth_url = f"{self.api_endpoints[self.environment]['auth_url']}?{urlencode(params)}"
            
            logger.info(f"Generated authorization URL for organization {organization_id}")
            return auth_url, state
            
        except Exception as e:
            logger.error(f"Failed to generate authorization URL: {str(e)}")
            raise
    
    def exchange_code_for_tokens(self, code: str, state: str) -> AppFolioConnection:
        """
        Exchange authorization code for access and refresh tokens
        
        Args:
            code: Authorization code from callback
            state: OAuth state parameter
            
        Returns:
            AppFolioConnection object
        """
        try:
            # Validate state
            if state not in self.oauth_states:
                raise ValueError("Invalid or expired OAuth state")
            
            oauth_state = self.oauth_states[state]
            
            # Check expiration
            if datetime.utcnow() > oauth_state.expires_at:
                raise ValueError("OAuth state has expired")
            
            # Prepare token request
            token_data = {
                'grant_type': 'authorization_code',
                'client_id': self.client_id,
                'client_secret': self.client_secret,
                'code': code,
                'redirect_uri': oauth_state.redirect_uri
            }
            
            # Add PKCE if used
            if oauth_state.code_verifier:
                token_data['code_verifier'] = oauth_state.code_verifier
            
            # Request tokens
            response = requests.post(
                self.api_endpoints[self.environment]['token_url'],
                data=token_data,
                headers={'Content-Type': 'application/x-www-form-urlencoded'},
                timeout=30
            )
            
            if not response.ok:
                logger.error(f"Token exchange failed: {response.status_code} {response.text}")
                raise Exception(f"Token exchange failed: {response.status_code}")
            
            token_info = response.json()
            
            # Get user/company information
            company_info = self._get_company_info(token_info['access_token'])
            
            # Create connection
            connection_id = str(uuid.uuid4())
            connection = AppFolioConnection(
                connection_id=connection_id,
                organization_id=oauth_state.organization_id,
                client_id=self.client_id,
                product_types=oauth_state.product_types,
                access_token=self._encrypt_token(token_info['access_token']),
                refresh_token=self._encrypt_token(token_info['refresh_token']),
                token_expires_at=datetime.utcnow() + timedelta(seconds=token_info['expires_in']),
                refresh_expires_at=datetime.utcnow() + timedelta(
                    seconds=token_info.get('refresh_expires_in', 7776000)  # 90 days default
                ),
                scopes=token_info.get('scope', '').split(),
                company_info=company_info,
                environment=self.environment,
                status=ConnectionStatus.ACTIVE,
                created_at=datetime.utcnow(),
                portfolio_count=company_info.get('portfolio_count', 0),
                unit_count=company_info.get('unit_count', 0),
                tenant_count=company_info.get('tenant_count', 0)
            )
            
            # Store connection
            self.active_connections[connection_id] = connection
            self.organization_connections[oauth_state.organization_id] = connection_id
            
            # Clean up OAuth state
            del self.oauth_states[state]
            
            logger.info(f"Successfully created AppFolio connection for organization {oauth_state.organization_id}")
            
            return connection
            
        except Exception as e:
            logger.error(f"Failed to exchange code for tokens: {str(e)}")
            raise
    
    def refresh_access_token(self, connection_id: str) -> bool:
        """
        Refresh access token using refresh token
        
        Args:
            connection_id: Connection identifier
            
        Returns:
            True if successful, False otherwise
        """
        try:
            connection = self.active_connections.get(connection_id)
            if not connection:
                logger.error(f"Connection {connection_id} not found")
                return False
            
            # Check if refresh token is still valid
            if datetime.utcnow() >= connection.refresh_expires_at:
                logger.error(f"Refresh token expired for connection {connection_id}")
                connection.status = ConnectionStatus.EXPIRED
                return False
            
            # Prepare refresh request
            refresh_data = {
                'grant_type': 'refresh_token',
                'client_id': self.client_id,
                'client_secret': self.client_secret,
                'refresh_token': self._decrypt_token(connection.refresh_token)
            }
            
            # Request new tokens
            response = requests.post(
                self.api_endpoints[self.environment]['token_url'],
                data=refresh_data,
                headers={'Content-Type': 'application/x-www-form-urlencoded'},
                timeout=30
            )
            
            if not response.ok:
                logger.error(f"Token refresh failed: {response.status_code} {response.text}")
                connection.status = ConnectionStatus.ERROR
                return False
            
            token_info = response.json()
            
            # Update connection with new tokens
            connection.access_token = self._encrypt_token(token_info['access_token'])
            if 'refresh_token' in token_info:
                connection.refresh_token = self._encrypt_token(token_info['refresh_token'])
            
            connection.token_expires_at = datetime.utcnow() + timedelta(
                seconds=token_info['expires_in']
            )
            
            if 'refresh_expires_in' in token_info:
                connection.refresh_expires_at = datetime.utcnow() + timedelta(
                    seconds=token_info['refresh_expires_in']
                )
            
            connection.status = ConnectionStatus.ACTIVE
            
            logger.info(f"Successfully refreshed tokens for connection {connection_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to refresh tokens: {str(e)}")
            if connection_id in self.active_connections:
                self.active_connections[connection_id].status = ConnectionStatus.ERROR
            return False
    
    def get_valid_access_token(self, connection_id: str) -> Optional[str]:
        """
        Get a valid access token, refreshing if necessary
        
        Args:
            connection_id: Connection identifier
            
        Returns:
            Valid access token or None if unavailable
        """
        try:
            connection = self.active_connections.get(connection_id)
            if not connection:
                return None
            
            if connection.status != ConnectionStatus.ACTIVE:
                return None
            
            # Check if token needs refresh (refresh 5 minutes before expiry)
            if datetime.utcnow() + timedelta(minutes=5) >= connection.token_expires_at:
                if not self.refresh_access_token(connection_id):
                    return None
                connection = self.active_connections[connection_id]  # Get updated connection
            
            return self._decrypt_token(connection.access_token)
            
        except Exception as e:
            logger.error(f"Failed to get valid access token: {str(e)}")
            return None
    
    def revoke_connection(self, connection_id: str) -> bool:
        """
        Revoke AppFolio connection and tokens
        
        Args:
            connection_id: Connection identifier
            
        Returns:
            True if successful, False otherwise
        """
        try:
            connection = self.active_connections.get(connection_id)
            if not connection:
                return True  # Already gone
            
            # Revoke tokens with AppFolio
            try:
                access_token = self._decrypt_token(connection.access_token)
                refresh_token = self._decrypt_token(connection.refresh_token)
                
                # Revoke access token
                requests.post(
                    self.api_endpoints[self.environment]['revoke_url'],
                    data={
                        'token': access_token,
                        'client_id': self.client_id,
                        'client_secret': self.client_secret
                    },
                    timeout=30
                )
                
                # Revoke refresh token
                requests.post(
                    self.api_endpoints[self.environment]['revoke_url'],
                    data={
                        'token': refresh_token,
                        'client_id': self.client_id,
                        'client_secret': self.client_secret
                    },
                    timeout=30
                )
                
            except Exception as revoke_error:
                logger.warning(f"Failed to revoke tokens with AppFolio: {revoke_error}")
            
            # Update connection status
            connection.status = ConnectionStatus.REVOKED
            
            # Remove from active connections
            del self.active_connections[connection_id]
            
            # Remove organization mapping
            if connection.organization_id in self.organization_connections:
                del self.organization_connections[connection.organization_id]
            
            logger.info(f"Successfully revoked connection {connection_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to revoke connection: {str(e)}")
            return False
    
    def get_organization_connection(self, organization_id: str) -> Optional[AppFolioConnection]:
        """Get active connection for organization"""
        connection_id = self.organization_connections.get(organization_id)
        if connection_id:
            return self.active_connections.get(connection_id)
        return None
    
    def test_connection(self, connection_id: str) -> Dict[str, Any]:
        """
        Test AppFolio connection validity
        
        Args:
            connection_id: Connection identifier
            
        Returns:
            Test results
        """
        try:
            connection = self.active_connections.get(connection_id)
            if not connection:
                return {
                    'success': False,
                    'error': 'Connection not found'
                }
            
            access_token = self.get_valid_access_token(connection_id)
            if not access_token:
                return {
                    'success': False,
                    'error': 'No valid access token available'
                }
            
            # Test API call
            start_time = datetime.utcnow()
            response = requests.get(
                self.api_endpoints[self.environment]['userinfo_url'],
                headers={'Authorization': f'Bearer {access_token}'},
                timeout=30
            )
            response_time = (datetime.utcnow() - start_time).total_seconds()
            
            if response.ok:
                user_info = response.json()
                return {
                    'success': True,
                    'status': 'connected',
                    'response_time': response_time,
                    'user_info': user_info,
                    'company_info': connection.company_info,
                    'products': [p.value for p in connection.product_types],
                    'scopes': connection.scopes,
                    'portfolio_count': connection.portfolio_count,
                    'unit_count': connection.unit_count,
                    'tenant_count': connection.tenant_count
                }
            else:
                return {
                    'success': False,
                    'error': f'API test failed: {response.status_code}',
                    'response_time': response_time
                }
                
        except Exception as e:
            logger.error(f"Connection test failed: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _get_company_info(self, access_token: str) -> Dict[str, Any]:
        """Get company information from AppFolio"""
        try:
            response = requests.get(
                self.api_endpoints[self.environment]['userinfo_url'],
                headers={'Authorization': f'Bearer {access_token}'},
                timeout=30
            )
            
            if response.ok:
                user_info = response.json()
                
                # Get additional company details
                company_response = requests.get(
                    f"{self.api_endpoints[self.environment]['base_api_url']}/company",
                    headers={'Authorization': f'Bearer {access_token}'},
                    timeout=30
                )
                
                if company_response.ok:
                    company_data = company_response.json()
                    user_info.update(company_data)
                
                return user_info
            else:
                logger.warning(f"Failed to get company info: {response.status_code}")
                return {}
                
        except Exception as e:
            logger.error(f"Failed to get company info: {str(e)}")
            return {}
    
    def _encrypt_token(self, token: str) -> str:
        """Encrypt token for secure storage"""
        return self.cipher.encrypt(token.encode()).decode()
    
    def _decrypt_token(self, encrypted_token: str) -> str:
        """Decrypt token from storage"""
        return self.cipher.decrypt(encrypted_token.encode()).decode()
    
    def get_connection_summary(self, organization_id: str) -> Dict[str, Any]:
        """Get comprehensive connection summary"""
        try:
            connection = self.get_organization_connection(organization_id)
            if not connection:
                return {
                    'connected': False,
                    'status': 'not_connected'
                }
            
            return {
                'connected': True,
                'connection_id': connection.connection_id,
                'status': connection.status.value,
                'products': [p.value for p in connection.product_types],
                'company_name': connection.company_info.get('company_name', 'Unknown'),
                'environment': connection.environment.value,
                'created_at': connection.created_at.isoformat(),
                'last_used_at': connection.last_used_at.isoformat() if connection.last_used_at else None,
                'token_expires_at': connection.token_expires_at.isoformat(),
                'scopes': connection.scopes,
                'rate_limit_remaining': connection.rate_limit_remaining,
                'portfolio_count': connection.portfolio_count,
                'unit_count': connection.unit_count,
                'tenant_count': connection.tenant_count
            }
            
        except Exception as e:
            logger.error(f"Failed to get connection summary: {str(e)}")
            return {
                'connected': False,
                'status': 'error',
                'error': str(e)
            }