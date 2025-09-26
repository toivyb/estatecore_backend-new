"""
Enterprise Features for QuickBooks Integration

Provides enterprise-level features including multi-property portfolio support,
role-based access control, white-label configuration, custom reporting,
and advanced analytics for property management companies.
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass, asdict
from enum import Enum
import uuid
from collections import defaultdict

from .quickbooks_api_client import QuickBooksAPIClient
from .financial_sync_service import FinancialSyncService
from .data_mapping_service import DataMappingService
from .reconciliation_service import ReconciliationService

logger = logging.getLogger(__name__)

class AccessLevel(Enum):
    """Access levels for QuickBooks features"""
    READ_ONLY = "read_only"
    BASIC = "basic"
    ADVANCED = "advanced"
    FULL_ACCESS = "full_access"
    ADMIN = "admin"

class ReportType(Enum):
    """Types of financial reports"""
    PROFIT_LOSS = "profit_loss"
    CASH_FLOW = "cash_flow"
    BALANCE_SHEET = "balance_sheet"
    RENT_ROLL = "rent_roll"
    EXPENSE_ANALYSIS = "expense_analysis"
    PROPERTY_PERFORMANCE = "property_performance"
    TAX_SUMMARY = "tax_summary"
    CUSTOM = "custom"

class IntegrationType(Enum):
    """Types of custom integrations"""
    WEBHOOK = "webhook"
    API_ENDPOINT = "api_endpoint"
    DATA_EXPORT = "data_export"
    SCHEDULED_SYNC = "scheduled_sync"

@dataclass
class PropertyPortfolio:
    """Multi-property portfolio configuration"""
    portfolio_id: str
    organization_id: str
    portfolio_name: str
    properties: List[str]  # Property IDs
    qb_class_mapping: Dict[str, str]  # Property ID -> QuickBooks Class ID
    qb_location_mapping: Dict[str, str]  # Property ID -> QuickBooks Location ID
    consolidated_reporting: bool = True
    separate_books: bool = False  # Each property has separate QB company
    master_company_id: Optional[str] = None
    created_at: datetime = None
    updated_at: datetime = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.updated_at is None:
            self.updated_at = datetime.now()

@dataclass
class UserAccess:
    """User access configuration for QuickBooks features"""
    user_id: str
    organization_id: str
    access_level: AccessLevel
    allowed_properties: Set[str]  # Property IDs user can access
    allowed_features: Set[str]  # Features user can access
    allowed_reports: Set[ReportType]
    sync_permissions: Dict[str, bool]  # Entity types user can sync
    created_at: datetime = None
    expires_at: Optional[datetime] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()

@dataclass
class WhiteLabelConfig:
    """White-label configuration for enterprise clients"""
    config_id: str
    organization_id: str
    company_name: str
    logo_url: Optional[str] = None
    primary_color: str = "#007bff"
    secondary_color: str = "#6c757d"
    custom_domain: Optional[str] = None
    email_templates: Dict[str, str] = None
    report_branding: Dict[str, Any] = None
    api_branding: Dict[str, Any] = None
    feature_flags: Dict[str, bool] = None
    created_at: datetime = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.email_templates is None:
            self.email_templates = {}
        if self.report_branding is None:
            self.report_branding = {}
        if self.api_branding is None:
            self.api_branding = {}
        if self.feature_flags is None:
            self.feature_flags = {}

@dataclass
class CustomReport:
    """Custom report configuration"""
    report_id: str
    organization_id: str
    report_name: str
    report_type: ReportType
    parameters: Dict[str, Any]
    filters: Dict[str, Any]
    columns: List[Dict[str, Any]]
    calculation_rules: Dict[str, Any]
    schedule: Optional[Dict[str, Any]] = None
    recipients: List[str] = None
    format: str = "pdf"  # pdf, excel, csv
    created_at: datetime = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.recipients is None:
            self.recipients = []

@dataclass
class CustomIntegration:
    """Custom integration configuration"""
    integration_id: str
    organization_id: str
    integration_name: str
    integration_type: IntegrationType
    endpoint_url: Optional[str] = None
    webhook_events: List[str] = None
    data_mapping: Dict[str, Any] = None
    authentication: Dict[str, Any] = None
    schedule: Optional[Dict[str, Any]] = None
    enabled: bool = True
    created_at: datetime = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.webhook_events is None:
            self.webhook_events = []
        if self.data_mapping is None:
            self.data_mapping = {}
        if self.authentication is None:
            self.authentication = {}

class EnterpriseQuickBooksService:
    """
    Enterprise-level QuickBooks integration service
    """
    
    def __init__(self, api_client: Optional[QuickBooksAPIClient] = None,
                 sync_service: Optional[FinancialSyncService] = None,
                 mapping_service: Optional[DataMappingService] = None,
                 reconciliation_service: Optional[ReconciliationService] = None):
        self.api_client = api_client or QuickBooksAPIClient()
        self.sync_service = sync_service or FinancialSyncService()
        self.mapping_service = mapping_service or DataMappingService()
        self.reconciliation_service = reconciliation_service or ReconciliationService()
        
        # Enterprise data storage
        self.portfolios: Dict[str, PropertyPortfolio] = {}
        self.user_access: Dict[str, UserAccess] = {}
        self.whitelabel_configs: Dict[str, WhiteLabelConfig] = {}
        self.custom_reports: Dict[str, CustomReport] = {}
        self.custom_integrations: Dict[str, CustomIntegration] = {}
        
        # Load configurations
        self._load_enterprise_data()
    
    def _load_enterprise_data(self):
        """Load enterprise configurations"""
        try:
            with open('instance/enterprise_config.json', 'r') as f:
                data = json.load(f)
                
                # Load portfolios
                for portfolio_data in data.get('portfolios', []):
                    portfolio_data['created_at'] = datetime.fromisoformat(portfolio_data['created_at'])
                    portfolio_data['updated_at'] = datetime.fromisoformat(portfolio_data['updated_at'])
                    portfolio = PropertyPortfolio(**portfolio_data)
                    self.portfolios[portfolio.portfolio_id] = portfolio
                
                # Load user access
                for access_data in data.get('user_access', []):
                    access_data['access_level'] = AccessLevel(access_data['access_level'])
                    access_data['allowed_properties'] = set(access_data['allowed_properties'])
                    access_data['allowed_features'] = set(access_data['allowed_features'])
                    access_data['allowed_reports'] = set(ReportType(r) for r in access_data['allowed_reports'])
                    access_data['created_at'] = datetime.fromisoformat(access_data['created_at'])
                    if access_data.get('expires_at'):
                        access_data['expires_at'] = datetime.fromisoformat(access_data['expires_at'])
                    
                    user_access = UserAccess(**access_data)
                    self.user_access[user_access.user_id] = user_access
                
                # Load whitelabel configs
                for config_data in data.get('whitelabel_configs', []):
                    config_data['created_at'] = datetime.fromisoformat(config_data['created_at'])
                    config = WhiteLabelConfig(**config_data)
                    self.whitelabel_configs[config.config_id] = config
                
                # Load custom reports
                for report_data in data.get('custom_reports', []):
                    report_data['report_type'] = ReportType(report_data['report_type'])
                    report_data['created_at'] = datetime.fromisoformat(report_data['created_at'])
                    report = CustomReport(**report_data)
                    self.custom_reports[report.report_id] = report
                
                # Load custom integrations
                for integration_data in data.get('custom_integrations', []):
                    integration_data['integration_type'] = IntegrationType(integration_data['integration_type'])
                    integration_data['created_at'] = datetime.fromisoformat(integration_data['created_at'])
                    integration = CustomIntegration(**integration_data)
                    self.custom_integrations[integration.integration_id] = integration
                    
        except FileNotFoundError:
            logger.info("No enterprise config found, using defaults")
        except Exception as e:
            logger.error(f"Error loading enterprise config: {e}")
    
    def _save_enterprise_data(self):
        """Save enterprise configurations"""
        try:
            import os
            os.makedirs('instance', exist_ok=True)
            
            data = {
                'portfolios': [
                    {**asdict(portfolio)} for portfolio in self.portfolios.values()
                ],
                'user_access': [
                    {
                        **asdict(access),
                        'access_level': access.access_level.value,
                        'allowed_properties': list(access.allowed_properties),
                        'allowed_features': list(access.allowed_features),
                        'allowed_reports': [r.value for r in access.allowed_reports]
                    }
                    for access in self.user_access.values()
                ],
                'whitelabel_configs': [
                    asdict(config) for config in self.whitelabel_configs.values()
                ],
                'custom_reports': [
                    {**asdict(report), 'report_type': report.report_type.value}
                    for report in self.custom_reports.values()
                ],
                'custom_integrations': [
                    {**asdict(integration), 'integration_type': integration.integration_type.value}
                    for integration in self.custom_integrations.values()
                ]
            }
            
            with open('instance/enterprise_config.json', 'w') as f:
                json.dump(data, f, indent=2, default=str)
                
        except Exception as e:
            logger.error(f"Error saving enterprise config: {e}")
    
    # Multi-Property Portfolio Management
    
    def create_property_portfolio(self, organization_id: str, portfolio_name: str,
                                properties: List[str], **kwargs) -> PropertyPortfolio:
        """Create a new property portfolio"""
        portfolio_id = str(uuid.uuid4())
        
        portfolio = PropertyPortfolio(
            portfolio_id=portfolio_id,
            organization_id=organization_id,
            portfolio_name=portfolio_name,
            properties=properties,
            qb_class_mapping={},
            qb_location_mapping={},
            **kwargs
        )
        
        self.portfolios[portfolio_id] = portfolio
        self._save_enterprise_data()
        
        logger.info(f"Created portfolio {portfolio_name} for organization {organization_id}")
        return portfolio
    
    def update_portfolio(self, portfolio_id: str, updates: Dict[str, Any]) -> bool:
        """Update a property portfolio"""
        if portfolio_id not in self.portfolios:
            return False
        
        portfolio = self.portfolios[portfolio_id]
        for key, value in updates.items():
            if hasattr(portfolio, key):
                setattr(portfolio, key, value)
        
        portfolio.updated_at = datetime.now()
        self._save_enterprise_data()
        return True
    
    def setup_portfolio_accounting(self, portfolio_id: str, qb_connection_id: str) -> Dict[str, Any]:
        """Setup QuickBooks accounting structure for portfolio"""
        portfolio = self.portfolios.get(portfolio_id)
        if not portfolio:
            return {"success": False, "error": "Portfolio not found"}
        
        try:
            # Create QuickBooks classes for each property
            for property_id in portfolio.properties:
                class_name = f"Property-{property_id}"
                
                # Create class in QuickBooks
                class_data = {
                    "Name": class_name,
                    "Active": True,
                    "SubClass": False
                }
                
                # This would create the actual class in QuickBooks
                # class_response = self.api_client.create_class(qb_connection_id, class_data)
                
                # For now, simulate success
                portfolio.qb_class_mapping[property_id] = f"class_{property_id}"
            
            # Create locations if needed
            if portfolio.separate_books:
                for property_id in portfolio.properties:
                    location_name = f"Location-{property_id}"
                    portfolio.qb_location_mapping[property_id] = f"location_{property_id}"
            
            # Update portfolio
            portfolio.updated_at = datetime.now()
            self._save_enterprise_data()
            
            return {
                "success": True,
                "classes_created": len(portfolio.qb_class_mapping),
                "locations_created": len(portfolio.qb_location_mapping)
            }
            
        except Exception as e:
            logger.error(f"Error setting up portfolio accounting: {e}")
            return {"success": False, "error": str(e)}
    
    def sync_portfolio_data(self, portfolio_id: str, entity_types: List[str] = None) -> Dict[str, Any]:
        """Sync data for entire portfolio"""
        portfolio = self.portfolios.get(portfolio_id)
        if not portfolio:
            return {"success": False, "error": "Portfolio not found"}
        
        results = {}
        total_synced = 0
        total_errors = 0
        
        for property_id in portfolio.properties:
            try:
                # Get property-specific data
                property_data = self._get_property_data(property_id, entity_types)
                
                # Sync each entity type
                for entity_type, data in property_data.items():
                    if entity_type == "tenants":
                        result = self.sync_service.sync_tenants_to_customers(
                            portfolio.organization_id, data
                        )
                    elif entity_type == "payments":
                        result = self.sync_service.sync_payments_to_quickbooks(
                            portfolio.organization_id, data
                        )
                    elif entity_type == "expenses":
                        result = self.sync_service.sync_expenses_to_quickbooks(
                            portfolio.organization_id, data
                        )
                    
                    if hasattr(result, 'successful_records'):
                        total_synced += result.successful_records
                        total_errors += result.failed_records
                
                results[property_id] = {"status": "completed"}
                
            except Exception as e:
                results[property_id] = {"status": "failed", "error": str(e)}
                total_errors += 1
        
        return {
            "success": True,
            "portfolio_id": portfolio_id,
            "properties_processed": len(portfolio.properties),
            "total_records_synced": total_synced,
            "total_errors": total_errors,
            "property_results": results
        }
    
    # Role-Based Access Control
    
    def create_user_access(self, user_id: str, organization_id: str, 
                          access_level: AccessLevel, **kwargs) -> UserAccess:
        """Create user access configuration"""
        user_access = UserAccess(
            user_id=user_id,
            organization_id=organization_id,
            access_level=access_level,
            allowed_properties=set(kwargs.get('allowed_properties', [])),
            allowed_features=set(kwargs.get('allowed_features', [])),
            allowed_reports=set(kwargs.get('allowed_reports', [])),
            sync_permissions=kwargs.get('sync_permissions', {}),
            expires_at=kwargs.get('expires_at')
        )
        
        self.user_access[user_id] = user_access
        self._save_enterprise_data()
        
        logger.info(f"Created access configuration for user {user_id}")
        return user_access
    
    def check_user_permission(self, user_id: str, feature: str, 
                            property_id: Optional[str] = None) -> bool:
        """Check if user has permission for a feature"""
        user_access = self.user_access.get(user_id)
        if not user_access:
            return False
        
        # Check if access is expired
        if user_access.expires_at and datetime.now() > user_access.expires_at:
            return False
        
        # Check feature access
        if feature not in user_access.allowed_features:
            return False
        
        # Check property access if specified
        if property_id and property_id not in user_access.allowed_properties:
            return False
        
        return True
    
    def get_user_accessible_properties(self, user_id: str) -> Set[str]:
        """Get properties accessible to user"""
        user_access = self.user_access.get(user_id)
        if not user_access:
            return set()
        
        return user_access.allowed_properties
    
    # White-Label Configuration
    
    def create_whitelabel_config(self, organization_id: str, company_name: str,
                               **kwargs) -> WhiteLabelConfig:
        """Create white-label configuration"""
        config_id = str(uuid.uuid4())
        
        config = WhiteLabelConfig(
            config_id=config_id,
            organization_id=organization_id,
            company_name=company_name,
            **kwargs
        )
        
        self.whitelabel_configs[config_id] = config
        self._save_enterprise_data()
        
        logger.info(f"Created white-label config for {company_name}")
        return config
    
    def get_whitelabel_config(self, organization_id: str) -> Optional[WhiteLabelConfig]:
        """Get white-label configuration for organization"""
        for config in self.whitelabel_configs.values():
            if config.organization_id == organization_id:
                return config
        return None
    
    def apply_branding(self, organization_id: str, content: str, 
                      content_type: str = "html") -> str:
        """Apply white-label branding to content"""
        config = self.get_whitelabel_config(organization_id)
        if not config:
            return content
        
        # Apply branding transformations
        branded_content = content
        
        if content_type == "html":
            # Replace colors
            branded_content = branded_content.replace("#007bff", config.primary_color)
            branded_content = branded_content.replace("#6c757d", config.secondary_color)
            
            # Replace company name
            branded_content = branded_content.replace("EstateCore", config.company_name)
            
            # Add logo if available
            if config.logo_url:
                branded_content = branded_content.replace(
                    "<img class=\"logo\"", 
                    f"<img src=\"{config.logo_url}\" class=\"logo\""
                )
        
        return branded_content
    
    # Custom Reporting
    
    def create_custom_report(self, organization_id: str, report_name: str,
                           report_type: ReportType, **kwargs) -> CustomReport:
        """Create custom report configuration"""
        report_id = str(uuid.uuid4())
        
        report = CustomReport(
            report_id=report_id,
            organization_id=organization_id,
            report_name=report_name,
            report_type=report_type,
            parameters=kwargs.get('parameters', {}),
            filters=kwargs.get('filters', {}),
            columns=kwargs.get('columns', []),
            calculation_rules=kwargs.get('calculation_rules', {}),
            **kwargs
        )
        
        self.custom_reports[report_id] = report
        self._save_enterprise_data()
        
        logger.info(f"Created custom report {report_name}")
        return report
    
    def generate_custom_report(self, report_id: str, 
                             date_range: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """Generate custom report"""
        report = self.custom_reports.get(report_id)
        if not report:
            return {"success": False, "error": "Report not found"}
        
        try:
            # Get data based on report type
            if report.report_type == ReportType.PROFIT_LOSS:
                data = self._generate_profit_loss_report(report, date_range)
            elif report.report_type == ReportType.CASH_FLOW:
                data = self._generate_cash_flow_report(report, date_range)
            elif report.report_type == ReportType.RENT_ROLL:
                data = self._generate_rent_roll_report(report, date_range)
            elif report.report_type == ReportType.PROPERTY_PERFORMANCE:
                data = self._generate_property_performance_report(report, date_range)
            else:
                data = {"error": "Report type not implemented"}
            
            # Apply branding
            if report.format == "html":
                data["content"] = self.apply_branding(
                    report.organization_id, 
                    data.get("content", ""), 
                    "html"
                )
            
            return {
                "success": True,
                "report_id": report_id,
                "report_name": report.report_name,
                "generated_at": datetime.now().isoformat(),
                "data": data
            }
            
        except Exception as e:
            logger.error(f"Error generating report {report_id}: {e}")
            return {"success": False, "error": str(e)}
    
    def schedule_report(self, report_id: str, schedule: Dict[str, Any]) -> bool:
        """Schedule automatic report generation"""
        if report_id not in self.custom_reports:
            return False
        
        report = self.custom_reports[report_id]
        report.schedule = schedule
        
        self._save_enterprise_data()
        
        # This would integrate with the automation engine
        # to schedule the report generation
        
        return True
    
    # Custom Integrations
    
    def create_custom_integration(self, organization_id: str, integration_name: str,
                                integration_type: IntegrationType, **kwargs) -> CustomIntegration:
        """Create custom integration"""
        integration_id = str(uuid.uuid4())
        
        integration = CustomIntegration(
            integration_id=integration_id,
            organization_id=organization_id,
            integration_name=integration_name,
            integration_type=integration_type,
            **kwargs
        )
        
        self.custom_integrations[integration_id] = integration
        self._save_enterprise_data()
        
        logger.info(f"Created custom integration {integration_name}")
        return integration
    
    def execute_integration(self, integration_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute custom integration"""
        integration = self.custom_integrations.get(integration_id)
        if not integration or not integration.enabled:
            return {"success": False, "error": "Integration not found or disabled"}
        
        try:
            if integration.integration_type == IntegrationType.WEBHOOK:
                return self._execute_webhook_integration(integration, data)
            elif integration.integration_type == IntegrationType.API_ENDPOINT:
                return self._execute_api_integration(integration, data)
            elif integration.integration_type == IntegrationType.DATA_EXPORT:
                return self._execute_export_integration(integration, data)
            else:
                return {"success": False, "error": "Integration type not supported"}
                
        except Exception as e:
            logger.error(f"Error executing integration {integration_id}: {e}")
            return {"success": False, "error": str(e)}
    
    # Analytics and Insights
    
    def get_portfolio_analytics(self, portfolio_id: str, 
                              period: str = "month") -> Dict[str, Any]:
        """Get analytics for property portfolio"""
        portfolio = self.portfolios.get(portfolio_id)
        if not portfolio:
            return {"error": "Portfolio not found"}
        
        analytics = {
            "portfolio_id": portfolio_id,
            "period": period,
            "properties": {},
            "totals": {
                "total_revenue": 0,
                "total_expenses": 0,
                "net_income": 0,
                "occupancy_rate": 0,
                "property_count": len(portfolio.properties)
            },
            "trends": {}
        }
        
        for property_id in portfolio.properties:
            property_analytics = self._get_property_analytics(property_id, period)
            analytics["properties"][property_id] = property_analytics
            
            # Aggregate totals
            analytics["totals"]["total_revenue"] += property_analytics.get("revenue", 0)
            analytics["totals"]["total_expenses"] += property_analytics.get("expenses", 0)
        
        analytics["totals"]["net_income"] = (
            analytics["totals"]["total_revenue"] - analytics["totals"]["total_expenses"]
        )
        
        return analytics
    
    def get_organization_insights(self, organization_id: str) -> Dict[str, Any]:
        """Get comprehensive insights for organization"""
        insights = {
            "organization_id": organization_id,
            "summary": {},
            "quickbooks_health": {},
            "sync_performance": {},
            "data_quality": {},
            "recommendations": []
        }
        
        # Get QuickBooks connection health
        insights["quickbooks_health"] = self._get_qb_health_metrics(organization_id)
        
        # Get sync performance
        insights["sync_performance"] = self._get_sync_performance(organization_id)
        
        # Get data quality score
        insights["data_quality"] = self.reconciliation_service.get_data_integrity_score(organization_id)
        
        # Generate recommendations
        insights["recommendations"] = self._generate_org_recommendations(insights)
        
        return insights
    
    # Private helper methods
    
    def _get_property_data(self, property_id: str, entity_types: List[str]) -> Dict[str, List[Dict[str, Any]]]:
        """Get data for a specific property"""
        # This would query the database for property-specific data
        return {
            "tenants": [],
            "payments": [],
            "expenses": []
        }
    
    def _generate_profit_loss_report(self, report: CustomReport, date_range: Optional[Dict[str, str]]) -> Dict[str, Any]:
        """Generate profit & loss report"""
        return {
            "report_type": "Profit & Loss",
            "revenue": {"rent": 0, "fees": 0, "other": 0},
            "expenses": {"maintenance": 0, "utilities": 0, "management": 0},
            "net_income": 0
        }
    
    def _generate_cash_flow_report(self, report: CustomReport, date_range: Optional[Dict[str, str]]) -> Dict[str, Any]:
        """Generate cash flow report"""
        return {
            "report_type": "Cash Flow",
            "cash_in": 0,
            "cash_out": 0,
            "net_cash_flow": 0
        }
    
    def _generate_rent_roll_report(self, report: CustomReport, date_range: Optional[Dict[str, str]]) -> Dict[str, Any]:
        """Generate rent roll report"""
        return {
            "report_type": "Rent Roll",
            "properties": [],
            "total_units": 0,
            "occupied_units": 0,
            "occupancy_rate": 0
        }
    
    def _generate_property_performance_report(self, report: CustomReport, date_range: Optional[Dict[str, str]]) -> Dict[str, Any]:
        """Generate property performance report"""
        return {
            "report_type": "Property Performance",
            "properties": [],
            "top_performers": [],
            "improvement_opportunities": []
        }
    
    def _execute_webhook_integration(self, integration: CustomIntegration, data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute webhook integration"""
        import requests
        
        try:
            response = requests.post(
                integration.endpoint_url,
                json=data,
                headers=integration.authentication,
                timeout=30
            )
            
            return {
                "success": response.ok,
                "status_code": response.status_code,
                "response": response.text
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _execute_api_integration(self, integration: CustomIntegration, data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute API integration"""
        # Custom API integration logic
        return {"success": True, "message": "API integration executed"}
    
    def _execute_export_integration(self, integration: CustomIntegration, data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute data export integration"""
        # Data export logic
        return {"success": True, "message": "Data exported"}
    
    def _get_property_analytics(self, property_id: str, period: str) -> Dict[str, Any]:
        """Get analytics for a single property"""
        return {
            "property_id": property_id,
            "revenue": 0,
            "expenses": 0,
            "occupancy_rate": 95.0,
            "units": 10
        }
    
    def _get_qb_health_metrics(self, organization_id: str) -> Dict[str, Any]:
        """Get QuickBooks connection health metrics"""
        return {
            "connection_status": "healthy",
            "last_sync": datetime.now().isoformat(),
            "sync_errors": 0,
            "api_response_time": 250
        }
    
    def _get_sync_performance(self, organization_id: str) -> Dict[str, Any]:
        """Get synchronization performance metrics"""
        return {
            "sync_success_rate": 98.5,
            "average_sync_time": 45,
            "records_synced_today": 150,
            "pending_sync_items": 5
        }
    
    def _generate_org_recommendations(self, insights: Dict[str, Any]) -> List[str]:
        """Generate recommendations for organization"""
        recommendations = []
        
        if insights["data_quality"]["integrity_score"] < 95:
            recommendations.append("Review and resolve data discrepancies to improve data quality")
        
        if insights["sync_performance"]["sync_success_rate"] < 95:
            recommendations.append("Investigate sync failures and optimize sync processes")
        
        return recommendations
    
    # Public API methods
    
    def list_portfolios(self, organization_id: str) -> List[Dict[str, Any]]:
        """List portfolios for organization"""
        portfolios = [
            p for p in self.portfolios.values()
            if p.organization_id == organization_id
        ]
        
        return [
            {
                "portfolio_id": p.portfolio_id,
                "portfolio_name": p.portfolio_name,
                "property_count": len(p.properties),
                "consolidated_reporting": p.consolidated_reporting,
                "created_at": p.created_at.isoformat()
            }
            for p in portfolios
        ]
    
    def get_user_permissions(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user permissions summary"""
        user_access = self.user_access.get(user_id)
        if not user_access:
            return None
        
        return {
            "user_id": user_id,
            "access_level": user_access.access_level.value,
            "allowed_properties": list(user_access.allowed_properties),
            "allowed_features": list(user_access.allowed_features),
            "allowed_reports": [r.value for r in user_access.allowed_reports],
            "expires_at": user_access.expires_at.isoformat() if user_access.expires_at else None
        }
    
    def list_custom_reports(self, organization_id: str) -> List[Dict[str, Any]]:
        """List custom reports for organization"""
        reports = [
            r for r in self.custom_reports.values()
            if r.organization_id == organization_id
        ]
        
        return [
            {
                "report_id": r.report_id,
                "report_name": r.report_name,
                "report_type": r.report_type.value,
                "scheduled": r.schedule is not None,
                "created_at": r.created_at.isoformat()
            }
            for r in reports
        ]
    
    def list_custom_integrations(self, organization_id: str) -> List[Dict[str, Any]]:
        """List custom integrations for organization"""
        integrations = [
            i for i in self.custom_integrations.values()
            if i.organization_id == organization_id
        ]
        
        return [
            {
                "integration_id": i.integration_id,
                "integration_name": i.integration_name,
                "integration_type": i.integration_type.value,
                "enabled": i.enabled,
                "created_at": i.created_at.isoformat()
            }
            for i in integrations
        ]

# Service instance
_enterprise_service = None

def get_enterprise_quickbooks_service() -> EnterpriseQuickBooksService:
    """Get singleton enterprise service instance"""
    global _enterprise_service
    if _enterprise_service is None:
        _enterprise_service = EnterpriseQuickBooksService()
    return _enterprise_service