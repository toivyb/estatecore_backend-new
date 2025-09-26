"""
Multi-Platform Data Integration Service for Compliance Monitoring
Real-time synchronization with property management platforms and external systems
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, asdict
from abc import ABC, abstractmethod
import aiohttp
import websockets
from sqlalchemy.orm import sessionmaker
from concurrent.futures import ThreadPoolExecutor
import redis
from celery import Celery
import hashlib

from models.base import db
from models.compliance import (
    ComplianceIntegration, ComplianceMonitoringRule, ComplianceViolation,
    ComplianceRequirement, ViolationSeverity, ComplianceStatus
)
from ai_modules.compliance.ai_compliance_monitor import get_ai_compliance_monitor


logger = logging.getLogger(__name__)


@dataclass
class IntegrationEvent:
    """Data structure for integration events"""
    source_system: str
    event_type: str
    property_id: str
    tenant_id: Optional[str]
    timestamp: datetime
    data: Dict[str, Any]
    compliance_relevant: bool = False


@dataclass
class ComplianceDataPoint:
    """Standardized compliance data point"""
    property_id: str
    data_type: str  # tenant_application, lease_agreement, maintenance_request, etc.
    source: str
    timestamp: datetime
    data: Dict[str, Any]
    risk_indicators: List[str] = None
    confidence_score: float = 1.0


class DataIntegrationInterface(ABC):
    """Abstract interface for data integration adapters"""
    
    @abstractmethod
    async def connect(self) -> bool:
        """Establish connection to external system"""
        pass
    
    @abstractmethod
    async def sync_data(self, since: datetime = None) -> List[ComplianceDataPoint]:
        """Sync data from external system"""
        pass
    
    @abstractmethod
    async def setup_real_time_monitoring(self, callback: Callable) -> bool:
        """Setup real-time data monitoring"""
        pass
    
    @abstractmethod
    def get_supported_data_types(self) -> List[str]:
        """Get list of supported data types"""
        pass


class YardiIntegrationAdapter(DataIntegrationInterface):
    """Integration adapter for Yardi property management system"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.base_url = config.get('base_url')
        self.api_key = config.get('api_key')
        self.session = None
        
    async def connect(self) -> bool:
        """Connect to Yardi API"""
        try:
            self.session = aiohttp.ClientSession(
                headers={
                    'Authorization': f'Bearer {self.api_key}',
                    'Content-Type': 'application/json'
                }
            )
            
            # Test connection
            async with self.session.get(f'{self.base_url}/api/v1/health') as response:
                if response.status == 200:
                    logger.info("Successfully connected to Yardi")
                    return True
                else:
                    logger.error(f"Failed to connect to Yardi: {response.status}")
                    return False
                    
        except Exception as e:
            logger.error(f"Error connecting to Yardi: {e}")
            return False
    
    async def sync_data(self, since: datetime = None) -> List[ComplianceDataPoint]:
        """Sync compliance-relevant data from Yardi"""
        data_points = []
        
        try:
            if not since:
                since = datetime.now() - timedelta(days=1)
            
            # Sync tenant applications
            applications = await self._fetch_tenant_applications(since)
            data_points.extend(applications)
            
            # Sync lease agreements
            leases = await self._fetch_lease_agreements(since)
            data_points.extend(leases)
            
            # Sync maintenance requests
            maintenance = await self._fetch_maintenance_requests(since)
            data_points.extend(maintenance)
            
            # Sync inspection reports
            inspections = await self._fetch_inspections(since)
            data_points.extend(inspections)
            
            logger.info(f"Synced {len(data_points)} data points from Yardi")
            return data_points
            
        except Exception as e:
            logger.error(f"Error syncing Yardi data: {e}")
            return []
    
    async def _fetch_tenant_applications(self, since: datetime) -> List[ComplianceDataPoint]:
        """Fetch tenant application data"""
        data_points = []
        
        try:
            url = f'{self.base_url}/api/v1/applications'
            params = {'modified_since': since.isoformat()}
            
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    applications = await response.json()
                    
                    for app in applications.get('data', []):
                        # Analyze application for compliance issues
                        risk_indicators = self._analyze_application_compliance(app)
                        
                        data_point = ComplianceDataPoint(
                            property_id=app.get('property_id'),
                            data_type='tenant_application',
                            source='yardi',
                            timestamp=datetime.fromisoformat(app.get('created_at')),
                            data=app,
                            risk_indicators=risk_indicators,
                            confidence_score=0.9
                        )
                        data_points.append(data_point)
                        
        except Exception as e:
            logger.error(f"Error fetching Yardi applications: {e}")
        
        return data_points
    
    async def _fetch_lease_agreements(self, since: datetime) -> List[ComplianceDataPoint]:
        """Fetch lease agreement data"""
        data_points = []
        
        try:
            url = f'{self.base_url}/api/v1/leases'
            params = {'modified_since': since.isoformat()}
            
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    leases = await response.json()
                    
                    for lease in leases.get('data', []):
                        # Analyze lease for compliance issues
                        risk_indicators = self._analyze_lease_compliance(lease)
                        
                        data_point = ComplianceDataPoint(
                            property_id=lease.get('property_id'),
                            data_type='lease_agreement',
                            source='yardi',
                            timestamp=datetime.fromisoformat(lease.get('created_at')),
                            data=lease,
                            risk_indicators=risk_indicators,
                            confidence_score=0.95
                        )
                        data_points.append(data_point)
                        
        except Exception as e:
            logger.error(f"Error fetching Yardi leases: {e}")
        
        return data_points
    
    async def _fetch_maintenance_requests(self, since: datetime) -> List[ComplianceDataPoint]:
        """Fetch maintenance request data"""
        data_points = []
        
        try:
            url = f'{self.base_url}/api/v1/maintenance'
            params = {'modified_since': since.isoformat()}
            
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    requests = await response.json()
                    
                    for request in requests.get('data', []):
                        # Analyze maintenance request for compliance issues
                        risk_indicators = self._analyze_maintenance_compliance(request)
                        
                        data_point = ComplianceDataPoint(
                            property_id=request.get('property_id'),
                            data_type='maintenance_request',
                            source='yardi',
                            timestamp=datetime.fromisoformat(request.get('created_at')),
                            data=request,
                            risk_indicators=risk_indicators,
                            confidence_score=0.85
                        )
                        data_points.append(data_point)
                        
        except Exception as e:
            logger.error(f"Error fetching Yardi maintenance: {e}")
        
        return data_points
    
    async def _fetch_inspections(self, since: datetime) -> List[ComplianceDataPoint]:
        """Fetch inspection data"""
        data_points = []
        
        try:
            url = f'{self.base_url}/api/v1/inspections'
            params = {'modified_since': since.isoformat()}
            
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    inspections = await response.json()
                    
                    for inspection in inspections.get('data', []):
                        # Analyze inspection for compliance issues
                        risk_indicators = self._analyze_inspection_compliance(inspection)
                        
                        data_point = ComplianceDataPoint(
                            property_id=inspection.get('property_id'),
                            data_type='inspection_report',
                            source='yardi',
                            timestamp=datetime.fromisoformat(inspection.get('inspection_date')),
                            data=inspection,
                            risk_indicators=risk_indicators,
                            confidence_score=0.95
                        )
                        data_points.append(data_point)
                        
        except Exception as e:
            logger.error(f"Error fetching Yardi inspections: {e}")
        
        return data_points
    
    def _analyze_application_compliance(self, application: Dict) -> List[str]:
        """Analyze tenant application for compliance risks"""
        risk_indicators = []
        
        # Check for potential fair housing issues
        if 'rejection_reason' in application:
            reason = application['rejection_reason'].lower()
            if any(keyword in reason for keyword in ['family', 'children', 'disability', 'race', 'religion']):
                risk_indicators.append('Potential fair housing violation in rejection reason')
        
        # Check income requirements
        if 'income_requirement' in application:
            income_req = application.get('income_requirement', 0)
            rent = application.get('monthly_rent', 0)
            if rent > 0 and income_req / rent > 3.5:  # Unusually high income requirement
                risk_indicators.append('High income requirement may violate fair housing')
        
        return risk_indicators
    
    def _analyze_lease_compliance(self, lease: Dict) -> List[str]:
        """Analyze lease agreement for compliance risks"""
        risk_indicators = []
        
        # Check lease terms
        lease_text = lease.get('terms', '').lower()
        
        # Look for discriminatory clauses
        discriminatory_terms = ['no children', 'adults only', 'no pets allowed', 'english only']
        for term in discriminatory_terms:
            if term in lease_text:
                risk_indicators.append(f'Potentially discriminatory lease clause: {term}')
        
        # Check for required addendums
        if lease.get('affordable_housing_program') == 'Section 8':
            if 'section_8_addendum' not in lease.get('addendums', []):
                risk_indicators.append('Missing Section 8 lease addendum')
        
        return risk_indicators
    
    def _analyze_maintenance_compliance(self, request: Dict) -> List[str]:
        """Analyze maintenance request for compliance risks"""
        risk_indicators = []
        
        description = request.get('description', '').lower()
        
        # Check for safety issues
        safety_keywords = ['gas leak', 'electrical', 'fire', 'carbon monoxide', 'mold', 'water damage']
        for keyword in safety_keywords:
            if keyword in description:
                risk_indicators.append(f'Safety-related maintenance issue: {keyword}')
        
        # Check response time for urgent issues
        if request.get('priority') == 'urgent':
            created_date = datetime.fromisoformat(request.get('created_at'))
            if datetime.now() - created_date > timedelta(hours=24):
                risk_indicators.append('Delayed response to urgent maintenance request')
        
        return risk_indicators
    
    def _analyze_inspection_compliance(self, inspection: Dict) -> List[str]:
        """Analyze inspection for compliance risks"""
        risk_indicators = []
        
        # Check inspection results
        if inspection.get('status') == 'failed':
            risk_indicators.append('Failed inspection - compliance violation likely')
        
        # Check for specific violations
        violations = inspection.get('violations', [])
        for violation in violations:
            if violation.get('severity') in ['critical', 'high']:
                risk_indicators.append(f'Critical violation: {violation.get("description")}')
        
        return risk_indicators
    
    async def setup_real_time_monitoring(self, callback: Callable) -> bool:
        """Setup real-time monitoring via webhooks"""
        try:
            # Register webhooks for relevant events
            webhook_url = self.config.get('webhook_url')
            if not webhook_url:
                logger.warning("No webhook URL configured for Yardi")
                return False
            
            # This would register webhooks with Yardi
            # Implementation depends on Yardi's webhook system
            logger.info("Real-time monitoring setup for Yardi")
            return True
            
        except Exception as e:
            logger.error(f"Error setting up Yardi real-time monitoring: {e}")
            return False
    
    def get_supported_data_types(self) -> List[str]:
        """Get supported data types"""
        return ['tenant_application', 'lease_agreement', 'maintenance_request', 'inspection_report']


class AppFolioIntegrationAdapter(DataIntegrationInterface):
    """Integration adapter for AppFolio property management system"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.base_url = config.get('base_url')
        self.api_key = config.get('api_key')
        self.session = None
    
    async def connect(self) -> bool:
        """Connect to AppFolio API"""
        try:
            self.session = aiohttp.ClientSession(
                headers={
                    'Authorization': f'Bearer {self.api_key}',
                    'Content-Type': 'application/json'
                }
            )
            
            # Test connection
            async with self.session.get(f'{self.base_url}/api/v1/properties') as response:
                if response.status == 200:
                    logger.info("Successfully connected to AppFolio")
                    return True
                else:
                    logger.error(f"Failed to connect to AppFolio: {response.status}")
                    return False
                    
        except Exception as e:
            logger.error(f"Error connecting to AppFolio: {e}")
            return False
    
    async def sync_data(self, since: datetime = None) -> List[ComplianceDataPoint]:
        """Sync compliance-relevant data from AppFolio"""
        # Similar implementation to Yardi but with AppFolio API structure
        data_points = []
        
        try:
            if not since:
                since = datetime.now() - timedelta(days=1)
            
            # Implementation would be similar to Yardi but adapted for AppFolio API
            logger.info(f"Synced {len(data_points)} data points from AppFolio")
            return data_points
            
        except Exception as e:
            logger.error(f"Error syncing AppFolio data: {e}")
            return []
    
    async def setup_real_time_monitoring(self, callback: Callable) -> bool:
        """Setup real-time monitoring for AppFolio"""
        # Implementation for AppFolio webhooks
        return True
    
    def get_supported_data_types(self) -> List[str]:
        """Get supported data types"""
        return ['tenant_application', 'lease_agreement', 'maintenance_request', 'inspection_report']


class ComplianceDataProcessor:
    """Process and analyze compliance data from integrations"""
    
    def __init__(self):
        self.ai_monitor = get_ai_compliance_monitor()
        self.session = db.session
        
        # Cache for processed data to avoid duplicates
        self.processed_cache = {}
    
    async def process_data_points(self, data_points: List[ComplianceDataPoint]) -> List[IntegrationEvent]:
        """Process compliance data points and generate events"""
        events = []
        
        try:
            for data_point in data_points:
                # Check if already processed
                data_hash = self._calculate_data_hash(data_point)
                if data_hash in self.processed_cache:
                    continue
                
                # Process data point
                event = await self._process_single_data_point(data_point)
                if event:
                    events.append(event)
                    self.processed_cache[data_hash] = datetime.now()
            
            # Clean old cache entries
            await self._clean_cache()
            
            logger.info(f"Processed {len(data_points)} data points, generated {len(events)} events")
            return events
            
        except Exception as e:
            logger.error(f"Error processing data points: {e}")
            return []
    
    async def _process_single_data_point(self, data_point: ComplianceDataPoint) -> Optional[IntegrationEvent]:
        """Process a single data point"""
        try:
            # Analyze data point for compliance relevance
            compliance_relevant = await self._is_compliance_relevant(data_point)
            
            if compliance_relevant:
                # Create compliance event
                event = IntegrationEvent(
                    source_system=data_point.source,
                    event_type=f'{data_point.data_type}_update',
                    property_id=data_point.property_id,
                    tenant_id=data_point.data.get('tenant_id'),
                    timestamp=data_point.timestamp,
                    data=data_point.data,
                    compliance_relevant=True
                )
                
                # Trigger compliance analysis if high risk
                if data_point.risk_indicators and len(data_point.risk_indicators) > 0:
                    await self._trigger_compliance_analysis(data_point)
                
                return event
            
            return None
            
        except Exception as e:
            logger.error(f"Error processing data point: {e}")
            return None
    
    async def _is_compliance_relevant(self, data_point: ComplianceDataPoint) -> bool:
        """Determine if data point is compliance relevant"""
        # Data points with risk indicators are always relevant
        if data_point.risk_indicators and len(data_point.risk_indicators) > 0:
            return True
        
        # Certain data types are always compliance relevant
        high_relevance_types = ['inspection_report', 'violation_notice', 'complaint']
        if data_point.data_type in high_relevance_types:
            return True
        
        # Use AI to analyze content
        try:
            content = json.dumps(data_point.data)
            analysis = self.ai_monitor.nlp_processor.analyze_document_compliance(content)
            
            # Consider relevant if compliance score is low or violations detected
            if analysis['compliance_score'] < 80 or len(analysis['violations_detected']) > 0:
                return True
                
        except Exception as e:
            logger.debug(f"Error in AI relevance analysis: {e}")
        
        return False
    
    async def _trigger_compliance_analysis(self, data_point: ComplianceDataPoint):
        """Trigger detailed compliance analysis for high-risk data"""
        try:
            # Run AI analysis on the property
            risk_assessment = self.ai_monitor.analyze_property_compliance(data_point.property_id)
            
            # Create violation if risk is high
            if risk_assessment.risk_score > 75:
                await self._create_potential_violation(data_point, risk_assessment)
            
        except Exception as e:
            logger.error(f"Error triggering compliance analysis: {e}")
    
    async def _create_potential_violation(self, data_point: ComplianceDataPoint, risk_assessment):
        """Create a potential compliance violation record"""
        try:
            # Check if similar violation already exists
            existing = self.session.query(ComplianceViolation).filter_by(
                property_id=data_point.property_id,
                violation_type=data_point.data_type,
                is_resolved=False
            ).first()
            
            if existing:
                return  # Don't create duplicate
            
            # Create new violation
            violation = ComplianceViolation(
                property_id=data_point.property_id,
                violation_type=data_point.data_type,
                title=f'Potential {data_point.data_type} violation',
                description=f'Risk indicators detected: {", ".join(data_point.risk_indicators or [])}',
                severity=ViolationSeverity.MEDIUM,  # Default to medium, can be adjusted
                detected_date=datetime.now(),
                detection_method='AI_Integration_Analysis',
                detection_confidence=data_point.confidence_score,
                data_sources=[data_point.source],
                ai_recommendations=risk_assessment.recommendations,
                pattern_indicators=data_point.risk_indicators
            )
            
            self.session.add(violation)
            self.session.commit()
            
            logger.info(f"Created potential violation for property {data_point.property_id}")
            
        except Exception as e:
            logger.error(f"Error creating potential violation: {e}")
            self.session.rollback()
    
    def _calculate_data_hash(self, data_point: ComplianceDataPoint) -> str:
        """Calculate hash for data point to detect duplicates"""
        content = f"{data_point.property_id}_{data_point.data_type}_{data_point.timestamp.isoformat()}"
        return hashlib.md5(content.encode()).hexdigest()
    
    async def _clean_cache(self):
        """Clean old entries from processed cache"""
        cutoff = datetime.now() - timedelta(hours=24)
        self.processed_cache = {
            k: v for k, v in self.processed_cache.items() 
            if v > cutoff
        }


class ComplianceIntegrationService:
    """Main service for managing compliance data integrations"""
    
    def __init__(self):
        self.session = db.session
        self.adapters = {}
        self.data_processor = ComplianceDataProcessor()
        
        # Redis for real-time event handling
        self.redis_client = None
        try:
            self.redis_client = redis.Redis(host='localhost', port=6379, db=0)
        except Exception as e:
            logger.warning(f"Redis not available: {e}")
        
        # Celery for background tasks
        self.celery_app = None
        try:
            self.celery_app = Celery('compliance_integration')
        except Exception as e:
            logger.warning(f"Celery not available: {e}")
    
    async def initialize_integrations(self) -> bool:
        """Initialize all configured integrations"""
        try:
            # Get integration configurations from database
            integrations = self.session.query(ComplianceIntegration).filter_by(
                is_active=True
            ).all()
            
            for integration in integrations:
                success = await self._setup_integration(integration)
                if success:
                    logger.info(f"Successfully initialized {integration.integration_name}")
                else:
                    logger.error(f"Failed to initialize {integration.integration_name}")
            
            logger.info(f"Initialized {len(self.adapters)} integrations")
            return len(self.adapters) > 0
            
        except Exception as e:
            logger.error(f"Error initializing integrations: {e}")
            return False
    
    async def _setup_integration(self, integration: ComplianceIntegration) -> bool:
        """Setup a single integration"""
        try:
            # Create appropriate adapter based on integration type
            adapter = None
            
            if integration.integration_name.lower() == 'yardi':
                config = self._decrypt_credentials(integration.credentials)
                config['base_url'] = integration.endpoint_url
                adapter = YardiIntegrationAdapter(config)
            
            elif integration.integration_name.lower() == 'appfolio':
                config = self._decrypt_credentials(integration.credentials)
                config['base_url'] = integration.endpoint_url
                adapter = AppFolioIntegrationAdapter(config)
            
            # Add more integration types here
            
            if adapter:
                # Test connection
                if await adapter.connect():
                    self.adapters[integration.id] = {
                        'adapter': adapter,
                        'config': integration,
                        'last_sync': None
                    }
                    
                    # Setup real-time monitoring
                    await adapter.setup_real_time_monitoring(self._handle_real_time_event)
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error setting up integration {integration.integration_name}: {e}")
            return False
    
    async def sync_all_integrations(self) -> Dict[str, int]:
        """Sync data from all active integrations"""
        results = {}
        
        try:
            tasks = []
            for integration_id, integration_data in self.adapters.items():
                task = self._sync_single_integration(integration_id, integration_data)
                tasks.append(task)
            
            # Run all syncs concurrently
            sync_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for i, (integration_id, _) in enumerate(self.adapters.items()):
                result = sync_results[i]
                if isinstance(result, Exception):
                    logger.error(f"Sync failed for integration {integration_id}: {result}")
                    results[integration_id] = 0
                else:
                    results[integration_id] = result
            
            total_synced = sum(results.values())
            logger.info(f"Synced {total_synced} total data points from {len(results)} integrations")
            
            return results
            
        except Exception as e:
            logger.error(f"Error syncing integrations: {e}")
            return {}
    
    async def _sync_single_integration(self, integration_id: str, integration_data: Dict) -> int:
        """Sync data from a single integration"""
        try:
            adapter = integration_data['adapter']
            config = integration_data['config']
            
            # Determine sync window
            since = integration_data['last_sync']
            if not since:
                since = datetime.now() - timedelta(days=config.sync_frequency or 1)
            
            # Sync data
            data_points = await adapter.sync_data(since)
            
            # Process data points
            events = await self.data_processor.process_data_points(data_points)
            
            # Update last sync time
            integration_data['last_sync'] = datetime.now()
            config.last_sync = datetime.now()
            self.session.commit()
            
            # Publish events to Redis if available
            if self.redis_client and events:
                for event in events:
                    await self._publish_event(event)
            
            return len(data_points)
            
        except Exception as e:
            logger.error(f"Error syncing integration {integration_id}: {e}")
            return 0
    
    async def _handle_real_time_event(self, event_data: Dict):
        """Handle real-time events from integrations"""
        try:
            # Convert to compliance data point
            data_point = ComplianceDataPoint(
                property_id=event_data.get('property_id'),
                data_type=event_data.get('event_type'),
                source=event_data.get('source', 'unknown'),
                timestamp=datetime.now(),
                data=event_data
            )
            
            # Process immediately
            events = await self.data_processor.process_data_points([data_point])
            
            # Publish events
            if self.redis_client and events:
                for event in events:
                    await self._publish_event(event)
            
            logger.info(f"Processed real-time event: {event_data.get('event_type')}")
            
        except Exception as e:
            logger.error(f"Error handling real-time event: {e}")
    
    async def _publish_event(self, event: IntegrationEvent):
        """Publish event to Redis for real-time processing"""
        try:
            if self.redis_client:
                event_json = json.dumps(asdict(event), default=str)
                self.redis_client.publish('compliance_events', event_json)
                
        except Exception as e:
            logger.debug(f"Error publishing event to Redis: {e}")
    
    def _decrypt_credentials(self, encrypted_credentials: Dict) -> Dict:
        """Decrypt integration credentials"""
        # In production, implement proper encryption/decryption
        # For now, return as-is
        return encrypted_credentials or {}
    
    async def get_integration_status(self) -> List[Dict[str, Any]]:
        """Get status of all integrations"""
        status_list = []
        
        try:
            for integration_id, integration_data in self.adapters.items():
                config = integration_data['config']
                
                status = {
                    'id': integration_id,
                    'name': config.integration_name,
                    'type': config.integration_type,
                    'status': 'active' if config.is_active else 'inactive',
                    'last_sync': config.last_sync,
                    'next_sync': config.next_sync,
                    'connection_status': config.connection_status,
                    'last_error': config.last_error,
                    'data_types': integration_data['adapter'].get_supported_data_types()
                }
                
                status_list.append(status)
            
            return status_list
            
        except Exception as e:
            logger.error(f"Error getting integration status: {e}")
            return []
    
    async def test_integration(self, integration_id: str) -> Dict[str, Any]:
        """Test a specific integration"""
        result = {
            'success': False,
            'message': '',
            'data_points': 0,
            'error': None
        }
        
        try:
            if integration_id not in self.adapters:
                result['message'] = 'Integration not found'
                return result
            
            adapter = self.adapters[integration_id]['adapter']
            
            # Test connection
            if not await adapter.connect():
                result['message'] = 'Connection failed'
                return result
            
            # Test data sync
            data_points = await adapter.sync_data(datetime.now() - timedelta(hours=1))
            
            result['success'] = True
            result['message'] = 'Test successful'
            result['data_points'] = len(data_points)
            
            return result
            
        except Exception as e:
            result['error'] = str(e)
            result['message'] = f'Test failed: {str(e)}'
            return result
    
    async def start_continuous_monitoring(self):
        """Start continuous monitoring of integrations"""
        logger.info("Starting continuous compliance data monitoring")
        
        while True:
            try:
                # Sync all integrations
                await self.sync_all_integrations()
                
                # Wait for next sync cycle (configurable)
                await asyncio.sleep(300)  # 5 minutes
                
            except Exception as e:
                logger.error(f"Error in continuous monitoring: {e}")
                await asyncio.sleep(60)  # Wait 1 minute before retrying


# Global service instance
_integration_service = None


def get_compliance_integration_service() -> ComplianceIntegrationService:
    """Get or create the compliance integration service instance"""
    global _integration_service
    if _integration_service is None:
        _integration_service = ComplianceIntegrationService()
    return _integration_service


# Async helper function to run the continuous monitoring
async def start_compliance_monitoring():
    """Start the compliance monitoring service"""
    service = get_compliance_integration_service()
    await service.initialize_integrations()
    await service.start_continuous_monitoring()


# CLI command to start monitoring
if __name__ == "__main__":
    asyncio.run(start_compliance_monitoring())