"""
Performance Optimization Service for EstateCore
Implements caching, database optimization, and performance monitoring
"""

import os
import time
import logging
from functools import wraps
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import threading
import json
from collections import defaultdict
import hashlib

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MemoryCache:
    """In-memory cache implementation with TTL support"""
    
    def __init__(self, default_ttl: int = 300):
        self.cache = {}
        self.ttl_data = {}
        self.default_ttl = default_ttl
        self._lock = threading.RLock()
        
        # Start cleanup thread
        self._cleanup_thread = threading.Thread(target=self._cleanup_expired, daemon=True)
        self._cleanup_thread.start()
    
    def get(self, key: str) -> Any:
        """Get value from cache"""
        with self._lock:
            if key in self.cache:
                # Check if expired
                if key in self.ttl_data and time.time() > self.ttl_data[key]:
                    del self.cache[key]
                    del self.ttl_data[key]
                    return None
                return self.cache[key]
            return None
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set value in cache with TTL"""
        with self._lock:
            self.cache[key] = value
            if ttl is None:
                ttl = self.default_ttl
            self.ttl_data[key] = time.time() + ttl
    
    def delete(self, key: str) -> None:
        """Delete key from cache"""
        with self._lock:
            if key in self.cache:
                del self.cache[key]
            if key in self.ttl_data:
                del self.ttl_data[key]
    
    def clear(self) -> None:
        """Clear all cache"""
        with self._lock:
            self.cache.clear()
            self.ttl_data.clear()
    
    def _cleanup_expired(self):
        """Background thread to cleanup expired entries"""
        while True:
            try:
                current_time = time.time()
                with self._lock:
                    expired_keys = [
                        key for key, expiry_time in self.ttl_data.items()
                        if current_time > expiry_time
                    ]
                    for key in expired_keys:
                        if key in self.cache:
                            del self.cache[key]
                        del self.ttl_data[key]
                
                time.sleep(60)  # Cleanup every minute
            except Exception as e:
                logger.error(f"Cache cleanup error: {e}")
                time.sleep(60)

class PerformanceMonitor:
    """Performance monitoring and metrics collection"""
    
    def __init__(self):
        self.metrics = defaultdict(list)
        self.request_counts = defaultdict(int)
        self.error_counts = defaultdict(int)
        self._lock = threading.RLock()
    
    def record_request(self, endpoint: str, duration: float, status_code: int = 200):
        """Record request performance metrics"""
        with self._lock:
            timestamp = datetime.utcnow()
            self.metrics[endpoint].append({
                'timestamp': timestamp,
                'duration': duration,
                'status_code': status_code
            })
            
            self.request_counts[endpoint] += 1
            if status_code >= 400:
                self.error_counts[endpoint] += 1
            
            # Keep only last 1000 entries per endpoint
            if len(self.metrics[endpoint]) > 1000:
                self.metrics[endpoint] = self.metrics[endpoint][-1000:]
    
    def get_endpoint_stats(self, endpoint: str, hours: int = 24) -> Dict[str, Any]:
        """Get performance statistics for an endpoint"""
        with self._lock:
            if endpoint not in self.metrics:
                return {}
            
            cutoff_time = datetime.utcnow() - timedelta(hours=hours)
            recent_metrics = [
                m for m in self.metrics[endpoint]
                if m['timestamp'] > cutoff_time
            ]
            
            if not recent_metrics:
                return {}
            
            durations = [m['duration'] for m in recent_metrics]
            error_count = sum(1 for m in recent_metrics if m['status_code'] >= 400)
            
            return {
                'endpoint': endpoint,
                'total_requests': len(recent_metrics),
                'error_count': error_count,
                'error_rate': error_count / len(recent_metrics) if recent_metrics else 0,
                'avg_duration': sum(durations) / len(durations),
                'min_duration': min(durations),
                'max_duration': max(durations),
                'p95_duration': sorted(durations)[int(len(durations) * 0.95)] if durations else 0,
                'requests_per_hour': len(recent_metrics) / hours if hours > 0 else 0
            }
    
    def get_slow_endpoints(self, threshold_ms: float = 1000, hours: int = 24) -> List[Dict[str, Any]]:
        """Get endpoints that are performing slowly"""
        slow_endpoints = []
        
        for endpoint in self.metrics:
            stats = self.get_endpoint_stats(endpoint, hours)
            if stats and stats['avg_duration'] * 1000 > threshold_ms:
                slow_endpoints.append(stats)
        
        return sorted(slow_endpoints, key=lambda x: x['avg_duration'], reverse=True)

class DatabaseOptimizer:
    """Database query optimization utilities"""
    
    def __init__(self):
        self.query_cache = {}
        self.query_stats = defaultdict(list)
        self._lock = threading.RLock()
    
    def get_cached_query_result(self, query_hash: str) -> Any:
        """Get cached query result"""
        return self.query_cache.get(query_hash)
    
    def cache_query_result(self, query_hash: str, result: Any, ttl: int = 300):
        """Cache query result with TTL"""
        with self._lock:
            self.query_cache[query_hash] = {
                'result': result,
                'expires_at': time.time() + ttl
            }
    
    def cleanup_query_cache(self):
        """Remove expired query results"""
        current_time = time.time()
        with self._lock:
            expired_keys = [
                key for key, data in self.query_cache.items()
                if data['expires_at'] < current_time
            ]
            for key in expired_keys:
                del self.query_cache[key]
    
    def record_query_stats(self, query: str, duration: float):
        """Record query performance statistics"""
        with self._lock:
            query_hash = hashlib.md5(query.encode()).hexdigest()
            self.query_stats[query_hash].append({
                'timestamp': datetime.utcnow(),
                'duration': duration,
                'query': query[:100]  # Store first 100 chars for identification
            })
    
    def get_slow_queries(self, threshold_ms: float = 500) -> List[Dict[str, Any]]:
        """Get queries that are running slowly"""
        slow_queries = []
        
        with self._lock:
            for query_hash, stats in self.query_stats.items():
                if not stats:
                    continue
                
                avg_duration = sum(s['duration'] for s in stats) / len(stats)
                if avg_duration * 1000 > threshold_ms:
                    slow_queries.append({
                        'query_hash': query_hash,
                        'query_preview': stats[0]['query'],
                        'avg_duration_ms': avg_duration * 1000,
                        'execution_count': len(stats),
                        'last_execution': max(s['timestamp'] for s in stats)
                    })
        
        return sorted(slow_queries, key=lambda x: x['avg_duration_ms'], reverse=True)

class PerformanceService:
    """Main performance optimization service"""
    
    def __init__(self):
        self.cache = MemoryCache(default_ttl=300)  # 5 minutes default
        self.monitor = PerformanceMonitor()
        self.db_optimizer = DatabaseOptimizer()
        
        # Performance settings
        self.settings = {
            'cache_enabled': True,
            'cache_default_ttl': 300,
            'slow_query_threshold_ms': 500,
            'slow_endpoint_threshold_ms': 1000,
            'max_cache_size_mb': 100,
            'enable_query_caching': True,
            'enable_gzip_compression': True
        }
        
        logger.info("Performance service initialized")
    
    def get_cache_key(self, prefix: str, **kwargs) -> str:
        """Generate cache key from parameters"""
        key_data = f"{prefix}:{':'.join(f'{k}={v}' for k, v in sorted(kwargs.items()))}"
        return hashlib.md5(key_data.encode()).hexdigest()
    
    def cached_function(self, ttl: int = None, key_prefix: str = None):
        """Decorator for caching function results"""
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                if not self.settings['cache_enabled']:
                    return func(*args, **kwargs)
                
                # Generate cache key
                prefix = key_prefix or func.__name__
                cache_key = self.get_cache_key(prefix, args=str(args), kwargs=str(kwargs))
                
                # Try to get from cache
                cached_result = self.cache.get(cache_key)
                if cached_result is not None:
                    return cached_result
                
                # Execute function and cache result
                start_time = time.time()
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                
                # Cache the result
                cache_ttl = ttl or self.settings['cache_default_ttl']
                self.cache.set(cache_key, result, cache_ttl)
                
                # Record performance metrics
                self.monitor.record_request(f"cached_func_{func.__name__}", duration)
                
                return result
            return wrapper
        return decorator
    
    def monitor_endpoint(self, endpoint_name: str = None):
        """Decorator for monitoring endpoint performance"""
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                name = endpoint_name or func.__name__
                start_time = time.time()
                status_code = 200
                
                try:
                    result = func(*args, **kwargs)
                    return result
                except Exception as e:
                    status_code = 500
                    logger.error(f"Error in {name}: {e}")
                    raise
                finally:
                    duration = time.time() - start_time
                    self.monitor.record_request(name, duration, status_code)
            
            return wrapper
        return decorator
    
    def optimize_database_query(self, query: str, params: tuple = None):
        """Optimize database query with caching"""
        if not self.settings['enable_query_caching']:
            return None
        
        # Generate query hash for caching
        query_data = f"{query}:{str(params) if params else ''}"
        query_hash = hashlib.md5(query_data.encode()).hexdigest()
        
        # Check cache first
        cached_result = self.db_optimizer.get_cached_query_result(query_hash)
        if cached_result and cached_result['expires_at'] > time.time():
            return cached_result['result']
        
        return None
    
    def cache_database_result(self, query: str, params: tuple, result: Any, ttl: int = 300):
        """Cache database query result"""
        if not self.settings['enable_query_caching']:
            return
        
        query_data = f"{query}:{str(params) if params else ''}"
        query_hash = hashlib.md5(query_data.encode()).hexdigest()
        
        self.db_optimizer.cache_query_result(query_hash, result, ttl)
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get comprehensive performance summary"""
        try:
            # Get slow endpoints
            slow_endpoints = self.monitor.get_slow_endpoints(
                threshold_ms=self.settings['slow_endpoint_threshold_ms']
            )
            
            # Get slow queries
            slow_queries = self.db_optimizer.get_slow_queries(
                threshold_ms=self.settings['slow_query_threshold_ms']
            )
            
            # Cache statistics
            cache_stats = {
                'total_keys': len(self.cache.cache),
                'enabled': self.settings['cache_enabled'],
                'default_ttl': self.settings['cache_default_ttl']
            }
            
            # Overall statistics
            total_requests = sum(self.monitor.request_counts.values())
            total_errors = sum(self.monitor.error_counts.values())
            
            return {
                'timestamp': datetime.utcnow().isoformat(),
                'cache_stats': cache_stats,
                'request_stats': {
                    'total_requests': total_requests,
                    'total_errors': total_errors,
                    'error_rate': total_errors / total_requests if total_requests > 0 else 0
                },
                'slow_endpoints': slow_endpoints[:10],  # Top 10 slow endpoints
                'slow_queries': slow_queries[:10],  # Top 10 slow queries
                'settings': self.settings
            }
        except Exception as e:
            logger.error(f"Error generating performance summary: {e}")
            return {'error': str(e)}
    
    def optimize_settings(self, new_settings: Dict[str, Any]):
        """Update performance optimization settings"""
        try:
            for key, value in new_settings.items():
                if key in self.settings:
                    self.settings[key] = value
                    logger.info(f"Updated setting {key} to {value}")
            
            # Apply cache settings
            if 'cache_default_ttl' in new_settings:
                self.cache.default_ttl = new_settings['cache_default_ttl']
            
            return {'success': True, 'updated_settings': new_settings}
        except Exception as e:
            logger.error(f"Error updating settings: {e}")
            return {'success': False, 'error': str(e)}
    
    def clear_caches(self):
        """Clear all caches"""
        try:
            self.cache.clear()
            self.db_optimizer.query_cache.clear()
            logger.info("All caches cleared")
            return {'success': True, 'message': 'All caches cleared'}
        except Exception as e:
            logger.error(f"Error clearing caches: {e}")
            return {'success': False, 'error': str(e)}
    
    def generate_optimization_recommendations(self) -> List[Dict[str, Any]]:
        """Generate performance optimization recommendations"""
        recommendations = []
        
        try:
            # Check slow endpoints
            slow_endpoints = self.monitor.get_slow_endpoints(threshold_ms=1000)
            if slow_endpoints:
                recommendations.append({
                    'type': 'slow_endpoints',
                    'priority': 'high',
                    'title': 'Slow API Endpoints Detected',
                    'description': f'Found {len(slow_endpoints)} endpoints with average response time > 1000ms',
                    'action': 'Consider adding caching, database optimization, or request pagination',
                    'affected_endpoints': [ep['endpoint'] for ep in slow_endpoints[:5]]
                })
            
            # Check slow queries
            slow_queries = self.db_optimizer.get_slow_queries(threshold_ms=500)
            if slow_queries:
                recommendations.append({
                    'type': 'slow_queries',
                    'priority': 'high',
                    'title': 'Slow Database Queries',
                    'description': f'Found {len(slow_queries)} queries with average execution time > 500ms',
                    'action': 'Add database indexes, optimize queries, or implement query caching',
                    'slow_query_count': len(slow_queries)
                })
            
            # Check cache hit rate (if we had this metric)
            cache_size = len(self.cache.cache)
            if cache_size < 10:
                recommendations.append({
                    'type': 'cache_utilization',
                    'priority': 'medium',
                    'title': 'Low Cache Utilization',
                    'description': 'Cache is underutilized, consider caching more frequently accessed data',
                    'action': 'Implement caching for database queries and API responses',
                    'current_cache_size': cache_size
                })
            
            # Check error rates
            total_requests = sum(self.monitor.request_counts.values())
            total_errors = sum(self.monitor.error_counts.values())
            if total_requests > 0:
                error_rate = total_errors / total_requests
                if error_rate > 0.05:  # 5% error rate
                    recommendations.append({
                        'type': 'high_error_rate',
                        'priority': 'critical',
                        'title': 'High Error Rate',
                        'description': f'Error rate is {error_rate:.2%}, which is above the 5% threshold',
                        'action': 'Investigate error causes and implement better error handling',
                        'error_rate': error_rate
                    })
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Error generating recommendations: {e}")
            return [{
                'type': 'error',
                'priority': 'low',
                'title': 'Recommendation Generation Failed',
                'description': f'Error: {str(e)}',
                'action': 'Check system logs for details'
            }]

# Singleton instance
_performance_service = None

def get_performance_service() -> PerformanceService:
    """Get singleton performance service instance"""
    global _performance_service
    if _performance_service is None:
        _performance_service = PerformanceService()
    return _performance_service

# Utility decorators for easy use
def cached(ttl: int = 300, key_prefix: str = None):
    """Easy caching decorator"""
    service = get_performance_service()
    return service.cached_function(ttl=ttl, key_prefix=key_prefix)

def monitored(endpoint_name: str = None):
    """Easy monitoring decorator"""
    service = get_performance_service()
    return service.monitor_endpoint(endpoint_name=endpoint_name)

if __name__ == "__main__":
    # Test the performance service
    service = get_performance_service()
    
    print("🚀 Performance Service Test")
    
    # Test caching
    @service.cached_function(ttl=60, key_prefix="test_func")
    def test_expensive_function(x, y):
        time.sleep(0.1)  # Simulate expensive operation
        return x * y + 42
    
    # Test monitoring
    @service.monitor_endpoint("test_endpoint")
    def test_monitored_function():
        time.sleep(0.05)
        return "Hello, World!"
    
    # Run tests
    start_time = time.time()
    result1 = test_expensive_function(5, 10)  # Should be slow (cached)
    first_call_time = time.time() - start_time
    
    start_time = time.time()
    result2 = test_expensive_function(5, 10)  # Should be fast (from cache)
    second_call_time = time.time() - start_time
    
    print(f"First call (cached): {first_call_time:.3f}s, Result: {result1}")
    print(f"Second call (from cache): {second_call_time:.3f}s, Result: {result2}")
    print(f"Cache speedup: {first_call_time / second_call_time:.1f}x")
    
    # Test monitoring
    for _ in range(5):
        test_monitored_function()
    
    # Get performance summary
    summary = service.get_performance_summary()
    print(f"Performance summary generated with {summary['request_stats']['total_requests']} total requests")
    
    # Generate recommendations
    recommendations = service.generate_optimization_recommendations()
    print(f"Generated {len(recommendations)} optimization recommendations")
    
    print("✅ Performance service is ready!")