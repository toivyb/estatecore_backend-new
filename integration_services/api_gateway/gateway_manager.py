#!/usr/bin/env python3
"""
Advanced API Gateway Manager for EstateCore Phase 8A
Enterprise-grade API management with routing, rate limiting, authentication, and monitoring
"""

import os
import json
import asyncio
import logging
import time
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import aiohttp
import redis
from collections import defaultdict, deque
import uuid
import jwt
from functools import wraps

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RequestMethod(Enum):
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    DELETE = "DELETE"
    PATCH = "PATCH"
    HEAD = "HEAD"
    OPTIONS = "OPTIONS"

class AuthType(Enum):
    NONE = "none"
    API_KEY = "api_key"
    JWT_TOKEN = "jwt_token"
    OAUTH2 = "oauth2"
    BASIC_AUTH = "basic_auth"

class RateLimitType(Enum):
    PER_MINUTE = "per_minute"
    PER_HOUR = "per_hour"
    PER_DAY = "per_day"
    BURST = "burst"

@dataclass
class Route:
    """API route configuration"""
    route_id: str
    path: str
    method: RequestMethod
    upstream_url: str
    auth_type: AuthType
    rate_limit: Dict[str, int]  # {type: limit}
    timeout: int
    retry_count: int
    circuit_breaker: bool
    cache_ttl: Optional[int]
    transform_request: bool
    transform_response: bool
    enabled: bool
    tags: List[str]

@dataclass
class RateLimitRule:
    """Rate limiting rule"""
    client_id: str
    rule_type: RateLimitType
    limit: int
    window_seconds: int
    current_count: int
    reset_time: datetime

@dataclass
class CircuitBreakerState:
    """Circuit breaker state tracking"""
    service_id: str
    state: str  # "closed", "open", "half_open"
    failure_count: int
    failure_threshold: int
    timeout: int
    next_attempt: datetime
    success_count: int

@dataclass
class APIRequest:
    """API request details"""
    request_id: str
    client_id: str
    route_id: str
    method: str
    path: str
    headers: Dict[str, str]
    query_params: Dict[str, str]
    body: Optional[bytes]
    timestamp: datetime
    ip_address: str
    user_agent: str

@dataclass
class APIResponse:
    """API response details"""
    request_id: str
    status_code: int
    headers: Dict[str, str]
    body: Optional[bytes]
    response_time: float
    upstream_service: str
    cached: bool
    timestamp: datetime

class APIGatewayManager:
    """Advanced API Gateway with enterprise features"""
    
    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.routes: Dict[str, Route] = {}
        self.rate_limits: Dict[str, Dict[str, RateLimitRule]] = defaultdict(dict)
        self.circuit_breakers: Dict[str, CircuitBreakerState] = {}
        self.request_cache: Dict[str, Tuple[Any, datetime]] = {}
        
        # Redis for distributed rate limiting and caching
        try:
            self.redis_client = redis.Redis.from_url(redis_url, decode_responses=True)
            self.redis_client.ping()
            logger.info("Connected to Redis for distributed caching")
        except Exception as e:
            logger.warning(f"Redis connection failed: {e}. Using in-memory storage.")
            self.redis_client = None
        
        # Request/response tracking
        self.request_history: deque = deque(maxlen=10000)
        self.response_metrics: Dict[str, List[float]] = defaultdict(list)
        
        # Authentication handlers
        self.auth_handlers: Dict[AuthType, Callable] = {
            AuthType.API_KEY: self._validate_api_key,
            AuthType.JWT_TOKEN: self._validate_jwt_token,
            AuthType.OAUTH2: self._validate_oauth2,
            AuthType.BASIC_AUTH: self._validate_basic_auth
        }
        
        # Load default routes
        self._load_default_routes()
        
        logger.info("API Gateway Manager initialized")
    
    def _load_default_routes(self):
        """Load default API routes for EstateCore services"""
        default_routes = [
            # Property Management APIs
            Route(
                route_id="properties_api",
                path="/api/properties/*",
                method=RequestMethod.GET,
                upstream_url="http://localhost:5000",
                auth_type=AuthType.JWT_TOKEN,
                rate_limit={RateLimitType.PER_MINUTE.value: 100, RateLimitType.PER_HOUR.value: 1000},
                timeout=5000,
                retry_count=3,
                circuit_breaker=True,
                cache_ttl=300,
                transform_request=False,
                transform_response=True,
                enabled=True,
                tags=["properties", "core"]
            ),
            
            # External MLS Integration
            Route(
                route_id="mls_integration",
                path="/api/integrations/mls/*",
                method=RequestMethod.GET,
                upstream_url="http://mls-service:8080",
                auth_type=AuthType.API_KEY,
                rate_limit={RateLimitType.PER_MINUTE.value: 50, RateLimitType.PER_HOUR.value: 500},
                timeout=10000,
                retry_count=2,
                circuit_breaker=True,
                cache_ttl=600,
                transform_request=True,
                transform_response=True,
                enabled=True,
                tags=["mls", "external", "integration"]
            ),
            
            # Payment Gateway Integration
            Route(
                route_id="payment_gateway",
                path="/api/payments/*",
                method=RequestMethod.POST,
                upstream_url="http://payment-service:9000",
                auth_type=AuthType.OAUTH2,
                rate_limit={RateLimitType.PER_MINUTE.value: 20, RateLimitType.PER_HOUR.value: 200},
                timeout=15000,
                retry_count=1,
                circuit_breaker=True,
                cache_ttl=None,
                transform_request=True,
                transform_response=True,
                enabled=True,
                tags=["payments", "external", "sensitive"]
            ),
            
            # AI Services
            Route(
                route_id="ai_services",
                path="/api/ai/*",
                method=RequestMethod.POST,
                upstream_url="http://localhost:5000",
                auth_type=AuthType.JWT_TOKEN,
                rate_limit={RateLimitType.PER_MINUTE.value: 30, RateLimitType.PER_HOUR.value: 300},
                timeout=30000,
                retry_count=2,
                circuit_breaker=True,
                cache_ttl=120,
                transform_request=False,
                transform_response=False,
                enabled=True,
                tags=["ai", "ml", "analytics"]
            )
        ]
        
        for route in default_routes:
            self.routes[route.route_id] = route
    
    async def process_request(self, request: APIRequest) -> APIResponse:
        """Process incoming API request through gateway"""
        try:
            start_time = time.time()
            
            # Find matching route
            route = self._find_route(request.path, request.method)
            if not route:
                return self._create_error_response(
                    request.request_id, 404, "Route not found"
                )
            
            # Check if route is enabled
            if not route.enabled:
                return self._create_error_response(
                    request.request_id, 503, "Service temporarily unavailable"
                )
            
            # Authentication
            auth_result = await self._authenticate_request(request, route)
            if not auth_result["success"]:
                return self._create_error_response(
                    request.request_id, 401, auth_result["error"]
                )
            
            # Rate limiting
            rate_limit_result = await self._check_rate_limit(request, route)
            if not rate_limit_result["allowed"]:
                return self._create_error_response(
                    request.request_id, 429, "Rate limit exceeded", 
                    headers={"Retry-After": str(rate_limit_result["retry_after"])}
                )
            
            # Circuit breaker check
            if route.circuit_breaker:
                circuit_result = self._check_circuit_breaker(route.route_id)
                if not circuit_result["closed"]:
                    return self._create_error_response(
                        request.request_id, 503, "Service circuit breaker is open"
                    )
            
            # Check cache
            if route.cache_ttl and request.method == "GET":
                cached_response = await self._get_cached_response(request, route)
                if cached_response:
                    cached_response.response_time = time.time() - start_time
                    return cached_response
            
            # Transform request if needed
            if route.transform_request:
                request = await self._transform_request(request, route)
            
            # Forward request to upstream service
            response = await self._forward_request(request, route)
            
            # Transform response if needed
            if route.transform_response:
                response = await self._transform_response(response, route)
            
            # Cache response if appropriate
            if route.cache_ttl and response.status_code == 200:
                await self._cache_response(request, response, route)
            
            # Update metrics
            response.response_time = time.time() - start_time
            await self._update_metrics(request, response, route)
            
            # Update circuit breaker
            if route.circuit_breaker:
                self._update_circuit_breaker(route.route_id, True, response.status_code)
            
            return response
            
        except Exception as e:
            logger.error(f"Error processing request {request.request_id}: {e}")
            
            # Update circuit breaker on failure
            if 'route' in locals() and route.circuit_breaker:
                self._update_circuit_breaker(route.route_id, False, 500)
            
            return self._create_error_response(
                request.request_id, 500, "Internal gateway error"
            )
    
    def _find_route(self, path: str, method: str) -> Optional[Route]:
        """Find matching route for request path and method"""
        for route in self.routes.values():
            # Simple wildcard matching
            if route.method.value == method:
                route_pattern = route.path.replace("*", "")
                if path.startswith(route_pattern):
                    return route
        return None
    
    async def _authenticate_request(self, request: APIRequest, route: Route) -> Dict[str, Any]:
        """Authenticate request based on route auth type"""
        if route.auth_type == AuthType.NONE:
            return {"success": True, "client_id": "anonymous"}
        
        auth_handler = self.auth_handlers.get(route.auth_type)
        if not auth_handler:
            return {"success": False, "error": "Unsupported auth type"}
        
        return await auth_handler(request, route)
    
    async def _validate_api_key(self, request: APIRequest, route: Route) -> Dict[str, Any]:
        """Validate API key authentication"""
        api_key = request.headers.get("X-API-Key") or request.query_params.get("api_key")
        
        if not api_key:
            return {"success": False, "error": "API key required"}
        
        # In production, validate against database
        # For now, accept any non-empty key
        client_id = hashlib.md5(api_key.encode()).hexdigest()[:8]
        
        return {"success": True, "client_id": client_id}
    
    async def _validate_jwt_token(self, request: APIRequest, route: Route) -> Dict[str, Any]:
        """Validate JWT token authentication"""
        auth_header = request.headers.get("Authorization", "")
        
        if not auth_header.startswith("Bearer "):
            return {"success": False, "error": "Bearer token required"}
        
        token = auth_header[7:]  # Remove "Bearer " prefix
        
        try:
            # In production, use proper JWT validation with secret
            # For now, decode without verification
            decoded = jwt.decode(token, options={"verify_signature": False})
            client_id = decoded.get("sub", "unknown")
            
            return {"success": True, "client_id": client_id}
            
        except jwt.InvalidTokenError:
            return {"success": False, "error": "Invalid JWT token"}
    
    async def _validate_oauth2(self, request: APIRequest, route: Route) -> Dict[str, Any]:
        """Validate OAuth2 token authentication"""
        # Placeholder for OAuth2 validation
        # In production, validate with OAuth2 provider
        auth_header = request.headers.get("Authorization", "")
        
        if not auth_header.startswith("Bearer "):
            return {"success": False, "error": "OAuth2 bearer token required"}
        
        # Simulate OAuth2 validation
        return {"success": True, "client_id": "oauth2_user"}
    
    async def _validate_basic_auth(self, request: APIRequest, route: Route) -> Dict[str, Any]:
        """Validate basic authentication"""
        auth_header = request.headers.get("Authorization", "")
        
        if not auth_header.startswith("Basic "):
            return {"success": False, "error": "Basic authentication required"}
        
        # Placeholder for basic auth validation
        return {"success": True, "client_id": "basic_auth_user"}
    
    async def _check_rate_limit(self, request: APIRequest, route: Route) -> Dict[str, Any]:
        """Check rate limiting for request"""
        client_key = f"{request.client_id}:{route.route_id}"
        
        for limit_type, limit_value in route.rate_limit.items():
            window_seconds = self._get_window_seconds(limit_type)
            
            if self.redis_client:
                # Use Redis for distributed rate limiting
                current_count = await self._check_redis_rate_limit(
                    client_key, limit_type, limit_value, window_seconds
                )
            else:
                # Use in-memory rate limiting
                current_count = self._check_memory_rate_limit(
                    client_key, limit_type, limit_value, window_seconds
                )
            
            if current_count > limit_value:
                return {
                    "allowed": False,
                    "limit_type": limit_type,
                    "limit": limit_value,
                    "current": current_count,
                    "retry_after": window_seconds
                }
        
        return {"allowed": True}
    
    def _get_window_seconds(self, limit_type: str) -> int:
        """Get window seconds for rate limit type"""
        windows = {
            RateLimitType.PER_MINUTE.value: 60,
            RateLimitType.PER_HOUR.value: 3600,
            RateLimitType.PER_DAY.value: 86400,
            RateLimitType.BURST.value: 1
        }
        return windows.get(limit_type, 60)
    
    async def _check_redis_rate_limit(self, client_key: str, limit_type: str, 
                                    limit_value: int, window_seconds: int) -> int:
        """Check rate limit using Redis"""
        try:
            redis_key = f"rate_limit:{client_key}:{limit_type}"
            current_count = self.redis_client.incr(redis_key)
            
            if current_count == 1:
                self.redis_client.expire(redis_key, window_seconds)
            
            return current_count
            
        except Exception as e:
            logger.error(f"Redis rate limit error: {e}")
            return 0  # Allow request if Redis fails
    
    def _check_memory_rate_limit(self, client_key: str, limit_type: str,
                               limit_value: int, window_seconds: int) -> int:
        """Check rate limit using in-memory storage"""
        now = datetime.now()
        rule_key = f"{client_key}:{limit_type}"
        
        if rule_key not in self.rate_limits[client_key]:
            self.rate_limits[client_key][rule_key] = RateLimitRule(
                client_id=client_key,
                rule_type=RateLimitType(limit_type),
                limit=limit_value,
                window_seconds=window_seconds,
                current_count=0,
                reset_time=now + timedelta(seconds=window_seconds)
            )
        
        rule = self.rate_limits[client_key][rule_key]
        
        # Reset counter if window has passed
        if now >= rule.reset_time:
            rule.current_count = 0
            rule.reset_time = now + timedelta(seconds=window_seconds)
        
        rule.current_count += 1
        return rule.current_count
    
    def _check_circuit_breaker(self, service_id: str) -> Dict[str, Any]:
        """Check circuit breaker state"""
        if service_id not in self.circuit_breakers:
            self.circuit_breakers[service_id] = CircuitBreakerState(
                service_id=service_id,
                state="closed",
                failure_count=0,
                failure_threshold=5,
                timeout=30,
                next_attempt=datetime.now(),
                success_count=0
            )
        
        breaker = self.circuit_breakers[service_id]
        now = datetime.now()
        
        if breaker.state == "open":
            if now >= breaker.next_attempt:
                breaker.state = "half_open"
                breaker.success_count = 0
                return {"closed": True, "state": "half_open"}
            else:
                return {"closed": False, "state": "open"}
        
        return {"closed": True, "state": breaker.state}
    
    def _update_circuit_breaker(self, service_id: str, success: bool, status_code: int):
        """Update circuit breaker state based on request result"""
        if service_id not in self.circuit_breakers:
            return
        
        breaker = self.circuit_breakers[service_id]
        
        if success and status_code < 500:
            if breaker.state == "half_open":
                breaker.success_count += 1
                if breaker.success_count >= 3:
                    breaker.state = "closed"
                    breaker.failure_count = 0
            elif breaker.state == "closed":
                breaker.failure_count = max(0, breaker.failure_count - 1)
        else:
            breaker.failure_count += 1
            if breaker.failure_count >= breaker.failure_threshold:
                breaker.state = "open"
                breaker.next_attempt = datetime.now() + timedelta(seconds=breaker.timeout)
    
    async def _get_cached_response(self, request: APIRequest, route: Route) -> Optional[APIResponse]:
        """Get cached response if available"""
        cache_key = self._generate_cache_key(request, route)
        
        if self.redis_client:
            try:
                cached_data = self.redis_client.get(f"cache:{cache_key}")
                if cached_data:
                    data = json.loads(cached_data)
                    return APIResponse(
                        request_id=request.request_id,
                        status_code=data["status_code"],
                        headers=data["headers"],
                        body=data["body"].encode() if data["body"] else None,
                        response_time=0,
                        upstream_service=route.upstream_url,
                        cached=True,
                        timestamp=datetime.now()
                    )
            except Exception as e:
                logger.error(f"Cache retrieval error: {e}")
        
        # Check in-memory cache
        if cache_key in self.request_cache:
            cached_response, cache_time = self.request_cache[cache_key]
            if datetime.now() - cache_time < timedelta(seconds=route.cache_ttl):
                cached_response.cached = True
                return cached_response
        
        return None
    
    async def _cache_response(self, request: APIRequest, response: APIResponse, route: Route):
        """Cache response for future requests"""
        cache_key = self._generate_cache_key(request, route)
        
        if self.redis_client:
            try:
                cache_data = {
                    "status_code": response.status_code,
                    "headers": response.headers,
                    "body": response.body.decode() if response.body else None
                }
                self.redis_client.setex(
                    f"cache:{cache_key}",
                    route.cache_ttl,
                    json.dumps(cache_data)
                )
            except Exception as e:
                logger.error(f"Cache storage error: {e}")
        
        # Store in memory cache as backup
        self.request_cache[cache_key] = (response, datetime.now())
    
    def _generate_cache_key(self, request: APIRequest, route: Route) -> str:
        """Generate cache key for request"""
        key_data = f"{route.route_id}:{request.path}:{request.method}"
        if request.query_params:
            sorted_params = sorted(request.query_params.items())
            key_data += ":" + "&".join([f"{k}={v}" for k, v in sorted_params])
        
        return hashlib.md5(key_data.encode()).hexdigest()
    
    async def _forward_request(self, request: APIRequest, route: Route) -> APIResponse:
        """Forward request to upstream service"""
        try:
            # Build upstream URL
            upstream_path = request.path.replace("/api", "", 1)  # Remove /api prefix
            upstream_url = f"{route.upstream_url}{upstream_path}"
            
            # Prepare headers
            headers = dict(request.headers)
            headers["X-Request-ID"] = request.request_id
            headers["X-Client-ID"] = request.client_id
            headers["X-Forwarded-For"] = request.ip_address
            
            # Make request with timeout and retry
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=route.timeout/1000)) as session:
                for attempt in range(route.retry_count + 1):
                    try:
                        async with session.request(
                            method=request.method,
                            url=upstream_url,
                            headers=headers,
                            params=request.query_params,
                            data=request.body
                        ) as response:
                            response_body = await response.read()
                            
                            return APIResponse(
                                request_id=request.request_id,
                                status_code=response.status,
                                headers=dict(response.headers),
                                body=response_body,
                                response_time=0,  # Will be set by caller
                                upstream_service=route.upstream_url,
                                cached=False,
                                timestamp=datetime.now()
                            )
                            
                    except asyncio.TimeoutError:
                        if attempt < route.retry_count:
                            await asyncio.sleep(2 ** attempt)  # Exponential backoff
                            continue
                        raise
                    except Exception as e:
                        if attempt < route.retry_count:
                            await asyncio.sleep(2 ** attempt)
                            continue
                        raise
                        
        except Exception as e:
            logger.error(f"Upstream request failed: {e}")
            return self._create_error_response(
                request.request_id, 502, "Upstream service error"
            )
    
    async def _transform_request(self, request: APIRequest, route: Route) -> APIRequest:
        """Transform request before forwarding"""
        # Add route-specific transformations here
        # For now, just add some standard headers
        
        if "mls" in route.tags:
            # Add MLS-specific headers
            request.headers["X-MLS-Integration"] = "true"
            request.headers["X-Source-System"] = "EstateCore"
        
        if "payments" in route.tags:
            # Add payment-specific headers
            request.headers["X-Payment-Gateway"] = "true"
            request.headers["X-Secure-Transaction"] = "true"
        
        return request
    
    async def _transform_response(self, response: APIResponse, route: Route) -> APIResponse:
        """Transform response before returning"""
        # Add standard response headers
        response.headers["X-Gateway"] = "EstateCore-Gateway"
        response.headers["X-Response-Time"] = str(response.response_time)
        response.headers["X-Cache-Status"] = "HIT" if response.cached else "MISS"
        
        return response
    
    async def _update_metrics(self, request: APIRequest, response: APIResponse, route: Route):
        """Update request/response metrics"""
        # Store request/response pair
        self.request_history.append({
            "request_id": request.request_id,
            "route_id": route.route_id,
            "method": request.method,
            "status_code": response.status_code,
            "response_time": response.response_time,
            "timestamp": response.timestamp.isoformat(),
            "cached": response.cached
        })
        
        # Update route-specific metrics
        self.response_metrics[route.route_id].append(response.response_time)
        
        # Keep only recent metrics
        if len(self.response_metrics[route.route_id]) > 1000:
            self.response_metrics[route.route_id] = self.response_metrics[route.route_id][-1000:]
    
    def _create_error_response(self, request_id: str, status_code: int, 
                             message: str, headers: Dict[str, str] = None) -> APIResponse:
        """Create error response"""
        error_body = json.dumps({
            "error": message,
            "status_code": status_code,
            "request_id": request_id,
            "timestamp": datetime.now().isoformat()
        }).encode()
        
        response_headers = {"Content-Type": "application/json"}
        if headers:
            response_headers.update(headers)
        
        return APIResponse(
            request_id=request_id,
            status_code=status_code,
            headers=response_headers,
            body=error_body,
            response_time=0,
            upstream_service="gateway",
            cached=False,
            timestamp=datetime.now()
        )
    
    async def get_gateway_metrics(self) -> Dict[str, Any]:
        """Get comprehensive gateway metrics"""
        total_requests = len(self.request_history)
        
        if total_requests == 0:
            return {"total_requests": 0, "message": "No requests processed yet"}
        
        # Calculate response time statistics
        response_times = [req["response_time"] for req in self.request_history]
        avg_response_time = sum(response_times) / len(response_times)
        
        # Status code distribution
        status_codes = defaultdict(int)
        for req in self.request_history:
            status_codes[req["status_code"]] += 1
        
        # Route performance
        route_metrics = {}
        for route_id, times in self.response_metrics.items():
            if times:
                route_metrics[route_id] = {
                    "avg_response_time": sum(times) / len(times),
                    "min_response_time": min(times),
                    "max_response_time": max(times),
                    "request_count": len(times)
                }
        
        # Circuit breaker states
        circuit_states = {
            service_id: breaker.state 
            for service_id, breaker in self.circuit_breakers.items()
        }
        
        return {
            "total_requests": total_requests,
            "avg_response_time": avg_response_time,
            "status_code_distribution": dict(status_codes),
            "route_performance": route_metrics,
            "circuit_breaker_states": circuit_states,
            "active_routes": len(self.routes),
            "cache_hit_rate": len([req for req in self.request_history if req["cached"]]) / total_requests,
            "last_updated": datetime.now().isoformat()
        }

# Global instance
_gateway_manager = None

def get_gateway_manager() -> APIGatewayManager:
    """Get global gateway manager instance"""
    global _gateway_manager
    if _gateway_manager is None:
        _gateway_manager = APIGatewayManager()
    return _gateway_manager

# API convenience functions
async def process_gateway_request(request_data: Dict[str, Any]) -> Dict[str, Any]:
    """Process request through API gateway"""
    gateway = get_gateway_manager()
    
    # Convert dict to APIRequest object
    api_request = APIRequest(
        request_id=request_data.get("request_id", str(uuid.uuid4())),
        client_id=request_data.get("client_id", "unknown"),
        route_id="",  # Will be determined by gateway
        method=request_data.get("method", "GET"),
        path=request_data.get("path", "/"),
        headers=request_data.get("headers", {}),
        query_params=request_data.get("query_params", {}),
        body=request_data.get("body", "").encode() if request_data.get("body") else None,
        timestamp=datetime.now(),
        ip_address=request_data.get("ip_address", "127.0.0.1"),
        user_agent=request_data.get("user_agent", "EstateCore-Client")
    )
    
    response = await gateway.process_request(api_request)
    
    return {
        "request_id": response.request_id,
        "status_code": response.status_code,
        "headers": response.headers,
        "body": response.body.decode() if response.body else None,
        "response_time": response.response_time,
        "cached": response.cached,
        "timestamp": response.timestamp.isoformat()
    }

async def get_gateway_metrics_api() -> Dict[str, Any]:
    """Get gateway metrics for API"""
    gateway = get_gateway_manager()
    return await gateway.get_gateway_metrics()

if __name__ == "__main__":
    # Test the API Gateway
    async def test_gateway():
        gateway = APIGatewayManager()
        
        print("Testing API Gateway Manager")
        print("=" * 50)
        
        # Test request processing
        test_request = APIRequest(
            request_id="test-001",
            client_id="test-client",
            route_id="",
            method="GET",
            path="/api/properties/list",
            headers={"Authorization": "Bearer test-token"},
            query_params={"limit": "10"},
            body=None,
            timestamp=datetime.now(),
            ip_address="192.168.1.100",
            user_agent="TestClient/1.0"
        )
        
        print("Processing test request...")
        response = await gateway.process_request(test_request)
        print(f"Response status: {response.status_code}")
        print(f"Response time: {response.response_time:.3f}s")
        
        # Get metrics
        print("\nGateway metrics:")
        metrics = await gateway.get_gateway_metrics()
        print(f"Total requests: {metrics['total_requests']}")
        print(f"Average response time: {metrics['avg_response_time']:.3f}s")
        
        print("\nAPI Gateway Test Complete!")
    
    asyncio.run(test_gateway())