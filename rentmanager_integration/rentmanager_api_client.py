"""
RentManager API Client

Comprehensive API client for RentManager integration with support for all property types,
compliance requirements, multi-family management, commercial properties, and specialized features.
"""

import os
import logging
import json
import uuid
import asyncio
import aiohttp
import requests
from datetime import datetime, date, timedelta
from typing import Dict, List, Optional, Any, Union, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import time
from urllib.parse import urljoin, urlencode

from .rentmanager_auth_service import RentManagerAuthService, RentManagerCredentials, AuthenticationType
from .models import (
    RentManagerProperty, RentManagerUnit, RentManagerResident, RentManagerLease,
    RentManagerPayment, RentManagerWorkOrder, RentManagerVendor, RentManagerAccount,
    PropertyType, UnitType, ComplianceType, ResidentStatus, WorkOrderStatus, PaymentStatus
)

logger = logging.getLogger(__name__)

class RentManagerEntityType(Enum):
    """RentManager entity types for API operations"""
    PROPERTIES = "properties"
    UNITS = "units"
    RESIDENTS = "residents"
    LEASES = "leases"
    PAYMENTS = "payments"
    WORK_ORDERS = "work_orders"
    VENDORS = "vendors"
    ACCOUNTS = "accounts"
    TRANSACTIONS = "transactions"
    DOCUMENTS = "documents"
    MESSAGES = "messages"
    COMPLIANCE = "compliance"
    PORTFOLIOS = "portfolios"
    APPLICATIONS = "applications"
    INSPECTIONS = "inspections"
    CHARGES = "charges"
    CONCESSIONS = "concessions"
    REPORTS = "reports"

class APIOperationType(Enum):
    """API operation types"""
    READ = "read"
    WRITE = "write"
    DELETE = "delete"
    SEARCH = "search"
    BULK = "bulk"
    SYNC = "sync"

@dataclass
class APIRequest:
    """API request configuration"""
    method: str
    endpoint: str
    params: Optional[Dict[str, Any]] = None
    data: Optional[Dict[str, Any]] = None
    headers: Optional[Dict[str, str]] = None
    timeout: int = 30
    retry_count: int = 3
    operation_type: Optional[APIOperationType] = None

@dataclass
class APIResponse:
    """API response wrapper"""
    success: bool
    status_code: int
    data: Optional[Any] = None
    error: Optional[str] = None
    headers: Optional[Dict[str, str]] = None
    request_id: Optional[str] = None
    rate_limit_remaining: Optional[int] = None
    rate_limit_reset: Optional[datetime] = None

class RentManagerAPIClient:
    """
    RentManager API Client
    
    Comprehensive API client for all RentManager operations including property management,
    compliance tracking, multi-family management, commercial properties, and specialized housing.
    """
    
    def __init__(self, auth_service: RentManagerAuthService):
        self.auth_service = auth_service
        
        # API configuration
        self.api_version = "v1"
        self.default_timeout = 30
        self.max_retries = 3
        self.retry_delay = 1  # seconds
        
        # Rate limiting
        self.rate_limit_enabled = True
        self.rate_limit_per_minute = 100
        self.rate_limit_per_hour = 5000
        self.request_counts = {}
        
        # Endpoint mappings
        self.endpoints = {
            # Property management
            RentManagerEntityType.PROPERTIES: "/properties",
            RentManagerEntityType.UNITS: "/units", 
            RentManagerEntityType.RESIDENTS: "/residents",
            RentManagerEntityType.LEASES: "/leases",
            RentManagerEntityType.PAYMENTS: "/payments",
            RentManagerEntityType.WORK_ORDERS: "/work-orders",
            RentManagerEntityType.VENDORS: "/vendors",
            RentManagerEntityType.ACCOUNTS: "/accounts",
            RentManagerEntityType.TRANSACTIONS: "/transactions",
            RentManagerEntityType.DOCUMENTS: "/documents",
            RentManagerEntityType.MESSAGES: "/messages",
            
            # Specialized modules
            RentManagerEntityType.COMPLIANCE: "/compliance",
            RentManagerEntityType.PORTFOLIOS: "/portfolios",
            RentManagerEntityType.APPLICATIONS: "/applications",
            RentManagerEntityType.INSPECTIONS: "/inspections",
            RentManagerEntityType.CHARGES: "/charges",
            RentManagerEntityType.CONCESSIONS: "/concessions",
            RentManagerEntityType.REPORTS: "/reports"
        }
        
        # Compliance endpoints
        self.compliance_endpoints = {
            "income_certifications": "/compliance/income-certifications",
            "recertifications": "/compliance/recertifications",
            "monitoring": "/compliance/monitoring",
            "violations": "/compliance/violations",
            "audits": "/compliance/audits",
            "affordable_housing": "/compliance/affordable-housing",
            "lihtc": "/compliance/lihtc",
            "section8": "/compliance/section8",
            "hud": "/compliance/hud"
        }
        
        # Specialized endpoints
        self.specialized_endpoints = {
            "student_housing": "/student-housing",
            "roommate_matching": "/student-housing/roommate-matching",
            "academic_calendar": "/student-housing/academic-calendar",
            "commercial_leases": "/commercial/leases",
            "cam_charges": "/commercial/cam-charges",
            "percentage_rent": "/commercial/percentage-rent",
            "hoa_management": "/hoa",
            "hoa_assessments": "/hoa/assessments",
            "hoa_violations": "/hoa/violations",
            "board_management": "/hoa/board"
        }
        
        logger.info("RentManager API Client initialized")
    
    # ===================================================
    # CORE API METHODS
    # ===================================================
    
    async def make_request(self, organization_id: str, request: APIRequest) -> APIResponse:
        """
        Make authenticated API request to RentManager
        
        Args:
            organization_id: Organization identifier
            request: API request configuration
            
        Returns:
            APIResponse object
        """
        try:
            # Get valid credentials
            credentials = self.auth_service.get_valid_credentials(organization_id)
            if not credentials:
                return APIResponse(
                    success=False,
                    status_code=401,
                    error="No valid credentials available"
                )
            
            # Check rate limits
            if self.rate_limit_enabled and not self._check_rate_limit(organization_id):
                return APIResponse(
                    success=False,
                    status_code=429,
                    error="Rate limit exceeded"
                )
            
            # Build full URL
            full_url = urljoin(credentials.base_url, f"/api/{self.api_version}{request.endpoint}")
            
            # Prepare headers
            headers = self._build_headers(credentials, request.headers)
            
            # Make request with retries
            for attempt in range(request.retry_count + 1):
                try:
                    async with aiohttp.ClientSession() as session:
                        async with session.request(
                            method=request.method,
                            url=full_url,
                            params=request.params,
                            json=request.data,
                            headers=headers,
                            timeout=aiohttp.ClientTimeout(total=request.timeout)
                        ) as response:
                            # Track rate limit
                            self._track_request(organization_id)
                            
                            # Parse response
                            response_data = None
                            if response.content_type == 'application/json':
                                response_data = await response.json()
                            else:
                                response_data = await response.text()
                            
                            # Extract rate limit headers
                            rate_limit_remaining = response.headers.get('X-RateLimit-Remaining')
                            rate_limit_reset = response.headers.get('X-RateLimit-Reset')
                            
                            if response.status >= 200 and response.status < 300:
                                return APIResponse(
                                    success=True,
                                    status_code=response.status,
                                    data=response_data,
                                    headers=dict(response.headers),
                                    request_id=response.headers.get('X-Request-ID'),
                                    rate_limit_remaining=int(rate_limit_remaining) if rate_limit_remaining else None,
                                    rate_limit_reset=datetime.fromtimestamp(int(rate_limit_reset)) if rate_limit_reset else None
                                )
                            else:
                                error_message = self._extract_error_message(response_data)
                                
                                # Handle specific error codes
                                if response.status == 401:
                                    # Try to refresh token and retry
                                    if credentials.auth_type == AuthenticationType.OAUTH2:
                                        if self.auth_service.refresh_access_token(organization_id):
                                            continue  # Retry with new token
                                
                                return APIResponse(
                                    success=False,
                                    status_code=response.status,
                                    error=error_message,
                                    data=response_data,
                                    headers=dict(response.headers),
                                    request_id=response.headers.get('X-Request-ID')
                                )
                
                except asyncio.TimeoutError:
                    if attempt < request.retry_count:
                        await asyncio.sleep(self.retry_delay * (attempt + 1))
                        continue
                    return APIResponse(
                        success=False,
                        status_code=408,
                        error="Request timeout"
                    )
                
                except Exception as e:
                    if attempt < request.retry_count:
                        await asyncio.sleep(self.retry_delay * (attempt + 1))
                        continue
                    return APIResponse(
                        success=False,
                        status_code=500,
                        error=f"Request failed: {str(e)}"
                    )
            
            return APIResponse(
                success=False,
                status_code=500,
                error="Max retries exceeded"
            )
            
        except Exception as e:
            logger.error(f"API request failed: {e}")
            return APIResponse(
                success=False,
                status_code=500,
                error=str(e)
            )
    
    def test_connection(self, connection_id: str) -> Dict[str, Any]:
        """
        Test RentManager API connection
        
        Args:
            connection_id: Connection identifier
            
        Returns:
            Dict with test results
        """
        try:
            # Find organization for connection
            connection = self.auth_service.get_connection_by_id(connection_id)
            if not connection:
                return {
                    "success": False,
                    "error": "Connection not found"
                }
            
            organization_id = connection.organization_id
            
            # Make a simple API call to test connection
            request = APIRequest(
                method="GET",
                endpoint="/system/status",
                timeout=10
            )
            
            # Run async request synchronously
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                response = loop.run_until_complete(
                    self.make_request(organization_id, request)
                )
            finally:
                loop.close()
            
            if response.success:
                return {
                    "success": True,
                    "status": "connected",
                    "response_time": response.headers.get('X-Response-Time'),
                    "server_version": response.data.get('version') if response.data else None,
                    "capabilities": response.data.get('capabilities', []) if response.data else []
                }
            else:
                return {
                    "success": False,
                    "status": "error",
                    "error": response.error,
                    "status_code": response.status_code
                }
                
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return {
                "success": False,
                "status": "error",
                "error": str(e)
            }
    
    # ===================================================
    # PROPERTY MANAGEMENT API
    # ===================================================
    
    async def get_properties(self, organization_id: str, 
                           filters: Optional[Dict[str, Any]] = None,
                           limit: int = 100, offset: int = 0) -> APIResponse:
        """Get properties from RentManager"""
        params = {"limit": limit, "offset": offset}
        if filters:
            params.update(filters)
        
        request = APIRequest(
            method="GET",
            endpoint=self.endpoints[RentManagerEntityType.PROPERTIES],
            params=params,
            operation_type=APIOperationType.READ
        )
        
        return await self.make_request(organization_id, request)
    
    async def create_property(self, organization_id: str, 
                            property_data: Dict[str, Any]) -> APIResponse:
        """Create new property in RentManager"""
        request = APIRequest(
            method="POST",
            endpoint=self.endpoints[RentManagerEntityType.PROPERTIES],
            data=property_data,
            operation_type=APIOperationType.WRITE
        )
        
        return await self.make_request(organization_id, request)
    
    async def update_property(self, organization_id: str, property_id: str,
                            property_data: Dict[str, Any]) -> APIResponse:
        """Update property in RentManager"""
        request = APIRequest(
            method="PUT",
            endpoint=f"{self.endpoints[RentManagerEntityType.PROPERTIES]}/{property_id}",
            data=property_data,
            operation_type=APIOperationType.WRITE
        )
        
        return await self.make_request(organization_id, request)
    
    async def get_units(self, organization_id: str, property_id: Optional[str] = None,
                       filters: Optional[Dict[str, Any]] = None,
                       limit: int = 100, offset: int = 0) -> APIResponse:
        """Get units from RentManager"""
        params = {"limit": limit, "offset": offset}
        if property_id:
            params["property_id"] = property_id
        if filters:
            params.update(filters)
        
        request = APIRequest(
            method="GET",
            endpoint=self.endpoints[RentManagerEntityType.UNITS],
            params=params,
            operation_type=APIOperationType.READ
        )
        
        return await self.make_request(organization_id, request)
    
    async def get_residents(self, organization_id: str, 
                          filters: Optional[Dict[str, Any]] = None,
                          limit: int = 100, offset: int = 0) -> APIResponse:
        """Get residents from RentManager"""
        params = {"limit": limit, "offset": offset}
        if filters:
            params.update(filters)
        
        request = APIRequest(
            method="GET",
            endpoint=self.endpoints[RentManagerEntityType.RESIDENTS],
            params=params,
            operation_type=APIOperationType.READ
        )
        
        return await self.make_request(organization_id, request)
    
    async def create_resident(self, organization_id: str,
                            resident_data: Dict[str, Any]) -> APIResponse:
        """Create new resident in RentManager"""
        request = APIRequest(
            method="POST",
            endpoint=self.endpoints[RentManagerEntityType.RESIDENTS],
            data=resident_data,
            operation_type=APIOperationType.WRITE
        )
        
        return await self.make_request(organization_id, request)
    
    async def get_leases(self, organization_id: str,
                        filters: Optional[Dict[str, Any]] = None,
                        limit: int = 100, offset: int = 0) -> APIResponse:
        """Get leases from RentManager"""
        params = {"limit": limit, "offset": offset}
        if filters:
            params.update(filters)
        
        request = APIRequest(
            method="GET",
            endpoint=self.endpoints[RentManagerEntityType.LEASES],
            params=params,
            operation_type=APIOperationType.READ
        )
        
        return await self.make_request(organization_id, request)
    
    async def create_lease(self, organization_id: str,
                         lease_data: Dict[str, Any]) -> APIResponse:
        """Create new lease in RentManager"""
        request = APIRequest(
            method="POST",
            endpoint=self.endpoints[RentManagerEntityType.LEASES],
            data=lease_data,
            operation_type=APIOperationType.WRITE
        )
        
        return await self.make_request(organization_id, request)
    
    # ===================================================
    # FINANCIAL MANAGEMENT API
    # ===================================================
    
    async def get_payments(self, organization_id: str,
                         filters: Optional[Dict[str, Any]] = None,
                         limit: int = 100, offset: int = 0) -> APIResponse:
        """Get payments from RentManager"""
        params = {"limit": limit, "offset": offset}
        if filters:
            params.update(filters)
        
        request = APIRequest(
            method="GET",
            endpoint=self.endpoints[RentManagerEntityType.PAYMENTS],
            params=params,
            operation_type=APIOperationType.READ
        )
        
        return await self.make_request(organization_id, request)
    
    async def record_payment(self, organization_id: str,
                           payment_data: Dict[str, Any]) -> APIResponse:
        """Record new payment in RentManager"""
        request = APIRequest(
            method="POST",
            endpoint=self.endpoints[RentManagerEntityType.PAYMENTS],
            data=payment_data,
            operation_type=APIOperationType.WRITE
        )
        
        return await self.make_request(organization_id, request)
    
    async def get_accounts(self, organization_id: str,
                         account_type: Optional[str] = None) -> APIResponse:
        """Get chart of accounts from RentManager"""
        params = {}
        if account_type:
            params["type"] = account_type
        
        request = APIRequest(
            method="GET",
            endpoint=self.endpoints[RentManagerEntityType.ACCOUNTS],
            params=params,
            operation_type=APIOperationType.READ
        )
        
        return await self.make_request(organization_id, request)
    
    async def get_transactions(self, organization_id: str,
                             filters: Optional[Dict[str, Any]] = None,
                             limit: int = 100, offset: int = 0) -> APIResponse:
        """Get financial transactions from RentManager"""
        params = {"limit": limit, "offset": offset}
        if filters:
            params.update(filters)
        
        request = APIRequest(
            method="GET",
            endpoint=self.endpoints[RentManagerEntityType.TRANSACTIONS],
            params=params,
            operation_type=APIOperationType.READ
        )
        
        return await self.make_request(organization_id, request)
    
    # ===================================================
    # MAINTENANCE MANAGEMENT API
    # ===================================================
    
    async def get_work_orders(self, organization_id: str,
                            filters: Optional[Dict[str, Any]] = None,
                            limit: int = 100, offset: int = 0) -> APIResponse:
        """Get work orders from RentManager"""
        params = {"limit": limit, "offset": offset}
        if filters:
            params.update(filters)
        
        request = APIRequest(
            method="GET",
            endpoint=self.endpoints[RentManagerEntityType.WORK_ORDERS],
            params=params,
            operation_type=APIOperationType.READ
        )
        
        return await self.make_request(organization_id, request)
    
    async def create_work_order(self, organization_id: str,
                              work_order_data: Dict[str, Any]) -> APIResponse:
        """Create new work order in RentManager"""
        request = APIRequest(
            method="POST",
            endpoint=self.endpoints[RentManagerEntityType.WORK_ORDERS],
            data=work_order_data,
            operation_type=APIOperationType.WRITE
        )
        
        return await self.make_request(organization_id, request)
    
    async def update_work_order(self, organization_id: str, work_order_id: str,
                              work_order_data: Dict[str, Any]) -> APIResponse:
        """Update work order in RentManager"""
        request = APIRequest(
            method="PUT",
            endpoint=f"{self.endpoints[RentManagerEntityType.WORK_ORDERS]}/{work_order_id}",
            data=work_order_data,
            operation_type=APIOperationType.WRITE
        )
        
        return await self.make_request(organization_id, request)
    
    async def get_vendors(self, organization_id: str,
                        vendor_type: Optional[str] = None) -> APIResponse:
        """Get vendors from RentManager"""
        params = {}
        if vendor_type:
            params["type"] = vendor_type
        
        request = APIRequest(
            method="GET",
            endpoint=self.endpoints[RentManagerEntityType.VENDORS],
            params=params,
            operation_type=APIOperationType.READ
        )
        
        return await self.make_request(organization_id, request)
    
    # ===================================================
    # COMPLIANCE MANAGEMENT API
    # ===================================================
    
    async def get_income_certifications(self, organization_id: str,
                                      property_id: Optional[str] = None,
                                      resident_id: Optional[str] = None) -> APIResponse:
        """Get income certifications for affordable housing compliance"""
        params = {}
        if property_id:
            params["property_id"] = property_id
        if resident_id:
            params["resident_id"] = resident_id
        
        request = APIRequest(
            method="GET",
            endpoint=self.compliance_endpoints["income_certifications"],
            params=params,
            operation_type=APIOperationType.READ
        )
        
        return await self.make_request(organization_id, request)
    
    async def create_income_certification(self, organization_id: str,
                                        certification_data: Dict[str, Any]) -> APIResponse:
        """Create new income certification"""
        request = APIRequest(
            method="POST",
            endpoint=self.compliance_endpoints["income_certifications"],
            data=certification_data,
            operation_type=APIOperationType.WRITE
        )
        
        return await self.make_request(organization_id, request)
    
    async def get_compliance_monitoring(self, organization_id: str,
                                      program_type: Optional[str] = None) -> APIResponse:
        """Get compliance monitoring data"""
        params = {}
        if program_type:
            params["program_type"] = program_type
        
        request = APIRequest(
            method="GET",
            endpoint=self.compliance_endpoints["monitoring"],
            params=params,
            operation_type=APIOperationType.READ
        )
        
        return await self.make_request(organization_id, request)
    
    async def get_compliance_violations(self, organization_id: str,
                                      property_id: Optional[str] = None) -> APIResponse:
        """Get compliance violations"""
        params = {}
        if property_id:
            params["property_id"] = property_id
        
        request = APIRequest(
            method="GET",
            endpoint=self.compliance_endpoints["violations"],
            params=params,
            operation_type=APIOperationType.READ
        )
        
        return await self.make_request(organization_id, request)
    
    # ===================================================
    # STUDENT HOUSING API
    # ===================================================
    
    async def get_student_applications(self, organization_id: str,
                                     property_id: Optional[str] = None) -> APIResponse:
        """Get student housing applications"""
        params = {}
        if property_id:
            params["property_id"] = property_id
        
        request = APIRequest(
            method="GET",
            endpoint=f"{self.specialized_endpoints['student_housing']}/applications",
            params=params,
            operation_type=APIOperationType.READ
        )
        
        return await self.make_request(organization_id, request)
    
    async def get_roommate_matches(self, organization_id: str,
                                 student_id: str) -> APIResponse:
        """Get roommate matching suggestions"""
        request = APIRequest(
            method="GET",
            endpoint=f"{self.specialized_endpoints['roommate_matching']}/{student_id}",
            operation_type=APIOperationType.READ
        )
        
        return await self.make_request(organization_id, request)
    
    # ===================================================
    # COMMERCIAL MANAGEMENT API
    # ===================================================
    
    async def get_commercial_leases(self, organization_id: str,
                                  property_id: Optional[str] = None) -> APIResponse:
        """Get commercial leases"""
        params = {}
        if property_id:
            params["property_id"] = property_id
        
        request = APIRequest(
            method="GET",
            endpoint=self.specialized_endpoints["commercial_leases"],
            params=params,
            operation_type=APIOperationType.READ
        )
        
        return await self.make_request(organization_id, request)
    
    async def get_cam_charges(self, organization_id: str,
                            property_id: str, year: int) -> APIResponse:
        """Get Common Area Maintenance charges"""
        params = {"property_id": property_id, "year": year}
        
        request = APIRequest(
            method="GET",
            endpoint=self.specialized_endpoints["cam_charges"],
            params=params,
            operation_type=APIOperationType.READ
        )
        
        return await self.make_request(organization_id, request)
    
    async def calculate_percentage_rent(self, organization_id: str,
                                      lease_id: str, sales_data: Dict[str, Any]) -> APIResponse:
        """Calculate percentage rent for commercial leases"""
        request = APIRequest(
            method="POST",
            endpoint=f"{self.specialized_endpoints['percentage_rent']}/{lease_id}/calculate",
            data=sales_data,
            operation_type=APIOperationType.WRITE
        )
        
        return await self.make_request(organization_id, request)
    
    # ===================================================
    # HOA MANAGEMENT API
    # ===================================================
    
    async def get_hoa_assessments(self, organization_id: str,
                                property_id: str) -> APIResponse:
        """Get HOA assessments"""
        params = {"property_id": property_id}
        
        request = APIRequest(
            method="GET",
            endpoint=self.specialized_endpoints["hoa_assessments"],
            params=params,
            operation_type=APIOperationType.READ
        )
        
        return await self.make_request(organization_id, request)
    
    async def get_hoa_violations(self, organization_id: str,
                               property_id: str) -> APIResponse:
        """Get HOA violations"""
        params = {"property_id": property_id}
        
        request = APIRequest(
            method="GET",
            endpoint=self.specialized_endpoints["hoa_violations"],
            params=params,
            operation_type=APIOperationType.READ
        )
        
        return await self.make_request(organization_id, request)
    
    async def get_board_information(self, organization_id: str,
                                  property_id: str) -> APIResponse:
        """Get HOA board information"""
        params = {"property_id": property_id}
        
        request = APIRequest(
            method="GET",
            endpoint=self.specialized_endpoints["board_management"],
            params=params,
            operation_type=APIOperationType.READ
        )
        
        return await self.make_request(organization_id, request)
    
    # ===================================================
    # BULK OPERATIONS API
    # ===================================================
    
    async def bulk_create(self, organization_id: str, entity_type: RentManagerEntityType,
                        entities: List[Dict[str, Any]]) -> APIResponse:
        """Bulk create entities"""
        request = APIRequest(
            method="POST",
            endpoint=f"{self.endpoints[entity_type]}/bulk",
            data={"entities": entities},
            operation_type=APIOperationType.BULK,
            timeout=120  # Longer timeout for bulk operations
        )
        
        return await self.make_request(organization_id, request)
    
    async def bulk_update(self, organization_id: str, entity_type: RentManagerEntityType,
                        updates: List[Dict[str, Any]]) -> APIResponse:
        """Bulk update entities"""
        request = APIRequest(
            method="PUT",
            endpoint=f"{self.endpoints[entity_type]}/bulk",
            data={"updates": updates},
            operation_type=APIOperationType.BULK,
            timeout=120
        )
        
        return await self.make_request(organization_id, request)
    
    # ===================================================
    # UTILITY METHODS
    # ===================================================
    
    def _build_headers(self, credentials: RentManagerCredentials, 
                      custom_headers: Optional[Dict[str, str]] = None) -> Dict[str, str]:
        """Build request headers with authentication"""
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "EstateCore-RentManager-Integration/1.0"
        }
        
        # Add authentication headers
        if credentials.auth_type == AuthenticationType.OAUTH2:
            headers["Authorization"] = f"Bearer {credentials.access_token}"
        elif credentials.auth_type == AuthenticationType.API_KEY:
            headers["X-API-Key"] = credentials.api_key
            if credentials.api_secret:
                headers["X-API-Secret"] = credentials.api_secret
        elif credentials.auth_type == AuthenticationType.JWT_TOKEN:
            headers["Authorization"] = f"Bearer {credentials.jwt_token}"
        elif credentials.auth_type == AuthenticationType.BASIC_AUTH:
            import base64
            auth_string = f"{credentials.username}:{credentials.password}"
            encoded_auth = base64.b64encode(auth_string.encode()).decode()
            headers["Authorization"] = f"Basic {encoded_auth}"
        
        # Add custom headers
        if custom_headers:
            headers.update(custom_headers)
        
        return headers
    
    def _check_rate_limit(self, organization_id: str) -> bool:
        """Check if request is within rate limits"""
        if not self.rate_limit_enabled:
            return True
        
        current_time = time.time()
        minute_window = int(current_time // 60)
        hour_window = int(current_time // 3600)
        
        if organization_id not in self.request_counts:
            self.request_counts[organization_id] = {}
        
        org_counts = self.request_counts[organization_id]
        
        # Check minute rate limit
        minute_count = org_counts.get(f"minute_{minute_window}", 0)
        if minute_count >= self.rate_limit_per_minute:
            return False
        
        # Check hour rate limit
        hour_count = org_counts.get(f"hour_{hour_window}", 0)
        if hour_count >= self.rate_limit_per_hour:
            return False
        
        return True
    
    def _track_request(self, organization_id: str):
        """Track request for rate limiting"""
        if not self.rate_limit_enabled:
            return
        
        current_time = time.time()
        minute_window = int(current_time // 60)
        hour_window = int(current_time // 3600)
        
        if organization_id not in self.request_counts:
            self.request_counts[organization_id] = {}
        
        org_counts = self.request_counts[organization_id]
        
        # Increment counters
        minute_key = f"minute_{minute_window}"
        hour_key = f"hour_{hour_window}"
        
        org_counts[minute_key] = org_counts.get(minute_key, 0) + 1
        org_counts[hour_key] = org_counts.get(hour_key, 0) + 1
        
        # Clean up old counters
        keys_to_remove = [
            k for k in org_counts.keys() 
            if (k.startswith("minute_") and int(k.split("_")[1]) < minute_window - 1) or
               (k.startswith("hour_") and int(k.split("_")[1]) < hour_window - 1)
        ]
        for key in keys_to_remove:
            del org_counts[key]
    
    def _extract_error_message(self, response_data: Any) -> str:
        """Extract error message from API response"""
        if isinstance(response_data, dict):
            if "error" in response_data:
                return response_data["error"]
            elif "message" in response_data:
                return response_data["message"]
            elif "errors" in response_data:
                if isinstance(response_data["errors"], list):
                    return "; ".join(response_data["errors"])
                else:
                    return str(response_data["errors"])
        
        return str(response_data) if response_data else "Unknown error"

# Global client instance
_api_client = None

def get_rentmanager_api_client(auth_service: RentManagerAuthService = None) -> RentManagerAPIClient:
    """Get singleton API client instance"""
    global _api_client
    if _api_client is None:
        if auth_service is None:
            from .rentmanager_auth_service import get_rentmanager_auth_service
            auth_service = get_rentmanager_auth_service()
        _api_client = RentManagerAPIClient(auth_service)
    return _api_client