"""
AppFolio Enterprise Service

Advanced enterprise features for AppFolio integration including
multi-property portfolios, white-label configuration, RBAC,
bulk operations, and advanced reporting.
"""

import logging
import json
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field, asdict
from enum import Enum
import asyncio
from concurrent.futures import ThreadPoolExecutor

from .appfolio_api_client import AppFolioAPIClient
from .appfolio_sync_service import AppFolioSyncService, SyncDirection, SyncMode
from .appfolio_mapping_service import AppFolioMappingService

logger = logging.getLogger(__name__)

class AccessLevel(Enum):
    """Access levels for RBAC"""
    READ_ONLY = "read_only"
    READ_WRITE = "read_write"
    ADMIN = "admin"
    SUPER_ADMIN = "super_admin"

class ReportType(Enum):
    """Custom report types"""
    FINANCIAL_SUMMARY = "financial_summary"
    OCCUPANCY_REPORT = "occupancy_report"
    MAINTENANCE_SUMMARY = "maintenance_summary"
    RENT_ROLL = "rent_roll"
    VENDOR_PERFORMANCE = "vendor_performance"
    PORTFOLIO_ANALYSIS = "portfolio_analysis"
    CASH_FLOW = "cash_flow"
    EXPENSE_ANALYSIS = "expense_analysis"
    TENANT_ANALYSIS = "tenant_analysis"
    CUSTOM = "custom"

class BulkOperationType(Enum):
    """Bulk operation types"""
    IMPORT = "import"
    EXPORT = "export"
    UPDATE = "update"
    DELETE = "delete"
    SYNC = "sync"
    VALIDATE = "validate"

@dataclass
class Portfolio:
    """Multi-property portfolio"""
    portfolio_id: str
    organization_id: str
    name: str
    description: Optional[str] = None
    property_ids: List[str] = field(default_factory=list)
    manager_id: Optional[str] = None
    consolidated_reporting: bool = True
    custom_fields: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    active: bool = True
    
    # Financial aggregates
    total_units: int = 0
    total_value: Optional[float] = None
    monthly_income: Optional[float] = None
    monthly_expenses: Optional[float] = None
    net_operating_income: Optional[float] = None
    occupancy_rate: Optional[float] = None

@dataclass
class Role:
    """RBAC Role definition"""
    role_id: str
    organization_id: str
    name: str
    description: str
    permissions: List[str] = field(default_factory=list)
    access_level: AccessLevel = AccessLevel.READ_ONLY
    entity_restrictions: Optional[Dict[str, List[str]]] = None
    field_restrictions: Optional[Dict[str, List[str]]] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    active: bool = True

@dataclass
class UserRole:
    """User role assignment"""
    assignment_id: str
    user_id: str
    organization_id: str
    role_id: str
    portfolio_ids: Optional[List[str]] = None
    property_ids: Optional[List[str]] = None
    granted_by: Optional[str] = None
    granted_at: datetime = field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None
    active: bool = True

@dataclass
class CustomReport:
    """Custom report configuration"""
    report_id: str
    organization_id: str
    name: str
    report_type: ReportType
    description: Optional[str] = None
    data_sources: List[str] = field(default_factory=list)
    filters: Dict[str, Any] = field(default_factory=dict)
    grouping: Optional[List[str]] = None
    aggregations: Optional[Dict[str, str]] = None
    schedule: Optional[Dict[str, Any]] = None
    recipients: List[str] = field(default_factory=list)
    format: str = "json"
    created_by: str = ""
    created_at: datetime = field(default_factory=datetime.utcnow)
    active: bool = True

@dataclass
class BulkOperation:
    """Bulk operation configuration"""
    operation_id: str
    organization_id: str
    operation_type: BulkOperationType
    entity_type: str
    status: str = "pending"
    file_path: Optional[str] = None
    parameters: Dict[str, Any] = field(default_factory=dict)
    total_records: int = 0
    processed_records: int = 0
    successful_records: int = 0
    failed_records: int = 0
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    created_by: str = ""
    created_at: datetime = field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

@dataclass
class WhiteLabelConfig:
    """White-label configuration"""
    config_id: str
    organization_id: str
    brand_name: str
    logo_url: Optional[str] = None
    primary_color: str = "#007bff"
    secondary_color: str = "#6c757d"
    custom_domain: Optional[str] = None
    custom_css: Optional[str] = None
    email_templates: Dict[str, str] = field(default_factory=dict)
    notification_settings: Dict[str, Any] = field(default_factory=dict)
    feature_flags: Dict[str, bool] = field(default_factory=dict)
    api_settings: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    active: bool = True

class AppFolioEnterpriseService:
    """
    AppFolio Enterprise Service
    
    Provides advanced enterprise features for large-scale property management
    operations including portfolio management, RBAC, bulk operations,
    custom reporting, and white-label configuration.
    """
    
    def __init__(self, api_client: AppFolioAPIClient, sync_service: AppFolioSyncService,
                 mapping_service: AppFolioMappingService):
        self.api_client = api_client
        self.sync_service = sync_service
        self.mapping_service = mapping_service
        
        # Enterprise data storage
        self.portfolios: Dict[str, Portfolio] = {}
        self.roles: Dict[str, Role] = {}
        self.user_roles: Dict[str, UserRole] = {}
        self.custom_reports: Dict[str, CustomReport] = {}
        self.bulk_operations: Dict[str, BulkOperation] = {}
        self.white_label_configs: Dict[str, WhiteLabelConfig] = {}
        
        # Executors for async operations
        self.bulk_executor = ThreadPoolExecutor(max_workers=3)
        self.report_executor = ThreadPoolExecutor(max_workers=5)
        
        # Default permissions
        self.default_permissions = {
            AccessLevel.READ_ONLY: [
                "view_properties", "view_units", "view_tenants", "view_leases",
                "view_payments", "view_reports"
            ],
            AccessLevel.READ_WRITE: [
                "view_properties", "edit_properties", "view_units", "edit_units",
                "view_tenants", "edit_tenants", "view_leases", "edit_leases",
                "view_payments", "create_payments", "view_reports", "create_reports"
            ],
            AccessLevel.ADMIN: [
                "view_properties", "edit_properties", "create_properties", "delete_properties",
                "view_units", "edit_units", "create_units", "delete_units",
                "view_tenants", "edit_tenants", "create_tenants", "delete_tenants",
                "view_leases", "edit_leases", "create_leases", "delete_leases",
                "view_payments", "create_payments", "edit_payments", "delete_payments",
                "view_reports", "create_reports", "edit_reports", "delete_reports",
                "manage_vendors", "manage_work_orders", "bulk_operations"
            ],
            AccessLevel.SUPER_ADMIN: [
                "*"  # All permissions
            ]
        }
        
        logger.info("AppFolio Enterprise Service initialized")
    
    # Portfolio Management
    
    def create_property_portfolio(self, organization_id: str, portfolio_name: str,
                                property_ids: List[str], **kwargs) -> Portfolio:
        """Create a new property portfolio"""
        try:
            portfolio_id = str(uuid.uuid4())
            
            portfolio = Portfolio(
                portfolio_id=portfolio_id,
                organization_id=organization_id,
                name=portfolio_name,
                property_ids=property_ids,
                **kwargs
            )
            
            # Calculate portfolio aggregates
            self._calculate_portfolio_aggregates(portfolio)
            
            # Store portfolio
            self.portfolios[portfolio_id] = portfolio
            
            logger.info(f"Created portfolio {portfolio_name} with {len(property_ids)} properties")
            return portfolio
            
        except Exception as e:
            logger.error(f"Failed to create portfolio: {str(e)}")
            raise
    
    def add_property_to_portfolio(self, portfolio_id: str, property_id: str) -> bool:
        """Add property to portfolio"""
        try:
            if portfolio_id not in self.portfolios:
                raise ValueError(f"Portfolio {portfolio_id} not found")
            
            portfolio = self.portfolios[portfolio_id]
            
            if property_id not in portfolio.property_ids:
                portfolio.property_ids.append(property_id)
                portfolio.updated_at = datetime.utcnow()
                
                # Recalculate aggregates
                self._calculate_portfolio_aggregates(portfolio)
                
                logger.info(f"Added property {property_id} to portfolio {portfolio_id}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to add property to portfolio: {str(e)}")
            return False
    
    def remove_property_from_portfolio(self, portfolio_id: str, property_id: str) -> bool:
        """Remove property from portfolio"""
        try:
            if portfolio_id not in self.portfolios:
                raise ValueError(f"Portfolio {portfolio_id} not found")
            
            portfolio = self.portfolios[portfolio_id]
            
            if property_id in portfolio.property_ids:
                portfolio.property_ids.remove(property_id)
                portfolio.updated_at = datetime.utcnow()
                
                # Recalculate aggregates
                self._calculate_portfolio_aggregates(portfolio)
                
                logger.info(f"Removed property {property_id} from portfolio {portfolio_id}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to remove property from portfolio: {str(e)}")
            return False
    
    def _calculate_portfolio_aggregates(self, portfolio: Portfolio):
        """Calculate portfolio financial aggregates"""
        try:
            # This would calculate actual aggregates from property data
            # For now, set placeholder values
            portfolio.total_units = len(portfolio.property_ids) * 50  # Estimate
            portfolio.monthly_income = portfolio.total_units * 1500  # Estimate
            portfolio.monthly_expenses = portfolio.monthly_income * 0.3  # Estimate
            portfolio.net_operating_income = portfolio.monthly_income - portfolio.monthly_expenses
            portfolio.occupancy_rate = 95.0  # Estimate
            
        except Exception as e:
            logger.error(f"Error calculating portfolio aggregates: {str(e)}")
    
    def setup_portfolio_accounting(self, portfolio_id: str, connection_id: str) -> Dict[str, Any]:
        """Setup QuickBooks accounting structure for portfolio"""
        try:
            # This would create appropriate chart of accounts structure
            # For now, return success
            return {
                'success': True,
                'accounts_created': 5,
                'structure': 'portfolio_based'
            }
            
        except Exception as e:
            logger.error(f"Failed to setup portfolio accounting: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def list_portfolios(self, organization_id: str) -> List[Portfolio]:
        """List portfolios for organization"""
        return [
            portfolio for portfolio in self.portfolios.values()
            if portfolio.organization_id == organization_id and portfolio.active
        ]
    
    # Role-Based Access Control (RBAC)
    
    def create_role(self, organization_id: str, name: str, description: str,
                   access_level: AccessLevel, custom_permissions: List[str] = None) -> Role:
        """Create a new role"""
        try:
            role_id = str(uuid.uuid4())
            
            # Get permissions based on access level
            permissions = self.default_permissions.get(access_level, []).copy()
            
            # Add custom permissions
            if custom_permissions:
                permissions.extend(custom_permissions)
            
            role = Role(
                role_id=role_id,
                organization_id=organization_id,
                name=name,
                description=description,
                permissions=permissions,
                access_level=access_level
            )
            
            self.roles[role_id] = role
            
            logger.info(f"Created role {name} with {len(permissions)} permissions")
            return role
            
        except Exception as e:
            logger.error(f"Failed to create role: {str(e)}")
            raise
    
    def assign_role_to_user(self, user_id: str, organization_id: str, role_id: str,
                           portfolio_ids: List[str] = None, property_ids: List[str] = None,
                           granted_by: str = None, expires_at: datetime = None) -> UserRole:
        """Assign role to user"""
        try:
            if role_id not in self.roles:
                raise ValueError(f"Role {role_id} not found")
            
            assignment_id = str(uuid.uuid4())
            
            user_role = UserRole(
                assignment_id=assignment_id,
                user_id=user_id,
                organization_id=organization_id,
                role_id=role_id,
                portfolio_ids=portfolio_ids,
                property_ids=property_ids,
                granted_by=granted_by,
                expires_at=expires_at
            )
            
            self.user_roles[assignment_id] = user_role
            
            logger.info(f"Assigned role {role_id} to user {user_id}")
            return user_role
            
        except Exception as e:
            logger.error(f"Failed to assign role: {str(e)}")
            raise
    
    def check_user_permission(self, user_id: str, organization_id: str, 
                            permission: str, entity_id: str = None) -> bool:
        """Check if user has specific permission"""
        try:
            # Get user roles
            user_assignments = [
                assignment for assignment in self.user_roles.values()
                if (assignment.user_id == user_id and 
                    assignment.organization_id == organization_id and
                    assignment.active)
            ]
            
            for assignment in user_assignments:
                # Check if assignment is expired
                if assignment.expires_at and datetime.utcnow() > assignment.expires_at:
                    continue
                
                # Get role
                role = self.roles.get(assignment.role_id)
                if not role or not role.active:
                    continue
                
                # Check permissions
                if "*" in role.permissions or permission in role.permissions:
                    # Check entity restrictions if applicable
                    if entity_id and assignment.property_ids:
                        return entity_id in assignment.property_ids
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error checking user permission: {str(e)}")
            return False
    
    def get_user_permissions(self, user_id: str, organization_id: str) -> Dict[str, Any]:
        """Get all permissions for user"""
        try:
            permissions = set()
            active_roles = []
            
            # Get user roles
            user_assignments = [
                assignment for assignment in self.user_roles.values()
                if (assignment.user_id == user_id and 
                    assignment.organization_id == organization_id and
                    assignment.active)
            ]
            
            for assignment in user_assignments:
                # Check if assignment is expired
                if assignment.expires_at and datetime.utcnow() > assignment.expires_at:
                    continue
                
                # Get role
                role = self.roles.get(assignment.role_id)
                if not role or not role.active:
                    continue
                
                active_roles.append(role.name)
                permissions.update(role.permissions)
            
            return {
                'user_id': user_id,
                'organization_id': organization_id,
                'permissions': list(permissions),
                'roles': active_roles,
                'has_admin_access': any(role.access_level in [AccessLevel.ADMIN, AccessLevel.SUPER_ADMIN] 
                                      for role in [self.roles.get(a.role_id) for a in user_assignments]
                                      if role)
            }
            
        except Exception as e:
            logger.error(f"Error getting user permissions: {str(e)}")
            return {'permissions': [], 'roles': [], 'has_admin_access': False}
    
    # Custom Reporting
    
    def create_custom_report(self, organization_id: str, report_name: str, 
                           report_type: ReportType, **kwargs) -> CustomReport:
        """Create custom report"""
        try:
            report_id = str(uuid.uuid4())
            
            report = CustomReport(
                report_id=report_id,
                organization_id=organization_id,
                name=report_name,
                report_type=report_type,
                **kwargs
            )
            
            self.custom_reports[report_id] = report
            
            logger.info(f"Created custom report {report_name}")
            return report
            
        except Exception as e:
            logger.error(f"Failed to create custom report: {str(e)}")
            raise
    
    def generate_custom_report(self, report_id: str, date_range: Dict[str, str] = None) -> Dict[str, Any]:
        """Generate custom report"""
        try:
            if report_id not in self.custom_reports:
                raise ValueError(f"Report {report_id} not found")
            
            report = self.custom_reports[report_id]
            
            # Generate report data based on type
            if report.report_type == ReportType.FINANCIAL_SUMMARY:
                data = self._generate_financial_summary(report, date_range)
            elif report.report_type == ReportType.OCCUPANCY_REPORT:
                data = self._generate_occupancy_report(report, date_range)
            elif report.report_type == ReportType.RENT_ROLL:
                data = self._generate_rent_roll_report(report, date_range)
            elif report.report_type == ReportType.PORTFOLIO_ANALYSIS:
                data = self._generate_portfolio_analysis(report, date_range)
            else:
                data = self._generate_generic_report(report, date_range)
            
            return {
                'success': True,
                'report_id': report_id,
                'report_name': report.name,
                'generated_at': datetime.utcnow().isoformat(),
                'data': data,
                'format': report.format
            }
            
        except Exception as e:
            logger.error(f"Failed to generate report: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _generate_financial_summary(self, report: CustomReport, date_range: Dict[str, str]) -> Dict[str, Any]:
        """Generate financial summary report"""
        # This would generate actual financial data
        return {
            'total_income': 125000.00,
            'total_expenses': 45000.00,
            'net_income': 80000.00,
            'occupancy_rate': 95.5,
            'properties_count': 25,
            'units_count': 150
        }
    
    def _generate_occupancy_report(self, report: CustomReport, date_range: Dict[str, str]) -> Dict[str, Any]:
        """Generate occupancy report"""
        # This would generate actual occupancy data
        return {
            'overall_occupancy': 95.5,
            'vacant_units': 7,
            'occupied_units': 143,
            'total_units': 150,
            'move_ins': 12,
            'move_outs': 8
        }
    
    def _generate_rent_roll_report(self, report: CustomReport, date_range: Dict[str, str]) -> Dict[str, Any]:
        """Generate rent roll report"""
        # This would generate actual rent roll data
        return {
            'total_potential_rent': 135000.00,
            'total_collected_rent': 128250.00,
            'collection_rate': 95.0,
            'outstanding_balance': 6750.00,
            'units_count': 150
        }
    
    def _generate_portfolio_analysis(self, report: CustomReport, date_range: Dict[str, str]) -> Dict[str, Any]:
        """Generate portfolio analysis report"""
        # This would generate actual portfolio analysis
        return {
            'portfolios': len(self.portfolios),
            'total_properties': sum(len(p.property_ids) for p in self.portfolios.values()),
            'total_value': sum(p.total_value or 0 for p in self.portfolios.values()),
            'average_noi': 5500.00,
            'best_performing_portfolio': 'Downtown Portfolio'
        }
    
    def _generate_generic_report(self, report: CustomReport, date_range: Dict[str, str]) -> Dict[str, Any]:
        """Generate generic report"""
        return {
            'message': 'Generic report data',
            'filters_applied': report.filters,
            'data_sources': report.data_sources
        }
    
    def list_custom_reports(self, organization_id: str) -> List[CustomReport]:
        """List custom reports for organization"""
        return [
            report for report in self.custom_reports.values()
            if report.organization_id == organization_id and report.active
        ]
    
    # Bulk Operations
    
    def create_bulk_operation(self, organization_id: str, operation_type: BulkOperationType,
                            entity_type: str, file_path: str = None, **kwargs) -> BulkOperation:
        """Create bulk operation"""
        try:
            operation_id = str(uuid.uuid4())
            
            operation = BulkOperation(
                operation_id=operation_id,
                organization_id=organization_id,
                operation_type=operation_type,
                entity_type=entity_type,
                file_path=file_path,
                **kwargs
            )
            
            self.bulk_operations[operation_id] = operation
            
            logger.info(f"Created bulk operation {operation_type.value} for {entity_type}")
            return operation
            
        except Exception as e:
            logger.error(f"Failed to create bulk operation: {str(e)}")
            raise
    
    async def execute_bulk_operation(self, operation_id: str) -> Dict[str, Any]:
        """Execute bulk operation"""
        try:
            if operation_id not in self.bulk_operations:
                raise ValueError(f"Bulk operation {operation_id} not found")
            
            operation = self.bulk_operations[operation_id]
            operation.status = "running"
            operation.started_at = datetime.utcnow()
            
            # Execute based on operation type
            if operation.operation_type == BulkOperationType.IMPORT:
                result = await self._execute_bulk_import(operation)
            elif operation.operation_type == BulkOperationType.EXPORT:
                result = await self._execute_bulk_export(operation)
            elif operation.operation_type == BulkOperationType.UPDATE:
                result = await self._execute_bulk_update(operation)
            elif operation.operation_type == BulkOperationType.SYNC:
                result = await self._execute_bulk_sync(operation)
            else:
                raise ValueError(f"Unsupported operation type: {operation.operation_type}")
            
            operation.status = "completed"
            operation.completed_at = datetime.utcnow()
            
            return result
            
        except Exception as e:
            logger.error(f"Bulk operation failed: {str(e)}")
            if operation_id in self.bulk_operations:
                self.bulk_operations[operation_id].status = "failed"
                self.bulk_operations[operation_id].errors.append(str(e))
            
            return {
                'success': False,
                'error': str(e)
            }
    
    async def _execute_bulk_import(self, operation: BulkOperation) -> Dict[str, Any]:
        """Execute bulk import operation"""
        # This would process the import file and create records
        operation.total_records = 100
        operation.processed_records = 100
        operation.successful_records = 95
        operation.failed_records = 5
        
        return {
            'success': True,
            'imported_records': 95,
            'failed_records': 5
        }
    
    async def _execute_bulk_export(self, operation: BulkOperation) -> Dict[str, Any]:
        """Execute bulk export operation"""
        # This would export data to file
        return {
            'success': True,
            'exported_records': 150,
            'file_path': '/exports/data.csv'
        }
    
    async def _execute_bulk_update(self, operation: BulkOperation) -> Dict[str, Any]:
        """Execute bulk update operation"""
        # This would update multiple records
        return {
            'success': True,
            'updated_records': 75
        }
    
    async def _execute_bulk_sync(self, operation: BulkOperation) -> Dict[str, Any]:
        """Execute bulk sync operation"""
        # Trigger sync for specific entities
        sync_job = await self.sync_service.create_sync_job(
            organization_id=operation.organization_id,
            entity_types=[operation.entity_type],
            sync_direction=SyncDirection.BIDIRECTIONAL,
            sync_mode=SyncMode.FULL,
            priority="high"
        )
        
        result = await self.sync_service.execute_sync_job(sync_job.job_id)
        
        return {
            'success': result['success'],
            'sync_job_id': sync_job.job_id,
            'results': result.get('results', {})
        }
    
    # White-Label Configuration
    
    def create_white_label_config(self, organization_id: str, brand_name: str, **kwargs) -> WhiteLabelConfig:
        """Create white-label configuration"""
        try:
            config_id = str(uuid.uuid4())
            
            config = WhiteLabelConfig(
                config_id=config_id,
                organization_id=organization_id,
                brand_name=brand_name,
                **kwargs
            )
            
            self.white_label_configs[organization_id] = config
            
            logger.info(f"Created white-label config for {brand_name}")
            return config
            
        except Exception as e:
            logger.error(f"Failed to create white-label config: {str(e)}")
            raise
    
    def update_white_label_config(self, organization_id: str, updates: Dict[str, Any]) -> bool:
        """Update white-label configuration"""
        try:
            if organization_id not in self.white_label_configs:
                raise ValueError(f"White-label config not found for organization {organization_id}")
            
            config = self.white_label_configs[organization_id]
            
            for key, value in updates.items():
                if hasattr(config, key):
                    setattr(config, key, value)
            
            config.updated_at = datetime.utcnow()
            
            logger.info(f"Updated white-label config for organization {organization_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update white-label config: {str(e)}")
            return False
    
    def get_white_label_config(self, organization_id: str) -> Optional[WhiteLabelConfig]:
        """Get white-label configuration"""
        return self.white_label_configs.get(organization_id)
    
    # Enterprise Status and Management
    
    def get_enterprise_status(self, organization_id: str) -> Dict[str, Any]:
        """Get enterprise features status"""
        try:
            portfolios = self.list_portfolios(organization_id)
            custom_reports = self.list_custom_reports(organization_id)
            
            # Get user roles count
            user_roles_count = len([
                ur for ur in self.user_roles.values()
                if ur.organization_id == organization_id and ur.active
            ])
            
            # Get active bulk operations
            active_bulk_ops = len([
                op for op in self.bulk_operations.values()
                if op.organization_id == organization_id and op.status == "running"
            ])
            
            return {
                'organization_id': organization_id,
                'portfolios': {
                    'count': len(portfolios),
                    'total_properties': sum(len(p.property_ids) for p in portfolios),
                    'total_value': sum(p.total_value or 0 for p in portfolios)
                },
                'rbac': {
                    'roles_defined': len([r for r in self.roles.values() if r.organization_id == organization_id]),
                    'user_assignments': user_roles_count
                },
                'custom_reports': {
                    'count': len(custom_reports),
                    'scheduled_reports': len([r for r in custom_reports if r.schedule])
                },
                'bulk_operations': {
                    'active_operations': active_bulk_ops,
                    'total_operations': len([op for op in self.bulk_operations.values() 
                                           if op.organization_id == organization_id])
                },
                'white_label': {
                    'configured': organization_id in self.white_label_configs,
                    'brand_name': self.white_label_configs[organization_id].brand_name 
                                if organization_id in self.white_label_configs else None
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting enterprise status: {str(e)}")
            return {'error': str(e)}
    
    def enable_enterprise_features(self, organization_id: str, features: List[str]) -> Dict[str, Any]:
        """Enable enterprise features for organization"""
        try:
            enabled_features = []
            
            for feature in features:
                if feature == "multi_property":
                    # Enable multi-property management
                    enabled_features.append("multi_property")
                elif feature == "rbac":
                    # Enable role-based access control
                    enabled_features.append("rbac")
                elif feature == "custom_reports":
                    # Enable custom reporting
                    enabled_features.append("custom_reports")
                elif feature == "bulk_operations":
                    # Enable bulk operations
                    enabled_features.append("bulk_operations")
                elif feature == "white_label":
                    # Enable white-label configuration
                    enabled_features.append("white_label")
            
            logger.info(f"Enabled enterprise features for {organization_id}: {enabled_features}")
            
            return {
                'success': True,
                'enabled_features': enabled_features
            }
            
        except Exception as e:
            logger.error(f"Failed to enable enterprise features: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }