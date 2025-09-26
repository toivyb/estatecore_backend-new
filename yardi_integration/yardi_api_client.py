"""
Yardi API Client

Comprehensive API client for interacting with various Yardi products including
Yardi Voyager, Yardi Breeze, Genesis2, and other Yardi systems.
"""

import os
import logging
import json
import time
import hashlib
import hmac
import base64
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union, Tuple
from dataclasses import dataclass, field
from enum import Enum
import asyncio
import aiohttp
import requests
from urllib.parse import urljoin, urlencode
import xml.etree.ElementTree as ET
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from .models import YardiProductType, YardiConnectionType, YardiAuthMethod

logger = logging.getLogger(__name__)

class YardiEntityType(Enum):
    """Supported Yardi entity types"""
    # Property Management
    PROPERTIES = "properties"
    BUILDINGS = "buildings"
    UNITS = "units"
    UNIT_TYPES = "unit_types"
    AMENITIES = "amenities"
    
    # Resident/Tenant Management
    RESIDENTS = "residents"
    TENANTS = "tenants"
    PROSPECTS = "prospects"
    APPLICATIONS = "applications"
    GUARANTORS = "guarantors"
    
    # Lease Management
    LEASES = "leases"
    LEASE_TERMS = "lease_terms"
    RENT_SCHEDULES = "rent_schedules"
    DEPOSITS = "deposits"
    RENEWALS = "renewals"
    
    # Financial Management
    RENT_ROLLS = "rent_rolls"
    PAYMENTS = "payments"
    CHARGES = "charges"
    CREDITS = "credits"
    LATE_FEES = "late_fees"
    INVOICES = "invoices"
    
    # Maintenance Management
    WORK_ORDERS = "work_orders"
    MAINTENANCE_REQUESTS = "maintenance_requests"
    VENDORS = "vendors"
    INVENTORY = "inventory"
    INSPECTIONS = "inspections"
    
    # Accounting
    CHART_OF_ACCOUNTS = "chart_of_accounts"
    GENERAL_LEDGER = "general_ledger"
    BUDGETS = "budgets"
    FINANCIAL_REPORTS = "financial_reports"
    
    # Utilities
    UTILITY_BILLS = "utility_bills"
    UTILITY_READINGS = "utility_readings"
    UTILITY_ALLOCATIONS = "utility_allocations"

class YardiOperationType(Enum):
    """Yardi API operation types"""
    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    SEARCH = "search"
    BULK_CREATE = "bulk_create"
    BULK_UPDATE = "bulk_update"
    BULK_DELETE = "bulk_delete"

class YardiResponseFormat(Enum):
    """Response format types"""
    JSON = "json"
    XML = "xml"
    CSV = "csv"

@dataclass
class YardiAPIRequest:
    """Yardi API request configuration"""
    endpoint: str
    method: str
    entity_type: YardiEntityType
    operation: YardiOperationType
    parameters: Dict[str, Any] = field(default_factory=dict)
    headers: Dict[str, str] = field(default_factory=dict)
    body: Optional[Dict[str, Any]] = None
    timeout: int = 30
    retries: int = 3
    response_format: YardiResponseFormat = YardiResponseFormat.JSON

@dataclass
class YardiAPIResponse:
    """Yardi API response wrapper"""
    success: bool
    status_code: int
    data: Any
    headers: Dict[str, str]
    response_time: float
    error_message: Optional[str] = None
    error_code: Optional[str] = None
    raw_response: Optional[str] = None
    request_id: Optional[str] = None

class YardiRateLimiter:
    """Rate limiter for Yardi API requests"""
    
    def __init__(self, requests_per_minute: int = 60):
        self.requests_per_minute = requests_per_minute
        self.request_times: List[float] = []
        self.lock = asyncio.Lock()
    
    async def wait_if_needed(self):
        """Wait if rate limit would be exceeded"""
        async with self.lock:
            now = time.time()
            
            # Remove requests older than 1 minute
            self.request_times = [t for t in self.request_times if now - t < 60]
            
            # Check if we need to wait
            if len(self.request_times) >= self.requests_per_minute:
                sleep_time = 60 - (now - self.request_times[0])
                if sleep_time > 0:
                    await asyncio.sleep(sleep_time)
                    # Remove the old request after waiting
                    self.request_times.pop(0)
            
            # Record this request
            self.request_times.append(now)

class YardiAPIClient:
    """
    Comprehensive Yardi API client supporting multiple Yardi products
    """
    
    def __init__(self, auth_service):
        self.auth_service = auth_service
        self.rate_limiters: Dict[str, YardiRateLimiter] = {}
        
        # HTTP session with retries
        self.session = requests.Session()
        retry_strategy = Retry(
            total=3,
            status_forcelist=[429, 500, 502, 503, 504],
            method_whitelist=["HEAD", "GET", "OPTIONS"],
            backoff_factor=1
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        
        # Product-specific configurations
        self.product_configs = self._load_product_configurations()
        
        logger.info("Yardi API Client initialized")
    
    def _load_product_configurations(self) -> Dict[YardiProductType, Dict[str, Any]]:
        """Load product-specific API configurations"""
        return {
            YardiProductType.VOYAGER: {
                "api_version": "1.0",
                "base_path": "/webservices",
                "auth_path": "/auth",
                "default_format": "json",
                "max_requests_per_minute": 60,
                "timeout": 30,
                "supported_entities": [
                    "properties", "units", "tenants", "leases", "payments",
                    "work_orders", "vendors", "invoices", "chart_of_accounts"
                ],
                "endpoints": {
                    "properties": "/api/properties",
                    "units": "/api/units",
                    "tenants": "/api/tenants",
                    "leases": "/api/leases",
                    "payments": "/api/payments",
                    "work_orders": "/api/workorders",
                    "vendors": "/api/vendors"
                }
            },
            YardiProductType.BREEZE: {
                "api_version": "2.0",
                "base_path": "/api",
                "auth_path": "/oauth",
                "default_format": "json",
                "max_requests_per_minute": 100,
                "timeout": 20,
                "supported_entities": [
                    "properties", "units", "residents", "leases", "payments",
                    "maintenance_requests", "vendors"
                ],
                "endpoints": {
                    "properties": "/v2/properties",
                    "units": "/v2/units",
                    "residents": "/v2/residents",
                    "leases": "/v2/leases",
                    "payments": "/v2/payments",
                    "maintenance_requests": "/v2/maintenance"
                }
            },
            YardiProductType.GENESIS2: {
                "api_version": "1.5",
                "base_path": "/genesis2/api",
                "auth_path": "/auth",
                "default_format": "xml",
                "max_requests_per_minute": 30,
                "timeout": 45,
                "supported_entities": [
                    "properties", "units", "tenants", "accounting",
                    "financial_reports", "budgets"
                ],
                "endpoints": {
                    "properties": "/property/list",
                    "units": "/unit/list",
                    "tenants": "/tenant/list",
                    "accounting": "/accounting/entries",
                    "reports": "/reports/financial"
                }
            }
        }
    
    def get_rate_limiter(self, connection_id: str, requests_per_minute: int = 60) -> YardiRateLimiter:
        """Get or create rate limiter for connection"""
        if connection_id not in self.rate_limiters:
            self.rate_limiters[connection_id] = YardiRateLimiter(requests_per_minute)
        return self.rate_limiters[connection_id]
    
    async def test_connection(self, connection_id: str) -> Dict[str, Any]:
        """Test connection to Yardi system"""
        try:
            connection = self.auth_service.get_connection(connection_id)
            if not connection:
                return {
                    "success": False,
                    "error": "Connection not found"
                }
            
            # Get product config
            product_config = self.product_configs.get(connection.yardi_product)
            if not product_config:
                return {
                    "success": False,
                    "error": f"Unsupported Yardi product: {connection.yardi_product}"
                }
            
            # Prepare test request
            test_endpoint = self._get_test_endpoint(connection.yardi_product)
            url = urljoin(connection.base_url, test_endpoint)
            
            # Get authentication headers
            auth_headers = await self._get_auth_headers(connection)
            
            start_time = time.time()
            
            # Make test request
            response = self.session.get(
                url,
                headers=auth_headers,
                timeout=product_config["timeout"]
            )
            
            response_time = (time.time() - start_time) * 1000  # milliseconds
            
            if response.status_code == 200:
                # Parse company information
                company_info = self._parse_company_info(response, connection.yardi_product)
                
                return {
                    "success": True,
                    "status": "connected",
                    "response_time": response_time,
                    "company_info": company_info,
                    "capabilities": product_config["supported_entities"],
                    "api_version": product_config["api_version"]
                }
            else:
                return {
                    "success": False,
                    "status": "error",
                    "error": f"HTTP {response.status_code}: {response.text}",
                    "response_time": response_time
                }
                
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return {
                "success": False,
                "status": "error",
                "error": str(e)
            }
    
    async def execute_request(self, connection_id: str, 
                            api_request: YardiAPIRequest) -> YardiAPIResponse:
        """Execute API request to Yardi system"""
        start_time = time.time()
        
        try:
            connection = self.auth_service.get_connection(connection_id)
            if not connection:
                return YardiAPIResponse(
                    success=False,
                    status_code=0,
                    data=None,
                    headers={},
                    response_time=0,
                    error_message="Connection not found"
                )
            
            # Rate limiting
            rate_limiter = self.get_rate_limiter(
                connection_id, 
                connection.rate_limit_per_minute
            )
            await rate_limiter.wait_if_needed()
            
            # Build request URL
            url = self._build_request_url(connection, api_request)
            
            # Get authentication headers
            auth_headers = await self._get_auth_headers(connection)
            headers = {**auth_headers, **api_request.headers}
            
            # Add content type if needed
            if api_request.body:
                if api_request.response_format == YardiResponseFormat.JSON:
                    headers["Content-Type"] = "application/json"
                elif api_request.response_format == YardiResponseFormat.XML:
                    headers["Content-Type"] = "application/xml"
            
            # Prepare request body
            request_body = self._prepare_request_body(api_request, connection.yardi_product)
            
            # Execute request with retries
            for attempt in range(api_request.retries + 1):
                try:
                    response = self.session.request(
                        method=api_request.method,
                        url=url,
                        headers=headers,
                        json=request_body if api_request.response_format == YardiResponseFormat.JSON else None,
                        data=request_body if api_request.response_format != YardiResponseFormat.JSON else None,
                        timeout=api_request.timeout,
                        params=api_request.parameters
                    )
                    
                    response_time = (time.time() - start_time) * 1000
                    
                    # Parse response
                    parsed_data = self._parse_response(
                        response, api_request.response_format, connection.yardi_product
                    )
                    
                    return YardiAPIResponse(
                        success=response.status_code < 400,
                        status_code=response.status_code,
                        data=parsed_data,
                        headers=dict(response.headers),
                        response_time=response_time,
                        error_message=None if response.status_code < 400 else parsed_data.get("error"),
                        raw_response=response.text,
                        request_id=headers.get("X-Request-ID")
                    )
                    
                except requests.exceptions.RequestException as e:
                    if attempt == api_request.retries:
                        response_time = (time.time() - start_time) * 1000
                        return YardiAPIResponse(
                            success=False,
                            status_code=0,
                            data=None,
                            headers={},
                            response_time=response_time,
                            error_message=str(e)
                        )
                    
                    # Wait before retry
                    await asyncio.sleep(2 ** attempt)
                    
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            logger.error(f"API request failed: {e}")
            return YardiAPIResponse(
                success=False,
                status_code=0,
                data=None,
                headers={},
                response_time=response_time,
                error_message=str(e)
            )
    
    # =====================================================
    # ENTITY-SPECIFIC METHODS
    # =====================================================
    
    async def get_properties(self, connection_id: str, 
                           filters: Optional[Dict[str, Any]] = None) -> YardiAPIResponse:
        """Get properties from Yardi"""
        request = YardiAPIRequest(
            endpoint="properties",
            method="GET",
            entity_type=YardiEntityType.PROPERTIES,
            operation=YardiOperationType.READ,
            parameters=filters or {}
        )
        return await self.execute_request(connection_id, request)
    
    async def get_units(self, connection_id: str, property_id: Optional[str] = None,
                      filters: Optional[Dict[str, Any]] = None) -> YardiAPIResponse:
        """Get units from Yardi"""
        params = filters or {}
        if property_id:
            params["property_id"] = property_id
            
        request = YardiAPIRequest(
            endpoint="units",
            method="GET",
            entity_type=YardiEntityType.UNITS,
            operation=YardiOperationType.READ,
            parameters=params
        )
        return await self.execute_request(connection_id, request)
    
    async def get_tenants(self, connection_id: str,
                        filters: Optional[Dict[str, Any]] = None) -> YardiAPIResponse:
        """Get tenants/residents from Yardi"""
        request = YardiAPIRequest(
            endpoint="tenants",
            method="GET",
            entity_type=YardiEntityType.TENANTS,
            operation=YardiOperationType.READ,
            parameters=filters or {}
        )
        return await self.execute_request(connection_id, request)
    
    async def get_leases(self, connection_id: str,
                       filters: Optional[Dict[str, Any]] = None) -> YardiAPIResponse:
        """Get leases from Yardi"""
        request = YardiAPIRequest(
            endpoint="leases",
            method="GET",
            entity_type=YardiEntityType.LEASES,
            operation=YardiOperationType.READ,
            parameters=filters or {}
        )
        return await self.execute_request(connection_id, request)
    
    async def get_payments(self, connection_id: str,
                         filters: Optional[Dict[str, Any]] = None) -> YardiAPIResponse:
        """Get payments from Yardi"""
        request = YardiAPIRequest(
            endpoint="payments",
            method="GET",
            entity_type=YardiEntityType.PAYMENTS,
            operation=YardiOperationType.READ,
            parameters=filters or {}
        )
        return await self.execute_request(connection_id, request)
    
    async def get_work_orders(self, connection_id: str,
                            filters: Optional[Dict[str, Any]] = None) -> YardiAPIResponse:
        """Get work orders from Yardi"""
        request = YardiAPIRequest(
            endpoint="work_orders",
            method="GET",
            entity_type=YardiEntityType.WORK_ORDERS,
            operation=YardiOperationType.READ,
            parameters=filters or {}
        )
        return await self.execute_request(connection_id, request)
    
    async def create_tenant(self, connection_id: str, 
                          tenant_data: Dict[str, Any]) -> YardiAPIResponse:
        """Create new tenant in Yardi"""
        request = YardiAPIRequest(
            endpoint="tenants",
            method="POST",
            entity_type=YardiEntityType.TENANTS,
            operation=YardiOperationType.CREATE,
            body=tenant_data
        )
        return await self.execute_request(connection_id, request)
    
    async def update_tenant(self, connection_id: str, tenant_id: str,
                          tenant_data: Dict[str, Any]) -> YardiAPIResponse:
        """Update tenant in Yardi"""
        request = YardiAPIRequest(
            endpoint=f"tenants/{tenant_id}",
            method="PUT",
            entity_type=YardiEntityType.TENANTS,
            operation=YardiOperationType.UPDATE,
            body=tenant_data
        )
        return await self.execute_request(connection_id, request)
    
    async def create_payment(self, connection_id: str,
                           payment_data: Dict[str, Any]) -> YardiAPIResponse:
        """Create payment record in Yardi"""
        request = YardiAPIRequest(
            endpoint="payments",
            method="POST",
            entity_type=YardiEntityType.PAYMENTS,
            operation=YardiOperationType.CREATE,
            body=payment_data
        )
        return await self.execute_request(connection_id, request)
    
    async def create_work_order(self, connection_id: str,
                              work_order_data: Dict[str, Any]) -> YardiAPIResponse:
        """Create work order in Yardi"""
        request = YardiAPIRequest(
            endpoint="work_orders",
            method="POST",
            entity_type=YardiEntityType.WORK_ORDERS,
            operation=YardiOperationType.CREATE,
            body=work_order_data
        )
        return await self.execute_request(connection_id, request)
    
    # =====================================================
    # BULK OPERATIONS
    # =====================================================
    
    async def bulk_create_entities(self, connection_id: str, entity_type: YardiEntityType,
                                 entities_data: List[Dict[str, Any]]) -> YardiAPIResponse:
        """Bulk create entities in Yardi"""
        endpoint = self._get_entity_endpoint(entity_type)
        request = YardiAPIRequest(
            endpoint=f"{endpoint}/bulk",
            method="POST",
            entity_type=entity_type,
            operation=YardiOperationType.BULK_CREATE,
            body={"entities": entities_data}
        )
        return await self.execute_request(connection_id, request)
    
    async def bulk_update_entities(self, connection_id: str, entity_type: YardiEntityType,
                                 entities_data: List[Dict[str, Any]]) -> YardiAPIResponse:
        """Bulk update entities in Yardi"""
        endpoint = self._get_entity_endpoint(entity_type)
        request = YardiAPIRequest(
            endpoint=f"{endpoint}/bulk",
            method="PUT",
            entity_type=entity_type,
            operation=YardiOperationType.BULK_UPDATE,
            body={"entities": entities_data}
        )
        return await self.execute_request(connection_id, request)
    
    # =====================================================
    # SEARCH AND QUERY
    # =====================================================
    
    async def search_entities(self, connection_id: str, entity_type: YardiEntityType,
                            search_criteria: Dict[str, Any]) -> YardiAPIResponse:
        """Search for entities in Yardi"""
        endpoint = self._get_entity_endpoint(entity_type)
        request = YardiAPIRequest(
            endpoint=f"{endpoint}/search",
            method="POST",
            entity_type=entity_type,
            operation=YardiOperationType.SEARCH,
            body=search_criteria
        )
        return await self.execute_request(connection_id, request)
    
    async def get_entity_changes(self, connection_id: str, entity_type: YardiEntityType,
                               since_timestamp: datetime) -> YardiAPIResponse:
        """Get entity changes since timestamp"""
        endpoint = self._get_entity_endpoint(entity_type)
        request = YardiAPIRequest(
            endpoint=f"{endpoint}/changes",
            method="GET",
            entity_type=entity_type,
            operation=YardiOperationType.READ,
            parameters={
                "since": since_timestamp.isoformat(),
                "include_deleted": "true"
            }
        )
        return await self.execute_request(connection_id, request)
    
    # =====================================================
    # PRIVATE HELPER METHODS
    # =====================================================
    
    def _get_test_endpoint(self, product_type: YardiProductType) -> str:
        """Get test endpoint for product type"""
        endpoints = {
            YardiProductType.VOYAGER: "/webservices/api/ping",
            YardiProductType.BREEZE: "/api/v2/health",
            YardiProductType.GENESIS2: "/genesis2/api/status"
        }
        return endpoints.get(product_type, "/api/health")
    
    def _build_request_url(self, connection, api_request: YardiAPIRequest) -> str:
        """Build complete request URL"""
        product_config = self.product_configs[connection.yardi_product]
        base_path = product_config["base_path"]
        
        # Get endpoint from configuration or use provided
        if api_request.endpoint in product_config["endpoints"]:
            endpoint = product_config["endpoints"][api_request.endpoint]
        else:
            endpoint = f"/{api_request.endpoint}"
        
        return urljoin(connection.base_url, base_path + endpoint)
    
    async def _get_auth_headers(self, connection) -> Dict[str, str]:
        """Get authentication headers for connection"""
        headers = {}
        
        if connection.auth_method == YardiAuthMethod.API_KEY:
            credentials = json.loads(connection.credentials)
            headers["X-API-Key"] = credentials["api_key"]
            if "client_id" in credentials:
                headers["X-Client-ID"] = credentials["client_id"]
        
        elif connection.auth_method == YardiAuthMethod.OAUTH2:
            token = await self.auth_service.get_valid_token(connection.connection_id)
            if token:
                headers["Authorization"] = f"Bearer {token}"
        
        elif connection.auth_method == YardiAuthMethod.USERNAME_PASSWORD:
            credentials = json.loads(connection.credentials)
            auth_string = f"{credentials['username']}:{credentials['password']}"
            encoded_auth = base64.b64encode(auth_string.encode()).decode()
            headers["Authorization"] = f"Basic {encoded_auth}"
        
        elif connection.auth_method == YardiAuthMethod.TOKEN:
            credentials = json.loads(connection.credentials)
            headers["Authorization"] = f"Token {credentials['token']}"
        
        # Add common headers
        headers["User-Agent"] = "EstateCore-Yardi-Integration/1.0"
        headers["Accept"] = "application/json"
        
        return headers
    
    def _prepare_request_body(self, api_request: YardiAPIRequest, 
                            product_type: YardiProductType) -> Any:
        """Prepare request body based on format and product"""
        if not api_request.body:
            return None
        
        if api_request.response_format == YardiResponseFormat.JSON:
            return api_request.body
        elif api_request.response_format == YardiResponseFormat.XML:
            return self._dict_to_xml(api_request.body, product_type)
        else:
            return json.dumps(api_request.body)
    
    def _parse_response(self, response, response_format: YardiResponseFormat,
                      product_type: YardiProductType) -> Any:
        """Parse API response based on format"""
        try:
            if response_format == YardiResponseFormat.JSON:
                return response.json()
            elif response_format == YardiResponseFormat.XML:
                return self._xml_to_dict(response.text, product_type)
            elif response_format == YardiResponseFormat.CSV:
                return self._csv_to_dict(response.text)
            else:
                return {"raw": response.text}
        except Exception as e:
            logger.error(f"Failed to parse response: {e}")
            return {"error": "Failed to parse response", "raw": response.text}
    
    def _parse_company_info(self, response, product_type: YardiProductType) -> Dict[str, Any]:
        """Parse company information from test response"""
        try:
            if product_type == YardiProductType.VOYAGER:
                data = response.json()
                return {
                    "name": data.get("company_name", "Unknown"),
                    "database_id": data.get("database_id"),
                    "server_version": data.get("server_version"),
                    "api_version": data.get("api_version")
                }
            elif product_type == YardiProductType.BREEZE:
                data = response.json()
                return {
                    "name": data.get("organization_name", "Unknown"),
                    "tenant_id": data.get("tenant_id"),
                    "region": data.get("region"),
                    "version": data.get("version")
                }
            else:
                return {"name": "Unknown", "status": "connected"}
        except Exception:
            return {"name": "Unknown", "status": "connected"}
    
    def _get_entity_endpoint(self, entity_type: YardiEntityType) -> str:
        """Get endpoint path for entity type"""
        endpoint_map = {
            YardiEntityType.PROPERTIES: "properties",
            YardiEntityType.UNITS: "units",
            YardiEntityType.TENANTS: "tenants",
            YardiEntityType.LEASES: "leases",
            YardiEntityType.PAYMENTS: "payments",
            YardiEntityType.WORK_ORDERS: "work_orders",
            YardiEntityType.VENDORS: "vendors",
            YardiEntityType.INVOICES: "invoices"
        }
        return endpoint_map.get(entity_type, entity_type.value)
    
    def _dict_to_xml(self, data: Dict[str, Any], product_type: YardiProductType) -> str:
        """Convert dictionary to XML format"""
        # Simplified XML conversion - would need product-specific implementation
        root = ET.Element("request")
        for key, value in data.items():
            element = ET.SubElement(root, key)
            element.text = str(value)
        return ET.tostring(root, encoding='unicode')
    
    def _xml_to_dict(self, xml_data: str, product_type: YardiProductType) -> Dict[str, Any]:
        """Convert XML to dictionary"""
        try:
            root = ET.fromstring(xml_data)
            return self._xml_element_to_dict(root)
        except Exception as e:
            logger.error(f"XML parsing failed: {e}")
            return {"error": "XML parsing failed", "raw": xml_data}
    
    def _xml_element_to_dict(self, element) -> Dict[str, Any]:
        """Convert XML element to dictionary"""
        result = {}
        
        # Add attributes
        if element.attrib:
            result.update(element.attrib)
        
        # Add text content
        if element.text and element.text.strip():
            if len(element) == 0:
                return element.text.strip()
            else:
                result['text'] = element.text.strip()
        
        # Add child elements
        for child in element:
            child_data = self._xml_element_to_dict(child)
            if child.tag in result:
                if not isinstance(result[child.tag], list):
                    result[child.tag] = [result[child.tag]]
                result[child.tag].append(child_data)
            else:
                result[child.tag] = child_data
        
        return result
    
    def _csv_to_dict(self, csv_data: str) -> Dict[str, Any]:
        """Convert CSV to dictionary format"""
        import csv
        import io
        
        try:
            reader = csv.DictReader(io.StringIO(csv_data))
            return {"data": list(reader)}
        except Exception as e:
            logger.error(f"CSV parsing failed: {e}")
            return {"error": "CSV parsing failed", "raw": csv_data}