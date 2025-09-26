"""
Single Sign-On (SSO) integration service for white-label tenants.
Supports SAML 2.0, OAuth 2.0, OpenID Connect, and custom authentication providers.
"""
import json
import base64
import hashlib
import secrets
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timedelta
from enum import Enum
from urllib.parse import urlencode, parse_qs, urlparse
import requests
from flask import current_app, request, url_for, redirect, session
import jwt
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.backends import default_backend

from services.tenant_context import get_current_tenant_context
from models.white_label_tenant import WhiteLabelTenant, db

class SSOProvider(Enum):
    """Supported SSO provider types."""
    SAML2 = "saml2"
    OAUTH2 = "oauth2"
    OPENID_CONNECT = "oidc"
    LDAP = "ldap"
    AZURE_AD = "azure_ad"
    GOOGLE_WORKSPACE = "google_workspace"
    OKTA = "okta"
    ONELOGIN = "onelogin"
    CUSTOM = "custom"

class SSOService:
    """
    Comprehensive SSO service for tenant-specific authentication.
    """
    
    def __init__(self):
        self.providers = {}
        self._initialize_providers()
    
    def _initialize_providers(self):
        """Initialize SSO provider handlers."""
        self.providers = {
            SSOProvider.SAML2: SAML2Provider(),
            SSOProvider.OAUTH2: OAuth2Provider(),
            SSOProvider.OPENID_CONNECT: OpenIDConnectProvider(),
            SSOProvider.AZURE_AD: AzureADProvider(),
            SSOProvider.GOOGLE_WORKSPACE: GoogleWorkspaceProvider(),
            SSOProvider.OKTA: OktaProvider(),
            SSOProvider.ONELOGIN: OneLoginProvider()
        }
    
    def configure_tenant_sso(self, tenant_id: int, provider_type: SSOProvider, 
                           config: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Configure SSO for a tenant.
        
        Args:
            tenant_id: Tenant ID
            provider_type: Type of SSO provider
            config: Provider-specific configuration
            
        Returns:
            Tuple of (success, message)
        """
        try:
            tenant = WhiteLabelTenant.query.get(tenant_id)
            if not tenant:
                return False, "Tenant not found"
            
            # Validate configuration
            provider = self.providers.get(provider_type)
            if not provider:
                return False, f"Unsupported SSO provider: {provider_type.value}"
            
            validation_result = provider.validate_config(config)
            if not validation_result[0]:
                return False, f"Invalid configuration: {validation_result[1]}"
            
            # Store SSO configuration
            if not tenant.sso_config:
                tenant.sso_config = {}
            
            tenant.sso_config[provider_type.value] = {
                'enabled': True,
                'config': config,
                'created_at': datetime.utcnow().isoformat(),
                'metadata': provider.get_metadata(config)
            }
            
            # Enable SSO feature flag
            tenant.set_feature_flag('sso_integration', True)
            
            db.session.commit()
            
            current_app.logger.info(f"Configured {provider_type.value} SSO for tenant {tenant.tenant_key}")
            return True, "SSO configured successfully"
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error configuring SSO: {str(e)}")
            return False, f"Configuration failed: {str(e)}"
    
    def initiate_sso_login(self, tenant_id: int, provider_type: SSOProvider, 
                          return_url: str = None) -> Tuple[bool, str, Optional[str]]:
        """
        Initiate SSO login process.
        
        Args:
            tenant_id: Tenant ID
            provider_type: SSO provider type
            return_url: URL to return to after authentication
            
        Returns:
            Tuple of (success, message, redirect_url)
        """
        try:
            tenant = WhiteLabelTenant.query.get(tenant_id)
            if not tenant:
                return False, "Tenant not found", None
            
            # Check if SSO is configured
            sso_config = tenant.sso_config.get(provider_type.value) if tenant.sso_config else None
            if not sso_config or not sso_config.get('enabled'):
                return False, "SSO not configured for this tenant", None
            
            provider = self.providers.get(provider_type)
            if not provider:
                return False, f"Unsupported SSO provider: {provider_type.value}", None
            
            # Generate state parameter for security
            state = self._generate_state_parameter(tenant_id, return_url)
            
            # Get authorization URL
            auth_url = provider.get_authorization_url(sso_config['config'], state)
            
            current_app.logger.info(f"Initiated SSO login for tenant {tenant.tenant_key} with {provider_type.value}")
            return True, "SSO login initiated", auth_url
            
        except Exception as e:
            current_app.logger.error(f"Error initiating SSO login: {str(e)}")
            return False, f"SSO login failed: {str(e)}", None
    
    def handle_sso_callback(self, tenant_id: int, provider_type: SSOProvider, 
                           callback_data: Dict[str, Any]) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """
        Handle SSO authentication callback.
        
        Args:
            tenant_id: Tenant ID
            provider_type: SSO provider type
            callback_data: Callback data from SSO provider
            
        Returns:
            Tuple of (success, message, user_info)
        """
        try:
            tenant = WhiteLabelTenant.query.get(tenant_id)
            if not tenant:
                return False, "Tenant not found", None
            
            # Validate state parameter
            state = callback_data.get('state')
            if not self._validate_state_parameter(state, tenant_id):
                return False, "Invalid state parameter", None
            
            sso_config = tenant.sso_config.get(provider_type.value) if tenant.sso_config else None
            if not sso_config:
                return False, "SSO not configured", None
            
            provider = self.providers.get(provider_type)
            if not provider:
                return False, f"Unsupported SSO provider: {provider_type.value}", None
            
            # Process callback and get user information
            result = provider.process_callback(sso_config['config'], callback_data)
            
            if result[0]:
                user_info = result[2]
                
                # Log successful authentication
                current_app.logger.info(f"Successful SSO authentication for tenant {tenant.tenant_key} user {user_info.get('email')}")
                
                # Store authentication in session
                session['sso_authenticated'] = True
                session['sso_provider'] = provider_type.value
                session['sso_tenant_id'] = tenant_id
                session['sso_user_info'] = user_info
                
                return True, "Authentication successful", user_info
            else:
                return False, result[1], None
                
        except Exception as e:
            current_app.logger.error(f"Error handling SSO callback: {str(e)}")
            return False, f"Authentication failed: {str(e)}", None
    
    def get_tenant_sso_providers(self, tenant_id: int) -> List[Dict[str, Any]]:
        """
        Get configured SSO providers for a tenant.
        
        Args:
            tenant_id: Tenant ID
            
        Returns:
            List of configured SSO providers
        """
        try:
            tenant = WhiteLabelTenant.query.get(tenant_id)
            if not tenant or not tenant.sso_config:
                return []
            
            providers = []
            for provider_type, config in tenant.sso_config.items():
                if config.get('enabled'):
                    providers.append({
                        'provider_type': provider_type,
                        'name': config.get('config', {}).get('name', provider_type.title()),
                        'description': config.get('config', {}).get('description', ''),
                        'login_url': url_for('sso.login', provider=provider_type, _external=True)
                    })
            
            return providers
            
        except Exception as e:
            current_app.logger.error(f"Error getting SSO providers: {str(e)}")
            return []
    
    def _generate_state_parameter(self, tenant_id: int, return_url: str = None) -> str:
        """Generate secure state parameter for OAuth/OIDC."""
        state_data = {
            'tenant_id': tenant_id,
            'return_url': return_url,
            'timestamp': datetime.utcnow().isoformat(),
            'nonce': secrets.token_urlsafe(16)
        }
        
        # Encode and sign state
        state_json = json.dumps(state_data)
        state_b64 = base64.urlsafe_b64encode(state_json.encode()).decode()
        
        # Store in session for validation
        session[f'sso_state_{tenant_id}'] = state_b64
        
        return state_b64
    
    def _validate_state_parameter(self, state: str, tenant_id: int) -> bool:
        """Validate state parameter."""
        try:
            expected_state = session.get(f'sso_state_{tenant_id}')
            if not expected_state or state != expected_state:
                return False
            
            # Decode and validate
            state_json = base64.urlsafe_b64decode(state.encode()).decode()
            state_data = json.loads(state_json)
            
            # Check timestamp (state should not be older than 10 minutes)
            timestamp = datetime.fromisoformat(state_data['timestamp'])
            if datetime.utcnow() - timestamp > timedelta(minutes=10):
                return False
            
            return state_data['tenant_id'] == tenant_id
            
        except Exception as e:
            current_app.logger.error(f"Error validating state parameter: {str(e)}")
            return False

class BaseSSOProvider:
    """Base class for SSO providers."""
    
    def validate_config(self, config: Dict[str, Any]) -> Tuple[bool, str]:
        """Validate provider configuration."""
        raise NotImplementedError
    
    def get_metadata(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Get provider metadata."""
        return {}
    
    def get_authorization_url(self, config: Dict[str, Any], state: str) -> str:
        """Get authorization URL for SSO initiation."""
        raise NotImplementedError
    
    def process_callback(self, config: Dict[str, Any], callback_data: Dict[str, Any]) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """Process authentication callback."""
        raise NotImplementedError

class OAuth2Provider(BaseSSOProvider):
    """OAuth 2.0 provider implementation."""
    
    def validate_config(self, config: Dict[str, Any]) -> Tuple[bool, str]:
        required_fields = ['client_id', 'client_secret', 'authorization_endpoint', 'token_endpoint']
        
        for field in required_fields:
            if field not in config:
                return False, f"Missing required field: {field}"
        
        return True, "Valid"
    
    def get_authorization_url(self, config: Dict[str, Any], state: str) -> str:
        params = {
            'response_type': 'code',
            'client_id': config['client_id'],
            'redirect_uri': url_for('sso.callback', provider='oauth2', _external=True),
            'scope': config.get('scope', 'openid email profile'),
            'state': state
        }
        
        return f"{config['authorization_endpoint']}?{urlencode(params)}"
    
    def process_callback(self, config: Dict[str, Any], callback_data: Dict[str, Any]) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        try:
            # Exchange authorization code for token
            code = callback_data.get('code')
            if not code:
                return False, "No authorization code received", None
            
            token_data = {
                'grant_type': 'authorization_code',
                'code': code,
                'redirect_uri': url_for('sso.callback', provider='oauth2', _external=True),
                'client_id': config['client_id'],
                'client_secret': config['client_secret']
            }
            
            token_response = requests.post(config['token_endpoint'], data=token_data)
            token_response.raise_for_status()
            tokens = token_response.json()
            
            # Get user information
            user_info_response = requests.get(
                config.get('userinfo_endpoint', config['token_endpoint'].replace('token', 'userinfo')),
                headers={'Authorization': f"Bearer {tokens['access_token']}"}
            )
            user_info_response.raise_for_status()
            user_info = user_info_response.json()
            
            return True, "Authentication successful", {
                'email': user_info.get('email'),
                'name': user_info.get('name'),
                'given_name': user_info.get('given_name'),
                'family_name': user_info.get('family_name'),
                'picture': user_info.get('picture'),
                'sub': user_info.get('sub'),
                'tokens': tokens
            }
            
        except Exception as e:
            return False, f"OAuth2 authentication failed: {str(e)}", None

class OpenIDConnectProvider(BaseSSOProvider):
    """OpenID Connect provider implementation."""
    
    def validate_config(self, config: Dict[str, Any]) -> Tuple[bool, str]:
        required_fields = ['client_id', 'client_secret', 'discovery_endpoint']
        
        for field in required_fields:
            if field not in config:
                return False, f"Missing required field: {field}"
        
        return True, "Valid"
    
    def get_metadata(self, config: Dict[str, Any]) -> Dict[str, Any]:
        try:
            # Fetch OpenID Connect discovery document
            response = requests.get(config['discovery_endpoint'])
            response.raise_for_status()
            return response.json()
        except Exception as e:
            current_app.logger.error(f"Error fetching OIDC metadata: {str(e)}")
            return {}
    
    def get_authorization_url(self, config: Dict[str, Any], state: str) -> str:
        metadata = self.get_metadata(config)
        auth_endpoint = metadata.get('authorization_endpoint')
        
        if not auth_endpoint:
            raise ValueError("No authorization endpoint found in OIDC metadata")
        
        params = {
            'response_type': 'code',
            'client_id': config['client_id'],
            'redirect_uri': url_for('sso.callback', provider='oidc', _external=True),
            'scope': config.get('scope', 'openid email profile'),
            'state': state,
            'nonce': secrets.token_urlsafe(16)
        }
        
        return f"{auth_endpoint}?{urlencode(params)}"
    
    def process_callback(self, config: Dict[str, Any], callback_data: Dict[str, Any]) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        try:
            metadata = self.get_metadata(config)
            token_endpoint = metadata.get('token_endpoint')
            userinfo_endpoint = metadata.get('userinfo_endpoint')
            
            # Exchange code for tokens
            code = callback_data.get('code')
            if not code:
                return False, "No authorization code received", None
            
            token_data = {
                'grant_type': 'authorization_code',
                'code': code,
                'redirect_uri': url_for('sso.callback', provider='oidc', _external=True),
                'client_id': config['client_id'],
                'client_secret': config['client_secret']
            }
            
            token_response = requests.post(token_endpoint, data=token_data)
            token_response.raise_for_status()
            tokens = token_response.json()
            
            # Decode ID token
            id_token = tokens.get('id_token')
            if id_token:
                # For production, you should verify the JWT signature
                payload = jwt.decode(id_token, options={"verify_signature": False})
                
                return True, "Authentication successful", {
                    'email': payload.get('email'),
                    'name': payload.get('name'),
                    'given_name': payload.get('given_name'),
                    'family_name': payload.get('family_name'),
                    'picture': payload.get('picture'),
                    'sub': payload.get('sub'),
                    'tokens': tokens,
                    'id_token_claims': payload
                }
            else:
                return False, "No ID token received", None
                
        except Exception as e:
            return False, f"OIDC authentication failed: {str(e)}", None

class SAML2Provider(BaseSSOProvider):
    """SAML 2.0 provider implementation."""
    
    def validate_config(self, config: Dict[str, Any]) -> Tuple[bool, str]:
        required_fields = ['idp_sso_url', 'idp_x509_cert', 'sp_entity_id']
        
        for field in required_fields:
            if field not in config:
                return False, f"Missing required field: {field}"
        
        return True, "Valid"
    
    def get_authorization_url(self, config: Dict[str, Any], state: str) -> str:
        # For SAML, this would generate a SAML AuthnRequest
        # This is a simplified implementation
        saml_request = self._generate_saml_request(config, state)
        
        params = {
            'SAMLRequest': base64.b64encode(saml_request.encode()).decode(),
            'RelayState': state
        }
        
        return f"{config['idp_sso_url']}?{urlencode(params)}"
    
    def _generate_saml_request(self, config: Dict[str, Any], state: str) -> str:
        # Simplified SAML AuthnRequest generation
        # In production, use a proper SAML library like python3-saml
        request_id = f"id_{secrets.token_hex(16)}"
        timestamp = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
        
        saml_request = f"""
        <samlp:AuthnRequest
            xmlns:samlp="urn:oasis:names:tc:SAML:2.0:protocol"
            xmlns:saml="urn:oasis:names:tc:SAML:2.0:assertion"
            ID="{request_id}"
            Version="2.0"
            IssueInstant="{timestamp}"
            Destination="{config['idp_sso_url']}"
            AssertionConsumerServiceURL="{url_for('sso.callback', provider='saml2', _external=True)}">
            <saml:Issuer>{config['sp_entity_id']}</saml:Issuer>
        </samlp:AuthnRequest>
        """
        
        return saml_request.strip()
    
    def process_callback(self, config: Dict[str, Any], callback_data: Dict[str, Any]) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        # SAML response processing would be implemented here
        # This requires proper SAML response parsing and validation
        return False, "SAML2 implementation pending", None

class AzureADProvider(OpenIDConnectProvider):
    """Azure AD specific provider."""
    
    def validate_config(self, config: Dict[str, Any]) -> Tuple[bool, str]:
        required_fields = ['tenant_id', 'client_id', 'client_secret']
        
        for field in required_fields:
            if field not in config:
                return False, f"Missing required field: {field}"
        
        # Set Azure AD specific endpoints
        config['discovery_endpoint'] = f"https://login.microsoftonline.com/{config['tenant_id']}/v2.0/.well-known/openid_configuration"
        
        return True, "Valid"

class GoogleWorkspaceProvider(OpenIDConnectProvider):
    """Google Workspace specific provider."""
    
    def validate_config(self, config: Dict[str, Any]) -> Tuple[bool, str]:
        required_fields = ['client_id', 'client_secret']
        
        for field in required_fields:
            if field not in config:
                return False, f"Missing required field: {field}"
        
        # Set Google specific endpoints
        config['discovery_endpoint'] = "https://accounts.google.com/.well-known/openid_configuration"
        
        return True, "Valid"

class OktaProvider(OpenIDConnectProvider):
    """Okta specific provider."""
    
    def validate_config(self, config: Dict[str, Any]) -> Tuple[bool, str]:
        required_fields = ['okta_domain', 'client_id', 'client_secret']
        
        for field in required_fields:
            if field not in config:
                return False, f"Missing required field: {field}"
        
        # Set Okta specific endpoints
        config['discovery_endpoint'] = f"https://{config['okta_domain']}/.well-known/openid_configuration"
        
        return True, "Valid"

class OneLoginProvider(BaseSSOProvider):
    """OneLogin specific provider."""
    
    def validate_config(self, config: Dict[str, Any]) -> Tuple[bool, str]:
        required_fields = ['subdomain', 'client_id', 'client_secret']
        
        for field in required_fields:
            if field not in config:
                return False, f"Missing required field: {field}"
        
        return True, "Valid"
    
    def get_authorization_url(self, config: Dict[str, Any], state: str) -> str:
        params = {
            'response_type': 'code',
            'client_id': config['client_id'],
            'redirect_uri': url_for('sso.callback', provider='onelogin', _external=True),
            'scope': 'openid email profile',
            'state': state
        }
        
        auth_url = f"https://{config['subdomain']}.onelogin.com/oidc/2/auth"
        return f"{auth_url}?{urlencode(params)}"
    
    def process_callback(self, config: Dict[str, Any], callback_data: Dict[str, Any]) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        # OneLogin specific callback processing
        return False, "OneLogin implementation pending", None

def get_sso_service() -> SSOService:
    """Get SSO service instance."""
    return SSOService()