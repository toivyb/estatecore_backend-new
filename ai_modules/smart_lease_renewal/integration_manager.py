"""
Platform Integration Manager
Comprehensive integration layer for all property management platforms and external data sources
"""

import asyncio
import aiohttp
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any, Union
from dataclasses import dataclass, asdict
from enum import Enum
import logging
import json
import base64
from abc import ABC, abstractmethod
import hashlib
import hmac
from urllib.parse import urlencode, quote
import xml.etree.ElementTree as ET

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class IntegrationType(Enum):
    """Types of integrations"""
    PROPERTY_MANAGEMENT = "property_management"
    MARKET_DATA = "market_data"
    CREDIT_REPORTING = "credit_reporting"
    PAYMENT_PROCESSING = "payment_processing"
    DOCUMENT_MANAGEMENT = "document_management"
    COMMUNICATION = "communication"
    ACCOUNTING = "accounting"

class DataSyncStatus(Enum):
    """Data synchronization status"""
    SUCCESS = "success"
    FAILED = "failed"
    PARTIAL = "partial"
    IN_PROGRESS = "in_progress"
    PENDING = "pending"

class AuthenticationType(Enum):
    """Authentication types for integrations"""
    API_KEY = "api_key"
    OAUTH2 = "oauth2"
    BASIC_AUTH = "basic_auth"
    JWT = "jwt"
    CUSTOM = "custom"

@dataclass
class IntegrationConfig:
    """Integration configuration"""
    platform_id: str
    platform_name: str
    integration_type: IntegrationType
    auth_type: AuthenticationType
    base_url: str
    api_version: str
    credentials: Dict[str, Any]
    sync_frequency: int  # minutes
    enabled: bool
    rate_limits: Dict[str, int]
    field_mappings: Dict[str, str]
    webhook_endpoints: List[str]
    last_sync: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

@dataclass
class SyncResult:
    """Data synchronization result"""
    integration_id: str
    sync_type: str
    status: DataSyncStatus
    records_processed: int
    records_successful: int
    records_failed: int
    errors: List[str]
    warnings: List[str]
    sync_duration_seconds: float
    last_sync_timestamp: datetime
    next_sync_scheduled: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

class BaseIntegration(ABC):
    """
    Base class for all platform integrations
    """
    
    def __init__(self, config: IntegrationConfig):
        self.config = config
        self.session = None
        self.auth_token = None
        self.rate_limit_tracker = {}
        
    async def initialize(self):
        """Initialize integration connection"""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            headers=self._get_default_headers()
        )
        await self._authenticate()
    
    async def cleanup(self):
        """Cleanup integration resources"""
        if self.session:
            await self.session.close()
    
    @abstractmethod
    async def _authenticate(self):
        """Authenticate with the platform"""
        pass
    
    @abstractmethod
    async def sync_tenant_data(self) -> List[Dict[str, Any]]:
        """Sync tenant data from platform"""
        pass
    
    @abstractmethod
    async def sync_lease_data(self) -> List[Dict[str, Any]]:
        """Sync lease data from platform"""
        pass
    
    @abstractmethod
    async def sync_property_data(self) -> List[Dict[str, Any]]:
        """Sync property data from platform"""
        pass
    
    @abstractmethod
    async def sync_payment_data(self) -> List[Dict[str, Any]]:
        """Sync payment data from platform"""
        pass
    
    def _get_default_headers(self) -> Dict[str, str]:
        """Get default HTTP headers"""
        return {
            'User-Agent': 'EstateCore-LeaseRenewal/1.0',
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }
    
    async def _check_rate_limits(self, endpoint: str) -> bool:
        """Check if rate limits allow request"""
        now = datetime.now()
        
        if endpoint not in self.rate_limit_tracker:
            self.rate_limit_tracker[endpoint] = {'requests': 0, 'reset_time': now + timedelta(minutes=1)}
            return True
        
        tracker = self.rate_limit_tracker[endpoint]
        
        if now > tracker['reset_time']:
            tracker['requests'] = 0
            tracker['reset_time'] = now + timedelta(minutes=1)
        
        limit = self.config.rate_limits.get(endpoint, 100)  # Default 100/min
        
        if tracker['requests'] >= limit:
            return False
        
        tracker['requests'] += 1
        return True
    
    def _map_fields(self, data: Dict[str, Any], reverse: bool = False) -> Dict[str, Any]:
        """Map fields between EstateCore and platform formats"""
        if not self.config.field_mappings:
            return data
        
        mapped_data = {}
        mappings = self.config.field_mappings
        
        if reverse:
            # Reverse mapping (platform -> EstateCore)
            mappings = {v: k for k, v in mappings.items()}
        
        for key, value in data.items():
            mapped_key = mappings.get(key, key)
            mapped_data[mapped_key] = value
        
        return mapped_data

class YardiIntegration(BaseIntegration):
    """Yardi Voyager integration"""
    
    async def _authenticate(self):
        """Authenticate with Yardi"""
        auth_url = f"{self.config.base_url}/auth/login"
        auth_data = {
            'username': self.config.credentials.get('username'),
            'password': self.config.credentials.get('password'),
            'database': self.config.credentials.get('database')
        }
        
        try:
            async with self.session.post(auth_url, json=auth_data) as response:
                if response.status == 200:
                    result = await response.json()
                    self.auth_token = result.get('token')
                    logger.info("Yardi authentication successful")
                else:
                    raise Exception(f"Yardi authentication failed: {response.status}")
        except Exception as e:
            logger.error(f"Yardi authentication error: {str(e)}")
            raise
    
    async def sync_tenant_data(self) -> List[Dict[str, Any]]:
        """Sync tenant data from Yardi"""
        endpoint = "/api/tenants"
        
        if not await self._check_rate_limits(endpoint):
            raise Exception("Rate limit exceeded for tenant data sync")
        
        headers = {'Authorization': f'Bearer {self.auth_token}'}
        
        try:
            async with self.session.get(
                f"{self.config.base_url}{endpoint}",
                headers=headers
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    tenants = data.get('tenants', [])
                    
                    # Map Yardi fields to EstateCore format
                    mapped_tenants = []
                    for tenant in tenants:
                        mapped_tenant = self._map_yardi_tenant(tenant)
                        mapped_tenants.append(mapped_tenant)
                    
                    logger.info(f"Synced {len(mapped_tenants)} tenants from Yardi")
                    return mapped_tenants
                else:
                    raise Exception(f"Failed to fetch Yardi tenants: {response.status}")
                    
        except Exception as e:
            logger.error(f"Yardi tenant sync error: {str(e)}")
            return []
    
    async def sync_lease_data(self) -> List[Dict[str, Any]]:
        """Sync lease data from Yardi"""
        endpoint = "/api/leases"
        headers = {'Authorization': f'Bearer {self.auth_token}'}
        
        try:
            async with self.session.get(
                f"{self.config.base_url}{endpoint}",
                headers=headers
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    leases = data.get('leases', [])
                    
                    mapped_leases = []
                    for lease in leases:
                        mapped_lease = self._map_yardi_lease(lease)
                        mapped_leases.append(mapped_lease)
                    
                    logger.info(f"Synced {len(mapped_leases)} leases from Yardi")
                    return mapped_leases
                else:
                    raise Exception(f"Failed to fetch Yardi leases: {response.status}")
                    
        except Exception as e:
            logger.error(f"Yardi lease sync error: {str(e)}")
            return []
    
    async def sync_property_data(self) -> List[Dict[str, Any]]:
        """Sync property data from Yardi"""
        endpoint = "/api/properties"
        headers = {'Authorization': f'Bearer {self.auth_token}'}
        
        try:
            async with self.session.get(
                f"{self.config.base_url}{endpoint}",
                headers=headers
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    properties = data.get('properties', [])
                    
                    mapped_properties = []
                    for prop in properties:
                        mapped_property = self._map_yardi_property(prop)
                        mapped_properties.append(mapped_property)
                    
                    logger.info(f"Synced {len(mapped_properties)} properties from Yardi")
                    return mapped_properties
                else:
                    raise Exception(f"Failed to fetch Yardi properties: {response.status}")
                    
        except Exception as e:
            logger.error(f"Yardi property sync error: {str(e)}")
            return []
    
    async def sync_payment_data(self) -> List[Dict[str, Any]]:
        """Sync payment data from Yardi"""
        endpoint = "/api/payments"
        headers = {'Authorization': f'Bearer {self.auth_token}'}
        
        # Get payments from last 90 days
        since_date = (datetime.now() - timedelta(days=90)).isoformat()
        params = {'since': since_date}
        
        try:
            async with self.session.get(
                f"{self.config.base_url}{endpoint}",
                headers=headers,
                params=params
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    payments = data.get('payments', [])
                    
                    mapped_payments = []
                    for payment in payments:
                        mapped_payment = self._map_yardi_payment(payment)
                        mapped_payments.append(mapped_payment)
                    
                    logger.info(f"Synced {len(mapped_payments)} payments from Yardi")
                    return mapped_payments
                else:
                    raise Exception(f"Failed to fetch Yardi payments: {response.status}")
                    
        except Exception as e:
            logger.error(f"Yardi payment sync error: {str(e)}")
            return []
    
    def _map_yardi_tenant(self, yardi_tenant: Dict[str, Any]) -> Dict[str, Any]:
        """Map Yardi tenant data to EstateCore format"""
        return {
            'tenant_id': yardi_tenant.get('TenantID'),
            'first_name': yardi_tenant.get('FirstName'),
            'last_name': yardi_tenant.get('LastName'),
            'email': yardi_tenant.get('Email'),
            'phone': yardi_tenant.get('Phone'),
            'move_in_date': yardi_tenant.get('MoveInDate'),
            'lease_start_date': yardi_tenant.get('LeaseStartDate'),
            'lease_end_date': yardi_tenant.get('LeaseEndDate'),
            'monthly_rent': yardi_tenant.get('MonthlyRent'),
            'security_deposit': yardi_tenant.get('SecurityDeposit'),
            'unit_id': yardi_tenant.get('UnitID'),
            'property_id': yardi_tenant.get('PropertyID'),
            'lease_status': yardi_tenant.get('LeaseStatus'),
            'source_platform': 'yardi',
            'last_updated': datetime.now().isoformat()
        }
    
    def _map_yardi_lease(self, yardi_lease: Dict[str, Any]) -> Dict[str, Any]:
        """Map Yardi lease data to EstateCore format"""
        return {
            'lease_id': yardi_lease.get('LeaseID'),
            'tenant_id': yardi_lease.get('TenantID'),
            'unit_id': yardi_lease.get('UnitID'),
            'lease_start_date': yardi_lease.get('StartDate'),
            'lease_end_date': yardi_lease.get('EndDate'),
            'monthly_rent': yardi_lease.get('MonthlyRent'),
            'lease_term_months': yardi_lease.get('LeaseTermMonths'),
            'security_deposit': yardi_lease.get('SecurityDeposit'),
            'lease_type': yardi_lease.get('LeaseType'),
            'lease_status': yardi_lease.get('Status'),
            'renewal_count': yardi_lease.get('RenewalCount', 0),
            'source_platform': 'yardi',
            'last_updated': datetime.now().isoformat()
        }
    
    def _map_yardi_property(self, yardi_property: Dict[str, Any]) -> Dict[str, Any]:
        """Map Yardi property data to EstateCore format"""
        return {
            'property_id': yardi_property.get('PropertyID'),
            'property_name': yardi_property.get('PropertyName'),
            'address': yardi_property.get('Address'),
            'city': yardi_property.get('City'),
            'state': yardi_property.get('State'),
            'zip_code': yardi_property.get('ZipCode'),
            'total_units': yardi_property.get('TotalUnits'),
            'property_type': yardi_property.get('PropertyType'),
            'year_built': yardi_property.get('YearBuilt'),
            'amenities': yardi_property.get('Amenities', []),
            'source_platform': 'yardi',
            'last_updated': datetime.now().isoformat()
        }
    
    def _map_yardi_payment(self, yardi_payment: Dict[str, Any]) -> Dict[str, Any]:
        """Map Yardi payment data to EstateCore format"""
        return {
            'payment_id': yardi_payment.get('PaymentID'),
            'tenant_id': yardi_payment.get('TenantID'),
            'lease_id': yardi_payment.get('LeaseID'),
            'amount': yardi_payment.get('Amount'),
            'payment_date': yardi_payment.get('PaymentDate'),
            'payment_type': yardi_payment.get('PaymentType'),
            'payment_method': yardi_payment.get('PaymentMethod'),
            'transaction_id': yardi_payment.get('TransactionID'),
            'status': yardi_payment.get('Status'),
            'late_fees': yardi_payment.get('LateFees', 0),
            'source_platform': 'yardi',
            'last_updated': datetime.now().isoformat()
        }

class AppFolioIntegration(BaseIntegration):
    """AppFolio integration"""
    
    async def _authenticate(self):
        """Authenticate with AppFolio"""
        auth_url = f"{self.config.base_url}/oauth/token"
        auth_data = {
            'grant_type': 'client_credentials',
            'client_id': self.config.credentials.get('client_id'),
            'client_secret': self.config.credentials.get('client_secret')
        }
        
        try:
            async with self.session.post(auth_url, data=auth_data) as response:
                if response.status == 200:
                    result = await response.json()
                    self.auth_token = result.get('access_token')
                    logger.info("AppFolio authentication successful")
                else:
                    raise Exception(f"AppFolio authentication failed: {response.status}")
        except Exception as e:
            logger.error(f"AppFolio authentication error: {str(e)}")
            raise
    
    async def sync_tenant_data(self) -> List[Dict[str, Any]]:
        """Sync tenant data from AppFolio"""
        endpoint = "/api/v1/tenants"
        headers = {'Authorization': f'Bearer {self.auth_token}'}
        
        try:
            tenants = []
            page = 1
            per_page = 100
            
            while True:
                params = {'page': page, 'per_page': per_page}
                
                async with self.session.get(
                    f"{self.config.base_url}{endpoint}",
                    headers=headers,
                    params=params
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        page_tenants = data.get('tenants', [])
                        
                        if not page_tenants:
                            break
                        
                        for tenant in page_tenants:
                            mapped_tenant = self._map_appfolio_tenant(tenant)
                            tenants.append(mapped_tenant)
                        
                        page += 1
                    else:
                        break
            
            logger.info(f"Synced {len(tenants)} tenants from AppFolio")
            return tenants
            
        except Exception as e:
            logger.error(f"AppFolio tenant sync error: {str(e)}")
            return []
    
    async def sync_lease_data(self) -> List[Dict[str, Any]]:
        """Sync lease data from AppFolio"""
        endpoint = "/api/v1/leases"
        headers = {'Authorization': f'Bearer {self.auth_token}'}
        
        try:
            leases = []
            page = 1
            per_page = 100
            
            while True:
                params = {'page': page, 'per_page': per_page}
                
                async with self.session.get(
                    f"{self.config.base_url}{endpoint}",
                    headers=headers,
                    params=params
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        page_leases = data.get('leases', [])
                        
                        if not page_leases:
                            break
                        
                        for lease in page_leases:
                            mapped_lease = self._map_appfolio_lease(lease)
                            leases.append(mapped_lease)
                        
                        page += 1
                    else:
                        break
            
            logger.info(f"Synced {len(leases)} leases from AppFolio")
            return leases
            
        except Exception as e:
            logger.error(f"AppFolio lease sync error: {str(e)}")
            return []
    
    async def sync_property_data(self) -> List[Dict[str, Any]]:
        """Sync property data from AppFolio"""
        endpoint = "/api/v1/rental_properties"
        headers = {'Authorization': f'Bearer {self.auth_token}'}
        
        try:
            properties = []
            page = 1
            per_page = 100
            
            while True:
                params = {'page': page, 'per_page': per_page}
                
                async with self.session.get(
                    f"{self.config.base_url}{endpoint}",
                    headers=headers,
                    params=params
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        page_properties = data.get('rental_properties', [])
                        
                        if not page_properties:
                            break
                        
                        for prop in page_properties:
                            mapped_property = self._map_appfolio_property(prop)
                            properties.append(mapped_property)
                        
                        page += 1
                    else:
                        break
            
            logger.info(f"Synced {len(properties)} properties from AppFolio")
            return properties
            
        except Exception as e:
            logger.error(f"AppFolio property sync error: {str(e)}")
            return []
    
    async def sync_payment_data(self) -> List[Dict[str, Any]]:
        """Sync payment data from AppFolio"""
        endpoint = "/api/v1/payments"
        headers = {'Authorization': f'Bearer {self.auth_token}'}
        
        since_date = (datetime.now() - timedelta(days=90)).isoformat()
        
        try:
            payments = []
            page = 1
            per_page = 100
            
            while True:
                params = {
                    'page': page,
                    'per_page': per_page,
                    'start_date': since_date
                }
                
                async with self.session.get(
                    f"{self.config.base_url}{endpoint}",
                    headers=headers,
                    params=params
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        page_payments = data.get('payments', [])
                        
                        if not page_payments:
                            break
                        
                        for payment in page_payments:
                            mapped_payment = self._map_appfolio_payment(payment)
                            payments.append(mapped_payment)
                        
                        page += 1
                    else:
                        break
            
            logger.info(f"Synced {len(payments)} payments from AppFolio")
            return payments
            
        except Exception as e:
            logger.error(f"AppFolio payment sync error: {str(e)}")
            return []
    
    def _map_appfolio_tenant(self, appfolio_tenant: Dict[str, Any]) -> Dict[str, Any]:
        """Map AppFolio tenant data to EstateCore format"""
        return {
            'tenant_id': str(appfolio_tenant.get('id')),
            'first_name': appfolio_tenant.get('first_name'),
            'last_name': appfolio_tenant.get('last_name'),
            'email': appfolio_tenant.get('email'),
            'phone': appfolio_tenant.get('primary_phone_number'),
            'move_in_date': appfolio_tenant.get('move_in_date'),
            'unit_id': str(appfolio_tenant.get('unit_id')),
            'property_id': str(appfolio_tenant.get('property_id')),
            'source_platform': 'appfolio',
            'last_updated': datetime.now().isoformat()
        }
    
    def _map_appfolio_lease(self, appfolio_lease: Dict[str, Any]) -> Dict[str, Any]:
        """Map AppFolio lease data to EstateCore format"""
        return {
            'lease_id': str(appfolio_lease.get('id')),
            'tenant_id': str(appfolio_lease.get('tenant_id')),
            'unit_id': str(appfolio_lease.get('unit_id')),
            'lease_start_date': appfolio_lease.get('start_date'),
            'lease_end_date': appfolio_lease.get('end_date'),
            'monthly_rent': appfolio_lease.get('monthly_rent'),
            'lease_term_months': appfolio_lease.get('term_months'),
            'security_deposit': appfolio_lease.get('security_deposit_amount'),
            'lease_status': appfolio_lease.get('status'),
            'source_platform': 'appfolio',
            'last_updated': datetime.now().isoformat()
        }
    
    def _map_appfolio_property(self, appfolio_property: Dict[str, Any]) -> Dict[str, Any]:
        """Map AppFolio property data to EstateCore format"""
        address = appfolio_property.get('address', {})
        return {
            'property_id': str(appfolio_property.get('id')),
            'property_name': appfolio_property.get('name'),
            'address': address.get('address_1'),
            'city': address.get('city'),
            'state': address.get('state'),
            'zip_code': address.get('postal_code'),
            'total_units': appfolio_property.get('unit_count'),
            'property_type': appfolio_property.get('property_type'),
            'source_platform': 'appfolio',
            'last_updated': datetime.now().isoformat()
        }
    
    def _map_appfolio_payment(self, appfolio_payment: Dict[str, Any]) -> Dict[str, Any]:
        """Map AppFolio payment data to EstateCore format"""
        return {
            'payment_id': str(appfolio_payment.get('id')),
            'tenant_id': str(appfolio_payment.get('tenant_id')),
            'amount': appfolio_payment.get('amount'),
            'payment_date': appfolio_payment.get('payment_date'),
            'payment_type': appfolio_payment.get('payment_type'),
            'payment_method': appfolio_payment.get('payment_method'),
            'status': appfolio_payment.get('status'),
            'source_platform': 'appfolio',
            'last_updated': datetime.now().isoformat()
        }

class BuildiumIntegration(BaseIntegration):
    """Buildium integration"""
    
    async def _authenticate(self):
        """Authenticate with Buildium"""
        # Buildium uses API key authentication
        api_key = self.config.credentials.get('api_key')
        if not api_key:
            raise Exception("Buildium API key not provided")
        
        # Set authorization header for all requests
        self.auth_token = api_key
        self.session.headers.update({'X-Buildium-Api-Key': api_key})
        logger.info("Buildium authentication configured")
    
    async def sync_tenant_data(self) -> List[Dict[str, Any]]:
        """Sync tenant data from Buildium"""
        endpoint = "/v1/leases/tenants"
        
        try:
            tenants = []
            offset = 0
            limit = 100
            
            while True:
                params = {'offset': offset, 'limit': limit}
                
                async with self.session.get(
                    f"{self.config.base_url}{endpoint}",
                    params=params
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        page_tenants = data
                        
                        if not page_tenants or len(page_tenants) == 0:
                            break
                        
                        for tenant in page_tenants:
                            mapped_tenant = self._map_buildium_tenant(tenant)
                            tenants.append(mapped_tenant)
                        
                        offset += limit
                    else:
                        break
            
            logger.info(f"Synced {len(tenants)} tenants from Buildium")
            return tenants
            
        except Exception as e:
            logger.error(f"Buildium tenant sync error: {str(e)}")
            return []
    
    async def sync_lease_data(self) -> List[Dict[str, Any]]:
        """Sync lease data from Buildium"""
        endpoint = "/v1/leases"
        
        try:
            leases = []
            offset = 0
            limit = 100
            
            while True:
                params = {'offset': offset, 'limit': limit}
                
                async with self.session.get(
                    f"{self.config.base_url}{endpoint}",
                    params=params
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        page_leases = data
                        
                        if not page_leases or len(page_leases) == 0:
                            break
                        
                        for lease in page_leases:
                            mapped_lease = self._map_buildium_lease(lease)
                            leases.append(mapped_lease)
                        
                        offset += limit
                    else:
                        break
            
            logger.info(f"Synced {len(leases)} leases from Buildium")
            return leases
            
        except Exception as e:
            logger.error(f"Buildium lease sync error: {str(e)}")
            return []
    
    async def sync_property_data(self) -> List[Dict[str, Any]]:
        """Sync property data from Buildium"""
        endpoint = "/v1/properties"
        
        try:
            properties = []
            offset = 0
            limit = 100
            
            while True:
                params = {'offset': offset, 'limit': limit}
                
                async with self.session.get(
                    f"{self.config.base_url}{endpoint}",
                    params=params
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        page_properties = data
                        
                        if not page_properties or len(page_properties) == 0:
                            break
                        
                        for prop in page_properties:
                            mapped_property = self._map_buildium_property(prop)
                            properties.append(mapped_property)
                        
                        offset += limit
                    else:
                        break
            
            logger.info(f"Synced {len(properties)} properties from Buildium")
            return properties
            
        except Exception as e:
            logger.error(f"Buildium property sync error: {str(e)}")
            return []
    
    async def sync_payment_data(self) -> List[Dict[str, Any]]:
        """Sync payment data from Buildium"""
        endpoint = "/v1/rentals/payments"
        
        since_date = (datetime.now() - timedelta(days=90)).strftime('%Y-%m-%d')
        
        try:
            payments = []
            offset = 0
            limit = 100
            
            while True:
                params = {
                    'offset': offset,
                    'limit': limit,
                    'paymentdatefrom': since_date
                }
                
                async with self.session.get(
                    f"{self.config.base_url}{endpoint}",
                    params=params
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        page_payments = data
                        
                        if not page_payments or len(page_payments) == 0:
                            break
                        
                        for payment in page_payments:
                            mapped_payment = self._map_buildium_payment(payment)
                            payments.append(mapped_payment)
                        
                        offset += limit
                    else:
                        break
            
            logger.info(f"Synced {len(payments)} payments from Buildium")
            return payments
            
        except Exception as e:
            logger.error(f"Buildium payment sync error: {str(e)}")
            return []
    
    def _map_buildium_tenant(self, buildium_tenant: Dict[str, Any]) -> Dict[str, Any]:
        """Map Buildium tenant data to EstateCore format"""
        return {
            'tenant_id': str(buildium_tenant.get('Id')),
            'first_name': buildium_tenant.get('FirstName'),
            'last_name': buildium_tenant.get('LastName'),
            'email': buildium_tenant.get('Email'),
            'phone': buildium_tenant.get('PhoneNumbers', [{}])[0].get('PhoneNumber') if buildium_tenant.get('PhoneNumbers') else None,
            'move_in_date': buildium_tenant.get('MoveInDate'),
            'source_platform': 'buildium',
            'last_updated': datetime.now().isoformat()
        }
    
    def _map_buildium_lease(self, buildium_lease: Dict[str, Any]) -> Dict[str, Any]:
        """Map Buildium lease data to EstateCore format"""
        return {
            'lease_id': str(buildium_lease.get('Id')),
            'unit_id': str(buildium_lease.get('UnitId')),
            'lease_start_date': buildium_lease.get('LeaseFromDate'),
            'lease_end_date': buildium_lease.get('LeaseToDate'),
            'monthly_rent': buildium_lease.get('Rent'),
            'lease_type': buildium_lease.get('LeaseType'),
            'lease_status': buildium_lease.get('LeaseStatus'),
            'source_platform': 'buildium',
            'last_updated': datetime.now().isoformat()
        }
    
    def _map_buildium_property(self, buildium_property: Dict[str, Any]) -> Dict[str, Any]:
        """Map Buildium property data to EstateCore format"""
        address = buildium_property.get('Address', {})
        return {
            'property_id': str(buildium_property.get('Id')),
            'property_name': buildium_property.get('Name'),
            'address': address.get('AddressLine1'),
            'city': address.get('City'),
            'state': address.get('State'),
            'zip_code': address.get('PostalCode'),
            'property_type': buildium_property.get('PropertyType'),
            'source_platform': 'buildium',
            'last_updated': datetime.now().isoformat()
        }
    
    def _map_buildium_payment(self, buildium_payment: Dict[str, Any]) -> Dict[str, Any]:
        """Map Buildium payment data to EstateCore format"""
        return {
            'payment_id': str(buildium_payment.get('Id')),
            'amount': buildium_payment.get('TotalAmount'),
            'payment_date': buildium_payment.get('PaymentDate'),
            'payment_method': buildium_payment.get('PaymentMethod'),
            'status': 'completed',  # Buildium typically only shows completed payments
            'source_platform': 'buildium',
            'last_updated': datetime.now().isoformat()
        }

class MarketDataIntegration(BaseIntegration):
    """Integration for market data sources (RentSpree, Apartments.com, etc.)"""
    
    async def _authenticate(self):
        """Authenticate with market data API"""
        api_key = self.config.credentials.get('api_key')
        if not api_key:
            raise Exception("Market data API key not provided")
        
        self.auth_token = api_key
        self.session.headers.update({'X-API-Key': api_key})
        logger.info("Market data authentication configured")
    
    async def sync_tenant_data(self) -> List[Dict[str, Any]]:
        """Market data sources don't have tenant data"""
        return []
    
    async def sync_lease_data(self) -> List[Dict[str, Any]]:
        """Market data sources don't have specific lease data"""
        return []
    
    async def sync_property_data(self) -> List[Dict[str, Any]]:
        """Sync property market data"""
        return []
    
    async def sync_payment_data(self) -> List[Dict[str, Any]]:
        """Market data sources don't have payment data"""
        return []
    
    async def get_market_rents(self, zip_code: str, property_type: str, bedrooms: int) -> Dict[str, Any]:
        """Get market rent data for specific criteria"""
        endpoint = "/api/market-rents"
        
        params = {
            'zip_code': zip_code,
            'property_type': property_type,
            'bedrooms': bedrooms
        }
        
        try:
            async with self.session.get(
                f"{self.config.base_url}{endpoint}",
                params=params
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    return {
                        'zip_code': zip_code,
                        'property_type': property_type,
                        'bedrooms': bedrooms,
                        'average_rent': data.get('average_rent'),
                        'median_rent': data.get('median_rent'),
                        'rent_range': {
                            'min': data.get('min_rent'),
                            'max': data.get('max_rent')
                        },
                        'sample_size': data.get('sample_size'),
                        'last_updated': data.get('last_updated')
                    }
                else:
                    raise Exception(f"Failed to fetch market rent data: {response.status}")
                    
        except Exception as e:
            logger.error(f"Market rent data error: {str(e)}")
            return {}

class PlatformIntegrationManager:
    """
    Main integration manager for all platforms
    """
    
    def __init__(self):
        self.integrations: Dict[str, BaseIntegration] = {}
        self.sync_results: List[SyncResult] = []
        self.webhook_handlers = {}
        
        # Integration registry
        self.integration_classes = {
            'yardi': YardiIntegration,
            'appfolio': AppFolioIntegration,
            'buildium': BuildiumIntegration,
            'market_data': MarketDataIntegration
        }
    
    async def initialize_integrations(self, configs: List[IntegrationConfig]):
        """Initialize all configured integrations"""
        for config in configs:
            if not config.enabled:
                continue
                
            try:
                integration_class = self.integration_classes.get(config.platform_id.lower())
                if not integration_class:
                    logger.warning(f"No integration class found for platform: {config.platform_id}")
                    continue
                
                integration = integration_class(config)
                await integration.initialize()
                
                self.integrations[config.platform_id] = integration
                logger.info(f"Initialized integration for {config.platform_name}")
                
            except Exception as e:
                logger.error(f"Failed to initialize {config.platform_name}: {str(e)}")
    
    async def sync_all_platforms(self) -> List[SyncResult]:
        """Sync data from all configured platforms"""
        sync_results = []
        
        for platform_id, integration in self.integrations.items():
            try:
                result = await self._sync_platform(platform_id, integration)
                sync_results.append(result)
                
            except Exception as e:
                logger.error(f"Error syncing platform {platform_id}: {str(e)}")
                sync_results.append(SyncResult(
                    integration_id=platform_id,
                    sync_type='full_sync',
                    status=DataSyncStatus.FAILED,
                    records_processed=0,
                    records_successful=0,
                    records_failed=0,
                    errors=[str(e)],
                    warnings=[],
                    sync_duration_seconds=0,
                    last_sync_timestamp=datetime.now(),
                    next_sync_scheduled=datetime.now() + timedelta(hours=1)
                ))
        
        self.sync_results.extend(sync_results)
        return sync_results
    
    async def _sync_platform(self, platform_id: str, integration: BaseIntegration) -> SyncResult:
        """Sync data from a specific platform"""
        start_time = datetime.now()
        errors = []
        warnings = []
        total_processed = 0
        total_successful = 0
        
        try:
            # Sync tenant data
            tenants = await integration.sync_tenant_data()
            tenant_result = await self._process_tenant_data(platform_id, tenants)
            total_processed += len(tenants)
            total_successful += tenant_result.get('successful', 0)
            errors.extend(tenant_result.get('errors', []))
            
            # Sync lease data
            leases = await integration.sync_lease_data()
            lease_result = await self._process_lease_data(platform_id, leases)
            total_processed += len(leases)
            total_successful += lease_result.get('successful', 0)
            errors.extend(lease_result.get('errors', []))
            
            # Sync property data
            properties = await integration.sync_property_data()
            property_result = await self._process_property_data(platform_id, properties)
            total_processed += len(properties)
            total_successful += property_result.get('successful', 0)
            errors.extend(property_result.get('errors', []))
            
            # Sync payment data
            payments = await integration.sync_payment_data()
            payment_result = await self._process_payment_data(platform_id, payments)
            total_processed += len(payments)
            total_successful += payment_result.get('successful', 0)
            errors.extend(payment_result.get('errors', []))
            
        except Exception as e:
            errors.append(f"Platform sync error: {str(e)}")
        
        # Calculate sync duration
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        # Determine sync status
        if errors:
            if total_successful == 0:
                status = DataSyncStatus.FAILED
            else:
                status = DataSyncStatus.PARTIAL
        else:
            status = DataSyncStatus.SUCCESS
        
        return SyncResult(
            integration_id=platform_id,
            sync_type='full_sync',
            status=status,
            records_processed=total_processed,
            records_successful=total_successful,
            records_failed=total_processed - total_successful,
            errors=errors,
            warnings=warnings,
            sync_duration_seconds=duration,
            last_sync_timestamp=end_time,
            next_sync_scheduled=end_time + timedelta(minutes=integration.config.sync_frequency)
        )
    
    async def _process_tenant_data(self, platform_id: str, tenants: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Process and store tenant data"""
        successful = 0
        errors = []
        
        for tenant in tenants:
            try:
                # Here you would store the tenant data in your database
                # For now, we'll just simulate success
                successful += 1
                
            except Exception as e:
                errors.append(f"Failed to process tenant {tenant.get('tenant_id', 'unknown')}: {str(e)}")
        
        logger.info(f"Processed {successful}/{len(tenants)} tenants from {platform_id}")
        
        return {
            'successful': successful,
            'errors': errors
        }
    
    async def _process_lease_data(self, platform_id: str, leases: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Process and store lease data"""
        successful = 0
        errors = []
        
        for lease in leases:
            try:
                # Here you would store the lease data in your database
                # For now, we'll just simulate success
                successful += 1
                
            except Exception as e:
                errors.append(f"Failed to process lease {lease.get('lease_id', 'unknown')}: {str(e)}")
        
        logger.info(f"Processed {successful}/{len(leases)} leases from {platform_id}")
        
        return {
            'successful': successful,
            'errors': errors
        }
    
    async def _process_property_data(self, platform_id: str, properties: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Process and store property data"""
        successful = 0
        errors = []
        
        for prop in properties:
            try:
                # Here you would store the property data in your database
                # For now, we'll just simulate success
                successful += 1
                
            except Exception as e:
                errors.append(f"Failed to process property {prop.get('property_id', 'unknown')}: {str(e)}")
        
        logger.info(f"Processed {successful}/{len(properties)} properties from {platform_id}")
        
        return {
            'successful': successful,
            'errors': errors
        }
    
    async def _process_payment_data(self, platform_id: str, payments: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Process and store payment data"""
        successful = 0
        errors = []
        
        for payment in payments:
            try:
                # Here you would store the payment data in your database
                # For now, we'll just simulate success
                successful += 1
                
            except Exception as e:
                errors.append(f"Failed to process payment {payment.get('payment_id', 'unknown')}: {str(e)}")
        
        logger.info(f"Processed {successful}/{len(payments)} payments from {platform_id}")
        
        return {
            'successful': successful,
            'errors': errors
        }
    
    async def sync_specific_platform(self, platform_id: str) -> Optional[SyncResult]:
        """Sync data from a specific platform"""
        if platform_id not in self.integrations:
            logger.error(f"Platform {platform_id} not configured")
            return None
        
        integration = self.integrations[platform_id]
        return await self._sync_platform(platform_id, integration)
    
    def get_sync_status(self, platform_id: Optional[str] = None) -> Dict[str, Any]:
        """Get synchronization status for all or specific platform"""
        if platform_id:
            # Get status for specific platform
            platform_results = [r for r in self.sync_results if r.integration_id == platform_id]
            latest_result = max(platform_results, key=lambda x: x.last_sync_timestamp) if platform_results else None
            
            return {
                'platform_id': platform_id,
                'latest_sync': latest_result.to_dict() if latest_result else None,
                'total_syncs': len(platform_results),
                'sync_history': [r.to_dict() for r in platform_results[-10:]]  # Last 10 syncs
            }
        else:
            # Get status for all platforms
            platform_status = {}
            
            for integration_id in self.integrations.keys():
                platform_results = [r for r in self.sync_results if r.integration_id == integration_id]
                latest_result = max(platform_results, key=lambda x: x.last_sync_timestamp) if platform_results else None
                
                platform_status[integration_id] = {
                    'latest_sync': latest_result.to_dict() if latest_result else None,
                    'total_syncs': len(platform_results),
                    'status': latest_result.status.value if latest_result else 'never_synced'
                }
            
            return {
                'platforms': platform_status,
                'total_platforms': len(self.integrations),
                'active_platforms': len([p for p in platform_status.values() if p['status'] != 'never_synced']),
                'last_global_sync': max([r.last_sync_timestamp for r in self.sync_results]) if self.sync_results else None
            }
    
    async def handle_webhook(self, platform_id: str, webhook_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle incoming webhook from platform"""
        try:
            if platform_id not in self.integrations:
                return {'status': 'error', 'message': f'Platform {platform_id} not configured'}
            
            # Process webhook data based on platform and event type
            event_type = webhook_data.get('event_type', 'unknown')
            
            if event_type == 'tenant_updated':
                await self._handle_tenant_webhook(platform_id, webhook_data)
            elif event_type == 'lease_updated':
                await self._handle_lease_webhook(platform_id, webhook_data)
            elif event_type == 'payment_received':
                await self._handle_payment_webhook(platform_id, webhook_data)
            else:
                logger.warning(f"Unknown webhook event type: {event_type} from {platform_id}")
            
            return {'status': 'success', 'message': 'Webhook processed successfully'}
            
        except Exception as e:
            logger.error(f"Webhook processing error for {platform_id}: {str(e)}")
            return {'status': 'error', 'message': str(e)}
    
    async def _handle_tenant_webhook(self, platform_id: str, data: Dict[str, Any]):
        """Handle tenant-related webhook"""
        # Process real-time tenant updates
        pass
    
    async def _handle_lease_webhook(self, platform_id: str, data: Dict[str, Any]):
        """Handle lease-related webhook"""
        # Process real-time lease updates
        pass
    
    async def _handle_payment_webhook(self, platform_id: str, data: Dict[str, Any]):
        """Handle payment-related webhook"""
        # Process real-time payment updates
        pass
    
    async def cleanup(self):
        """Cleanup all integrations"""
        for integration in self.integrations.values():
            try:
                await integration.cleanup()
            except Exception as e:
                logger.error(f"Error cleaning up integration: {str(e)}")
        
        self.integrations.clear()
        logger.info("All integrations cleaned up")
    
    def get_integration_health(self) -> Dict[str, Any]:
        """Get health status of all integrations"""
        health_status = {}
        
        for platform_id, integration in self.integrations.items():
            # Get recent sync results
            recent_syncs = [
                r for r in self.sync_results 
                if r.integration_id == platform_id and 
                r.last_sync_timestamp > datetime.now() - timedelta(hours=24)
            ]
            
            success_rate = 0
            if recent_syncs:
                successful_syncs = len([r for r in recent_syncs if r.status == DataSyncStatus.SUCCESS])
                success_rate = successful_syncs / len(recent_syncs)
            
            health_status[platform_id] = {
                'status': 'healthy' if success_rate > 0.8 else 'degraded' if success_rate > 0.5 else 'unhealthy',
                'success_rate_24h': success_rate,
                'last_successful_sync': max([r.last_sync_timestamp for r in recent_syncs 
                                           if r.status == DataSyncStatus.SUCCESS], default=None),
                'sync_frequency_minutes': integration.config.sync_frequency,
                'rate_limit_status': 'normal'  # This would check actual rate limit status
            }
        
        return health_status