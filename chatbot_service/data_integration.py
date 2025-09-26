"""
Data Integration Service for EstateCore Tenant Chatbot

Integrates with all property management systems (Yardi, RealPage, AppFolio,
RentManager, Buildium, QuickBooks) to provide unified data access for the chatbot.
"""

import logging
import json
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
import redis
from abc import ABC, abstractmethod

# Import property management integrations
try:
    from yardi_integration.yardi_integration_service import YardiIntegrationService
    from realpage_integration.realpage_integration_service import RealPageIntegrationService
    from appfolio_integration.appfolio_integration_service import AppFolioIntegrationService
    from rentmanager_integration.rentmanager_integration_service import RentManagerIntegrationService
    from buildium_integration.buildium_integration_service import BuildiumIntegrationService
    from quickbooks_integration.quickbooks_integration_service import QuickBooksIntegrationService
except ImportError as e:
    logging.warning(f"Some property management integrations not available: {e}")

@dataclass
class TenantData:
    """Unified tenant data structure"""
    tenant_id: str
    user_id: str
    property_id: str
    unit_number: str
    tenant_name: str
    email: str
    phone: Optional[str] = None
    lease_start_date: Optional[datetime] = None
    lease_end_date: Optional[datetime] = None
    monthly_rent: Optional[float] = None
    current_balance: float = 0.0
    last_payment: Optional[Dict] = None
    emergency_contact: Optional[Dict] = None
    move_in_date: Optional[datetime] = None

@dataclass
class PropertyData:
    """Unified property data structure"""
    property_id: str
    property_name: str
    address: str
    property_type: str
    total_units: int
    amenities: List[str]
    office_hours: str
    office_phone: str
    emergency_phone: str
    office_email: str
    office_address: str
    parking_info: Optional[Dict] = None
    pet_policy: Optional[Dict] = None
    amenity_hours: Optional[Dict] = None

@dataclass
class AccountData:
    """Unified account/financial data"""
    account_id: str
    tenant_id: str
    current_balance: float
    last_payment_amount: float
    last_payment_date: Optional[datetime]
    next_due_date: Optional[datetime]
    payment_history: List[Dict]
    outstanding_charges: List[Dict]
    payment_methods: List[str]
    auto_pay_enabled: bool = False

class PropertyManagementIntegration(ABC):
    """Abstract base class for property management integrations"""
    
    @abstractmethod
    async def get_tenant_data(self, tenant_id: str) -> Optional[TenantData]:
        """Get tenant data"""
        pass
    
    @abstractmethod
    async def get_property_data(self, property_id: str) -> Optional[PropertyData]:
        """Get property data"""
        pass
    
    @abstractmethod
    async def get_account_data(self, tenant_id: str) -> Optional[AccountData]:
        """Get account/financial data"""
        pass
    
    @abstractmethod
    async def submit_maintenance_request(self, tenant_id: str, request_data: Dict) -> Dict:
        """Submit maintenance request"""
        pass
    
    @abstractmethod
    async def get_maintenance_requests(self, tenant_id: str) -> List[Dict]:
        """Get maintenance request history"""
        pass

class DataIntegrationService:
    """
    Unified data integration service for all property management systems
    """
    
    def __init__(self, redis_client: Optional[redis.Redis] = None):
        """
        Initialize Data Integration Service
        
        Args:
            redis_client: Redis client for caching
        """
        self.logger = logging.getLogger(__name__)
        
        # Redis for caching
        self.redis = redis_client
        if not self.redis:
            try:
                self.redis = redis.Redis(host='localhost', port=6379, db=1, decode_responses=True)
                self.redis.ping()
            except Exception as e:
                self.logger.warning(f"Redis not available: {e}")
                self.redis = None
        
        # Cache configuration
        self.cache_ttl = {
            'tenant_data': 300,      # 5 minutes
            'property_data': 1800,   # 30 minutes
            'account_data': 60,      # 1 minute
            'maintenance_data': 180, # 3 minutes
        }
        
        # Initialize property management integrations
        self.integrations: Dict[str, PropertyManagementIntegration] = {}
        self._initialize_integrations()
        
        # Data mapping and transformation
        self.data_mappers = {
            'yardi': YardiDataMapper(),
            'realpage': RealPageDataMapper(),
            'appfolio': AppFolioDataMapper(),
            'rentmanager': RentManagerDataMapper(),
            'buildium': BuildiumDataMapper(),
            'quickbooks': QuickBooksDataMapper()
        }
        
        self.logger.info("Data Integration Service initialized")
    
    def _initialize_integrations(self):
        """Initialize all property management system integrations"""
        try:
            # Initialize available integrations
            integration_classes = {
                'yardi': YardiIntegrationService,
                'realpage': RealPageIntegrationService,
                'appfolio': AppFolioIntegrationService,
                'rentmanager': RentManagerIntegrationService,
                'buildium': BuildiumIntegrationService,
                'quickbooks': QuickBooksIntegrationService
            }
            
            for system_name, integration_class in integration_classes.items():
                try:
                    # This would typically be configured with credentials
                    integration = integration_class()
                    self.integrations[system_name] = integration
                    self.logger.info(f"Initialized {system_name} integration")
                except Exception as e:
                    self.logger.warning(f"Failed to initialize {system_name} integration: {e}")
        
        except Exception as e:
            self.logger.error(f"Error initializing integrations: {e}")
    
    def get_user_context(self, user_id: str) -> Dict[str, Any]:
        """
        Get comprehensive user context from all integrated systems
        
        Args:
            user_id: User identifier
            
        Returns:
            Unified user context dictionary
        """
        try:
            cache_key = f"user_context:{user_id}"
            
            # Try cache first
            if self.redis:
                cached_data = self.redis.get(cache_key)
                if cached_data:
                    return json.loads(cached_data)
            
            # Fetch from database or property management systems
            user_context = self._fetch_user_context(user_id)
            
            # Cache result
            if self.redis and user_context:
                self.redis.setex(
                    cache_key, 
                    self.cache_ttl['tenant_data'], 
                    json.dumps(user_context, default=str)
                )
            
            return user_context or {}
            
        except Exception as e:
            self.logger.error(f"Error getting user context: {e}")
            return {}
    
    def get_tenant_context(self, user_id: str) -> Optional[TenantData]:
        """
        Get unified tenant data
        
        Args:
            user_id: User identifier
            
        Returns:
            TenantData object or None
        """
        try:
            # Determine which property management system to use
            pm_system = self._get_user_property_system(user_id)
            if not pm_system or pm_system not in self.integrations:
                return None
            
            # Get tenant ID mapping
            tenant_id = self._get_tenant_id_mapping(user_id, pm_system)
            if not tenant_id:
                return None
            
            # Fetch from appropriate system
            integration = self.integrations[pm_system]
            tenant_data = asyncio.run(integration.get_tenant_data(tenant_id))
            
            return tenant_data
            
        except Exception as e:
            self.logger.error(f"Error getting tenant context: {e}")
            return None
    
    def get_property_context(self, property_id: str) -> Optional[PropertyData]:
        """
        Get unified property data
        
        Args:
            property_id: Property identifier
            
        Returns:
            PropertyData object or None
        """
        try:
            cache_key = f"property_context:{property_id}"
            
            # Try cache first
            if self.redis:
                cached_data = self.redis.get(cache_key)
                if cached_data:
                    data = json.loads(cached_data)
                    return PropertyData(**data)
            
            # Determine which system to use
            pm_system = self._get_property_system(property_id)
            if not pm_system or pm_system not in self.integrations:
                return None
            
            # Fetch from appropriate system
            integration = self.integrations[pm_system]
            property_data = asyncio.run(integration.get_property_data(property_id))
            
            # Cache result
            if self.redis and property_data:
                self.redis.setex(
                    cache_key,
                    self.cache_ttl['property_data'],
                    json.dumps(property_data.__dict__, default=str)
                )
            
            return property_data
            
        except Exception as e:
            self.logger.error(f"Error getting property context: {e}")
            return None
    
    def get_account_info(self, user_id: str) -> Optional[AccountData]:
        """
        Get account/financial information
        
        Args:
            user_id: User identifier
            
        Returns:
            AccountData object or None
        """
        try:
            cache_key = f"account_data:{user_id}"
            
            # Try cache first
            if self.redis:
                cached_data = self.redis.get(cache_key)
                if cached_data:
                    data = json.loads(cached_data)
                    # Convert date strings back to datetime objects
                    if data.get('last_payment_date'):
                        data['last_payment_date'] = datetime.fromisoformat(data['last_payment_date'])
                    if data.get('next_due_date'):
                        data['next_due_date'] = datetime.fromisoformat(data['next_due_date'])
                    return AccountData(**data)
            
            # Determine system and fetch data
            pm_system = self._get_user_property_system(user_id)
            if not pm_system or pm_system not in self.integrations:
                return None
            
            tenant_id = self._get_tenant_id_mapping(user_id, pm_system)
            if not tenant_id:
                return None
            
            integration = self.integrations[pm_system]
            account_data = asyncio.run(integration.get_account_data(tenant_id))
            
            # Cache result
            if self.redis and account_data:
                self.redis.setex(
                    cache_key,
                    self.cache_ttl['account_data'],
                    json.dumps(account_data.__dict__, default=str)
                )
            
            return account_data
            
        except Exception as e:
            self.logger.error(f"Error getting account info: {e}")
            return None
    
    async def submit_maintenance_request(self, user_id: str, request_data: Dict) -> Dict[str, Any]:
        """
        Submit maintenance request to appropriate property management system
        
        Args:
            user_id: User identifier
            request_data: Maintenance request data
            
        Returns:
            Result dictionary
        """
        try:
            # Determine system
            pm_system = self._get_user_property_system(user_id)
            if not pm_system or pm_system not in self.integrations:
                return {'success': False, 'error': 'No property management system found'}
            
            tenant_id = self._get_tenant_id_mapping(user_id, pm_system)
            if not tenant_id:
                return {'success': False, 'error': 'Tenant mapping not found'}
            
            # Submit to appropriate system
            integration = self.integrations[pm_system]
            result = await integration.submit_maintenance_request(tenant_id, request_data)
            
            # Clear cache for maintenance data
            if self.redis:
                self.redis.delete(f"maintenance_requests:{user_id}")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error submitting maintenance request: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_maintenance_requests(self, user_id: str) -> List[Dict]:
        """
        Get maintenance request history
        
        Args:
            user_id: User identifier
            
        Returns:
            List of maintenance requests
        """
        try:
            cache_key = f"maintenance_requests:{user_id}"
            
            # Try cache first
            if self.redis:
                cached_data = self.redis.get(cache_key)
                if cached_data:
                    return json.loads(cached_data)
            
            # Fetch from system
            pm_system = self._get_user_property_system(user_id)
            if not pm_system or pm_system not in self.integrations:
                return []
            
            tenant_id = self._get_tenant_id_mapping(user_id, pm_system)
            if not tenant_id:
                return []
            
            integration = self.integrations[pm_system]
            requests = asyncio.run(integration.get_maintenance_requests(tenant_id))
            
            # Cache result
            if self.redis:
                self.redis.setex(
                    cache_key,
                    self.cache_ttl['maintenance_data'],
                    json.dumps(requests, default=str)
                )
            
            return requests or []
            
        except Exception as e:
            self.logger.error(f"Error getting maintenance requests: {e}")
            return []
    
    def search_tenants(self, query: str, limit: int = 20) -> List[Dict]:
        """
        Search for tenants across all systems
        
        Args:
            query: Search query
            limit: Maximum results to return
            
        Returns:
            List of tenant search results
        """
        try:
            results = []
            
            # Search across all integrated systems
            for system_name, integration in self.integrations.items():
                try:
                    # This would need to be implemented in each integration
                    system_results = []  # integration.search_tenants(query, limit)
                    results.extend(system_results)
                except Exception as e:
                    self.logger.error(f"Error searching {system_name}: {e}")
            
            # Deduplicate and sort results
            unique_results = []
            seen = set()
            
            for result in results:
                key = f"{result.get('tenant_id', '')}:{result.get('email', '')}"
                if key not in seen:
                    seen.add(key)
                    unique_results.append(result)
            
            return unique_results[:limit]
            
        except Exception as e:
            self.logger.error(f"Error searching tenants: {e}")
            return []
    
    def _fetch_user_context(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Fetch user context from database or PM systems"""
        # This would typically query your EstateCore database
        # For now, return a placeholder structure
        return {
            'user_id': user_id,
            'tenant_id': f'tenant_{user_id}',
            'property_id': f'property_{user_id}',
            'unit_number': '101',
            'user_name': 'Tenant User',
            'email': 'tenant@example.com',
            'phone': '(555) 123-4567',
            'property_management_system': 'yardi'  # This would be looked up
        }
    
    def _get_user_property_system(self, user_id: str) -> Optional[str]:
        """Determine which property management system a user belongs to"""
        # This would query your database to find the PM system
        # For now, return a default
        user_context = self._fetch_user_context(user_id)
        return user_context.get('property_management_system') if user_context else None
    
    def _get_property_system(self, property_id: str) -> Optional[str]:
        """Determine which property management system a property belongs to"""
        # This would query your database
        return 'yardi'  # Default for now
    
    def _get_tenant_id_mapping(self, user_id: str, pm_system: str) -> Optional[str]:
        """Get tenant ID mapping for specific PM system"""
        # This would look up the tenant ID in the specific PM system
        return f'{pm_system}_tenant_{user_id}'
    
    def invalidate_cache(self, user_id: str, cache_type: Optional[str] = None):
        """
        Invalidate cached data for a user
        
        Args:
            user_id: User identifier
            cache_type: Specific cache type to invalidate (None for all)
        """
        if not self.redis:
            return
        
        try:
            if cache_type:
                cache_key = f"{cache_type}:{user_id}"
                self.redis.delete(cache_key)
            else:
                # Clear all cache types for user
                for cache_name in self.cache_ttl.keys():
                    cache_key = f"{cache_name}:{user_id}"
                    self.redis.delete(cache_key)
                
                # Also clear user context
                self.redis.delete(f"user_context:{user_id}")
            
            self.logger.debug(f"Cache invalidated for user {user_id}, type: {cache_type}")
            
        except Exception as e:
            self.logger.error(f"Error invalidating cache: {e}")
    
    def get_integration_health(self) -> Dict[str, Any]:
        """Get health status of all integrations"""
        health_status = {}
        
        for system_name, integration in self.integrations.items():
            try:
                # Test connection (this would need to be implemented in each integration)
                # For now, just mark as healthy if initialized
                health_status[system_name] = {
                    'status': 'healthy',
                    'last_check': datetime.now().isoformat()
                }
            except Exception as e:
                health_status[system_name] = {
                    'status': 'unhealthy',
                    'error': str(e),
                    'last_check': datetime.now().isoformat()
                }
        
        return health_status

# Data Mapper Classes (simplified implementations)
class YardiDataMapper:
    """Maps Yardi data to unified format"""
    def map_tenant_data(self, yardi_data: Dict) -> TenantData:
        # Implementation would map Yardi-specific fields
        return TenantData(**yardi_data)

class RealPageDataMapper:
    """Maps RealPage data to unified format"""  
    def map_tenant_data(self, realpage_data: Dict) -> TenantData:
        # Implementation would map RealPage-specific fields
        return TenantData(**realpage_data)

class AppFolioDataMapper:
    """Maps AppFolio data to unified format"""
    def map_tenant_data(self, appfolio_data: Dict) -> TenantData:
        # Implementation would map AppFolio-specific fields
        return TenantData(**appfolio_data)

class RentManagerDataMapper:
    """Maps RentManager data to unified format"""
    def map_tenant_data(self, rentmanager_data: Dict) -> TenantData:
        # Implementation would map RentManager-specific fields
        return TenantData(**rentmanager_data)

class BuildiumDataMapper:
    """Maps Buildium data to unified format"""
    def map_tenant_data(self, buildium_data: Dict) -> TenantData:
        # Implementation would map Buildium-specific fields
        return TenantData(**buildium_data)

class QuickBooksDataMapper:
    """Maps QuickBooks data to unified format"""
    def map_account_data(self, quickbooks_data: Dict) -> AccountData:
        # Implementation would map QuickBooks-specific fields
        return AccountData(**quickbooks_data)