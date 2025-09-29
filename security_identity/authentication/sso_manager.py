#!/usr/bin/env python3
"""
Single Sign-On (SSO) Manager for EstateCore Phase 8D
SAML 2.0 and OAuth 2.0/OpenID Connect integration for enterprise authentication
"""

import os
import json
import base64
import hashlib
import hmac
import secrets
import asyncio
import logging
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import sqlite3
import uuid
import jwt
import aiohttp
from urllib.parse import urlencode, parse_qs, urlparse
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.x509 import load_pem_x509_certificate
import xmlsec

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SSOProvider(Enum):
    SAML_GENERIC = "saml_generic"
    AZURE_AD = "azure_ad"
    GOOGLE_WORKSPACE = "google_workspace"
    OKTA = "okta"
    ONELOGIN = "onelogin"
    OAUTH_GENERIC = "oauth_generic"
    OIDC_GENERIC = "oidc_generic"

class SSOProtocol(Enum):
    SAML2 = "saml2"
    OAUTH2 = "oauth2"
    OIDC = "oidc"

class SSOStatus(Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    PENDING_CONFIGURATION = "pending_configuration"
    ERROR = "error"

@dataclass
class SSOConfiguration:
    """SSO provider configuration"""
    provider_id: str
    provider_name: str
    provider_type: SSOProvider
    protocol: SSOProtocol
    status: SSOStatus
    
    # SAML Configuration
    idp_entity_id: Optional[str]
    idp_sso_url: Optional[str]
    idp_slo_url: Optional[str]
    idp_certificate: Optional[str]
    sp_entity_id: Optional[str]
    sp_acs_url: Optional[str]
    sp_slo_url: Optional[str]
    sp_certificate: Optional[str]
    sp_private_key: Optional[str]
    
    # OAuth/OIDC Configuration
    client_id: Optional[str]
    client_secret: Optional[str]
    authorization_endpoint: Optional[str]
    token_endpoint: Optional[str]
    userinfo_endpoint: Optional[str]
    jwks_uri: Optional[str]
    issuer: Optional[str]
    
    # General Configuration
    scopes: List[str]
    attribute_mapping: Dict[str, str]
    auto_provision: bool
    default_roles: List[str]
    created_at: datetime
    updated_at: datetime
    metadata: Dict[str, Any]

@dataclass
class SSOSession:
    """SSO session information"""
    session_id: str
    user_id: str
    provider_id: str
    provider_session_id: Optional[str]
    saml_session_index: Optional[str]
    created_at: datetime
    expires_at: datetime
    last_activity: datetime
    ip_address: str
    user_agent: str
    attributes: Dict[str, Any]

@dataclass
class SSOAuthRequest:
    """SSO authentication request"""
    request_id: str
    provider_id: str
    redirect_uri: str
    state: str
    nonce: Optional[str]
    created_at: datetime
    expires_at: datetime
    metadata: Dict[str, Any]

@dataclass
class SSOAuthResult:
    """SSO authentication result"""
    success: bool
    user_id: Optional[str]
    provider_id: str
    session_id: Optional[str]
    error_message: Optional[str]
    user_attributes: Dict[str, Any]
    is_new_user: bool
    metadata: Dict[str, Any]

class SSOManager:
    """Single Sign-On Manager"""
    
    def __init__(self, database_path: str = "sso_database.db"):
        self.database_path = database_path
        
        # SAML configuration
        self.saml_settings = {
            'sp_entity_id': f"https://{os.getenv('DOMAIN', 'localhost')}/sso/metadata",
            'sp_acs_url': f"https://{os.getenv('DOMAIN', 'localhost')}/sso/acs",
            'sp_slo_url': f"https://{os.getenv('DOMAIN', 'localhost')}/sso/sls",
            'attribute_consuming_service': {
                'serviceName': 'EstateCore',
                'serviceDescription': 'EstateCore Property Management',
                'requestedAttributes': [
                    {'name': 'email', 'isRequired': True},
                    {'name': 'firstName', 'isRequired': True},
                    {'name': 'lastName', 'isRequired': True},
                    {'name': 'groups', 'isRequired': False}
                ]
            }
        }
        
        # OAuth/OIDC configuration
        self.oauth_settings = {
            'redirect_uri': f"https://{os.getenv('DOMAIN', 'localhost')}/sso/oauth/callback",
            'response_type': 'code',
            'response_mode': 'form_post',
            'scope': 'openid profile email'
        }
        
        # Session settings
        self.session_timeout_hours = 8
        self.request_timeout_minutes = 10
        
        # Initialize database
        self._initialize_database()
        
        logger.info("SSO Manager initialized")
    
    def _initialize_database(self):
        """Initialize SSO database"""
        conn = sqlite3.connect(self.database_path)
        cursor = conn.cursor()
        
        # SSO configurations table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sso_configurations (
                provider_id TEXT PRIMARY KEY,
                provider_name TEXT NOT NULL,
                provider_type TEXT NOT NULL,
                protocol TEXT NOT NULL,
                status TEXT NOT NULL,
                idp_entity_id TEXT,
                idp_sso_url TEXT,
                idp_slo_url TEXT,
                idp_certificate TEXT,
                sp_entity_id TEXT,
                sp_acs_url TEXT,
                sp_slo_url TEXT,
                sp_certificate TEXT,
                sp_private_key TEXT,
                client_id TEXT,
                client_secret TEXT,
                authorization_endpoint TEXT,
                token_endpoint TEXT,
                userinfo_endpoint TEXT,
                jwks_uri TEXT,
                issuer TEXT,
                scopes TEXT,
                attribute_mapping TEXT,
                auto_provision BOOLEAN DEFAULT 1,
                default_roles TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                metadata TEXT
            )
        """)
        
        # SSO sessions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sso_sessions (
                session_id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                provider_id TEXT NOT NULL,
                provider_session_id TEXT,
                saml_session_index TEXT,
                created_at TEXT NOT NULL,
                expires_at TEXT NOT NULL,
                last_activity TEXT NOT NULL,
                ip_address TEXT,
                user_agent TEXT,
                attributes TEXT,
                FOREIGN KEY (provider_id) REFERENCES sso_configurations (provider_id)
            )
        """)
        
        # SSO auth requests table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sso_auth_requests (
                request_id TEXT PRIMARY KEY,
                provider_id TEXT NOT NULL,
                redirect_uri TEXT NOT NULL,
                state TEXT NOT NULL,
                nonce TEXT,
                created_at TEXT NOT NULL,
                expires_at TEXT NOT NULL,
                metadata TEXT,
                FOREIGN KEY (provider_id) REFERENCES sso_configurations (provider_id)
            )
        """)
        
        # User provider mappings table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_provider_mappings (
                mapping_id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                provider_id TEXT NOT NULL,
                provider_user_id TEXT NOT NULL,
                provider_username TEXT,
                created_at TEXT NOT NULL,
                last_login TEXT,
                login_count INTEGER DEFAULT 1,
                attributes TEXT,
                FOREIGN KEY (provider_id) REFERENCES sso_configurations (provider_id),
                UNIQUE(provider_id, provider_user_id)
            )
        """)
        
        # Create indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_sso_sessions_user ON sso_sessions (user_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_sso_sessions_expires ON sso_sessions (expires_at)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_user_mappings_user ON user_provider_mappings (user_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_user_mappings_provider ON user_provider_mappings (provider_id, provider_user_id)")
        
        conn.commit()
        conn.close()
    
    async def configure_saml_provider(self, provider_config: Dict[str, Any]) -> str:
        """Configure SAML 2.0 provider"""
        try:
            provider_id = str(uuid.uuid4())
            
            config = SSOConfiguration(
                provider_id=provider_id,
                provider_name=provider_config['name'],
                provider_type=SSOProvider(provider_config['type']),
                protocol=SSOProtocol.SAML2,
                status=SSOStatus.PENDING_CONFIGURATION,
                
                # SAML specific
                idp_entity_id=provider_config.get('idp_entity_id'),
                idp_sso_url=provider_config.get('idp_sso_url'),
                idp_slo_url=provider_config.get('idp_slo_url'),
                idp_certificate=provider_config.get('idp_certificate'),
                sp_entity_id=self.saml_settings['sp_entity_id'],
                sp_acs_url=self.saml_settings['sp_acs_url'],
                sp_slo_url=self.saml_settings['sp_slo_url'],
                sp_certificate=provider_config.get('sp_certificate'),
                sp_private_key=provider_config.get('sp_private_key'),
                
                # OAuth/OIDC (not used)
                client_id=None,
                client_secret=None,
                authorization_endpoint=None,
                token_endpoint=None,
                userinfo_endpoint=None,
                jwks_uri=None,
                issuer=None,
                
                scopes=[],
                attribute_mapping=provider_config.get('attribute_mapping', {
                    'email': 'http://schemas.xmlsoap.org/ws/2005/05/identity/claims/emailaddress',
                    'firstName': 'http://schemas.xmlsoap.org/ws/2005/05/identity/claims/givenname',
                    'lastName': 'http://schemas.xmlsoap.org/ws/2005/05/identity/claims/surname',
                    'groups': 'http://schemas.microsoft.com/ws/2008/06/identity/claims/groups'
                }),
                auto_provision=provider_config.get('auto_provision', True),
                default_roles=provider_config.get('default_roles', ['user']),
                created_at=datetime.now(),
                updated_at=datetime.now(),
                metadata=provider_config.get('metadata', {})
            )
            
            await self._save_sso_configuration(config)
            
            # Validate configuration
            if await self._validate_saml_configuration(config):
                config.status = SSOStatus.ACTIVE
                await self._save_sso_configuration(config)
            
            logger.info(f"SAML provider {provider_config['name']} configured with ID {provider_id}")
            return provider_id
            
        except Exception as e:
            logger.error(f"Error configuring SAML provider: {e}")
            raise
    
    async def configure_oauth_provider(self, provider_config: Dict[str, Any]) -> str:
        """Configure OAuth 2.0/OIDC provider"""
        try:
            provider_id = str(uuid.uuid4())
            
            config = SSOConfiguration(
                provider_id=provider_id,
                provider_name=provider_config['name'],
                provider_type=SSOProvider(provider_config['type']),
                protocol=SSOProtocol(provider_config.get('protocol', 'oidc')),
                status=SSOStatus.PENDING_CONFIGURATION,
                
                # SAML (not used)
                idp_entity_id=None,
                idp_sso_url=None,
                idp_slo_url=None,
                idp_certificate=None,
                sp_entity_id=None,
                sp_acs_url=None,
                sp_slo_url=None,
                sp_certificate=None,
                sp_private_key=None,
                
                # OAuth/OIDC specific
                client_id=provider_config['client_id'],
                client_secret=provider_config['client_secret'],
                authorization_endpoint=provider_config['authorization_endpoint'],
                token_endpoint=provider_config['token_endpoint'],
                userinfo_endpoint=provider_config.get('userinfo_endpoint'),
                jwks_uri=provider_config.get('jwks_uri'),
                issuer=provider_config.get('issuer'),
                
                scopes=provider_config.get('scopes', ['openid', 'profile', 'email']),
                attribute_mapping=provider_config.get('attribute_mapping', {
                    'email': 'email',
                    'firstName': 'given_name',
                    'lastName': 'family_name',
                    'groups': 'groups'
                }),
                auto_provision=provider_config.get('auto_provision', True),
                default_roles=provider_config.get('default_roles', ['user']),
                created_at=datetime.now(),
                updated_at=datetime.now(),
                metadata=provider_config.get('metadata', {})
            )
            
            await self._save_sso_configuration(config)
            
            # Validate configuration
            if await self._validate_oauth_configuration(config):
                config.status = SSOStatus.ACTIVE
                await self._save_sso_configuration(config)
            
            logger.info(f"OAuth provider {provider_config['name']} configured with ID {provider_id}")
            return provider_id
            
        except Exception as e:
            logger.error(f"Error configuring OAuth provider: {e}")
            raise
    
    async def initiate_saml_auth(self, provider_id: str, redirect_uri: str) -> Dict[str, Any]:
        """Initiate SAML authentication"""
        try:
            config = await self._get_sso_configuration(provider_id)
            if not config or config.protocol != SSOProtocol.SAML2:
                raise ValueError("Invalid SAML provider")
            
            # Generate request ID and state
            request_id = str(uuid.uuid4())
            state = secrets.token_urlsafe(32)
            
            # Store auth request
            auth_request = SSOAuthRequest(
                request_id=request_id,
                provider_id=provider_id,
                redirect_uri=redirect_uri,
                state=state,
                nonce=None,
                created_at=datetime.now(),
                expires_at=datetime.now() + timedelta(minutes=self.request_timeout_minutes),
                metadata={}
            )
            
            await self._save_auth_request(auth_request)
            
            # Generate SAML AuthnRequest
            saml_request = self._generate_saml_authn_request(config, request_id)
            
            # Encode and sign
            saml_request_encoded = base64.b64encode(saml_request.encode()).decode()
            
            # Create redirect URL
            auth_url = f"{config.idp_sso_url}?{urlencode({
                'SAMLRequest': saml_request_encoded,
                'RelayState': state
            })}"
            
            return {
                'auth_url': auth_url,
                'request_id': request_id,
                'state': state
            }
            
        except Exception as e:
            logger.error(f"Error initiating SAML auth: {e}")
            raise
    
    async def initiate_oauth_auth(self, provider_id: str, redirect_uri: str) -> Dict[str, Any]:
        """Initiate OAuth/OIDC authentication"""
        try:
            config = await self._get_sso_configuration(provider_id)
            if not config or config.protocol not in [SSOProtocol.OAUTH2, SSOProtocol.OIDC]:
                raise ValueError("Invalid OAuth provider")
            
            # Generate state and nonce
            state = secrets.token_urlsafe(32)
            nonce = secrets.token_urlsafe(32) if config.protocol == SSOProtocol.OIDC else None
            
            # Store auth request
            auth_request = SSOAuthRequest(
                request_id=str(uuid.uuid4()),
                provider_id=provider_id,
                redirect_uri=redirect_uri,
                state=state,
                nonce=nonce,
                created_at=datetime.now(),
                expires_at=datetime.now() + timedelta(minutes=self.request_timeout_minutes),
                metadata={}
            )
            
            await self._save_auth_request(auth_request)
            
            # Build authorization URL
            params = {
                'client_id': config.client_id,
                'response_type': 'code',
                'scope': ' '.join(config.scopes),
                'redirect_uri': self.oauth_settings['redirect_uri'],
                'state': state
            }
            
            if nonce:
                params['nonce'] = nonce
            
            auth_url = f"{config.authorization_endpoint}?{urlencode(params)}"
            
            return {
                'auth_url': auth_url,
                'request_id': auth_request.request_id,
                'state': state
            }
            
        except Exception as e:
            logger.error(f"Error initiating OAuth auth: {e}")
            raise
    
    async def handle_saml_response(self, saml_response: str, relay_state: str, 
                                 ip_address: str, user_agent: str) -> SSOAuthResult:
        """Handle SAML authentication response"""
        try:
            # Validate relay state and get auth request
            auth_request = await self._get_auth_request_by_state(relay_state)
            if not auth_request:
                return SSOAuthResult(
                    success=False,
                    user_id=None,
                    provider_id="",
                    session_id=None,
                    error_message="Invalid or expired request",
                    user_attributes={},
                    is_new_user=False,
                    metadata={}
                )
            
            config = await self._get_sso_configuration(auth_request.provider_id)
            
            # Decode and validate SAML response
            decoded_response = base64.b64decode(saml_response).decode()
            attributes = await self._parse_saml_response(decoded_response, config)
            
            if not attributes:
                return SSOAuthResult(
                    success=False,
                    user_id=None,
                    provider_id=auth_request.provider_id,
                    session_id=None,
                    error_message="Invalid SAML response",
                    user_attributes={},
                    is_new_user=False,
                    metadata={}
                )
            
            # Map attributes to user profile
            user_profile = self._map_attributes(attributes, config.attribute_mapping)
            
            # Find or create user
            user_id, is_new_user = await self._find_or_create_user(
                auth_request.provider_id, user_profile, config
            )
            
            # Create SSO session
            session_id = await self._create_sso_session(
                user_id, auth_request.provider_id, attributes,
                ip_address, user_agent
            )
            
            # Clean up auth request
            await self._delete_auth_request(auth_request.request_id)
            
            return SSOAuthResult(
                success=True,
                user_id=user_id,
                provider_id=auth_request.provider_id,
                session_id=session_id,
                error_message=None,
                user_attributes=user_profile,
                is_new_user=is_new_user,
                metadata={"saml_attributes": attributes}
            )
            
        except Exception as e:
            logger.error(f"Error handling SAML response: {e}")
            return SSOAuthResult(
                success=False,
                user_id=None,
                provider_id="",
                session_id=None,
                error_message=str(e),
                user_attributes={},
                is_new_user=False,
                metadata={}
            )
    
    async def handle_oauth_callback(self, code: str, state: str, 
                                  ip_address: str, user_agent: str) -> SSOAuthResult:
        """Handle OAuth/OIDC callback"""
        try:
            # Validate state and get auth request
            auth_request = await self._get_auth_request_by_state(state)
            if not auth_request:
                return SSOAuthResult(
                    success=False,
                    user_id=None,
                    provider_id="",
                    session_id=None,
                    error_message="Invalid or expired request",
                    user_attributes={},
                    is_new_user=False,
                    metadata={}
                )
            
            config = await self._get_sso_configuration(auth_request.provider_id)
            
            # Exchange code for tokens
            token_response = await self._exchange_oauth_code(code, config)
            if not token_response:
                return SSOAuthResult(
                    success=False,
                    user_id=None,
                    provider_id=auth_request.provider_id,
                    session_id=None,
                    error_message="Token exchange failed",
                    user_attributes={},
                    is_new_user=False,
                    metadata={}
                )
            
            # Get user info
            user_info = await self._get_oauth_user_info(token_response['access_token'], config)
            if not user_info:
                return SSOAuthResult(
                    success=False,
                    user_id=None,
                    provider_id=auth_request.provider_id,
                    session_id=None,
                    error_message="Failed to get user info",
                    user_attributes={},
                    is_new_user=False,
                    metadata={}
                )
            
            # Map attributes to user profile
            user_profile = self._map_attributes(user_info, config.attribute_mapping)
            
            # Find or create user
            user_id, is_new_user = await self._find_or_create_user(
                auth_request.provider_id, user_profile, config
            )
            
            # Create SSO session
            session_id = await self._create_sso_session(
                user_id, auth_request.provider_id, user_info,
                ip_address, user_agent
            )
            
            # Clean up auth request
            await self._delete_auth_request(auth_request.request_id)
            
            return SSOAuthResult(
                success=True,
                user_id=user_id,
                provider_id=auth_request.provider_id,
                session_id=session_id,
                error_message=None,
                user_attributes=user_profile,
                is_new_user=is_new_user,
                metadata={"oauth_tokens": token_response, "user_info": user_info}
            )
            
        except Exception as e:
            logger.error(f"Error handling OAuth callback: {e}")
            return SSOAuthResult(
                success=False,
                user_id=None,
                provider_id="",
                session_id=None,
                error_message=str(e),
                user_attributes={},
                is_new_user=False,
                metadata={}
            )
    
    def _generate_saml_authn_request(self, config: SSOConfiguration, request_id: str) -> str:
        """Generate SAML AuthnRequest"""
        now = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
        
        return f"""<?xml version="1.0" encoding="UTF-8"?>
<samlp:AuthnRequest xmlns:samlp="urn:oasis:names:tc:SAML:2.0:protocol"
                    xmlns:saml="urn:oasis:names:tc:SAML:2.0:assertion"
                    ID="{request_id}"
                    Version="2.0"
                    IssueInstant="{now}"
                    Destination="{config.idp_sso_url}"
                    ProtocolBinding="urn:oasis:names:tc:SAML:2.0:bindings:HTTP-POST"
                    AssertionConsumerServiceURL="{config.sp_acs_url}">
    <saml:Issuer>{config.sp_entity_id}</saml:Issuer>
    <samlp:NameIDPolicy Format="urn:oasis:names:tc:SAML:1.1:nameid-format:emailAddress"
                        AllowCreate="true"/>
</samlp:AuthnRequest>"""
    
    async def _parse_saml_response(self, saml_response: str, config: SSOConfiguration) -> Dict[str, Any]:
        """Parse and validate SAML response"""
        try:
            # Parse XML
            root = ET.fromstring(saml_response)
            
            # Basic validation (in production, use proper SAML library with signature validation)
            assertion = root.find('.//{urn:oasis:names:tc:SAML:2.0:assertion}Assertion')
            if assertion is None:
                return {}
            
            # Extract attributes
            attributes = {}
            attr_statements = assertion.findall('.//{urn:oasis:names:tc:SAML:2.0:assertion}AttributeStatement')
            
            for attr_statement in attr_statements:
                for attr in attr_statement.findall('.//{urn:oasis:names:tc:SAML:2.0:assertion}Attribute'):
                    attr_name = attr.get('Name')
                    attr_values = []
                    
                    for value in attr.findall('.//{urn:oasis:names:tc:SAML:2.0:assertion}AttributeValue'):
                        if value.text:
                            attr_values.append(value.text)
                    
                    if attr_values:
                        attributes[attr_name] = attr_values[0] if len(attr_values) == 1 else attr_values
            
            # Extract NameID
            subject = assertion.find('.//{urn:oasis:names:tc:SAML:2.0:assertion}Subject')
            if subject is not None:
                name_id = subject.find('.//{urn:oasis:names:tc:SAML:2.0:assertion}NameID')
                if name_id is not None and name_id.text:
                    attributes['NameID'] = name_id.text
            
            return attributes
            
        except Exception as e:
            logger.error(f"Error parsing SAML response: {e}")
            return {}
    
    async def _exchange_oauth_code(self, code: str, config: SSOConfiguration) -> Optional[Dict[str, Any]]:
        """Exchange OAuth authorization code for tokens"""
        try:
            token_data = {
                'grant_type': 'authorization_code',
                'code': code,
                'redirect_uri': self.oauth_settings['redirect_uri'],
                'client_id': config.client_id,
                'client_secret': config.client_secret
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    config.token_endpoint,
                    data=token_data,
                    headers={'Content-Type': 'application/x-www-form-urlencoded'}
                ) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        logger.error(f"Token exchange failed: {response.status}")
                        return None
                        
        except Exception as e:
            logger.error(f"Error exchanging OAuth code: {e}")
            return None
    
    async def _get_oauth_user_info(self, access_token: str, config: SSOConfiguration) -> Optional[Dict[str, Any]]:
        """Get user info from OAuth userinfo endpoint"""
        try:
            if not config.userinfo_endpoint:
                return None
            
            headers = {'Authorization': f'Bearer {access_token}'}
            
            async with aiohttp.ClientSession() as session:
                async with session.get(config.userinfo_endpoint, headers=headers) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        logger.error(f"User info request failed: {response.status}")
                        return None
                        
        except Exception as e:
            logger.error(f"Error getting OAuth user info: {e}")
            return None
    
    def _map_attributes(self, source_attributes: Dict[str, Any], 
                       attribute_mapping: Dict[str, str]) -> Dict[str, Any]:
        """Map provider attributes to internal user profile"""
        mapped = {}
        
        for internal_name, external_name in attribute_mapping.items():
            if external_name in source_attributes:
                mapped[internal_name] = source_attributes[external_name]
        
        return mapped
    
    async def _find_or_create_user(self, provider_id: str, user_profile: Dict[str, Any], 
                                 config: SSOConfiguration) -> Tuple[str, bool]:
        """Find existing user or create new one"""
        try:
            # Look for existing mapping by provider user ID or email
            provider_user_id = user_profile.get('email') or user_profile.get('NameID')
            if not provider_user_id:
                raise ValueError("No unique identifier found in user profile")
            
            conn = sqlite3.connect(self.database_path)
            cursor = conn.cursor()
            
            # Check for existing mapping
            cursor.execute("""
                SELECT user_id FROM user_provider_mappings 
                WHERE provider_id = ? AND provider_user_id = ?
            """, (provider_id, provider_user_id))
            
            result = cursor.fetchone()
            
            if result:
                # Update existing mapping
                user_id = result[0]
                cursor.execute("""
                    UPDATE user_provider_mappings 
                    SET last_login = ?, login_count = login_count + 1, attributes = ?
                    WHERE provider_id = ? AND provider_user_id = ?
                """, (datetime.now().isoformat(), json.dumps(user_profile), 
                      provider_id, provider_user_id))
                
                conn.commit()
                conn.close()
                return user_id, False
            else:
                # Create new user (simplified - integrate with your user management system)
                user_id = str(uuid.uuid4())
                
                # Create provider mapping
                mapping_id = str(uuid.uuid4())
                cursor.execute("""
                    INSERT INTO user_provider_mappings 
                    (mapping_id, user_id, provider_id, provider_user_id, 
                     provider_username, created_at, last_login, attributes)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (mapping_id, user_id, provider_id, provider_user_id,
                      user_profile.get('email'), datetime.now().isoformat(),
                      datetime.now().isoformat(), json.dumps(user_profile)))
                
                conn.commit()
                conn.close()
                
                logger.info(f"Created new user {user_id} from SSO provider {provider_id}")
                return user_id, True
                
        except Exception as e:
            logger.error(f"Error finding/creating user: {e}")
            raise
    
    async def _create_sso_session(self, user_id: str, provider_id: str, 
                                attributes: Dict[str, Any], ip_address: str, 
                                user_agent: str) -> str:
        """Create SSO session"""
        try:
            session_id = str(uuid.uuid4())
            now = datetime.now()
            expires_at = now + timedelta(hours=self.session_timeout_hours)
            
            session = SSOSession(
                session_id=session_id,
                user_id=user_id,
                provider_id=provider_id,
                provider_session_id=attributes.get('SessionIndex'),
                saml_session_index=attributes.get('SessionIndex'),
                created_at=now,
                expires_at=expires_at,
                last_activity=now,
                ip_address=ip_address,
                user_agent=user_agent,
                attributes=attributes
            )
            
            await self._save_sso_session(session)
            
            logger.info(f"Created SSO session {session_id} for user {user_id}")
            return session_id
            
        except Exception as e:
            logger.error(f"Error creating SSO session: {e}")
            raise
    
    async def get_sso_session(self, session_id: str) -> Optional[SSOSession]:
        """Get SSO session by ID"""
        try:
            conn = sqlite3.connect(self.database_path)
            cursor = conn.cursor()
            
            cursor.execute("SELECT * FROM sso_sessions WHERE session_id = ?", (session_id,))
            row = cursor.fetchone()
            conn.close()
            
            if row:
                return SSOSession(
                    session_id=row[0],
                    user_id=row[1],
                    provider_id=row[2],
                    provider_session_id=row[3],
                    saml_session_index=row[4],
                    created_at=datetime.fromisoformat(row[5]),
                    expires_at=datetime.fromisoformat(row[6]),
                    last_activity=datetime.fromisoformat(row[7]),
                    ip_address=row[8],
                    user_agent=row[9],
                    attributes=json.loads(row[10]) if row[10] else {}
                )
            return None
            
        except Exception as e:
            logger.error(f"Error getting SSO session: {e}")
            return None
    
    async def invalidate_sso_session(self, session_id: str) -> bool:
        """Invalidate SSO session"""
        try:
            conn = sqlite3.connect(self.database_path)
            cursor = conn.cursor()
            
            cursor.execute("DELETE FROM sso_sessions WHERE session_id = ?", (session_id,))
            conn.commit()
            
            deleted = cursor.rowcount > 0
            conn.close()
            
            if deleted:
                logger.info(f"SSO session {session_id} invalidated")
            
            return deleted
            
        except Exception as e:
            logger.error(f"Error invalidating SSO session: {e}")
            return False
    
    async def get_user_sso_sessions(self, user_id: str) -> List[SSOSession]:
        """Get all active SSO sessions for user"""
        try:
            conn = sqlite3.connect(self.database_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT * FROM sso_sessions 
                WHERE user_id = ? AND expires_at > ?
                ORDER BY last_activity DESC
            """, (user_id, datetime.now().isoformat()))
            
            rows = cursor.fetchall()
            conn.close()
            
            sessions = []
            for row in rows:
                sessions.append(SSOSession(
                    session_id=row[0],
                    user_id=row[1],
                    provider_id=row[2],
                    provider_session_id=row[3],
                    saml_session_index=row[4],
                    created_at=datetime.fromisoformat(row[5]),
                    expires_at=datetime.fromisoformat(row[6]),
                    last_activity=datetime.fromisoformat(row[7]),
                    ip_address=row[8],
                    user_agent=row[9],
                    attributes=json.loads(row[10]) if row[10] else {}
                ))
            
            return sessions
            
        except Exception as e:
            logger.error(f"Error getting user SSO sessions: {e}")
            return []
    
    async def get_sso_providers(self) -> List[Dict[str, Any]]:
        """Get all configured SSO providers"""
        try:
            conn = sqlite3.connect(self.database_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT provider_id, provider_name, provider_type, protocol, status
                FROM sso_configurations WHERE status = 'active'
            """)
            
            rows = cursor.fetchall()
            conn.close()
            
            providers = []
            for row in rows:
                providers.append({
                    'provider_id': row[0],
                    'provider_name': row[1],
                    'provider_type': row[2],
                    'protocol': row[3],
                    'status': row[4]
                })
            
            return providers
            
        except Exception as e:
            logger.error(f"Error getting SSO providers: {e}")
            return []
    
    async def cleanup_expired_sessions(self):
        """Clean up expired sessions and requests"""
        try:
            conn = sqlite3.connect(self.database_path)
            cursor = conn.cursor()
            
            now = datetime.now().isoformat()
            
            # Remove expired sessions
            cursor.execute("DELETE FROM sso_sessions WHERE expires_at < ?", (now,))
            expired_sessions = cursor.rowcount
            
            # Remove expired auth requests
            cursor.execute("DELETE FROM sso_auth_requests WHERE expires_at < ?", (now,))
            expired_requests = cursor.rowcount
            
            conn.commit()
            conn.close()
            
            if expired_sessions > 0 or expired_requests > 0:
                logger.info(f"Cleaned up {expired_sessions} sessions and {expired_requests} requests")
                
        except Exception as e:
            logger.error(f"Error during SSO cleanup: {e}")
    
    # Database helper methods
    async def _save_sso_configuration(self, config: SSOConfiguration):
        """Save SSO configuration"""
        conn = sqlite3.connect(self.database_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT OR REPLACE INTO sso_configurations 
            (provider_id, provider_name, provider_type, protocol, status,
             idp_entity_id, idp_sso_url, idp_slo_url, idp_certificate,
             sp_entity_id, sp_acs_url, sp_slo_url, sp_certificate, sp_private_key,
             client_id, client_secret, authorization_endpoint, token_endpoint,
             userinfo_endpoint, jwks_uri, issuer, scopes, attribute_mapping,
             auto_provision, default_roles, created_at, updated_at, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            config.provider_id, config.provider_name, config.provider_type.value,
            config.protocol.value, config.status.value, config.idp_entity_id,
            config.idp_sso_url, config.idp_slo_url, config.idp_certificate,
            config.sp_entity_id, config.sp_acs_url, config.sp_slo_url,
            config.sp_certificate, config.sp_private_key, config.client_id,
            config.client_secret, config.authorization_endpoint, config.token_endpoint,
            config.userinfo_endpoint, config.jwks_uri, config.issuer,
            json.dumps(config.scopes), json.dumps(config.attribute_mapping),
            config.auto_provision, json.dumps(config.default_roles),
            config.created_at.isoformat(), config.updated_at.isoformat(),
            json.dumps(config.metadata)
        ))
        
        conn.commit()
        conn.close()
    
    async def _get_sso_configuration(self, provider_id: str) -> Optional[SSOConfiguration]:
        """Get SSO configuration"""
        conn = sqlite3.connect(self.database_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM sso_configurations WHERE provider_id = ?", (provider_id,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return SSOConfiguration(
                provider_id=row[0],
                provider_name=row[1],
                provider_type=SSOProvider(row[2]),
                protocol=SSOProtocol(row[3]),
                status=SSOStatus(row[4]),
                idp_entity_id=row[5],
                idp_sso_url=row[6],
                idp_slo_url=row[7],
                idp_certificate=row[8],
                sp_entity_id=row[9],
                sp_acs_url=row[10],
                sp_slo_url=row[11],
                sp_certificate=row[12],
                sp_private_key=row[13],
                client_id=row[14],
                client_secret=row[15],
                authorization_endpoint=row[16],
                token_endpoint=row[17],
                userinfo_endpoint=row[18],
                jwks_uri=row[19],
                issuer=row[20],
                scopes=json.loads(row[21]) if row[21] else [],
                attribute_mapping=json.loads(row[22]) if row[22] else {},
                auto_provision=bool(row[23]),
                default_roles=json.loads(row[24]) if row[24] else [],
                created_at=datetime.fromisoformat(row[25]),
                updated_at=datetime.fromisoformat(row[26]),
                metadata=json.loads(row[27]) if row[27] else {}
            )
        return None
    
    async def _save_auth_request(self, request: SSOAuthRequest):
        """Save SSO auth request"""
        conn = sqlite3.connect(self.database_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO sso_auth_requests 
            (request_id, provider_id, redirect_uri, state, nonce, created_at, expires_at, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            request.request_id, request.provider_id, request.redirect_uri,
            request.state, request.nonce, request.created_at.isoformat(),
            request.expires_at.isoformat(), json.dumps(request.metadata)
        ))
        
        conn.commit()
        conn.close()
    
    async def _get_auth_request_by_state(self, state: str) -> Optional[SSOAuthRequest]:
        """Get auth request by state"""
        conn = sqlite3.connect(self.database_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM sso_auth_requests 
            WHERE state = ? AND expires_at > ?
        """, (state, datetime.now().isoformat()))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return SSOAuthRequest(
                request_id=row[0],
                provider_id=row[1],
                redirect_uri=row[2],
                state=row[3],
                nonce=row[4],
                created_at=datetime.fromisoformat(row[5]),
                expires_at=datetime.fromisoformat(row[6]),
                metadata=json.loads(row[7]) if row[7] else {}
            )
        return None
    
    async def _delete_auth_request(self, request_id: str):
        """Delete auth request"""
        conn = sqlite3.connect(self.database_path)
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM sso_auth_requests WHERE request_id = ?", (request_id,))
        conn.commit()
        conn.close()
    
    async def _save_sso_session(self, session: SSOSession):
        """Save SSO session"""
        conn = sqlite3.connect(self.database_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT OR REPLACE INTO sso_sessions 
            (session_id, user_id, provider_id, provider_session_id, saml_session_index,
             created_at, expires_at, last_activity, ip_address, user_agent, attributes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            session.session_id, session.user_id, session.provider_id,
            session.provider_session_id, session.saml_session_index,
            session.created_at.isoformat(), session.expires_at.isoformat(),
            session.last_activity.isoformat(), session.ip_address,
            session.user_agent, json.dumps(session.attributes)
        ))
        
        conn.commit()
        conn.close()
    
    async def _validate_saml_configuration(self, config: SSOConfiguration) -> bool:
        """Validate SAML configuration"""
        try:
            # Basic validation
            required_fields = [
                config.idp_entity_id,
                config.idp_sso_url,
                config.sp_entity_id,
                config.sp_acs_url
            ]
            
            if not all(required_fields):
                logger.error("Missing required SAML configuration fields")
                return False
            
            # TODO: Add certificate validation, metadata parsing, etc.
            return True
            
        except Exception as e:
            logger.error(f"SAML configuration validation failed: {e}")
            return False
    
    async def _validate_oauth_configuration(self, config: SSOConfiguration) -> bool:
        """Validate OAuth configuration"""
        try:
            # Basic validation
            required_fields = [
                config.client_id,
                config.client_secret,
                config.authorization_endpoint,
                config.token_endpoint
            ]
            
            if not all(required_fields):
                logger.error("Missing required OAuth configuration fields")
                return False
            
            # TODO: Add endpoint connectivity tests, OIDC discovery, etc.
            return True
            
        except Exception as e:
            logger.error(f"OAuth configuration validation failed: {e}")
            return False

# Global instance
_sso_manager = None

def get_sso_manager() -> SSOManager:
    """Get global SSO manager instance"""
    global _sso_manager
    if _sso_manager is None:
        _sso_manager = SSOManager()
    return _sso_manager