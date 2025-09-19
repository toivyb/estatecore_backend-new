"""
Advanced Rate Limiting Service for EstateCore
Implements sophisticated rate limiting with multiple algorithms and strategies
"""

import time
import logging
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
from collections import defaultdict, deque
from threading import Lock
from enum import Enum
import hashlib
import json
try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RateLimitAlgorithm(Enum):
    """Rate limiting algorithms"""
    TOKEN_BUCKET = "token_bucket"
    SLIDING_WINDOW = "sliding_window"
    FIXED_WINDOW = "fixed_window"
    LEAKY_BUCKET = "leaky_bucket"

class RateLimitScope(Enum):
    """Rate limiting scopes"""
    GLOBAL = "global"
    PER_IP = "per_ip"
    PER_USER = "per_user"
    PER_ENDPOINT = "per_endpoint"
    PER_API_KEY = "per_api_key"

class RateLimitAction(Enum):
    """Actions to take when rate limit is exceeded"""
    REJECT = "reject"
    DELAY = "delay"
    THROTTLE = "throttle"
    CAPTCHA = "captcha"

class RateLimitConfig:
    """Rate limit configuration"""
    
    def __init__(self, 
                 requests_per_minute: int = 60,
                 requests_per_hour: int = 1000,
                 requests_per_day: int = 10000,
                 algorithm: RateLimitAlgorithm = RateLimitAlgorithm.SLIDING_WINDOW,
                 scope: RateLimitScope = RateLimitScope.PER_IP,
                 action: RateLimitAction = RateLimitAction.REJECT,
                 burst_allowance: int = 10,
                 whitelist: List[str] = None,
                 blacklist: List[str] = None):
        
        self.requests_per_minute = requests_per_minute
        self.requests_per_hour = requests_per_hour
        self.requests_per_day = requests_per_day
        self.algorithm = algorithm
        self.scope = scope
        self.action = action
        self.burst_allowance = burst_allowance
        self.whitelist = whitelist or []
        self.blacklist = blacklist or []

class TokenBucket:
    """Token bucket rate limiter implementation"""
    
    def __init__(self, capacity: int, refill_rate: float):
        self.capacity = capacity
        self.tokens = capacity
        self.refill_rate = refill_rate  # tokens per second
        self.last_refill = time.time()
        self._lock = Lock()
    
    def consume(self, tokens: int = 1) -> bool:
        """Try to consume tokens from bucket"""
        with self._lock:
            now = time.time()
            
            # Refill tokens based on elapsed time
            elapsed = now - self.last_refill
            self.tokens = min(self.capacity, self.tokens + elapsed * self.refill_rate)
            self.last_refill = now
            
            # Check if we have enough tokens
            if self.tokens >= tokens:
                self.tokens -= tokens
                return True
            
            return False
    
    def get_status(self) -> Dict[str, Any]:
        """Get current bucket status"""
        with self._lock:
            return {
                'tokens': self.tokens,
                'capacity': self.capacity,
                'refill_rate': self.refill_rate,
                'utilization': (self.capacity - self.tokens) / self.capacity
            }

class SlidingWindow:
    """Sliding window rate limiter implementation"""
    
    def __init__(self, window_size: int, max_requests: int):
        self.window_size = window_size  # seconds
        self.max_requests = max_requests
        self.requests = deque()
        self._lock = Lock()
    
    def is_allowed(self) -> bool:
        """Check if request is allowed"""
        with self._lock:
            now = time.time()
            
            # Remove old requests outside the window
            while self.requests and self.requests[0] <= now - self.window_size:
                self.requests.popleft()
            
            # Check if we're under the limit
            if len(self.requests) < self.max_requests:
                self.requests.append(now)
                return True
            
            return False
    
    def get_status(self) -> Dict[str, Any]:
        """Get current window status"""
        with self._lock:
            now = time.time()
            
            # Clean up old requests
            while self.requests and self.requests[0] <= now - self.window_size:
                self.requests.popleft()
            
            return {
                'current_requests': len(self.requests),
                'max_requests': self.max_requests,
                'window_size': self.window_size,
                'utilization': len(self.requests) / self.max_requests,
                'reset_time': min(self.requests) + self.window_size if self.requests else now
            }

class FixedWindow:
    """Fixed window rate limiter implementation"""
    
    def __init__(self, window_size: int, max_requests: int):
        self.window_size = window_size  # seconds
        self.max_requests = max_requests
        self.current_window = 0
        self.request_count = 0
        self._lock = Lock()
    
    def is_allowed(self) -> bool:
        """Check if request is allowed"""
        with self._lock:
            now = time.time()
            current_window = int(now // self.window_size)
            
            # Reset counter if we're in a new window
            if current_window != self.current_window:
                self.current_window = current_window
                self.request_count = 0
            
            # Check if we're under the limit
            if self.request_count < self.max_requests:
                self.request_count += 1
                return True
            
            return False
    
    def get_status(self) -> Dict[str, Any]:
        """Get current window status"""
        with self._lock:
            now = time.time()
            current_window = int(now // self.window_size)
            
            if current_window != self.current_window:
                return {
                    'current_requests': 0,
                    'max_requests': self.max_requests,
                    'window_size': self.window_size,
                    'utilization': 0.0,
                    'reset_time': (current_window + 1) * self.window_size
                }
            
            return {
                'current_requests': self.request_count,
                'max_requests': self.max_requests,
                'window_size': self.window_size,
                'utilization': self.request_count / self.max_requests,
                'reset_time': (self.current_window + 1) * self.window_size
            }

class RateLimitingService:
    """Advanced rate limiting service"""
    
    def __init__(self, redis_url: Optional[str] = None):
        self.redis_client = None
        if redis_url and REDIS_AVAILABLE:
            try:
                self.redis_client = redis.from_url(redis_url)
                self.redis_client.ping()
                logger.info("Connected to Redis for distributed rate limiting")
            except Exception as e:
                logger.warning(f"Failed to connect to Redis: {e}, using in-memory storage")
                self.redis_client = None
        elif redis_url and not REDIS_AVAILABLE:
            logger.warning("Redis not available, using in-memory storage")
        
        # In-memory storage for rate limiters
        self.limiters = defaultdict(dict)
        self.global_lock = Lock()
        
        # Default configurations
        self.default_configs = {
            'api': RateLimitConfig(
                requests_per_minute=100,
                requests_per_hour=2000,
                algorithm=RateLimitAlgorithm.SLIDING_WINDOW,
                scope=RateLimitScope.PER_IP
            ),
            'auth': RateLimitConfig(
                requests_per_minute=10,
                requests_per_hour=100,
                algorithm=RateLimitAlgorithm.FIXED_WINDOW,
                scope=RateLimitScope.PER_IP,
                action=RateLimitAction.DELAY
            ),
            'upload': RateLimitConfig(
                requests_per_minute=5,
                requests_per_hour=50,
                algorithm=RateLimitAlgorithm.TOKEN_BUCKET,
                scope=RateLimitScope.PER_USER
            ),
            'bulk': RateLimitConfig(
                requests_per_minute=2,
                requests_per_hour=10,
                algorithm=RateLimitAlgorithm.TOKEN_BUCKET,
                scope=RateLimitScope.PER_USER
            )
        }
        
        # Custom endpoint configurations
        self.endpoint_configs = {}
        
        # Statistics tracking
        self.stats = {
            'total_requests': 0,
            'blocked_requests': 0,
            'delayed_requests': 0,
            'endpoints': defaultdict(lambda: {
                'requests': 0,
                'blocked': 0,
                'delayed': 0
            })
        }
        
        logger.info("Rate limiting service initialized")
    
    def configure_endpoint(self, endpoint: str, config: RateLimitConfig):
        """Configure rate limiting for specific endpoint"""
        self.endpoint_configs[endpoint] = config
        logger.info(f"Configured rate limiting for endpoint: {endpoint}")
    
    def get_limiter_key(self, identifier: str, endpoint: str, scope: RateLimitScope) -> str:
        """Generate unique key for rate limiter"""
        if scope == RateLimitScope.GLOBAL:
            return f"global:{endpoint}"
        elif scope == RateLimitScope.PER_IP:
            return f"ip:{identifier}:{endpoint}"
        elif scope == RateLimitScope.PER_USER:
            return f"user:{identifier}:{endpoint}"
        elif scope == RateLimitScope.PER_ENDPOINT:
            return f"endpoint:{endpoint}"
        elif scope == RateLimitScope.PER_API_KEY:
            return f"apikey:{identifier}:{endpoint}"
        else:
            return f"unknown:{identifier}:{endpoint}"
    
    def get_or_create_limiter(self, key: str, config: RateLimitConfig) -> Any:
        """Get or create rate limiter for given key"""
        if key not in self.limiters:
            if config.algorithm == RateLimitAlgorithm.TOKEN_BUCKET:
                # Convert per-minute to per-second rate
                refill_rate = config.requests_per_minute / 60.0
                self.limiters[key] = TokenBucket(
                    capacity=config.requests_per_minute + config.burst_allowance,
                    refill_rate=refill_rate
                )
            elif config.algorithm == RateLimitAlgorithm.SLIDING_WINDOW:
                self.limiters[key] = SlidingWindow(
                    window_size=60,  # 1 minute window
                    max_requests=config.requests_per_minute
                )
            elif config.algorithm == RateLimitAlgorithm.FIXED_WINDOW:
                self.limiters[key] = FixedWindow(
                    window_size=60,  # 1 minute window
                    max_requests=config.requests_per_minute
                )
            else:
                # Default to sliding window
                self.limiters[key] = SlidingWindow(
                    window_size=60,
                    max_requests=config.requests_per_minute
                )
        
        return self.limiters[key]
    
    def is_whitelisted(self, identifier: str, config: RateLimitConfig) -> bool:
        """Check if identifier is whitelisted"""
        return identifier in config.whitelist
    
    def is_blacklisted(self, identifier: str, config: RateLimitConfig) -> bool:
        """Check if identifier is blacklisted"""
        return identifier in config.blacklist
    
    def check_rate_limit(self, identifier: str, endpoint: str, 
                        user_id: Optional[int] = None) -> Dict[str, Any]:
        """Check if request should be rate limited"""
        try:
            # Update statistics
            self.stats['total_requests'] += 1
            self.stats['endpoints'][endpoint]['requests'] += 1
            
            # Get configuration for endpoint
            config = self.endpoint_configs.get(endpoint)
            if not config:
                # Try to match with default patterns
                if 'auth' in endpoint or 'login' in endpoint:
                    config = self.default_configs['auth']
                elif 'upload' in endpoint or 'file' in endpoint:
                    config = self.default_configs['upload']
                elif 'bulk' in endpoint:
                    config = self.default_configs['bulk']
                else:
                    config = self.default_configs['api']
            
            # Check blacklist first
            if self.is_blacklisted(identifier, config):
                self.stats['blocked_requests'] += 1
                self.stats['endpoints'][endpoint]['blocked'] += 1
                return {
                    'allowed': False,
                    'reason': 'blacklisted',
                    'retry_after': None,
                    'remaining': 0,
                    'reset_time': None
                }
            
            # Check whitelist
            if self.is_whitelisted(identifier, config):
                return {
                    'allowed': True,
                    'reason': 'whitelisted',
                    'retry_after': None,
                    'remaining': 999999,
                    'reset_time': None
                }
            
            # Determine which identifier to use based on scope
            if config.scope == RateLimitScope.PER_USER and user_id:
                rate_limit_id = str(user_id)
            else:
                rate_limit_id = identifier
            
            # Generate limiter key
            limiter_key = self.get_limiter_key(rate_limit_id, endpoint, config.scope)
            
            # Get or create limiter
            with self.global_lock:
                limiter = self.get_or_create_limiter(limiter_key, config)
            
            # Check rate limit based on algorithm
            if config.algorithm == RateLimitAlgorithm.TOKEN_BUCKET:
                allowed = limiter.consume(1)
                status = limiter.get_status()
                remaining = int(status['tokens'])
                reset_time = None
            else:
                allowed = limiter.is_allowed()
                status = limiter.get_status()
                remaining = status['max_requests'] - status['current_requests']
                reset_time = status.get('reset_time')
            
            if not allowed:
                self.stats['blocked_requests'] += 1
                self.stats['endpoints'][endpoint]['blocked'] += 1
                
                # Calculate retry after time
                if config.algorithm == RateLimitAlgorithm.TOKEN_BUCKET:
                    # Time to get one token back
                    retry_after = 1.0 / limiter.refill_rate
                elif reset_time:
                    retry_after = max(0, reset_time - time.time())
                else:
                    retry_after = 60  # Default 1 minute
                
                return {
                    'allowed': False,
                    'reason': 'rate_limited',
                    'retry_after': retry_after,
                    'remaining': remaining,
                    'reset_time': reset_time,
                    'algorithm': config.algorithm.value,
                    'scope': config.scope.value
                }
            
            return {
                'allowed': True,
                'reason': 'within_limits',
                'retry_after': None,
                'remaining': remaining,
                'reset_time': reset_time,
                'algorithm': config.algorithm.value,
                'scope': config.scope.value
            }
            
        except Exception as e:
            logger.error(f"Rate limit check failed: {e}")
            # Fail open - allow request if rate limiting fails
            return {
                'allowed': True,
                'reason': 'error',
                'retry_after': None,
                'remaining': 999,
                'reset_time': None,
                'error': str(e)
            }
    
    def get_rate_limit_status(self, identifier: str, endpoint: str, 
                             user_id: Optional[int] = None) -> Dict[str, Any]:
        """Get current rate limit status without consuming quota"""
        try:
            config = self.endpoint_configs.get(endpoint, self.default_configs['api'])
            
            if config.scope == RateLimitScope.PER_USER and user_id:
                rate_limit_id = str(user_id)
            else:
                rate_limit_id = identifier
            
            limiter_key = self.get_limiter_key(rate_limit_id, endpoint, config.scope)
            
            if limiter_key in self.limiters:
                limiter = self.limiters[limiter_key]
                status = limiter.get_status()
                return {
                    'endpoint': endpoint,
                    'algorithm': config.algorithm.value,
                    'scope': config.scope.value,
                    'status': status
                }
            
            return {
                'endpoint': endpoint,
                'algorithm': config.algorithm.value,
                'scope': config.scope.value,
                'status': 'no_data'
            }
            
        except Exception as e:
            logger.error(f"Failed to get rate limit status: {e}")
            return {'error': str(e)}
    
    def reset_rate_limit(self, identifier: str, endpoint: str, 
                        user_id: Optional[int] = None) -> Dict[str, Any]:
        """Reset rate limit for specific identifier/endpoint"""
        try:
            config = self.endpoint_configs.get(endpoint, self.default_configs['api'])
            
            if config.scope == RateLimitScope.PER_USER and user_id:
                rate_limit_id = str(user_id)
            else:
                rate_limit_id = identifier
            
            limiter_key = self.get_limiter_key(rate_limit_id, endpoint, config.scope)
            
            with self.global_lock:
                if limiter_key in self.limiters:
                    del self.limiters[limiter_key]
                    logger.info(f"Reset rate limit for {limiter_key}")
                    return {'success': True, 'message': 'Rate limit reset'}
                else:
                    return {'success': False, 'message': 'No rate limit data found'}
                    
        except Exception as e:
            logger.error(f"Failed to reset rate limit: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get rate limiting statistics"""
        try:
            total_requests = self.stats['total_requests']
            blocked_requests = self.stats['blocked_requests']
            
            return {
                'total_requests': total_requests,
                'blocked_requests': blocked_requests,
                'allowed_requests': total_requests - blocked_requests,
                'block_rate': blocked_requests / total_requests if total_requests > 0 else 0,
                'active_limiters': len(self.limiters),
                'endpoint_stats': dict(self.stats['endpoints']),
                'configurations': {
                    endpoint: {
                        'algorithm': config.algorithm.value,
                        'scope': config.scope.value,
                        'requests_per_minute': config.requests_per_minute
                    } for endpoint, config in self.endpoint_configs.items()
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to get statistics: {e}")
            return {'error': str(e)}
    
    def cleanup_expired_limiters(self):
        """Clean up expired rate limiters to save memory"""
        try:
            current_time = time.time()
            expired_keys = []
            
            with self.global_lock:
                for key, limiter in self.limiters.items():
                    # Check if limiter has been inactive for more than 1 hour
                    if hasattr(limiter, 'last_refill'):
                        if current_time - limiter.last_refill > 3600:
                            expired_keys.append(key)
                    elif hasattr(limiter, 'requests'):
                        if limiter.requests and current_time - limiter.requests[-1] > 3600:
                            expired_keys.append(key)
                
                for key in expired_keys:
                    del self.limiters[key]
            
            if expired_keys:
                logger.info(f"Cleaned up {len(expired_keys)} expired rate limiters")
                
        except Exception as e:
            logger.error(f"Failed to cleanup expired limiters: {e}")

# Singleton instance
_rate_limiting_service = None

def get_rate_limiting_service(redis_url: Optional[str] = None) -> RateLimitingService:
    """Get singleton rate limiting service instance"""
    global _rate_limiting_service
    if _rate_limiting_service is None:
        _rate_limiting_service = RateLimitingService(redis_url)
    return _rate_limiting_service

# Decorator for easy rate limiting
def rate_limit(endpoint: str = None, 
               requests_per_minute: int = 60,
               algorithm: RateLimitAlgorithm = RateLimitAlgorithm.SLIDING_WINDOW,
               scope: RateLimitScope = RateLimitScope.PER_IP):
    """Rate limiting decorator"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            from flask import request, jsonify, g
            
            # Get rate limiting service
            service = get_rate_limiting_service()
            
            # Determine endpoint name
            endpoint_name = endpoint or func.__name__
            
            # Get identifier based on scope
            if scope == RateLimitScope.PER_IP:
                identifier = request.remote_addr
            elif scope == RateLimitScope.PER_USER:
                identifier = getattr(g, 'user_id', request.remote_addr)
            else:
                identifier = request.remote_addr
            
            # Configure endpoint if not already configured
            if endpoint_name not in service.endpoint_configs:
                config = RateLimitConfig(
                    requests_per_minute=requests_per_minute,
                    algorithm=algorithm,
                    scope=scope
                )
                service.configure_endpoint(endpoint_name, config)
            
            # Check rate limit
            result = service.check_rate_limit(
                identifier=identifier,
                endpoint=endpoint_name,
                user_id=getattr(g, 'user_id', None)
            )
            
            if not result['allowed']:
                response = jsonify({
                    'error': 'Rate limit exceeded',
                    'reason': result['reason'],
                    'retry_after': result['retry_after'],
                    'remaining': result['remaining']
                })
                response.status_code = 429
                response.headers['X-RateLimit-Remaining'] = str(result['remaining'])
                if result['retry_after']:
                    response.headers['Retry-After'] = str(int(result['retry_after']))
                return response
            
            # Add rate limit headers to successful responses
            response = func(*args, **kwargs)
            if hasattr(response, 'headers'):
                response.headers['X-RateLimit-Remaining'] = str(result['remaining'])
                if result['reset_time']:
                    response.headers['X-RateLimit-Reset'] = str(int(result['reset_time']))
            
            return response
        
        wrapper.__name__ = func.__name__
        return wrapper
    return decorator

if __name__ == "__main__":
    # Test the rate limiting service
    service = get_rate_limiting_service()
    
    print("🛡️ Rate Limiting Service Test")
    
    # Configure test endpoint
    config = RateLimitConfig(
        requests_per_minute=5,
        algorithm=RateLimitAlgorithm.TOKEN_BUCKET,
        scope=RateLimitScope.PER_IP
    )
    service.configure_endpoint('/api/test', config)
    
    # Test rate limiting
    ip_address = '127.0.0.1'
    endpoint = '/api/test'
    
    print(f"Testing rate limiting for {endpoint} with limit 5/minute")
    
    for i in range(8):
        result = service.check_rate_limit(ip_address, endpoint)
        status = "ALLOWED" if result['allowed'] else "BLOCKED"
        print(f"Request {i+1}: {status} - Remaining: {result['remaining']}")
        
        if not result['allowed']:
            print(f"  Reason: {result['reason']}")
            print(f"  Retry after: {result['retry_after']:.2f}s")
    
    # Test statistics
    stats = service.get_statistics()
    print(f"\nStatistics:")
    print(f"Total requests: {stats['total_requests']}")
    print(f"Blocked requests: {stats['blocked_requests']}")
    print(f"Block rate: {stats['block_rate']:.1%}")
    
    print("✅ Rate limiting service is ready!")