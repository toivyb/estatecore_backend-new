"""
AppFolio API Client

Comprehensive API client for AppFolio Property Manager, Investment Manager,
and related services with support for all major entities and operations.
"""

import logging
import json
import time
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union, Tuple
from dataclasses import dataclass, field, asdict
from enum import Enum
import requests
from urllib.parse import urljoin, urlencode
import backoff
from concurrent.futures import ThreadPoolExecutor
import threading

from .appfolio_auth_service import AppFolioAuthService, AppFolioConnection

logger = logging.getLogger(__name__)

class AppFolioEntityType(Enum):
    """AppFolio entity types"""
    # Core Property Management
    PROPERTIES = "properties"
    UNITS = "units"
    TENANTS = "tenants"
    RESIDENTS = "residents"
    LEASES = "leases"
    RENT_ROLLS = "rent_rolls"
    
    # Financial
    PAYMENTS = "payments"
    INVOICES = "invoices"
    CHARGES = "charges"
    ACCOUNTS = "accounts"
    BANK_ACCOUNTS = "bank_accounts"
    BUDGETS = "budgets"
    FINANCIAL_REPORTS = "financial_reports"
    
    # Maintenance
    WORK_ORDERS = "work_orders"
    MAINTENANCE_REQUESTS = "maintenance_requests"
    VENDORS = "vendors"
    PURCHASE_ORDERS = "purchase_orders"
    
    # Leasing
    APPLICATIONS = "applications"
    PROSPECTS = "prospects"
    SHOWINGS = "showings"
    SCREENING_REPORTS = "screening_reports"
    
    # Communications
    MESSAGES = "messages"
    NOTIFICATIONS = "notifications"
    DOCUMENTS = "documents"
    
    # Investment Management
    PORTFOLIOS = "portfolios"
    INVESTMENTS = "investments"
    PERFORMANCE_REPORTS = "performance_reports"
    
    # Administration
    USERS = "users"
    ROLES = "roles"
    COMPANIES = "companies"
    SETTINGS = "settings"

class AppFolioOperationType(Enum):
    """AppFolio operation types"""
    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    LIST = "list"
    SEARCH = "search"
    BULK = "bulk"

class AppFolioRequestType(Enum):
    """AppFolio request types"""
    SYNC = "sync"
    ASYNC = "async"
    WEBHOOK = "webhook"
    BATCH = "batch"

@dataclass
class AppFolioRequest:
    """AppFolio API request structure"""
    entity_type: AppFolioEntityType
    operation: AppFolioOperationType
    request_type: AppFolioRequestType = AppFolioRequestType.SYNC
    entity_id: Optional[str] = None
    data: Optional[Dict[str, Any]] = None
    filters: Optional[Dict[str, Any]] = None
    pagination: Optional[Dict[str, Any]] = None
    includes: Optional[List[str]] = None
    fields: Optional[List[str]] = None
    timeout: int = 30
    retry_count: int = 3
    priority: str = "normal"
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class AppFolioResponse:
    """AppFolio API response structure"""
    success: bool
    status_code: int
    data: Any
    headers: Dict[str, str]
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    pagination: Optional[Dict[str, Any]] = None
    rate_limit: Optional[Dict[str, Any]] = None
    request_id: Optional[str] = None
    processing_time: float = 0.0
    cached: bool = False

@dataclass
class RateLimitInfo:
    """Rate limit information"""
    requests_remaining: int
    requests_limit: int
    reset_time: datetime
    retry_after: Optional[int] = None

class AppFolioAPIClient:
    """
    AppFolio API Client
    
    Comprehensive client for interacting with AppFolio's API ecosystem
    including Property Manager, Investment Manager, and related services.
    """
    
    def __init__(self, auth_service: AppFolioAuthService):
        self.auth_service = auth_service
        self.session = requests.Session()
        self.rate_limits: Dict[str, RateLimitInfo] = {}
        self.request_cache: Dict[str, Tuple[AppFolioResponse, datetime]] = {}
        self.executor = ThreadPoolExecutor(max_workers=10)
        
        # API endpoints by entity type
        self.entity_endpoints = {
            AppFolioEntityType.PROPERTIES: "properties",
            AppFolioEntityType.UNITS: "units",
            AppFolioEntityType.TENANTS: "tenants",
            AppFolioEntityType.RESIDENTS: "residents",
            AppFolioEntityType.LEASES: "leases",
            AppFolioEntityType.RENT_ROLLS: "rent_rolls",
            AppFolioEntityType.PAYMENTS: "payments",
            AppFolioEntityType.INVOICES: "invoices",
            AppFolioEntityType.CHARGES: "charges",
            AppFolioEntityType.ACCOUNTS: "accounts",
            AppFolioEntityType.BANK_ACCOUNTS: "bank_accounts",
            AppFolioEntityType.BUDGETS: "budgets",
            AppFolioEntityType.FINANCIAL_REPORTS: "financial_reports",
            AppFolioEntityType.WORK_ORDERS: "work_orders",
            AppFolioEntityType.MAINTENANCE_REQUESTS: "maintenance_requests",
            AppFolioEntityType.VENDORS: "vendors",
            AppFolioEntityType.PURCHASE_ORDERS: "purchase_orders",
            AppFolioEntityType.APPLICATIONS: "applications",
            AppFolioEntityType.PROSPECTS: "prospects",
            AppFolioEntityType.SHOWINGS: "showings",
            AppFolioEntityType.SCREENING_REPORTS: "screening_reports",
            AppFolioEntityType.MESSAGES: "messages",
            AppFolioEntityType.NOTIFICATIONS: "notifications",
            AppFolioEntityType.DOCUMENTS: "documents",
            AppFolioEntityType.PORTFOLIOS: "portfolios",
            AppFolioEntityType.INVESTMENTS: "investments",
            AppFolioEntityType.PERFORMANCE_REPORTS: "performance_reports",
            AppFolioEntityType.USERS: "users",
            AppFolioEntityType.ROLES: "roles",
            AppFolioEntityType.COMPANIES: "companies",
            AppFolioEntityType.SETTINGS: "settings"
        }
        
        # Default headers
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'User-Agent': 'EstateCore-AppFolio-Integration/1.0'
        })
        
        logger.info("AppFolio API Client initialized")
    
    def execute_request(self, connection_id: str, request: AppFolioRequest) -> AppFolioResponse:
        """
        Execute an AppFolio API request
        
        Args:
            connection_id: AppFolio connection identifier
            request: Request configuration
            
        Returns:
            AppFolio response
        """
        start_time = time.time()
        request_id = str(uuid.uuid4())
        
        try:
            # Get connection and validate
            connection = self.auth_service.active_connections.get(connection_id)
            if not connection:
                return AppFolioResponse(
                    success=False,
                    status_code=401,
                    data=None,
                    headers={},
                    errors=["Invalid connection ID"],
                    request_id=request_id
                )
            
            # Get valid access token
            access_token = self.auth_service.get_valid_access_token(connection_id)
            if not access_token:
                return AppFolioResponse(
                    success=False,
                    status_code=401,
                    data=None,
                    headers={},
                    errors=["No valid access token"],
                    request_id=request_id
                )
            
            # Check rate limits
            rate_limit_check = self._check_rate_limits(connection_id)
            if not rate_limit_check['allowed']:
                return AppFolioResponse(
                    success=False,
                    status_code=429,
                    data=None,
                    headers={},
                    errors=["Rate limit exceeded"],
                    request_id=request_id,
                    rate_limit=rate_limit_check
                )
            
            # Check cache for GET requests
            if request.operation == AppFolioOperationType.READ and request.request_type == AppFolioRequestType.SYNC:
                cache_key = self._generate_cache_key(request)
                cached_response = self._get_cached_response(cache_key)
                if cached_response:
                    cached_response.request_id = request_id
                    cached_response.cached = True
                    return cached_response
            
            # Build request URL and parameters
            url = self._build_request_url(connection, request)
            headers = self._build_request_headers(access_token, request_id)
            
            # Execute request with retry logic
            response = self._execute_with_retry(request, url, headers)
            
            # Parse response
            api_response = self._parse_response(response, request_id, start_time)
            
            # Update rate limit info
            self._update_rate_limits(connection_id, response.headers)
            
            # Cache successful GET responses
            if (request.operation == AppFolioOperationType.READ and 
                api_response.success and 
                request.request_type == AppFolioRequestType.SYNC):
                cache_key = self._generate_cache_key(request)
                self._cache_response(cache_key, api_response)
            
            return api_response
            
        except Exception as e:
            logger.error(f"Request execution failed: {str(e)}")
            return AppFolioResponse(
                success=False,
                status_code=500,
                data=None,
                headers={},
                errors=[str(e)],
                request_id=request_id,
                processing_time=time.time() - start_time
            )
    
    @backoff.on_exception(
        backoff.expo,
        (requests.exceptions.RequestException, requests.exceptions.Timeout),
        max_tries=3,
        max_time=60
    )
    def _execute_with_retry(self, request: AppFolioRequest, url: str, headers: Dict[str, str]) -> requests.Response:
        """Execute HTTP request with retry logic"""
        
        if request.operation == AppFolioOperationType.CREATE:
            return self.session.post(
                url, 
                json=request.data, 
                headers=headers, 
                timeout=request.timeout
            )
        elif request.operation == AppFolioOperationType.READ:
            params = {}
            if request.filters:
                params.update(request.filters)
            if request.pagination:
                params.update(request.pagination)
            if request.fields:
                params['fields'] = ','.join(request.fields)
            if request.includes:
                params['include'] = ','.join(request.includes)
            
            return self.session.get(
                url, 
                params=params, 
                headers=headers, 
                timeout=request.timeout
            )
        elif request.operation == AppFolioOperationType.UPDATE:
            return self.session.put(
                url, 
                json=request.data, 
                headers=headers, 
                timeout=request.timeout
            )
        elif request.operation == AppFolioOperationType.DELETE:
            return self.session.delete(
                url, 
                headers=headers, 
                timeout=request.timeout
            )
        elif request.operation == AppFolioOperationType.LIST:
            params = {}
            if request.filters:
                params.update(request.filters)
            if request.pagination:
                params.update(request.pagination)
            
            return self.session.get(
                url, 
                params=params, 
                headers=headers, 
                timeout=request.timeout
            )
        else:
            raise ValueError(f"Unsupported operation: {request.operation}")
    
    def _build_request_url(self, connection: AppFolioConnection, request: AppFolioRequest) -> str:
        """Build request URL"""
        base_url = self.auth_service.api_endpoints[connection.environment]['base_api_url']
        endpoint = self.entity_endpoints[request.entity_type]
        
        if request.entity_id:
            url = f"{base_url}/{endpoint}/{request.entity_id}"
        else:
            url = f"{base_url}/{endpoint}"
        
        return url
    
    def _build_request_headers(self, access_token: str, request_id: str) -> Dict[str, str]:
        """Build request headers"""
        headers = self.session.headers.copy()
        headers['Authorization'] = f'Bearer {access_token}'
        headers['X-Request-ID'] = request_id
        return headers
    
    def _parse_response(self, response: requests.Response, request_id: str, start_time: float) -> AppFolioResponse:
        """Parse HTTP response into AppFolioResponse"""
        processing_time = time.time() - start_time
        
        try:
            if response.headers.get('content-type', '').startswith('application/json'):
                data = response.json()
            else:
                data = response.text
        except json.JSONDecodeError:
            data = response.text
        
        # Extract pagination info if present
        pagination = None
        if isinstance(data, dict) and 'pagination' in data:
            pagination = data['pagination']
        
        # Extract errors and warnings
        errors = []
        warnings = []
        if not response.ok:
            if isinstance(data, dict):
                errors = data.get('errors', [str(data)])
                warnings = data.get('warnings', [])
            else:
                errors = [f"HTTP {response.status_code}: {data}"]
        
        return AppFolioResponse(
            success=response.ok,
            status_code=response.status_code,
            data=data,
            headers=dict(response.headers),
            errors=errors,
            warnings=warnings,
            pagination=pagination,
            request_id=request_id,
            processing_time=processing_time
        )
    
    def _check_rate_limits(self, connection_id: str) -> Dict[str, Any]:
        """Check if request is within rate limits"""
        rate_limit = self.rate_limits.get(connection_id)
        
        if not rate_limit:
            return {'allowed': True}
        
        now = datetime.utcnow()
        if now >= rate_limit.reset_time:
            # Rate limit window has reset
            return {'allowed': True}
        
        if rate_limit.requests_remaining <= 0:
            return {
                'allowed': False,
                'retry_after': (rate_limit.reset_time - now).total_seconds()
            }
        
        return {'allowed': True}
    
    def _update_rate_limits(self, connection_id: str, headers: Dict[str, str]):
        """Update rate limit information from response headers"""
        try:
            if 'X-RateLimit-Remaining' in headers:
                remaining = int(headers['X-RateLimit-Remaining'])
                limit = int(headers.get('X-RateLimit-Limit', 1000))
                reset_time = datetime.utcfromtimestamp(
                    int(headers.get('X-RateLimit-Reset', time.time() + 3600))
                )
                
                self.rate_limits[connection_id] = RateLimitInfo(
                    requests_remaining=remaining,
                    requests_limit=limit,
                    reset_time=reset_time
                )
        except (ValueError, KeyError):
            # Rate limit headers not present or invalid
            pass
    
    def _generate_cache_key(self, request: AppFolioRequest) -> str:
        """Generate cache key for request"""
        key_parts = [
            request.entity_type.value,
            request.operation.value,
            request.entity_id or 'all',
            str(sorted(request.filters.items())) if request.filters else '',
            str(sorted(request.pagination.items())) if request.pagination else '',
            ','.join(sorted(request.fields)) if request.fields else '',
            ','.join(sorted(request.includes)) if request.includes else ''
        ]
        return ':'.join(key_parts)
    
    def _get_cached_response(self, cache_key: str, ttl: int = 300) -> Optional[AppFolioResponse]:
        """Get cached response if still valid"""
        if cache_key in self.request_cache:
            response, timestamp = self.request_cache[cache_key]
            if (datetime.utcnow() - timestamp).total_seconds() < ttl:
                return response
            else:
                del self.request_cache[cache_key]
        return None
    
    def _cache_response(self, cache_key: str, response: AppFolioResponse):
        """Cache successful response"""
        self.request_cache[cache_key] = (response, datetime.utcnow())
        
        # Clean old cache entries (keep last 1000)
        if len(self.request_cache) > 1000:
            oldest_keys = sorted(
                self.request_cache.keys(),
                key=lambda k: self.request_cache[k][1]
            )[:100]
            for key in oldest_keys:
                del self.request_cache[key]
    
    def test_connection(self, connection_id: str) -> Dict[str, Any]:
        """Test connection to AppFolio API"""
        try:
            # Simple API call to test connectivity
            request = AppFolioRequest(
                entity_type=AppFolioEntityType.COMPANIES,
                operation=AppFolioOperationType.READ,
                timeout=10
            )
            
            response = self.execute_request(connection_id, request)
            
            return {
                'success': response.success,
                'status_code': response.status_code,
                'response_time': response.processing_time,
                'rate_limit': response.rate_limit,
                'errors': response.errors
            }
            
        except Exception as e:
            logger.error(f"Connection test failed: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    # Convenience methods for common operations
    
    def get_properties(self, connection_id: str, filters: Dict[str, Any] = None) -> AppFolioResponse:
        """Get properties"""
        request = AppFolioRequest(
            entity_type=AppFolioEntityType.PROPERTIES,
            operation=AppFolioOperationType.LIST,
            filters=filters
        )
        return self.execute_request(connection_id, request)
    
    def get_property(self, connection_id: str, property_id: str) -> AppFolioResponse:
        """Get specific property"""
        request = AppFolioRequest(
            entity_type=AppFolioEntityType.PROPERTIES,
            operation=AppFolioOperationType.READ,
            entity_id=property_id
        )
        return self.execute_request(connection_id, request)
    
    def get_units(self, connection_id: str, property_id: str = None, filters: Dict[str, Any] = None) -> AppFolioResponse:
        """Get units"""
        if filters is None:
            filters = {}
        if property_id:
            filters['property_id'] = property_id
            
        request = AppFolioRequest(
            entity_type=AppFolioEntityType.UNITS,
            operation=AppFolioOperationType.LIST,
            filters=filters
        )
        return self.execute_request(connection_id, request)
    
    def get_tenants(self, connection_id: str, filters: Dict[str, Any] = None) -> AppFolioResponse:
        """Get tenants"""
        request = AppFolioRequest(
            entity_type=AppFolioEntityType.TENANTS,
            operation=AppFolioOperationType.LIST,
            filters=filters
        )
        return self.execute_request(connection_id, request)
    
    def get_leases(self, connection_id: str, filters: Dict[str, Any] = None) -> AppFolioResponse:
        """Get leases"""
        request = AppFolioRequest(
            entity_type=AppFolioEntityType.LEASES,
            operation=AppFolioOperationType.LIST,
            filters=filters
        )
        return self.execute_request(connection_id, request)
    
    def get_payments(self, connection_id: str, filters: Dict[str, Any] = None) -> AppFolioResponse:
        """Get payments"""
        request = AppFolioRequest(
            entity_type=AppFolioEntityType.PAYMENTS,
            operation=AppFolioOperationType.LIST,
            filters=filters
        )
        return self.execute_request(connection_id, request)
    
    def get_work_orders(self, connection_id: str, filters: Dict[str, Any] = None) -> AppFolioResponse:
        """Get work orders"""
        request = AppFolioRequest(
            entity_type=AppFolioEntityType.WORK_ORDERS,
            operation=AppFolioOperationType.LIST,
            filters=filters
        )
        return self.execute_request(connection_id, request)
    
    def get_vendors(self, connection_id: str, filters: Dict[str, Any] = None) -> AppFolioResponse:
        """Get vendors"""
        request = AppFolioRequest(
            entity_type=AppFolioEntityType.VENDORS,
            operation=AppFolioOperationType.LIST,
            filters=filters
        )
        return self.execute_request(connection_id, request)
    
    def create_work_order(self, connection_id: str, work_order_data: Dict[str, Any]) -> AppFolioResponse:
        """Create work order"""
        request = AppFolioRequest(
            entity_type=AppFolioEntityType.WORK_ORDERS,
            operation=AppFolioOperationType.CREATE,
            data=work_order_data
        )
        return self.execute_request(connection_id, request)
    
    def update_work_order(self, connection_id: str, work_order_id: str, update_data: Dict[str, Any]) -> AppFolioResponse:
        """Update work order"""
        request = AppFolioRequest(
            entity_type=AppFolioEntityType.WORK_ORDERS,
            operation=AppFolioOperationType.UPDATE,
            entity_id=work_order_id,
            data=update_data
        )
        return self.execute_request(connection_id, request)
    
    def get_financial_reports(self, connection_id: str, report_type: str, filters: Dict[str, Any] = None) -> AppFolioResponse:
        """Get financial reports"""
        if filters is None:
            filters = {}
        filters['report_type'] = report_type
        
        request = AppFolioRequest(
            entity_type=AppFolioEntityType.FINANCIAL_REPORTS,
            operation=AppFolioOperationType.LIST,
            filters=filters
        )
        return self.execute_request(connection_id, request)
    
    def clear_cache(self):
        """Clear request cache"""
        self.request_cache.clear()
        logger.info("Request cache cleared")
    
    def get_rate_limit_status(self, connection_id: str) -> Optional[Dict[str, Any]]:
        """Get current rate limit status"""
        rate_limit = self.rate_limits.get(connection_id)
        if rate_limit:
            return {
                'requests_remaining': rate_limit.requests_remaining,
                'requests_limit': rate_limit.requests_limit,
                'reset_time': rate_limit.reset_time.isoformat(),
                'seconds_until_reset': (rate_limit.reset_time - datetime.utcnow()).total_seconds()
            }
        return None