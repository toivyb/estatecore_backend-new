"""
Buildium API Client

Comprehensive API client for Buildium property management platform
with rate limiting, error handling, and optimizations for small portfolios.
"""

import os
import logging
import json
import asyncio
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union, Tuple
from dataclasses import dataclass, asdict, field
from enum import Enum
import aiohttp
import backoff
from urllib.parse import urlencode, urljoin

from .buildium_auth_service import BuildiumAuthService, BuildiumConnection
from .models import (
    BuildiumProperty, BuildiumUnit, BuildiumTenant, BuildiumLease,
    BuildiumPayment, BuildiumMaintenanceRequest, BuildiumVendor,
    BuildiumApplication, BuildiumOwner, BuildiumDocument,
    BuildiumFinancialTransaction, PropertyType, UnitType
)

logger = logging.getLogger(__name__)


class BuildiumEntityType(Enum):
    """Buildium entity types for API operations"""
    PROPERTIES = "properties"
    UNITS = "units"
    TENANTS = "tenants"
    LEASES = "leases"
    PAYMENTS = "payments"
    MAINTENANCE = "maintenance"
    VENDORS = "vendors"
    APPLICATIONS = "applications"
    OWNERS = "owners"
    DOCUMENTS = "documents"
    TRANSACTIONS = "transactions"
    ACCOUNTING = "accounting"
    REPORTS = "reports"


class BuildiumOperationType(Enum):
    """API operation types"""
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    PATCH = "PATCH"
    DELETE = "DELETE"


class APIErrorType(Enum):
    """API error categories"""
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    RATE_LIMIT = "rate_limit"
    VALIDATION = "validation"
    NOT_FOUND = "not_found"
    SERVER_ERROR = "server_error"
    NETWORK_ERROR = "network_error"
    TIMEOUT = "timeout"


@dataclass
class BuildiumRequest:
    """Buildium API request configuration"""
    method: BuildiumOperationType
    endpoint: str
    params: Optional[Dict[str, Any]] = None
    data: Optional[Dict[str, Any]] = None
    headers: Optional[Dict[str, str]] = None
    timeout: int = 30
    retry_count: int = 3
    retry_delay: float = 1.0
    small_portfolio_optimized: bool = False


@dataclass
class BuildiumResponse:
    """Buildium API response wrapper"""
    status_code: int
    data: Optional[Any] = None
    headers: Optional[Dict[str, str]] = None
    error: Optional[str] = None
    error_type: Optional[APIErrorType] = None
    rate_limit_info: Optional[Dict[str, Any]] = None
    execution_time: float = 0.0
    request_id: Optional[str] = None


@dataclass
class RateLimitInfo:
    """Rate limiting information"""
    limit: int
    remaining: int
    reset_time: datetime
    retry_after: Optional[int] = None


class BuildiumAPIClient:
    """
    Buildium API Client
    
    Handles all communication with Buildium APIs including:
    - Authentication and authorization
    - Rate limiting and retry logic
    - Request/response handling
    - Error management
    - Small portfolio optimizations
    """
    
    def __init__(self, auth_service: BuildiumAuthService):
        self.auth_service = auth_service
        self.base_url = "https://api.buildium.com"
        self.api_version = "v1"
        
        # Rate limiting
        self.rate_limits: Dict[str, RateLimitInfo] = {}
        self.request_semaphore = asyncio.Semaphore(100)  # Max concurrent requests
        
        # Performance tracking
        self.request_stats = {
            'total_requests': 0,
            'failed_requests': 0,
            'average_response_time': 0.0,
            'rate_limit_hits': 0
        }
        
        # Small portfolio optimizations
        self.small_portfolio_batch_size = 25
        self.standard_batch_size = 100
        
        # Entity endpoint mappings
        self.endpoints = {
            BuildiumEntityType.PROPERTIES: "/properties",
            BuildiumEntityType.UNITS: "/units",
            BuildiumEntityType.TENANTS: "/tenants",
            BuildiumEntityType.LEASES: "/leases",
            BuildiumEntityType.PAYMENTS: "/payments",
            BuildiumEntityType.MAINTENANCE: "/workorders",
            BuildiumEntityType.VENDORS: "/vendors",
            BuildiumEntityType.APPLICATIONS: "/applications",
            BuildiumEntityType.OWNERS: "/owners",
            BuildiumEntityType.DOCUMENTS: "/documents",
            BuildiumEntityType.TRANSACTIONS: "/transactions",
            BuildiumEntityType.ACCOUNTING: "/accounting",
            BuildiumEntityType.REPORTS: "/reports"
        }
    
    async def execute_request(
        self,
        connection_id: str,
        request: BuildiumRequest
    ) -> BuildiumResponse:
        """Execute API request with full error handling and rate limiting"""
        start_time = time.time()
        
        try:
            # Check rate limits
            await self._check_rate_limits(connection_id)
            
            # Get authentication headers
            auth_headers = await self.auth_service.get_auth_header(connection_id)
            if not auth_headers:
                return BuildiumResponse(
                    status_code=401,
                    error="Authentication failed",
                    error_type=APIErrorType.AUTHENTICATION
                )
            
            # Prepare request
            url = self._build_url(request.endpoint)
            headers = {**auth_headers, **(request.headers or {})}
            headers.setdefault('Content-Type', 'application/json')
            headers.setdefault('Accept', 'application/json')
            
            # Execute with semaphore for concurrency control
            async with self.request_semaphore:
                response = await self._execute_with_retry(
                    url, request, headers, start_time
                )
            
            # Update statistics
            self._update_stats(response, time.time() - start_time)
            
            return response
            
        except Exception as e:
            logger.error(f"Request execution failed: {e}")
            return BuildiumResponse(
                status_code=500,
                error=str(e),
                error_type=APIErrorType.NETWORK_ERROR,
                execution_time=time.time() - start_time
            )
    
    @backoff.on_exception(
        backoff.expo,
        (aiohttp.ClientError, asyncio.TimeoutError),
        max_tries=3
    )
    async def _execute_with_retry(
        self,
        url: str,
        request: BuildiumRequest,
        headers: Dict[str, str],
        start_time: float
    ) -> BuildiumResponse:
        """Execute HTTP request with retry logic"""
        timeout = aiohttp.ClientTimeout(total=request.timeout)
        
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.request(
                method=request.method.value,
                url=url,
                params=request.params,
                json=request.data,
                headers=headers
            ) as response:
                
                # Parse rate limit headers
                rate_limit_info = self._parse_rate_limit_headers(response.headers)
                
                # Handle different response codes
                if response.status == 200:
                    data = await response.json()
                    return BuildiumResponse(
                        status_code=response.status,
                        data=data,
                        headers=dict(response.headers),
                        rate_limit_info=rate_limit_info,
                        execution_time=time.time() - start_time,
                        request_id=response.headers.get('X-Request-ID')
                    )
                
                elif response.status == 429:  # Rate limited
                    self.request_stats['rate_limit_hits'] += 1
                    retry_after = int(response.headers.get('Retry-After', 60))
                    await asyncio.sleep(retry_after)
                    
                    return BuildiumResponse(
                        status_code=response.status,
                        error="Rate limit exceeded",
                        error_type=APIErrorType.RATE_LIMIT,
                        rate_limit_info=rate_limit_info,
                        execution_time=time.time() - start_time
                    )
                
                elif response.status in [401, 403]:
                    error_data = await response.json() if response.content_type == 'application/json' else {}
                    return BuildiumResponse(
                        status_code=response.status,
                        error=error_data.get('message', 'Authentication/Authorization failed'),
                        error_type=APIErrorType.AUTHENTICATION if response.status == 401 else APIErrorType.AUTHORIZATION,
                        execution_time=time.time() - start_time
                    )
                
                elif response.status == 404:
                    return BuildiumResponse(
                        status_code=response.status,
                        error="Resource not found",
                        error_type=APIErrorType.NOT_FOUND,
                        execution_time=time.time() - start_time
                    )
                
                elif response.status >= 400:
                    error_data = await response.json() if response.content_type == 'application/json' else {}
                    error_type = APIErrorType.VALIDATION if response.status < 500 else APIErrorType.SERVER_ERROR
                    
                    return BuildiumResponse(
                        status_code=response.status,
                        error=error_data.get('message', f'HTTP {response.status}'),
                        error_type=error_type,
                        execution_time=time.time() - start_time
                    )
                
                else:
                    data = await response.json() if response.content_type == 'application/json' else None
                    return BuildiumResponse(
                        status_code=response.status,
                        data=data,
                        headers=dict(response.headers),
                        rate_limit_info=rate_limit_info,
                        execution_time=time.time() - start_time
                    )
    
    # Entity-specific methods
    
    async def get_properties(
        self,
        connection_id: str,
        property_ids: Optional[List[str]] = None,
        property_types: Optional[List[PropertyType]] = None,
        offset: int = 0,
        limit: int = 100
    ) -> BuildiumResponse:
        """Get properties with optional filtering"""
        params = {
            'offset': offset,
            'limit': limit
        }
        
        if property_ids:
            params['propertyids'] = ','.join(property_ids)
        
        if property_types:
            params['propertytypes'] = ','.join([pt.value for pt in property_types])
        
        request = BuildiumRequest(
            method=BuildiumOperationType.GET,
            endpoint=self.endpoints[BuildiumEntityType.PROPERTIES],
            params=params
        )
        
        return await self.execute_request(connection_id, request)
    
    async def create_property(
        self,
        connection_id: str,
        property_data: BuildiumProperty
    ) -> BuildiumResponse:
        """Create a new property"""
        # Convert property data to Buildium API format
        api_data = self._convert_property_to_api_format(property_data)
        
        request = BuildiumRequest(
            method=BuildiumOperationType.POST,
            endpoint=self.endpoints[BuildiumEntityType.PROPERTIES],
            data=api_data
        )
        
        return await self.execute_request(connection_id, request)
    
    async def update_property(
        self,
        connection_id: str,
        property_id: str,
        property_data: BuildiumProperty
    ) -> BuildiumResponse:
        """Update an existing property"""
        api_data = self._convert_property_to_api_format(property_data)
        
        request = BuildiumRequest(
            method=BuildiumOperationType.PUT,
            endpoint=f"{self.endpoints[BuildiumEntityType.PROPERTIES]}/{property_id}",
            data=api_data
        )
        
        return await self.execute_request(connection_id, request)
    
    async def get_units(
        self,
        connection_id: str,
        property_id: Optional[str] = None,
        unit_types: Optional[List[UnitType]] = None,
        available_only: bool = False,
        offset: int = 0,
        limit: int = 100
    ) -> BuildiumResponse:
        """Get units with optional filtering"""
        params = {
            'offset': offset,
            'limit': limit
        }
        
        if property_id:
            params['propertyid'] = property_id
        
        if unit_types:
            params['unittypes'] = ','.join([ut.value for ut in unit_types])
        
        if available_only:
            params['availableonly'] = 'true'
        
        request = BuildiumRequest(
            method=BuildiumOperationType.GET,
            endpoint=self.endpoints[BuildiumEntityType.UNITS],
            params=params
        )
        
        return await self.execute_request(connection_id, request)
    
    async def get_tenants(
        self,
        connection_id: str,
        property_ids: Optional[List[str]] = None,
        lease_statuses: Optional[List[str]] = None,
        offset: int = 0,
        limit: int = 100
    ) -> BuildiumResponse:
        """Get tenants with optional filtering"""
        params = {
            'offset': offset,
            'limit': limit
        }
        
        if property_ids:
            params['propertyids'] = ','.join(property_ids)
        
        if lease_statuses:
            params['leasestatuses'] = ','.join(lease_statuses)
        
        request = BuildiumRequest(
            method=BuildiumOperationType.GET,
            endpoint=self.endpoints[BuildiumEntityType.TENANTS],
            params=params
        )
        
        return await self.execute_request(connection_id, request)
    
    async def get_payments(
        self,
        connection_id: str,
        tenant_ids: Optional[List[str]] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        payment_statuses: Optional[List[str]] = None,
        offset: int = 0,
        limit: int = 100
    ) -> BuildiumResponse:
        """Get payments with optional filtering"""
        params = {
            'offset': offset,
            'limit': limit
        }
        
        if tenant_ids:
            params['tenantids'] = ','.join(tenant_ids)
        
        if start_date:
            params['startdate'] = start_date.strftime('%Y-%m-%d')
        
        if end_date:
            params['enddate'] = end_date.strftime('%Y-%m-%d')
        
        if payment_statuses:
            params['paymentstatuses'] = ','.join(payment_statuses)
        
        request = BuildiumRequest(
            method=BuildiumOperationType.GET,
            endpoint=self.endpoints[BuildiumEntityType.PAYMENTS],
            params=params
        )
        
        return await self.execute_request(connection_id, request)
    
    async def get_maintenance_requests(
        self,
        connection_id: str,
        property_ids: Optional[List[str]] = None,
        statuses: Optional[List[str]] = None,
        priorities: Optional[List[str]] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        offset: int = 0,
        limit: int = 100
    ) -> BuildiumResponse:
        """Get maintenance requests with optional filtering"""
        params = {
            'offset': offset,
            'limit': limit
        }
        
        if property_ids:
            params['propertyids'] = ','.join(property_ids)
        
        if statuses:
            params['statuses'] = ','.join(statuses)
        
        if priorities:
            params['priorities'] = ','.join(priorities)
        
        if start_date:
            params['startdate'] = start_date.strftime('%Y-%m-%d')
        
        if end_date:
            params['enddate'] = end_date.strftime('%Y-%m-%d')
        
        request = BuildiumRequest(
            method=BuildiumOperationType.GET,
            endpoint=self.endpoints[BuildiumEntityType.MAINTENANCE],
            params=params
        )
        
        return await self.execute_request(connection_id, request)
    
    async def create_maintenance_request(
        self,
        connection_id: str,
        maintenance_data: BuildiumMaintenanceRequest
    ) -> BuildiumResponse:
        """Create a new maintenance request"""
        api_data = self._convert_maintenance_to_api_format(maintenance_data)
        
        request = BuildiumRequest(
            method=BuildiumOperationType.POST,
            endpoint=self.endpoints[BuildiumEntityType.MAINTENANCE],
            data=api_data
        )
        
        return await self.execute_request(connection_id, request)
    
    async def get_applications(
        self,
        connection_id: str,
        property_ids: Optional[List[str]] = None,
        statuses: Optional[List[str]] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        offset: int = 0,
        limit: int = 100
    ) -> BuildiumResponse:
        """Get tenant applications with optional filtering"""
        params = {
            'offset': offset,
            'limit': limit
        }
        
        if property_ids:
            params['propertyids'] = ','.join(property_ids)
        
        if statuses:
            params['statuses'] = ','.join(statuses)
        
        if start_date:
            params['startdate'] = start_date.strftime('%Y-%m-%d')
        
        if end_date:
            params['enddate'] = end_date.strftime('%Y-%m-%d')
        
        request = BuildiumRequest(
            method=BuildiumOperationType.GET,
            endpoint=self.endpoints[BuildiumEntityType.APPLICATIONS],
            params=params
        )
        
        return await self.execute_request(connection_id, request)
    
    async def get_financial_transactions(
        self,
        connection_id: str,
        property_ids: Optional[List[str]] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        transaction_types: Optional[List[str]] = None,
        offset: int = 0,
        limit: int = 100
    ) -> BuildiumResponse:
        """Get financial transactions"""
        params = {
            'offset': offset,
            'limit': limit
        }
        
        if property_ids:
            params['propertyids'] = ','.join(property_ids)
        
        if start_date:
            params['startdate'] = start_date.strftime('%Y-%m-%d')
        
        if end_date:
            params['enddate'] = end_date.strftime('%Y-%m-%d')
        
        if transaction_types:
            params['transactiontypes'] = ','.join(transaction_types)
        
        request = BuildiumRequest(
            method=BuildiumOperationType.GET,
            endpoint=self.endpoints[BuildiumEntityType.TRANSACTIONS],
            params=params
        )
        
        return await self.execute_request(connection_id, request)
    
    # Small portfolio optimized methods
    
    async def get_small_portfolio_summary(
        self,
        connection_id: str
    ) -> BuildiumResponse:
        """Get optimized summary for small portfolios"""
        # Get basic property count first
        properties_response = await self.get_properties(
            connection_id, 
            limit=self.small_portfolio_batch_size
        )
        
        if properties_response.status_code != 200:
            return properties_response
        
        properties = properties_response.data.get('data', [])
        property_ids = [p['Id'] for p in properties]
        
        # Batch requests for small portfolio efficiency
        summary_data = {
            'properties': properties,
            'total_properties': len(properties),
            'units': [],
            'active_tenants': 0,
            'recent_payments': [],
            'pending_maintenance': []
        }
        
        # Get units for all properties
        if property_ids:
            units_response = await self.get_units(
                connection_id,
                limit=self.small_portfolio_batch_size * 5
            )
            if units_response.status_code == 200:
                summary_data['units'] = units_response.data.get('data', [])
        
        return BuildiumResponse(
            status_code=200,
            data=summary_data,
            execution_time=0.0
        )
    
    # Helper methods
    
    def _build_url(self, endpoint: str) -> str:
        """Build full API URL"""
        return urljoin(f"{self.base_url}/{self.api_version}", endpoint.lstrip('/'))
    
    def _parse_rate_limit_headers(self, headers: Dict[str, str]) -> Dict[str, Any]:
        """Parse rate limit information from response headers"""
        return {
            'limit': headers.get('X-RateLimit-Limit'),
            'remaining': headers.get('X-RateLimit-Remaining'),
            'reset': headers.get('X-RateLimit-Reset'),
            'retry_after': headers.get('Retry-After')
        }
    
    async def _check_rate_limits(self, connection_id: str) -> None:
        """Check and enforce rate limits"""
        rate_limit = self.rate_limits.get(connection_id)
        if not rate_limit:
            return
        
        if rate_limit.remaining <= 0:
            wait_time = (rate_limit.reset_time - datetime.utcnow()).total_seconds()
            if wait_time > 0:
                logger.warning(f"Rate limit exceeded, waiting {wait_time} seconds")
                await asyncio.sleep(wait_time)
    
    def _update_stats(self, response: BuildiumResponse, execution_time: float) -> None:
        """Update request statistics"""
        self.request_stats['total_requests'] += 1
        
        if response.status_code >= 400:
            self.request_stats['failed_requests'] += 1
        
        # Update average response time
        total_requests = self.request_stats['total_requests']
        current_avg = self.request_stats['average_response_time']
        self.request_stats['average_response_time'] = (
            (current_avg * (total_requests - 1) + execution_time) / total_requests
        )
    
    def _convert_property_to_api_format(self, property_data: BuildiumProperty) -> Dict[str, Any]:
        """Convert property data to Buildium API format"""
        return {
            'Name': property_data.name,
            'PropertyType': property_data.property_type.value,
            'Address': property_data.address,
            'UnitCount': property_data.unit_count,
            'YearBuilt': property_data.year_built,
            'SquareFootage': property_data.square_footage,
            'LotSize': property_data.lot_size,
            'Amenities': property_data.amenities,
            'ParkingSpaces': property_data.parking_spaces,
            'Notes': property_data.notes
        }
    
    def _convert_maintenance_to_api_format(self, maintenance_data: BuildiumMaintenanceRequest) -> Dict[str, Any]:
        """Convert maintenance request data to Buildium API format"""
        return {
            'PropertyId': maintenance_data.property_id,
            'UnitId': maintenance_data.unit_id,
            'TenantId': maintenance_data.tenant_id,
            'Title': maintenance_data.title,
            'Description': maintenance_data.description,
            'Priority': maintenance_data.priority.value,
            'Category': maintenance_data.category,
            'RequestedDate': maintenance_data.requested_date.isoformat(),
            'PermissionToEnter': maintenance_data.permission_to_enter,
            'TenantCaused': maintenance_data.tenant_caused
        }
    
    def get_stats(self) -> Dict[str, Any]:
        """Get API client statistics"""
        return self.request_stats.copy()