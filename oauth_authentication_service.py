"""
OAuth 2.0 and JWT Authentication Service for EstateCore API Gateway
Comprehensive authentication and authorization with enterprise-grade security
"""

import os
import jwt
import secrets
import hashlib
import base64
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum
import json
import uuid
from urllib.parse import urlencode, parse_qs
import requests
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import serialization

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GrantType(Enum):
    """OAuth 2.0 grant types"""
    AUTHORIZATION_CODE = "authorization_code"
    CLIENT_CREDENTIALS = "client_credentials"
    REFRESH_TOKEN = "refresh_token"
    IMPLICIT = "implicit"
    PASSWORD = "password"  # Not recommended for production

class TokenType(Enum):
    """Token types"""
    ACCESS_TOKEN = "access_token"
    REFRESH_TOKEN = "refresh_token"
    ID_TOKEN = "id_token"

class ClientType(Enum):
    """OAuth client types"""
    CONFIDENTIAL = "confidential"  # Can securely store credentials
    PUBLIC = "public"  # Cannot securely store credentials

class ResponseType(Enum):
    """OAuth response types"""
    CODE = "code"
    TOKEN = "token"
    ID_TOKEN = "id_token"

@dataclass
class OAuthScope:
    """OAuth scope definition"""
    name: str
    description: str
    resource_server: str
    permissions: List[str] = field(default_factory=list)
    is_sensitive: bool = False

@dataclass
class OAuthClient:
    """OAuth client configuration"""
    client_id: str
    client_secret: str
    client_name: str
    client_type: ClientType
    organization_id: str
    redirect_uris: List[str] = field(default_factory=list)
    allowed_scopes: List[str] = field(default_factory=list)
    allowed_grant_types: List[GrantType] = field(default_factory=list)
    access_token_lifetime: int = 3600  # 1 hour
    refresh_token_lifetime: int = 2592000  # 30 days
    is_active: bool = True
    created_at: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)
    require_pkce: bool = True  # Proof Key for Code Exchange
    require_consent: bool = True
    trusted: bool = False  # Skip consent for trusted clients

@dataclass
class AuthorizationCode:
    """Authorization code for OAuth flow"""
    code: str
    client_id: str
    user_id: str
    scopes: List[str]
    redirect_uri: str
    code_challenge: Optional[str] = None
    code_challenge_method: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    expires_at: datetime = field(default_factory=lambda: datetime.utcnow() + timedelta(minutes=10))
    used: bool = False

@dataclass
class AccessToken:
    """Access token for API access"""
    token: str
    token_hash: str
    client_id: str
    user_id: Optional[str]
    scopes: List[str]
    token_type: str = "Bearer"
    created_at: datetime = field(default_factory=datetime.utcnow)
    expires_at: datetime = field(default_factory=lambda: datetime.utcnow() + timedelta(hours=1))
    is_revoked: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class RefreshToken:
    """Refresh token for token renewal"""
    token: str
    token_hash: str
    client_id: str
    user_id: Optional[str]
    scopes: List[str]
    created_at: datetime = field(default_factory=datetime.utcnow)
    expires_at: datetime = field(default_factory=lambda: datetime.utcnow() + timedelta(days=30))
    is_revoked: bool = False
    access_token_hash: Optional[str] = None

@dataclass
class JWTClaims:
    """JWT token claims"""
    iss: str  # Issuer
    sub: str  # Subject (user ID)
    aud: str  # Audience (client ID)
    exp: int  # Expiration time
    iat: int  # Issued at
    nbf: int  # Not before
    jti: str  # JWT ID
    scopes: List[str] = field(default_factory=list)
    client_id: Optional[str] = None
    organization_id: Optional[str] = None
    user_roles: List[str] = field(default_factory=list)
    custom_claims: Dict[str, Any] = field(default_factory=dict)

class PKCEVerifier:
    """Proof Key for Code Exchange implementation"""
    
    @staticmethod
    def generate_code_verifier() -> str:
        """Generate PKCE code verifier"""
        return base64.urlsafe_b64encode(secrets.token_bytes(32)).decode('utf-8').rstrip('=')
    
    @staticmethod
    def generate_code_challenge(verifier: str, method: str = "S256") -> str:
        """Generate PKCE code challenge"""
        if method == "S256":
            digest = hashlib.sha256(verifier.encode('utf-8')).digest()
            return base64.urlsafe_b64encode(digest).decode('utf-8').rstrip('=')
        elif method == "plain":
            return verifier
        else:
            raise ValueError(f"Unsupported PKCE method: {method}")
    
    @staticmethod
    def verify_code_challenge(verifier: str, challenge: str, method: str = "S256") -> bool:
        """Verify PKCE code challenge"""
        try:
            expected_challenge = PKCEVerifier.generate_code_challenge(verifier, method)
            return expected_challenge == challenge
        except Exception:
            return False

class JWTManager:
    """JWT token management"""
    
    def __init__(self, secret_key: Optional[str] = None, private_key: Optional[str] = None):
        self.secret_key = secret_key or os.environ.get('JWT_SECRET_KEY', 'your-secret-key')
        self.private_key = private_key or os.environ.get('JWT_PRIVATE_KEY')
        self.issuer = os.environ.get('JWT_ISSUER', 'estatecore-api-gateway')
        self.algorithm = 'RS256' if self.private_key else 'HS256'
        
        # Generate RSA key pair if not provided
        if not self.private_key and self.algorithm == 'RS256':
            self._generate_rsa_keys()
    
    def _generate_rsa_keys(self):
        """Generate RSA key pair for JWT signing"""
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048
        )
        
        self.private_key_obj = private_key
        self.public_key_obj = private_key.public_key()
        
        # Serialize keys
        self.private_key = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        ).decode('utf-8')
        
        self.public_key = self.public_key_obj.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        ).decode('utf-8')
    
    def create_access_token(self, claims: JWTClaims) -> str:
        """Create JWT access token"""
        payload = {
            'iss': claims.iss or self.issuer,
            'sub': claims.sub,
            'aud': claims.aud,
            'exp': claims.exp,
            'iat': claims.iat,
            'nbf': claims.nbf,
            'jti': claims.jti,
            'scope': ' '.join(claims.scopes),
            'client_id': claims.client_id,
            'organization_id': claims.organization_id,
            'user_roles': claims.user_roles,
            **claims.custom_claims
        }
        
        if self.algorithm == 'RS256':
            return jwt.encode(payload, self.private_key, algorithm='RS256')
        else:
            return jwt.encode(payload, self.secret_key, algorithm='HS256')
    
    def verify_token(self, token: str) -> Tuple[bool, Optional[Dict[str, Any]], Optional[str]]:
        """Verify and decode JWT token"""
        try:
            if self.algorithm == 'RS256':
                payload = jwt.decode(token, self.public_key, algorithms=['RS256'])
            else:
                payload = jwt.decode(token, self.secret_key, algorithms=['HS256'])
            
            # Verify issuer
            if payload.get('iss') != self.issuer:
                return False, None, "Invalid issuer"
            
            return True, payload, None
            
        except jwt.ExpiredSignatureError:
            return False, None, "Token has expired"
        except jwt.InvalidTokenError as e:
            return False, None, f"Invalid token: {str(e)}"
    
    def get_public_key_jwks(self) -> Dict[str, Any]:
        """Get public key in JWKS format"""
        if self.algorithm != 'RS256':
            return {}
        
        # This is a simplified JWKS implementation
        # In production, you would use a proper library
        return {
            "keys": [
                {
                    "kty": "RSA",
                    "use": "sig",
                    "alg": "RS256",
                    "n": base64.urlsafe_b64encode(
                        self.public_key_obj.public_numbers().n.to_bytes(256, 'big')
                    ).decode('utf-8').rstrip('='),
                    "e": base64.urlsafe_b64encode(
                        self.public_key_obj.public_numbers().e.to_bytes(3, 'big')
                    ).decode('utf-8').rstrip('=')
                }
            ]
        }

class OAuthAuthenticationService:
    """Main OAuth 2.0 authentication service"""
    
    def __init__(self):
        self.clients: Dict[str, OAuthClient] = {}
        self.scopes: Dict[str, OAuthScope] = {}
        self.authorization_codes: Dict[str, AuthorizationCode] = {}
        self.access_tokens: Dict[str, AccessToken] = {}
        self.refresh_tokens: Dict[str, RefreshToken] = {}
        self.jwt_manager = JWTManager()
        
        # Initialize default scopes
        self._initialize_default_scopes()
        
        # Load existing data
        self._load_oauth_data()
    
    def _initialize_default_scopes(self):
        """Initialize default OAuth scopes"""
        default_scopes = [
            OAuthScope("read", "Read access to resources", "api", ["read"]),
            OAuthScope("write", "Write access to resources", "api", ["write"]),
            OAuthScope("admin", "Administrative access", "api", ["read", "write", "admin"], True),
            OAuthScope("properties:read", "Read property data", "properties", ["read"]),
            OAuthScope("properties:write", "Modify property data", "properties", ["write"]),
            OAuthScope("tenants:read", "Read tenant data", "tenants", ["read"]),
            OAuthScope("tenants:write", "Modify tenant data", "tenants", ["write"]),
            OAuthScope("payments:read", "Read payment data", "payments", ["read"]),
            OAuthScope("payments:write", "Process payments", "payments", ["write"]),
            OAuthScope("maintenance:read", "Read maintenance data", "maintenance", ["read"]),
            OAuthScope("maintenance:write", "Manage maintenance", "maintenance", ["write"]),
            OAuthScope("analytics:read", "Access analytics", "analytics", ["read"], True),
            OAuthScope("webhooks:manage", "Manage webhooks", "webhooks", ["read", "write"])
        ]
        
        for scope in default_scopes:
            self.scopes[scope.name] = scope
    
    def _load_oauth_data(self):
        """Load OAuth data from storage"""
        # Implementation would load from database
        # For now, using file-based storage
        pass
    
    def _save_oauth_data(self):
        """Save OAuth data to storage"""
        # Implementation would save to database
        pass
    
    def register_client(self, client_name: str, organization_id: str, 
                       client_type: ClientType, redirect_uris: List[str],
                       allowed_scopes: List[str]) -> OAuthClient:
        """Register a new OAuth client"""
        
        client_id = f"ec_{secrets.token_urlsafe(16)}"
        client_secret = secrets.token_urlsafe(32) if client_type == ClientType.CONFIDENTIAL else ""
        
        # Default grant types based on client type
        if client_type == ClientType.CONFIDENTIAL:
            allowed_grant_types = [
                GrantType.AUTHORIZATION_CODE,
                GrantType.CLIENT_CREDENTIALS,
                GrantType.REFRESH_TOKEN
            ]
        else:
            allowed_grant_types = [
                GrantType.AUTHORIZATION_CODE
            ]
        
        client = OAuthClient(
            client_id=client_id,
            client_secret=client_secret,
            client_name=client_name,
            client_type=client_type,
            organization_id=organization_id,
            redirect_uris=redirect_uris,
            allowed_scopes=allowed_scopes,
            allowed_grant_types=allowed_grant_types
        )
        
        self.clients[client_id] = client
        self._save_oauth_data()
        
        logger.info(f"Registered OAuth client: {client_id}")
        return client
    
    def create_authorization_url(self, client_id: str, redirect_uri: str, 
                               scopes: List[str], state: str,
                               code_challenge: Optional[str] = None,
                               code_challenge_method: Optional[str] = None) -> Tuple[bool, Optional[str], Optional[str]]:
        """Create authorization URL for OAuth flow"""
        
        # Validate client
        if client_id not in self.clients:
            return False, None, "Invalid client ID"
        
        client = self.clients[client_id]
        
        if not client.is_active:
            return False, None, "Client is inactive"
        
        # Validate redirect URI
        if redirect_uri not in client.redirect_uris:
            return False, None, "Invalid redirect URI"
        
        # Validate scopes
        invalid_scopes = [s for s in scopes if s not in self.scopes or s not in client.allowed_scopes]
        if invalid_scopes:
            return False, None, f"Invalid scopes: {', '.join(invalid_scopes)}"
        
        # Check PKCE requirement
        if client.require_pkce and not code_challenge:
            return False, None, "PKCE is required for this client"
        
        # Build authorization URL
        base_url = os.environ.get('OAUTH_AUTHORIZE_URL', 'https://api.estatecore.com/oauth/authorize')
        params = {
            'response_type': 'code',
            'client_id': client_id,
            'redirect_uri': redirect_uri,
            'scope': ' '.join(scopes),
            'state': state
        }
        
        if code_challenge:
            params['code_challenge'] = code_challenge
            params['code_challenge_method'] = code_challenge_method or 'S256'
        
        auth_url = f"{base_url}?{urlencode(params)}"
        
        return True, auth_url, None
    
    def create_authorization_code(self, client_id: str, user_id: str, 
                                scopes: List[str], redirect_uri: str,
                                code_challenge: Optional[str] = None,
                                code_challenge_method: Optional[str] = None) -> str:
        """Create authorization code"""
        
        code = secrets.token_urlsafe(32)
        
        auth_code = AuthorizationCode(
            code=code,
            client_id=client_id,
            user_id=user_id,
            scopes=scopes,
            redirect_uri=redirect_uri,
            code_challenge=code_challenge,
            code_challenge_method=code_challenge_method
        )
        
        self.authorization_codes[code] = auth_code
        
        # Clean up expired codes
        self._cleanup_expired_codes()
        
        return code
    
    def exchange_code_for_token(self, code: str, client_id: str, client_secret: str,
                               redirect_uri: str, code_verifier: Optional[str] = None) -> Tuple[bool, Optional[Dict[str, Any]], Optional[str]]:
        """Exchange authorization code for access token"""
        
        # Validate authorization code
        if code not in self.authorization_codes:
            return False, None, "Invalid authorization code"
        
        auth_code = self.authorization_codes[code]
        
        if auth_code.used:
            return False, None, "Authorization code already used"
        
        if auth_code.expires_at < datetime.utcnow():
            return False, None, "Authorization code expired"
        
        if auth_code.client_id != client_id:
            return False, None, "Client ID mismatch"
        
        if auth_code.redirect_uri != redirect_uri:
            return False, None, "Redirect URI mismatch"
        
        # Validate client credentials
        if client_id not in self.clients:
            return False, None, "Invalid client"
        
        client = self.clients[client_id]
        
        if client.client_type == ClientType.CONFIDENTIAL and client.client_secret != client_secret:
            return False, None, "Invalid client secret"
        
        # Validate PKCE if required
        if auth_code.code_challenge:
            if not code_verifier:
                return False, None, "Code verifier required"
            
            if not PKCEVerifier.verify_code_challenge(
                code_verifier, auth_code.code_challenge, auth_code.code_challenge_method or 'S256'
            ):
                return False, None, "Invalid code verifier"
        
        # Mark code as used
        auth_code.used = True
        
        # Create access token
        access_token = self._create_access_token(
            client_id, auth_code.user_id, auth_code.scopes
        )
        
        # Create refresh token
        refresh_token = self._create_refresh_token(
            client_id, auth_code.user_id, auth_code.scopes, access_token.token_hash
        )
        
        # Create JWT token
        jwt_claims = JWTClaims(
            iss=self.jwt_manager.issuer,
            sub=auth_code.user_id,
            aud=client_id,
            exp=int(access_token.expires_at.timestamp()),
            iat=int(access_token.created_at.timestamp()),
            nbf=int(access_token.created_at.timestamp()),
            jti=str(uuid.uuid4()),
            scopes=auth_code.scopes,
            client_id=client_id,
            organization_id=client.organization_id
        )
        
        jwt_token = self.jwt_manager.create_access_token(jwt_claims)
        
        response = {
            'access_token': jwt_token,
            'token_type': 'Bearer',
            'expires_in': client.access_token_lifetime,
            'refresh_token': refresh_token.token,
            'scope': ' '.join(auth_code.scopes)
        }
        
        return True, response, None
    
    def client_credentials_grant(self, client_id: str, client_secret: str, 
                               scopes: List[str]) -> Tuple[bool, Optional[Dict[str, Any]], Optional[str]]:
        """Handle client credentials grant"""
        
        # Validate client
        if client_id not in self.clients:
            return False, None, "Invalid client"
        
        client = self.clients[client_id]
        
        if not client.is_active:
            return False, None, "Client is inactive"
        
        if client.client_secret != client_secret:
            return False, None, "Invalid client secret"
        
        if GrantType.CLIENT_CREDENTIALS not in client.allowed_grant_types:
            return False, None, "Client credentials grant not allowed"
        
        # Validate scopes
        invalid_scopes = [s for s in scopes if s not in self.scopes or s not in client.allowed_scopes]
        if invalid_scopes:
            return False, None, f"Invalid scopes: {', '.join(invalid_scopes)}"
        
        # Create access token (no user context for client credentials)
        access_token = self._create_access_token(client_id, None, scopes)
        
        # Create JWT token
        jwt_claims = JWTClaims(
            iss=self.jwt_manager.issuer,
            sub=client_id,  # Client is the subject
            aud=client_id,
            exp=int(access_token.expires_at.timestamp()),
            iat=int(access_token.created_at.timestamp()),
            nbf=int(access_token.created_at.timestamp()),
            jti=str(uuid.uuid4()),
            scopes=scopes,
            client_id=client_id,
            organization_id=client.organization_id
        )
        
        jwt_token = self.jwt_manager.create_access_token(jwt_claims)
        
        response = {
            'access_token': jwt_token,
            'token_type': 'Bearer',
            'expires_in': client.access_token_lifetime,
            'scope': ' '.join(scopes)
        }
        
        return True, response, None
    
    def refresh_access_token(self, refresh_token: str, client_id: str, 
                           client_secret: str) -> Tuple[bool, Optional[Dict[str, Any]], Optional[str]]:
        """Refresh access token using refresh token"""
        
        # Find refresh token
        refresh_token_obj = None
        for token_obj in self.refresh_tokens.values():
            if token_obj.token == refresh_token:
                refresh_token_obj = token_obj
                break
        
        if not refresh_token_obj:
            return False, None, "Invalid refresh token"
        
        if refresh_token_obj.is_revoked:
            return False, None, "Refresh token revoked"
        
        if refresh_token_obj.expires_at < datetime.utcnow():
            return False, None, "Refresh token expired"
        
        if refresh_token_obj.client_id != client_id:
            return False, None, "Client ID mismatch"
        
        # Validate client credentials
        if client_id not in self.clients:
            return False, None, "Invalid client"
        
        client = self.clients[client_id]
        
        if client.client_type == ClientType.CONFIDENTIAL and client.client_secret != client_secret:
            return False, None, "Invalid client secret"
        
        # Revoke old access token
        if refresh_token_obj.access_token_hash:
            for token in self.access_tokens.values():
                if token.token_hash == refresh_token_obj.access_token_hash:
                    token.is_revoked = True
                    break
        
        # Create new access token
        access_token = self._create_access_token(
            client_id, refresh_token_obj.user_id, refresh_token_obj.scopes
        )
        
        # Update refresh token
        refresh_token_obj.access_token_hash = access_token.token_hash
        
        # Create JWT token
        jwt_claims = JWTClaims(
            iss=self.jwt_manager.issuer,
            sub=refresh_token_obj.user_id or client_id,
            aud=client_id,
            exp=int(access_token.expires_at.timestamp()),
            iat=int(access_token.created_at.timestamp()),
            nbf=int(access_token.created_at.timestamp()),
            jti=str(uuid.uuid4()),
            scopes=refresh_token_obj.scopes,
            client_id=client_id,
            organization_id=client.organization_id
        )
        
        jwt_token = self.jwt_manager.create_access_token(jwt_claims)
        
        response = {
            'access_token': jwt_token,
            'token_type': 'Bearer',
            'expires_in': client.access_token_lifetime,
            'scope': ' '.join(refresh_token_obj.scopes)
        }
        
        return True, response, None
    
    def verify_access_token(self, token: str) -> Tuple[bool, Optional[Dict[str, Any]], Optional[str]]:
        """Verify access token (JWT)"""
        return self.jwt_manager.verify_token(token)
    
    def revoke_token(self, token: str, client_id: str, client_secret: str) -> Tuple[bool, Optional[str]]:
        """Revoke access or refresh token"""
        
        # Validate client
        if client_id not in self.clients:
            return False, "Invalid client"
        
        client = self.clients[client_id]
        
        if client.client_type == ClientType.CONFIDENTIAL and client.client_secret != client_secret:
            return False, "Invalid client secret"
        
        # Try to find and revoke access token
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        for access_token in self.access_tokens.values():
            if access_token.token_hash == token_hash and access_token.client_id == client_id:
                access_token.is_revoked = True
                logger.info(f"Revoked access token for client {client_id}")
                return True, None
        
        # Try to find and revoke refresh token
        for refresh_token in self.refresh_tokens.values():
            if refresh_token.token == token and refresh_token.client_id == client_id:
                refresh_token.is_revoked = True
                logger.info(f"Revoked refresh token for client {client_id}")
                return True, None
        
        return False, "Token not found"
    
    def _create_access_token(self, client_id: str, user_id: Optional[str], 
                           scopes: List[str]) -> AccessToken:
        """Create access token"""
        token = secrets.token_urlsafe(32)
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        
        client = self.clients[client_id]
        expires_at = datetime.utcnow() + timedelta(seconds=client.access_token_lifetime)
        
        access_token = AccessToken(
            token=token,
            token_hash=token_hash,
            client_id=client_id,
            user_id=user_id,
            scopes=scopes,
            expires_at=expires_at
        )
        
        self.access_tokens[token_hash] = access_token
        return access_token
    
    def _create_refresh_token(self, client_id: str, user_id: Optional[str], 
                            scopes: List[str], access_token_hash: str) -> RefreshToken:
        """Create refresh token"""
        token = secrets.token_urlsafe(32)
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        
        client = self.clients[client_id]
        expires_at = datetime.utcnow() + timedelta(seconds=client.refresh_token_lifetime)
        
        refresh_token = RefreshToken(
            token=token,
            token_hash=token_hash,
            client_id=client_id,
            user_id=user_id,
            scopes=scopes,
            expires_at=expires_at,
            access_token_hash=access_token_hash
        )
        
        self.refresh_tokens[token_hash] = refresh_token
        return refresh_token
    
    def _cleanup_expired_codes(self):
        """Clean up expired authorization codes"""
        now = datetime.utcnow()
        expired_codes = [
            code for code, auth_code in self.authorization_codes.items()
            if auth_code.expires_at < now
        ]
        
        for code in expired_codes:
            del self.authorization_codes[code]
    
    def get_client_info(self, client_id: str) -> Optional[Dict[str, Any]]:
        """Get OAuth client information"""
        if client_id not in self.clients:
            return None
        
        client = self.clients[client_id]
        return {
            'client_id': client.client_id,
            'client_name': client.client_name,
            'client_type': client.client_type.value,
            'organization_id': client.organization_id,
            'allowed_scopes': client.allowed_scopes,
            'allowed_grant_types': [gt.value for gt in client.allowed_grant_types],
            'is_active': client.is_active,
            'created_at': client.created_at.isoformat()
        }
    
    def get_jwks(self) -> Dict[str, Any]:
        """Get JSON Web Key Set"""
        return self.jwt_manager.get_public_key_jwks()

# Global OAuth service instance
_oauth_service = None

def get_oauth_service() -> OAuthAuthenticationService:
    """Get or create the OAuth authentication service instance"""
    global _oauth_service
    if _oauth_service is None:
        _oauth_service = OAuthAuthenticationService()
    return _oauth_service