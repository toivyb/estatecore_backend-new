"""
Enterprise-Grade API Gateway for EstateCore
Comprehensive API management, routing, security, and monitoring system
"""

import os
import logging
import json
import time
import uuid
import hashlib
import hmac
import jwt
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Callable
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict
import threading
from functools import wraps
from flask import Flask, request, jsonify, g, Response, current_app
import requests
from urllib.parse import urlparse, parse_qs
import yaml

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class APIVersion(Enum):
    """API version enumeration"""
    V1 = "v1"
    V2 = "v2"
    V3 = "v3"
    BETA = "beta"
    ALPHA = "alpha"

class HTTPMethod(Enum):
    """HTTP methods"""
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    PATCH = "PATCH"
    DELETE = "DELETE"
    OPTIONS = "OPTIONS"
    HEAD = "HEAD"

class AuthenticationType(Enum):
    """Authentication types supported by the gateway"""
    API_KEY = "api_key"
    JWT_TOKEN = "jwt_token"
    OAUTH2 = "oauth2"
    BASIC_AUTH = "basic_auth"
    HMAC_SIGNATURE = "hmac_signature"
    NONE = "none"

class CircuitBreakerState(Enum):
    """Circuit breaker states"""
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"

class RateLimitType(Enum):
    """Rate limiting types"""
    PER_SECOND = "per_second"
    PER_MINUTE = "per_minute"
    PER_HOUR = "per_hour"
    PER_DAY = "per_day"

@dataclass
class APIEndpoint:
    """API endpoint configuration"""
    path: str
    method: HTTPMethod
    version: APIVersion
    upstream_url: str
    authentication: AuthenticationType = AuthenticationType.API_KEY
    rate_limit: Optional[int] = None
    rate_limit_type: RateLimitType = RateLimitType.PER_MINUTE
    required_scopes: List[str] = field(default_factory=list)
    enable_caching: bool = False
    cache_ttl: int = 300  # 5 minutes
    request_timeout: int = 30
    circuit_breaker_enabled: bool = True
    circuit_breaker_threshold: int = 5
    circuit_breaker_timeout: int = 60
    enable_transformation: bool = False
    request_transformer: Optional[str] = None
    response_transformer: Optional[str] = None
    webhook_enabled: bool = False
    webhook_events: List[str] = field(default_factory=list)
    documentation: Dict[str, Any] = field(default_factory=dict)
    deprecation_date: Optional[datetime] = None
    sunset_date: Optional[datetime] = None

@dataclass
class APIClient:
    """API client configuration"""
    client_id: str
    client_secret: str
    name: str
    organization_id: str
    api_keys: List[str] = field(default_factory=list)
    allowed_endpoints: List[str] = field(default_factory=list)
    rate_limits: Dict[str, int] = field(default_factory=dict)
    scopes: List[str] = field(default_factory=list)
    webhook_url: Optional[str] = None
    webhook_secret: Optional[str] = None
    is_active: bool = True
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_used_at: Optional[datetime] = None
    request_count: int = 0
    is_sandbox: bool = False
    custom_transformations: Dict[str, str] = field(default_factory=dict)

@dataclass
class APIRequest:
    """API request context"""
    request_id: str
    client_id: Optional[str]
    endpoint: APIEndpoint
    method: str
    path: str
    headers: Dict[str, str]
    query_params: Dict[str, Any]
    body: Any
    remote_addr: str
    user_agent: str
    timestamp: datetime
    version: APIVersion
    authentication_method: AuthenticationType
    scopes: List[str] = field(default_factory=list)

@dataclass
class APIResponse:
    """API response context"""
    request_id: str
    status_code: int
    headers: Dict[str, str]
    body: Any
    processing_time: float
    cache_hit: bool = False
    transformed: bool = False
    upstream_service: Optional[str] = None

@dataclass
class CircuitBreaker:
    """Circuit breaker implementation"""
    failure_count: int = 0
    last_failure_time: Optional[datetime] = None
    state: CircuitBreakerState = CircuitBreakerState.CLOSED
    failure_threshold: int = 5
    timeout: int = 60
    half_open_max_calls: int = 3
    half_open_calls: int = 0

class APIMetrics:
    """API metrics collection"""
    
    def __init__(self):
        self.requests_total = defaultdict(int)
        self.requests_by_status = defaultdict(lambda: defaultdict(int))
        self.response_times = defaultdict(list)
        self.error_counts = defaultdict(int)
        self.client_usage = defaultdict(lambda: defaultdict(int))
        self.endpoint_usage = defaultdict(int)
        self.bandwidth_usage = defaultdict(int)
        self.lock = threading.Lock()
    
    def record_request(self, client_id: str, endpoint: str, method: str, 
                      status_code: int, response_time: float, response_size: int):
        """Record API request metrics"""
        with self.lock:
            key = f"{endpoint}:{method}"
            self.requests_total[key] += 1
            self.requests_by_status[key][status_code] += 1
            self.response_times[key].append(response_time)
            self.client_usage[client_id][key] += 1
            self.endpoint_usage[endpoint] += 1
            self.bandwidth_usage[client_id] += response_size
            
            if status_code >= 400:
                self.error_counts[key] += 1
    
    def get_metrics(self, time_window: int = 3600) -> Dict[str, Any]:
        """Get aggregated metrics"""
        with self.lock:
            return {
                'requests_total': dict(self.requests_total),
                'requests_by_status': {k: dict(v) for k, v in self.requests_by_status.items()},
                'average_response_times': {
                    k: sum(v) / len(v) if v else 0 
                    for k, v in self.response_times.items()
                },
                'error_rates': {
                    k: (self.error_counts[k] / self.requests_total[k]) * 100 
                    if self.requests_total[k] > 0 else 0
                    for k in self.requests_total.keys()
                },
                'client_usage': {k: dict(v) for k, v in self.client_usage.items()},
                'endpoint_usage': dict(self.endpoint_usage),
                'bandwidth_usage': dict(self.bandwidth_usage)
            }

class RequestTransformer:
    """Request transformation engine"""
    
    @staticmethod
    def transform_request(request_data: Dict[str, Any], 
                         transformation_config: Dict[str, Any]) -> Dict[str, Any]:
        """Transform incoming request data"""
        try:
            if not transformation_config:
                return request_data
            
            transformed = request_data.copy()
            
            # Field mapping
            if 'field_mapping' in transformation_config:
                for old_field, new_field in transformation_config['field_mapping'].items():
                    if old_field in transformed:
                        transformed[new_field] = transformed.pop(old_field)
            
            # Data type conversions
            if 'type_conversions' in transformation_config:
                for field, target_type in transformation_config['type_conversions'].items():
                    if field in transformed:
                        if target_type == 'int':
                            transformed[field] = int(transformed[field])
                        elif target_type == 'float':
                            transformed[field] = float(transformed[field])
                        elif target_type == 'str':
                            transformed[field] = str(transformed[field])
            
            # Default values
            if 'defaults' in transformation_config:
                for field, value in transformation_config['defaults'].items():
                    if field not in transformed:
                        transformed[field] = value
            
            # Field validation and sanitization
            if 'validations' in transformation_config:
                for field, rules in transformation_config['validations'].items():
                    if field in transformed:
                        value = transformed[field]
                        if 'max_length' in rules and len(str(value)) > rules['max_length']:
                            transformed[field] = str(value)[:rules['max_length']]
                        if 'regex' in rules:
                            if not re.match(rules['regex'], str(value)):
                                raise ValueError(f"Field {field} does not match required pattern")
            
            return transformed
            
        except Exception as e:
            logger.error(f"Request transformation failed: {str(e)}")
            raise

class ResponseTransformer:
    """Response transformation engine"""
    
    @staticmethod
    def transform_response(response_data: Dict[str, Any], 
                          transformation_config: Dict[str, Any]) -> Dict[str, Any]:
        """Transform outgoing response data"""
        try:
            if not transformation_config:
                return response_data
            
            transformed = response_data.copy()
            
            # Field filtering
            if 'include_fields' in transformation_config:
                include_fields = transformation_config['include_fields']
                transformed = {k: v for k, v in transformed.items() if k in include_fields}
            
            if 'exclude_fields' in transformation_config:
                exclude_fields = transformation_config['exclude_fields']
                transformed = {k: v for k, v in transformed.items() if k not in exclude_fields}
            
            # Field renaming
            if 'field_mapping' in transformation_config:
                for old_field, new_field in transformation_config['field_mapping'].items():
                    if old_field in transformed:
                        transformed[new_field] = transformed.pop(old_field)
            
            # Data formatting
            if 'formatting' in transformation_config:
                for field, format_config in transformation_config['formatting'].items():
                    if field in transformed:
                        if format_config['type'] == 'date':
                            if isinstance(transformed[field], datetime):
                                transformed[field] = transformed[field].strftime(
                                    format_config.get('format', '%Y-%m-%d %H:%M:%S')
                                )
                        elif format_config['type'] == 'currency':
                            transformed[field] = f"${float(transformed[field]):.2f}"
            
            # Nested transformations
            if 'nested' in transformation_config:
                for field, nested_config in transformation_config['nested'].items():
                    if field in transformed and isinstance(transformed[field], dict):
                        transformed[field] = ResponseTransformer.transform_response(
                            transformed[field], nested_config
                        )
            
            return transformed
            
        except Exception as e:
            logger.error(f"Response transformation failed: {str(e)}")
            raise

class APIGatewayService:
    """Main API Gateway service class"""
    
    def __init__(self):
        self.endpoints: Dict[str, APIEndpoint] = {}
        self.clients: Dict[str, APIClient] = {}
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}
        self.metrics = APIMetrics()
        self.cache = {}
        self.rate_limits = defaultdict(lambda: defaultdict(list))
        self.request_transformations = {}
        self.response_transformations = {}
        self.webhook_handlers = {}
        
        # Load configuration
        self._load_configuration()
        
    def _load_configuration(self):
        """Load API Gateway configuration"""
        config_path = os.environ.get('API_GATEWAY_CONFIG', 'api_gateway_config.yaml')
        if os.path.exists(config_path):
            try:
                with open(config_path, 'r') as f:
                    config = yaml.safe_load(f)
                    self._parse_configuration(config)
            except Exception as e:
                logger.error(f"Failed to load configuration: {str(e)}")
        else:
            logger.info("No configuration file found, using defaults")
    
    def _parse_configuration(self, config: Dict[str, Any]):
        """Parse and apply configuration"""
        # Load endpoints
        if 'endpoints' in config:
            for endpoint_config in config['endpoints']:
                endpoint = APIEndpoint(**endpoint_config)
                self.register_endpoint(endpoint)
        
        # Load clients
        if 'clients' in config:
            for client_config in config['clients']:
                client = APIClient(**client_config)
                self.register_client(client)
    
    def register_endpoint(self, endpoint: APIEndpoint):
        """Register a new API endpoint"""
        endpoint_key = f"{endpoint.version.value}:{endpoint.method.value}:{endpoint.path}"
        self.endpoints[endpoint_key] = endpoint
        
        # Initialize circuit breaker
        if endpoint.circuit_breaker_enabled:
            self.circuit_breakers[endpoint_key] = CircuitBreaker(
                failure_threshold=endpoint.circuit_breaker_threshold,
                timeout=endpoint.circuit_breaker_timeout
            )
        
        logger.info(f"Registered endpoint: {endpoint_key}")
    
    def register_client(self, client: APIClient):
        """Register a new API client"""
        self.clients[client.client_id] = client
        logger.info(f"Registered client: {client.client_id}")
    
    def authenticate_request(self, request_data: APIRequest) -> Tuple[bool, Optional[str], List[str]]:
        """Authenticate incoming request"""
        auth_header = request_data.headers.get('Authorization', '')
        api_key = request_data.headers.get('X-API-Key', '')
        
        # API Key authentication
        if api_key:
            for client in self.clients.values():
                if api_key in client.api_keys and client.is_active:
                    request_data.client_id = client.client_id
                    return True, client.client_id, client.scopes
            return False, None, []
        
        # JWT Token authentication
        if auth_header.startswith('Bearer '):
            token = auth_header[7:]
            try:
                payload = jwt.decode(
                    token, 
                    os.environ.get('JWT_SECRET_KEY', 'secret'), 
                    algorithms=['HS256']
                )
                client_id = payload.get('client_id')
                if client_id and client_id in self.clients:
                    client = self.clients[client_id]
                    if client.is_active:
                        request_data.client_id = client_id
                        return True, client_id, payload.get('scopes', [])
            except jwt.InvalidTokenError:
                return False, None, []
        
        # Check if endpoint allows unauthenticated access
        if request_data.endpoint.authentication == AuthenticationType.NONE:
            return True, None, []
        
        return False, None, []
    
    def check_rate_limit(self, client_id: str, endpoint_key: str, rate_limit: int, 
                        rate_limit_type: RateLimitType) -> bool:
        """Check if request is within rate limits"""
        now = time.time()
        
        # Determine time window
        if rate_limit_type == RateLimitType.PER_SECOND:
            window = 1
        elif rate_limit_type == RateLimitType.PER_MINUTE:
            window = 60
        elif rate_limit_type == RateLimitType.PER_HOUR:
            window = 3600
        elif rate_limit_type == RateLimitType.PER_DAY:
            window = 86400
        else:
            window = 60  # Default to per minute
        
        # Clean old requests
        key = f"{client_id}:{endpoint_key}"
        self.rate_limits[key] = [
            req_time for req_time in self.rate_limits[key] 
            if now - req_time < window
        ]
        
        # Check limit
        if len(self.rate_limits[key]) >= rate_limit:
            return False
        
        # Add current request
        self.rate_limits[key].append(now)
        return True
    
    def check_circuit_breaker(self, endpoint_key: str) -> bool:
        """Check circuit breaker state"""
        if endpoint_key not in self.circuit_breakers:
            return True
        
        breaker = self.circuit_breakers[endpoint_key]
        now = datetime.utcnow()
        
        if breaker.state == CircuitBreakerState.OPEN:
            if breaker.last_failure_time and \
               (now - breaker.last_failure_time).seconds >= breaker.timeout:
                breaker.state = CircuitBreakerState.HALF_OPEN
                breaker.half_open_calls = 0
                return True
            return False
        
        elif breaker.state == CircuitBreakerState.HALF_OPEN:
            if breaker.half_open_calls >= breaker.half_open_max_calls:
                return False
            breaker.half_open_calls += 1
            return True
        
        return True  # CLOSED state
    
    def record_request_result(self, endpoint_key: str, success: bool):
        """Record request result for circuit breaker"""
        if endpoint_key not in self.circuit_breakers:
            return
        
        breaker = self.circuit_breakers[endpoint_key]
        
        if success:
            if breaker.state == CircuitBreakerState.HALF_OPEN:
                breaker.state = CircuitBreakerState.CLOSED
                breaker.failure_count = 0
        else:
            breaker.failure_count += 1
            breaker.last_failure_time = datetime.utcnow()
            
            if breaker.failure_count >= breaker.failure_threshold:
                breaker.state = CircuitBreakerState.OPEN
    
    def get_cache_key(self, request_data: APIRequest) -> str:
        """Generate cache key for request"""
        key_parts = [
            request_data.method,
            request_data.path,
            str(sorted(request_data.query_params.items())),
            request_data.client_id or 'anonymous'
        ]
        return hashlib.md5(':'.join(key_parts).encode()).hexdigest()
    
    def process_request(self, flask_request) -> Response:
        """Main request processing pipeline"""
        start_time = time.time()
        request_id = str(uuid.uuid4())
        
        try:
            # Parse request
            api_request = self._parse_flask_request(flask_request, request_id)
            
            # Find matching endpoint
            endpoint_key = f"{api_request.version.value}:{api_request.method}:{api_request.path}"
            if endpoint_key not in self.endpoints:
                return self._create_error_response(404, "Endpoint not found", request_id)
            
            endpoint = self.endpoints[endpoint_key]
            api_request.endpoint = endpoint
            
            # Authentication
            is_authenticated, client_id, scopes = self.authenticate_request(api_request)
            if not is_authenticated and endpoint.authentication != AuthenticationType.NONE:
                return self._create_error_response(401, "Authentication required", request_id)
            
            api_request.client_id = client_id
            api_request.scopes = scopes
            
            # Authorization (scope check)
            if endpoint.required_scopes:
                if not all(scope in scopes for scope in endpoint.required_scopes):
                    return self._create_error_response(403, "Insufficient permissions", request_id)
            
            # Rate limiting
            if endpoint.rate_limit and client_id:
                if not self.check_rate_limit(client_id, endpoint_key, 
                                           endpoint.rate_limit, endpoint.rate_limit_type):
                    return self._create_error_response(429, "Rate limit exceeded", request_id)
            
            # Circuit breaker
            if not self.check_circuit_breaker(endpoint_key):
                return self._create_error_response(503, "Service temporarily unavailable", request_id)
            
            # Check cache
            if endpoint.enable_caching and api_request.method == 'GET':
                cache_key = self.get_cache_key(api_request)
                if cache_key in self.cache:
                    cached_response, cache_time = self.cache[cache_key]
                    if time.time() - cache_time < endpoint.cache_ttl:
                        return self._create_cached_response(cached_response, request_id)
            
            # Request transformation
            if endpoint.enable_transformation and endpoint.request_transformer:
                try:
                    if api_request.body:
                        transformed_body = RequestTransformer.transform_request(
                            api_request.body, 
                            self.request_transformations.get(endpoint.request_transformer, {})
                        )
                        api_request.body = transformed_body
                except Exception as e:
                    return self._create_error_response(400, f"Request transformation failed: {str(e)}", request_id)
            
            # Forward request to upstream service
            response = self._forward_request(api_request, endpoint)
            
            # Record success
            self.record_request_result(endpoint_key, True)
            
            # Response transformation
            if endpoint.enable_transformation and endpoint.response_transformer:
                try:
                    if hasattr(response, 'json') and response.json:
                        transformed_response = ResponseTransformer.transform_response(
                            response.json,
                            self.response_transformations.get(endpoint.response_transformer, {})
                        )
                        response.data = json.dumps(transformed_response)
                except Exception as e:
                    logger.error(f"Response transformation failed: {str(e)}")
            
            # Cache response
            if endpoint.enable_caching and api_request.method == 'GET' and response.status_code == 200:
                cache_key = self.get_cache_key(api_request)
                self.cache[cache_key] = (response.data, time.time())
            
            # Record metrics
            processing_time = time.time() - start_time
            self.metrics.record_request(
                client_id or 'anonymous',
                endpoint.path,
                api_request.method,
                response.status_code,
                processing_time,
                len(response.data) if hasattr(response, 'data') else 0
            )
            
            # Trigger webhooks
            if endpoint.webhook_enabled and client_id:
                self._trigger_webhooks(api_request, response, endpoint)
            
            return response
            
        except Exception as e:
            logger.error(f"Request processing failed: {str(e)}")
            self.record_request_result(endpoint_key if 'endpoint_key' in locals() else 'unknown', False)
            return self._create_error_response(500, "Internal server error", request_id)
    
    def _parse_flask_request(self, flask_request, request_id: str) -> APIRequest:
        """Parse Flask request into APIRequest object"""
        # Extract version from path or header
        version = APIVersion.V1  # Default
        path = flask_request.path
        
        # Check for version in path (e.g., /api/v2/...)
        version_match = re.match(r'^/api/(v\d+|beta|alpha)/', path)
        if version_match:
            version_str = version_match.group(1)
            try:
                version = APIVersion(version_str)
                path = path.replace(f'/api/{version_str}', '')
            except ValueError:
                pass
        
        # Check for version in header
        version_header = flask_request.headers.get('API-Version')
        if version_header:
            try:
                version = APIVersion(version_header)
            except ValueError:
                pass
        
        # Parse request body
        body = None
        if flask_request.content_type and 'application/json' in flask_request.content_type:
            try:
                body = flask_request.get_json()
            except Exception:
                body = {}
        
        return APIRequest(
            request_id=request_id,
            client_id=None,  # Will be set during authentication
            endpoint=None,   # Will be set after endpoint lookup
            method=flask_request.method,
            path=path,
            headers=dict(flask_request.headers),
            query_params=dict(flask_request.args),
            body=body,
            remote_addr=flask_request.remote_addr,
            user_agent=flask_request.headers.get('User-Agent', ''),
            timestamp=datetime.utcnow(),
            version=version,
            authentication_method=AuthenticationType.NONE  # Will be determined during auth
        )
    
    def _forward_request(self, api_request: APIRequest, endpoint: APIEndpoint) -> Response:
        """Forward request to upstream service"""
        # Prepare upstream URL
        upstream_url = endpoint.upstream_url
        if api_request.query_params:
            query_string = '&'.join([f"{k}={v}" for k, v in api_request.query_params.items()])
            upstream_url += f"?{query_string}"
        
        # Prepare headers
        headers = api_request.headers.copy()
        headers['X-Request-ID'] = api_request.request_id
        if api_request.client_id:
            headers['X-Client-ID'] = api_request.client_id
        
        # Remove gateway-specific headers
        headers.pop('X-API-Key', None)
        headers.pop('API-Version', None)
        
        try:
            # Make upstream request
            response = requests.request(
                method=api_request.method,
                url=upstream_url,
                headers=headers,
                json=api_request.body if api_request.body else None,
                timeout=endpoint.request_timeout
            )
            
            # Create Flask response
            flask_response = Response(
                response.content,
                status=response.status_code,
                headers=dict(response.headers)
            )
            
            # Add gateway headers
            flask_response.headers['X-Request-ID'] = api_request.request_id
            flask_response.headers['X-Gateway-Version'] = 'EstateCore-Gateway-1.0'
            
            return flask_response
            
        except requests.exceptions.Timeout:
            return self._create_error_response(504, "Gateway timeout", api_request.request_id)
        except requests.exceptions.ConnectionError:
            return self._create_error_response(502, "Bad gateway", api_request.request_id)
        except Exception as e:
            logger.error(f"Upstream request failed: {str(e)}")
            return self._create_error_response(502, "Bad gateway", api_request.request_id)
    
    def _create_error_response(self, status_code: int, message: str, request_id: str) -> Response:
        """Create standardized error response"""
        error_response = {
            'error': {
                'code': status_code,
                'message': message,
                'request_id': request_id,
                'timestamp': datetime.utcnow().isoformat()
            }
        }
        
        response = Response(
            json.dumps(error_response),
            status=status_code,
            content_type='application/json'
        )
        response.headers['X-Request-ID'] = request_id
        return response
    
    def _create_cached_response(self, cached_data: str, request_id: str) -> Response:
        """Create response from cached data"""
        response = Response(cached_data, content_type='application/json')
        response.headers['X-Request-ID'] = request_id
        response.headers['X-Cache-Status'] = 'HIT'
        return response
    
    def _trigger_webhooks(self, api_request: APIRequest, response: Response, endpoint: APIEndpoint):
        """Trigger webhooks for the request"""
        if not endpoint.webhook_events:
            return
        
        client = self.clients.get(api_request.client_id)
        if not client or not client.webhook_url:
            return
        
        # Prepare webhook payload
        webhook_payload = {
            'event': f"{endpoint.path}:{api_request.method}",
            'request_id': api_request.request_id,
            'client_id': api_request.client_id,
            'timestamp': api_request.timestamp.isoformat(),
            'endpoint': endpoint.path,
            'method': api_request.method,
            'status_code': response.status_code,
            'data': {
                'request': {
                    'headers': api_request.headers,
                    'query_params': api_request.query_params,
                    'body': api_request.body
                },
                'response': {
                    'status_code': response.status_code,
                    'headers': dict(response.headers)
                }
            }
        }
        
        # Send webhook asynchronously
        def send_webhook():
            try:
                headers = {'Content-Type': 'application/json'}
                if client.webhook_secret:
                    signature = hmac.new(
                        client.webhook_secret.encode(),
                        json.dumps(webhook_payload).encode(),
                        hashlib.sha256
                    ).hexdigest()
                    headers['X-Webhook-Signature'] = f"sha256={signature}"
                
                requests.post(
                    client.webhook_url,
                    json=webhook_payload,
                    headers=headers,
                    timeout=10
                )
            except Exception as e:
                logger.error(f"Webhook delivery failed: {str(e)}")
        
        # Start webhook delivery in background thread
        threading.Thread(target=send_webhook, daemon=True).start()

# Global API Gateway instance
_api_gateway_service = None

def get_api_gateway_service() -> APIGatewayService:
    """Get or create the API Gateway service instance"""
    global _api_gateway_service
    if _api_gateway_service is None:
        _api_gateway_service = APIGatewayService()
    return _api_gateway_service

# Flask decorators for API Gateway integration
def api_gateway_route(path: str, methods: List[str] = None, version: APIVersion = APIVersion.V1,
                     authentication: AuthenticationType = AuthenticationType.API_KEY,
                     rate_limit: int = None, required_scopes: List[str] = None):
    """Decorator to register routes with the API Gateway"""
    def decorator(func):
        gateway = get_api_gateway_service()
        
        for method in (methods or ['GET']):
            endpoint = APIEndpoint(
                path=path,
                method=HTTPMethod(method),
                version=version,
                upstream_url=f"http://localhost:5000{path}",  # Internal service URL
                authentication=authentication,
                rate_limit=rate_limit,
                required_scopes=required_scopes or []
            )
            gateway.register_endpoint(endpoint)
        
        @wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)
        return wrapper
    return decorator

def require_api_gateway():
    """Decorator to process requests through API Gateway"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            gateway = get_api_gateway_service()
            return gateway.process_request(request)
        return wrapper
    return decorator