"""
RentManager Authentication Service

Comprehensive authentication service for RentManager integration with support for
enterprise security, OAuth 2.0, API key management, and compliance requirements.
"""

import os
import logging
import json
import uuid
import hashlib
import jwt
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict, field
from enum import Enum
import asyncio
import threading
from urllib.parse import urlencode, quote
import secrets
import base64

logger = logging.getLogger(__name__)

class RentManagerProductType(Enum):
    """RentManager product types"""
    PROPERTY_MANAGEMENT = "property_management"
    ASSET_MANAGEMENT = "asset_management" 
    COMPLIANCE_MANAGEMENT = "compliance_management"
    STUDENT_HOUSING = "student_housing"
    AFFORDABLE_HOUSING = "affordable_housing"
    COMMERCIAL_MANAGEMENT = "commercial_management"
    HOA_MANAGEMENT = "hoa_management"
    MAINTENANCE_MANAGEMENT = "maintenance_management"

class AuthenticationType(Enum):
    """Authentication types supported by RentManager"""
    OAUTH2 = "oauth2"
    API_KEY = "api_key"
    JWT_TOKEN = "jwt_token"
    SAML_SSO = "saml_sso"
    BASIC_AUTH = "basic_auth"

class ConnectionStatus(Enum):
    """Connection status"""
    ACTIVE = "active"
    EXPIRED = "expired"
    REVOKED = "revoked"
    SUSPENDED = "suspended"
    PENDING = "pending"

@dataclass
class RentManagerCredentials:
    """RentManager authentication credentials"""
    auth_type: AuthenticationType
    
    # OAuth 2.0 credentials
    client_id: Optional[str] = None
    client_secret: Optional[str] = None
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None
    token_expires_at: Optional[datetime] = None
    
    # API Key authentication
    api_key: Optional[str] = None
    api_secret: Optional[str] = None
    
    # JWT Token authentication
    jwt_token: Optional[str] = None
    jwt_secret: Optional[str] = None
    
    # SAML SSO
    saml_assertion: Optional[str] = None
    saml_response: Optional[str] = None
    
    # Basic authentication
    username: Optional[str] = None
    password: Optional[str] = None
    
    # Environment and endpoints
    base_url: Optional[str] = None
    environment: str = "production"  # production, sandbox, staging
    
    # Security
    encryption_key: Optional[str] = None
    
    # Metadata
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

@dataclass
class RentManagerConnection:
    """RentManager connection information"""
    connection_id: str
    organization_id: str
    
    # Connection details
    product_types: List[RentManagerProductType]
    auth_type: AuthenticationType
    status: ConnectionStatus
    
    # Endpoints and configuration
    base_url: str
    api_version: str = "v1"
    environment: str = "production"
    
    # Company information from RentManager
    company_info: Dict[str, Any] = field(default_factory=dict)
    user_info: Dict[str, Any] = field(default_factory=dict)
    
    # Permissions and scopes
    scopes: List[str] = field(default_factory=list)
    permissions: Dict[str, List[str]] = field(default_factory=dict)
    
    # Portfolio information
    property_count: int = 0
    unit_count: int = 0
    resident_count: int = 0
    portfolio_ids: List[str] = field(default_factory=list)
    
    # Connection tracking
    established_at: datetime = field(default_factory=datetime.utcnow)
    last_used_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    
    # Security and compliance
    security_level: str = "standard"  # basic, standard, enhanced, enterprise
    compliance_flags: List[str] = field(default_factory=list)
    
    # Rate limiting
    rate_limit_per_minute: int = 100
    rate_limit_per_hour: int = 5000
    rate_limit_per_day: int = 50000
    
    # Custom configuration
    custom_config: Dict[str, Any] = field(default_factory=dict)

class RentManagerAuthService:
    """
    RentManager Authentication Service
    
    Manages authentication, connections, and security for RentManager integration
    """
    
    def __init__(self):
        self.connections: Dict[str, RentManagerConnection] = {}
        self.credentials_store: Dict[str, RentManagerCredentials] = {}
        self.oauth_states: Dict[str, Dict[str, Any]] = {}
        self.security_policies: Dict[str, Any] = {}
        
        # Security configuration
        self.encryption_enabled = True
        self.token_refresh_threshold = 300  # 5 minutes before expiry
        self.max_connection_attempts = 3
        self.connection_timeout = 30  # seconds
        
        # OAuth configuration
        self.oauth_config = {
            "authorization_endpoint": "/oauth/authorize",
            "token_endpoint": "/oauth/token",
            "revoke_endpoint": "/oauth/revoke",
            "scope_separator": " ",
            "response_type": "code",
            "grant_type": "authorization_code"
        }
        
        # Compliance configuration
        self.compliance_config = {
            "require_mfa": False,
            "audit_all_requests": True,
            "encrypt_credentials": True,
            "token_rotation_days": 30,
            "session_timeout_minutes": 60
        }
        
        logger.info("RentManager Authentication Service initialized")
    
    # ===================================================
    # OAUTH 2.0 AUTHENTICATION
    # ===================================================
    
    def generate_authorization_url(self, organization_id: str, 
                                 product_types: List[RentManagerProductType],
                                 redirect_uri: str,
                                 custom_scopes: List[str] = None,
                                 state_data: Dict[str, Any] = None) -> tuple[str, str]:
        """
        Generate OAuth 2.0 authorization URL for RentManager
        
        Args:
            organization_id: Organization identifier
            product_types: List of RentManager products to access
            redirect_uri: OAuth redirect URI
            custom_scopes: Additional custom scopes
            state_data: Additional state data
            
        Returns:
            Tuple of (authorization_url, state)
        """
        try:
            # Generate secure state parameter
            state = self._generate_secure_state()
            
            # Build scopes based on product types
            scopes = self._build_scopes_for_products(product_types)
            if custom_scopes:
                scopes.extend(custom_scopes)
            
            # Store OAuth state
            self.oauth_states[state] = {
                "organization_id": organization_id,
                "product_types": [pt.value for pt in product_types],
                "scopes": scopes,
                "redirect_uri": redirect_uri,
                "created_at": datetime.utcnow(),
                "state_data": state_data or {}
            }
            
            # Get OAuth configuration
            client_id = self._get_oauth_client_id(organization_id)
            base_url = self._get_rentmanager_base_url(organization_id)
            
            # Build authorization URL
            auth_params = {
                "response_type": self.oauth_config["response_type"],
                "client_id": client_id,
                "redirect_uri": redirect_uri,
                "scope": self.oauth_config["scope_separator"].join(scopes),
                "state": state,
                "access_type": "offline",  # Request refresh token
                "approval_prompt": "force"
            }
            
            auth_url = f"{base_url}{self.oauth_config['authorization_endpoint']}?{urlencode(auth_params)}"
            
            logger.info(f"Generated OAuth authorization URL for organization {organization_id}")
            
            return auth_url, state
            
        except Exception as e:
            logger.error(f"Failed to generate authorization URL: {e}")
            raise
    
    def exchange_code_for_tokens(self, code: str, state: str) -> RentManagerConnection:
        """
        Exchange authorization code for access and refresh tokens
        
        Args:
            code: Authorization code from RentManager
            state: OAuth state parameter
            
        Returns:
            RentManagerConnection object
        """
        try:
            # Validate state
            if state not in self.oauth_states:
                raise ValueError("Invalid OAuth state parameter")
            
            oauth_state = self.oauth_states[state]
            organization_id = oauth_state["organization_id"]
            
            # Exchange code for tokens
            token_response = self._exchange_authorization_code(
                code, oauth_state["redirect_uri"], organization_id
            )
            
            # Create credentials
            credentials = RentManagerCredentials(
                auth_type=AuthenticationType.OAUTH2,
                client_id=self._get_oauth_client_id(organization_id),
                client_secret=self._get_oauth_client_secret(organization_id),
                access_token=token_response["access_token"],
                refresh_token=token_response.get("refresh_token"),
                token_expires_at=datetime.utcnow() + timedelta(seconds=token_response.get("expires_in", 3600)),
                base_url=self._get_rentmanager_base_url(organization_id)
            )
            
            # Store encrypted credentials
            self._store_credentials(organization_id, credentials)
            
            # Get user and company information
            user_info = self._get_user_info(credentials)
            company_info = self._get_company_info(credentials)
            portfolio_info = self._get_portfolio_info(credentials)
            
            # Create connection
            connection = RentManagerConnection(
                connection_id=str(uuid.uuid4()),
                organization_id=organization_id,
                product_types=[RentManagerProductType(pt) for pt in oauth_state["product_types"]],
                auth_type=AuthenticationType.OAUTH2,
                status=ConnectionStatus.ACTIVE,
                base_url=credentials.base_url,
                company_info=company_info,
                user_info=user_info,
                scopes=oauth_state["scopes"],
                property_count=portfolio_info.get("property_count", 0),
                unit_count=portfolio_info.get("unit_count", 0),
                resident_count=portfolio_info.get("resident_count", 0),
                portfolio_ids=portfolio_info.get("portfolio_ids", []),
                expires_at=credentials.token_expires_at
            )
            
            # Store connection
            self.connections[organization_id] = connection
            
            # Clean up OAuth state
            del self.oauth_states[state]
            
            logger.info(f"Successfully established RentManager connection for organization {organization_id}")
            
            return connection
            
        except Exception as e:
            logger.error(f"Failed to exchange authorization code: {e}")
            raise
    
    # ===================================================
    # API KEY AUTHENTICATION
    # ===================================================
    
    def create_api_key_connection(self, organization_id: str, api_key: str, 
                                api_secret: str, base_url: str,
                                product_types: List[RentManagerProductType]) -> RentManagerConnection:
        """
        Create connection using API key authentication
        
        Args:
            organization_id: Organization identifier
            api_key: RentManager API key
            api_secret: RentManager API secret
            base_url: RentManager API base URL
            product_types: List of RentManager products
            
        Returns:
            RentManagerConnection object
        """
        try:
            # Create credentials
            credentials = RentManagerCredentials(
                auth_type=AuthenticationType.API_KEY,
                api_key=api_key,
                api_secret=api_secret,
                base_url=base_url
            )
            
            # Test connection
            if not self._test_api_key_connection(credentials):
                raise ValueError("Invalid API credentials")
            
            # Store encrypted credentials
            self._store_credentials(organization_id, credentials)
            
            # Get company and portfolio information
            company_info = self._get_company_info(credentials)
            portfolio_info = self._get_portfolio_info(credentials)
            
            # Create connection
            connection = RentManagerConnection(
                connection_id=str(uuid.uuid4()),
                organization_id=organization_id,
                product_types=product_types,
                auth_type=AuthenticationType.API_KEY,
                status=ConnectionStatus.ACTIVE,
                base_url=base_url,
                company_info=company_info,
                property_count=portfolio_info.get("property_count", 0),
                unit_count=portfolio_info.get("unit_count", 0),
                resident_count=portfolio_info.get("resident_count", 0),
                portfolio_ids=portfolio_info.get("portfolio_ids", [])
            )
            
            # Store connection
            self.connections[organization_id] = connection
            
            logger.info(f"Successfully created API key connection for organization {organization_id}")
            
            return connection
            
        except Exception as e:
            logger.error(f"Failed to create API key connection: {e}")
            raise
    
    # ===================================================
    # TOKEN MANAGEMENT
    # ===================================================
    
    def refresh_access_token(self, organization_id: str) -> bool:
        """
        Refresh OAuth access token
        
        Args:
            organization_id: Organization identifier
            
        Returns:
            True if token refreshed successfully
        """
        try:
            credentials = self._get_credentials(organization_id)
            if not credentials or credentials.auth_type != AuthenticationType.OAUTH2:
                return False
            
            if not credentials.refresh_token:
                logger.warning(f"No refresh token available for organization {organization_id}")
                return False
            
            # Check if token needs refresh
            if credentials.token_expires_at and \
               credentials.token_expires_at > datetime.utcnow() + timedelta(seconds=self.token_refresh_threshold):
                return True  # Token still valid
            
            # Refresh token
            token_response = self._refresh_oauth_token(credentials)
            
            # Update credentials
            credentials.access_token = token_response["access_token"]
            if "refresh_token" in token_response:
                credentials.refresh_token = token_response["refresh_token"]
            credentials.token_expires_at = datetime.utcnow() + timedelta(
                seconds=token_response.get("expires_in", 3600)
            )
            credentials.updated_at = datetime.utcnow()
            
            # Store updated credentials
            self._store_credentials(organization_id, credentials)
            
            # Update connection expiry
            if organization_id in self.connections:
                self.connections[organization_id].expires_at = credentials.token_expires_at
                self.connections[organization_id].last_used_at = datetime.utcnow()
            
            logger.info(f"Successfully refreshed access token for organization {organization_id}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to refresh access token: {e}")
            return False
    
    def revoke_connection(self, connection_id: str) -> Dict[str, Any]:
        """
        Revoke RentManager connection and tokens
        
        Args:
            connection_id: Connection identifier
            
        Returns:
            Dict with revocation results
        """
        try:
            # Find connection by ID
            connection = None
            organization_id = None
            
            for org_id, conn in self.connections.items():
                if conn.connection_id == connection_id:
                    connection = conn
                    organization_id = org_id
                    break
            
            if not connection:
                return {"success": False, "error": "Connection not found"}
            
            credentials = self._get_credentials(organization_id)
            
            # Revoke tokens if OAuth
            if credentials and credentials.auth_type == AuthenticationType.OAUTH2:
                try:
                    self._revoke_oauth_token(credentials)
                except Exception as e:
                    logger.warning(f"Failed to revoke OAuth token: {e}")
            
            # Update connection status
            connection.status = ConnectionStatus.REVOKED
            
            # Remove credentials
            if organization_id in self.credentials_store:
                del self.credentials_store[organization_id]
            
            logger.info(f"Successfully revoked connection {connection_id}")
            
            return {"success": True}
            
        except Exception as e:
            logger.error(f"Failed to revoke connection: {e}")
            return {"success": False, "error": str(e)}
    
    # ===================================================
    # CONNECTION MANAGEMENT
    # ===================================================
    
    def get_organization_connection(self, organization_id: str) -> Optional[RentManagerConnection]:
        """Get active connection for organization"""
        return self.connections.get(organization_id)
    
    def get_connection_by_id(self, connection_id: str) -> Optional[RentManagerConnection]:
        """Get connection by connection ID"""
        for connection in self.connections.values():
            if connection.connection_id == connection_id:
                return connection
        return None
    
    def get_valid_credentials(self, organization_id: str) -> Optional[RentManagerCredentials]:
        """
        Get valid credentials for organization, refreshing if necessary
        
        Args:
            organization_id: Organization identifier
            
        Returns:
            Valid RentManagerCredentials or None
        """
        try:
            credentials = self._get_credentials(organization_id)
            if not credentials:
                return None
            
            # Check if OAuth token needs refresh
            if credentials.auth_type == AuthenticationType.OAUTH2:
                if credentials.token_expires_at and \
                   credentials.token_expires_at <= datetime.utcnow() + timedelta(seconds=self.token_refresh_threshold):
                    if not self.refresh_access_token(organization_id):
                        return None
                    credentials = self._get_credentials(organization_id)
            
            return credentials
            
        except Exception as e:
            logger.error(f"Failed to get valid credentials: {e}")
            return None
    
    def validate_connection(self, organization_id: str) -> Dict[str, Any]:
        """
        Validate existing connection
        
        Args:
            organization_id: Organization identifier
            
        Returns:
            Dict with validation results
        """
        try:
            connection = self.get_organization_connection(organization_id)
            if not connection:
                return {
                    "valid": False,
                    "error": "No connection found",
                    "status": "not_connected"
                }
            
            credentials = self.get_valid_credentials(organization_id)
            if not credentials:
                return {
                    "valid": False,
                    "error": "Invalid or expired credentials",
                    "status": "expired"
                }
            
            # Test connection with a simple API call
            test_result = self._test_connection(credentials)
            
            if test_result:
                connection.last_used_at = datetime.utcnow()
                connection.status = ConnectionStatus.ACTIVE
                
                return {
                    "valid": True,
                    "status": "active",
                    "connection_id": connection.connection_id,
                    "company_name": connection.company_info.get("name", "Unknown"),
                    "last_used": connection.last_used_at.isoformat()
                }
            else:
                connection.status = ConnectionStatus.SUSPENDED
                return {
                    "valid": False,
                    "error": "Connection test failed",
                    "status": "suspended"
                }
                
        except Exception as e:
            logger.error(f"Failed to validate connection: {e}")
            return {
                "valid": False,
                "error": str(e),
                "status": "error"
            }
    
    # ===================================================
    # SECURITY AND ENCRYPTION
    # ===================================================
    
    def _store_credentials(self, organization_id: str, credentials: RentManagerCredentials):
        """Store credentials with encryption if enabled"""
        if self.encryption_enabled:
            encrypted_credentials = self._encrypt_credentials(credentials)
            self.credentials_store[organization_id] = encrypted_credentials
        else:
            self.credentials_store[organization_id] = credentials
    
    def _get_credentials(self, organization_id: str) -> Optional[RentManagerCredentials]:
        """Get and decrypt credentials if needed"""
        if organization_id not in self.credentials_store:
            return None
        
        credentials = self.credentials_store[organization_id]
        
        if self.encryption_enabled and hasattr(credentials, 'encrypted'):
            return self._decrypt_credentials(credentials)
        
        return credentials
    
    def _encrypt_credentials(self, credentials: RentManagerCredentials) -> RentManagerCredentials:
        """Encrypt sensitive credential data"""
        # Implementation would use proper encryption library
        # For now, just mark as encrypted
        credentials.encryption_key = self._generate_encryption_key()
        return credentials
    
    def _decrypt_credentials(self, credentials: RentManagerCredentials) -> RentManagerCredentials:
        """Decrypt credential data"""
        # Implementation would decrypt using stored encryption key
        return credentials
    
    def _generate_encryption_key(self) -> str:
        """Generate encryption key for credentials"""
        return base64.b64encode(secrets.token_bytes(32)).decode('utf-8')
    
    def _generate_secure_state(self) -> str:
        """Generate secure OAuth state parameter"""
        return base64.b64encode(secrets.token_bytes(32)).decode('utf-8')
    
    # ===================================================
    # RENTMANAGER API INTERACTIONS
    # ===================================================
    
    def _exchange_authorization_code(self, code: str, redirect_uri: str, 
                                   organization_id: str) -> Dict[str, Any]:
        """Exchange authorization code for tokens"""
        # Implementation would make actual API call to RentManager
        # Simulated response for now
        return {
            "access_token": f"access_token_{uuid.uuid4()}",
            "refresh_token": f"refresh_token_{uuid.uuid4()}",
            "expires_in": 3600,
            "token_type": "Bearer"
        }
    
    def _refresh_oauth_token(self, credentials: RentManagerCredentials) -> Dict[str, Any]:
        """Refresh OAuth access token"""
        # Implementation would make actual API call to RentManager
        # Simulated response for now
        return {
            "access_token": f"new_access_token_{uuid.uuid4()}",
            "expires_in": 3600,
            "token_type": "Bearer"
        }
    
    def _revoke_oauth_token(self, credentials: RentManagerCredentials):
        """Revoke OAuth tokens"""
        # Implementation would make actual API call to RentManager
        logger.info("OAuth token revoked")
    
    def _test_api_key_connection(self, credentials: RentManagerCredentials) -> bool:
        """Test API key connection"""
        # Implementation would make actual API call to RentManager
        return True
    
    def _test_connection(self, credentials: RentManagerCredentials) -> bool:
        """Test connection with a simple API call"""
        # Implementation would make actual API call to RentManager
        return True
    
    def _get_user_info(self, credentials: RentManagerCredentials) -> Dict[str, Any]:
        """Get user information from RentManager"""
        # Implementation would make actual API call to RentManager
        return {
            "user_id": str(uuid.uuid4()),
            "username": "api_user",
            "email": "user@company.com",
            "name": "API User",
            "roles": ["property_manager", "compliance_officer"]
        }
    
    def _get_company_info(self, credentials: RentManagerCredentials) -> Dict[str, Any]:
        """Get company information from RentManager"""
        # Implementation would make actual API call to RentManager
        return {
            "company_id": str(uuid.uuid4()),
            "name": "Sample Property Management",
            "type": "property_management",
            "license_number": "PM123456",
            "address": {
                "street": "123 Management St",
                "city": "Property City",
                "state": "CA",
                "zip": "90210"
            },
            "contact": {
                "phone": "(555) 123-4567",
                "email": "info@samplepm.com",
                "website": "www.samplepm.com"
            }
        }
    
    def _get_portfolio_info(self, credentials: RentManagerCredentials) -> Dict[str, Any]:
        """Get portfolio information from RentManager"""
        # Implementation would make actual API call to RentManager
        return {
            "property_count": 25,
            "unit_count": 1250,
            "resident_count": 1100,
            "portfolio_ids": [str(uuid.uuid4()) for _ in range(3)],
            "property_types": ["multi_family", "commercial", "affordable_housing"]
        }
    
    # ===================================================
    # UTILITY METHODS
    # ===================================================
    
    def _build_scopes_for_products(self, product_types: List[RentManagerProductType]) -> List[str]:
        """Build OAuth scopes based on product types"""
        scope_mapping = {
            RentManagerProductType.PROPERTY_MANAGEMENT: [
                "properties:read", "properties:write", "units:read", "units:write",
                "residents:read", "residents:write", "leases:read", "leases:write"
            ],
            RentManagerProductType.ASSET_MANAGEMENT: [
                "assets:read", "assets:write", "portfolio:read", "portfolio:write",
                "financials:read", "reporting:read"
            ],
            RentManagerProductType.COMPLIANCE_MANAGEMENT: [
                "compliance:read", "compliance:write", "certifications:read",
                "certifications:write", "audits:read", "audits:write"
            ],
            RentManagerProductType.STUDENT_HOUSING: [
                "students:read", "students:write", "roommates:read", "roommates:write",
                "academic:read", "academic:write"
            ],
            RentManagerProductType.AFFORDABLE_HOUSING: [
                "income_cert:read", "income_cert:write", "ami:read", "ami:write",
                "compliance:read", "compliance:write"
            ],
            RentManagerProductType.COMMERCIAL_MANAGEMENT: [
                "commercial:read", "commercial:write", "cam:read", "cam:write",
                "leases_commercial:read", "leases_commercial:write"
            ],
            RentManagerProductType.HOA_MANAGEMENT: [
                "hoa:read", "hoa:write", "assessments:read", "assessments:write",
                "board:read", "violations:read", "violations:write"
            ],
            RentManagerProductType.MAINTENANCE_MANAGEMENT: [
                "workorders:read", "workorders:write", "vendors:read", "vendors:write",
                "maintenance:read", "maintenance:write"
            ]
        }
        
        scopes = set()
        for product_type in product_types:
            scopes.update(scope_mapping.get(product_type, []))
        
        # Always include basic scopes
        scopes.update(["profile:read", "company:read"])
        
        return list(scopes)
    
    def _get_oauth_client_id(self, organization_id: str) -> str:
        """Get OAuth client ID for organization"""
        # Implementation would retrieve from secure configuration
        return os.getenv("RENTMANAGER_CLIENT_ID", "default_client_id")
    
    def _get_oauth_client_secret(self, organization_id: str) -> str:
        """Get OAuth client secret for organization"""
        # Implementation would retrieve from secure configuration
        return os.getenv("RENTMANAGER_CLIENT_SECRET", "default_client_secret")
    
    def _get_rentmanager_base_url(self, organization_id: str) -> str:
        """Get RentManager base URL for organization"""
        # Implementation would determine correct endpoint based on organization
        return os.getenv("RENTMANAGER_BASE_URL", "https://api.rentmanager.com")

# Global service instance
_auth_service = None

def get_rentmanager_auth_service() -> RentManagerAuthService:
    """Get singleton auth service instance"""
    global _auth_service
    if _auth_service is None:
        _auth_service = RentManagerAuthService()
    return _auth_service