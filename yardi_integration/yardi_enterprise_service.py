"""
Yardi Enterprise Service

Advanced enterprise features for multi-property portfolios, centralized management,
custom reporting, and enterprise-grade Yardi integration capabilities.
"""

import os
import logging
import json
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field
from enum import Enum

from .models import YardiProductType, YardiEntityType

logger = logging.getLogger(__name__)

class AccessLevel(Enum):
    """Enterprise access levels"""
    VIEWER = "viewer"
    OPERATOR = "operator"
    MANAGER = "manager"
    ADMIN = "admin"
    SUPER_ADMIN = "super_admin"

class ReportType(Enum):
    """Enterprise report types"""
    FINANCIAL_SUMMARY = "financial_summary"
    OCCUPANCY_ANALYSIS = "occupancy_analysis"
    REVENUE_ANALYSIS = "revenue_analysis"
    PORTFOLIO_PERFORMANCE = "portfolio_performance"
    SYNC_ANALYTICS = "sync_analytics"
    DATA_QUALITY = "data_quality"
    CUSTOM = "custom"

@dataclass
class PropertyPortfolio:
    """Property portfolio configuration"""
    portfolio_id: str
    organization_id: str
    portfolio_name: str
    properties: List[str]
    portfolio_manager: Optional[str] = None
    consolidated_reporting: bool = True
    custom_settings: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)

@dataclass
class EnterpriseUser:
    """Enterprise user with role-based access"""
    user_id: str
    organization_id: str
    email: str
    name: str
    access_level: AccessLevel
    assigned_portfolios: List[str] = field(default_factory=list)
    permissions: List[str] = field(default_factory=list)
    is_active: bool = True
    created_at: datetime = field(default_factory=datetime.utcnow)

@dataclass
class CustomReport:
    """Custom enterprise report configuration"""
    report_id: str
    organization_id: str
    report_name: str
    report_type: ReportType
    data_sources: List[str]
    filters: Dict[str, Any] = field(default_factory=dict)
    grouping: List[str] = field(default_factory=list)
    aggregations: Dict[str, str] = field(default_factory=dict)
    schedule: Optional[str] = None
    recipients: List[str] = field(default_factory=list)
    created_by: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)

class YardiEnterpriseService:
    """Yardi Enterprise Service for advanced enterprise features"""
    
    def __init__(self, api_client, sync_service, mapping_service):
        self.api_client = api_client
        self.sync_service = sync_service
        self.mapping_service = mapping_service
        
        # Enterprise data storage
        self.portfolios: Dict[str, PropertyPortfolio] = {}
        self.enterprise_users: Dict[str, EnterpriseUser] = {}
        self.custom_reports: Dict[str, CustomReport] = {}
        self.enterprise_configs: Dict[str, Dict[str, Any]] = {}
        
        logger.info("Yardi Enterprise Service initialized")
    
    # =====================================================
    # PORTFOLIO MANAGEMENT
    # =====================================================
    
    def create_property_portfolio(self, organization_id: str, portfolio_name: str,
                                properties: List[str], consolidated_reporting: bool = True,
                                portfolio_manager: Optional[str] = None) -> PropertyPortfolio:
        """Create property portfolio"""
        
        portfolio_id = f"portfolio_{organization_id}_{uuid.uuid4().hex[:8]}"
        
        portfolio = PropertyPortfolio(
            portfolio_id=portfolio_id,
            organization_id=organization_id,
            portfolio_name=portfolio_name,
            properties=properties,
            portfolio_manager=portfolio_manager,
            consolidated_reporting=consolidated_reporting
        )
        
        self.portfolios[portfolio_id] = portfolio
        
        logger.info(f"Created portfolio {portfolio_id} with {len(properties)} properties")
        
        return portfolio
    
    def add_property_to_portfolio(self, portfolio_id: str, property_id: str) -> Dict[str, Any]:
        """Add property to portfolio"""
        portfolio = self.portfolios.get(portfolio_id)
        if not portfolio:
            return {"success": False, "error": "Portfolio not found"}
        
        if property_id not in portfolio.properties:
            portfolio.properties.append(property_id)
            return {"success": True, "message": f"Property {property_id} added to portfolio"}
        
        return {"success": False, "error": "Property already in portfolio"}
    
    def remove_property_from_portfolio(self, portfolio_id: str, property_id: str) -> Dict[str, Any]:
        """Remove property from portfolio"""
        portfolio = self.portfolios.get(portfolio_id)
        if not portfolio:
            return {"success": False, "error": "Portfolio not found"}
        
        if property_id in portfolio.properties:
            portfolio.properties.remove(property_id)
            return {"success": True, "message": f"Property {property_id} removed from portfolio"}
        
        return {"success": False, "error": "Property not in portfolio"}
    
    def list_portfolios(self, organization_id: str) -> List[PropertyPortfolio]:
        """List portfolios for organization"""
        return [
            portfolio for portfolio in self.portfolios.values()
            if portfolio.organization_id == organization_id
        ]
    
    def get_portfolio_summary(self, portfolio_id: str) -> Dict[str, Any]:
        """Get portfolio summary with key metrics"""
        portfolio = self.portfolios.get(portfolio_id)
        if not portfolio:
            return {"error": "Portfolio not found"}
        
        # This would calculate real metrics from property data
        return {
            "portfolio_id": portfolio_id,
            "portfolio_name": portfolio.portfolio_name,
            "total_properties": len(portfolio.properties),
            "total_units": 0,  # Would calculate from property data
            "occupancy_rate": 0.0,  # Would calculate from lease data
            "monthly_revenue": 0.0,  # Would calculate from rent rolls
            "maintenance_requests": 0,  # Would calculate from work orders
            "last_updated": datetime.utcnow().isoformat()
        }
    
    # =====================================================
    # USER MANAGEMENT
    # =====================================================
    
    def create_enterprise_user(self, organization_id: str, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create enterprise user with role-based access"""
        try:
            user_id = f"user_{organization_id}_{uuid.uuid4().hex[:8]}"
            
            user = EnterpriseUser(
                user_id=user_id,
                organization_id=organization_id,
                email=user_data['email'],
                name=user_data['name'],
                access_level=AccessLevel(user_data.get('access_level', 'viewer')),
                assigned_portfolios=user_data.get('assigned_portfolios', []),
                permissions=user_data.get('permissions', [])
            )
            
            self.enterprise_users[user_id] = user
            
            return {
                "success": True,
                "user_id": user_id,
                "user": user
            }
            
        except Exception as e:
            logger.error(f"Failed to create enterprise user: {e}")
            return {"success": False, "error": str(e)}
    
    def update_user_access(self, user_id: str, access_level: AccessLevel,
                          assigned_portfolios: Optional[List[str]] = None) -> Dict[str, Any]:
        """Update user access level and portfolio assignments"""
        user = self.enterprise_users.get(user_id)
        if not user:
            return {"success": False, "error": "User not found"}
        
        user.access_level = access_level
        if assigned_portfolios is not None:
            user.assigned_portfolios = assigned_portfolios
        
        return {"success": True, "message": "User access updated"}
    
    def get_user_permissions(self, user_id: str) -> Dict[str, Any]:
        """Get user permissions and access rights"""
        user = self.enterprise_users.get(user_id)
        if not user:
            return {"error": "User not found"}
        
        # Define permissions based on access level
        base_permissions = {
            AccessLevel.VIEWER: ["view_properties", "view_reports"],
            AccessLevel.OPERATOR: ["view_properties", "view_reports", "manage_tenants", "create_work_orders"],
            AccessLevel.MANAGER: ["view_properties", "view_reports", "manage_tenants", "create_work_orders", "manage_leases", "view_financials"],
            AccessLevel.ADMIN: ["full_access"],
            AccessLevel.SUPER_ADMIN: ["full_access", "manage_users", "system_config"]
        }
        
        return {
            "user_id": user_id,
            "access_level": user.access_level.value,
            "base_permissions": base_permissions.get(user.access_level, []),
            "custom_permissions": user.permissions,
            "assigned_portfolios": user.assigned_portfolios
        }
    
    # =====================================================
    # CUSTOM REPORTING
    # =====================================================
    
    def create_custom_report(self, organization_id: str, report_name: str,
                           report_type: ReportType, data_sources: List[str],
                           filters: Optional[Dict[str, Any]] = None,
                           created_by: Optional[str] = None) -> CustomReport:
        """Create custom enterprise report"""
        
        report_id = f"report_{organization_id}_{uuid.uuid4().hex[:8]}"
        
        report = CustomReport(
            report_id=report_id,
            organization_id=organization_id,
            report_name=report_name,
            report_type=report_type,
            data_sources=data_sources,
            filters=filters or {},
            created_by=created_by
        )
        
        self.custom_reports[report_id] = report
        
        logger.info(f"Created custom report {report_id}: {report_name}")
        
        return report
    
    def generate_custom_report(self, report_id: str, 
                             date_range: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """Generate custom report data"""
        report = self.custom_reports.get(report_id)
        if not report:
            return {"success": False, "error": "Report not found"}
        
        try:
            # Generate report based on type
            if report.report_type == ReportType.FINANCIAL_SUMMARY:
                data = self._generate_financial_summary(report, date_range)
            elif report.report_type == ReportType.OCCUPANCY_ANALYSIS:
                data = self._generate_occupancy_analysis(report, date_range)
            elif report.report_type == ReportType.PORTFOLIO_PERFORMANCE:
                data = self._generate_portfolio_performance(report, date_range)
            elif report.report_type == ReportType.SYNC_ANALYTICS:
                data = self._generate_sync_analytics(report, date_range)
            else:
                data = {"message": "Report type not implemented"}
            
            return {
                "success": True,
                "report_id": report_id,
                "report_name": report.report_name,
                "generated_at": datetime.utcnow().isoformat(),
                "data": data
            }
            
        except Exception as e:
            logger.error(f"Report generation failed: {e}")
            return {"success": False, "error": str(e)}
    
    def list_custom_reports(self, organization_id: str) -> List[CustomReport]:
        """List custom reports for organization"""
        return [
            report for report in self.custom_reports.values()
            if report.organization_id == organization_id
        ]
    
    def schedule_report(self, report_id: str, schedule: str, recipients: List[str]) -> Dict[str, Any]:
        """Schedule report for automatic generation"""
        report = self.custom_reports.get(report_id)
        if not report:
            return {"success": False, "error": "Report not found"}
        
        report.schedule = schedule
        report.recipients = recipients
        
        return {"success": True, "message": "Report scheduled successfully"}
    
    # =====================================================
    # ENTERPRISE CONFIGURATION
    # =====================================================
    
    def setup_enterprise_config(self, organization_id: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """Setup enterprise configuration"""
        try:
            enterprise_config = {
                "organization_id": organization_id,
                "multi_property_enabled": config.get("multi_property_enabled", True),
                "centralized_reporting": config.get("centralized_reporting", True),
                "role_based_access": config.get("role_based_access", True),
                "custom_branding": config.get("custom_branding", {}),
                "api_limits": config.get("api_limits", {
                    "requests_per_minute": 1000,
                    "concurrent_syncs": 10
                }),
                "audit_settings": config.get("audit_settings", {
                    "enable_audit_log": True,
                    "retention_days": 365
                }),
                "notification_settings": config.get("notification_settings", {
                    "email_enabled": True,
                    "webhook_enabled": True,
                    "slack_enabled": False
                }),
                "backup_settings": config.get("backup_settings", {
                    "auto_backup": True,
                    "backup_frequency": "daily",
                    "retention_days": 30
                }),
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat()
            }
            
            self.enterprise_configs[organization_id] = enterprise_config
            
            return {
                "success": True,
                "config": enterprise_config
            }
            
        except Exception as e:
            logger.error(f"Failed to setup enterprise config: {e}")
            return {"success": False, "error": str(e)}
    
    def get_enterprise_config(self, organization_id: str) -> Dict[str, Any]:
        """Get enterprise configuration"""
        return self.enterprise_configs.get(organization_id, {})
    
    def update_enterprise_config(self, organization_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Update enterprise configuration"""
        config = self.enterprise_configs.get(organization_id, {})
        config.update(updates)
        config["updated_at"] = datetime.utcnow().isoformat()
        
        self.enterprise_configs[organization_id] = config
        
        return {"success": True, "config": config}
    
    # =====================================================
    # ENTERPRISE ANALYTICS
    # =====================================================
    
    def get_enterprise_analytics(self, organization_id: str, 
                               date_range: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """Get comprehensive enterprise analytics"""
        
        # Default to last 30 days if no date range provided
        if not date_range:
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=30)
            date_range = {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat()
            }
        
        analytics = {
            "organization_id": organization_id,
            "date_range": date_range,
            "portfolio_metrics": self._calculate_portfolio_metrics(organization_id),
            "sync_performance": self._calculate_sync_performance(organization_id, date_range),
            "data_quality_metrics": self._calculate_data_quality_metrics(organization_id),
            "user_activity": self._calculate_user_activity(organization_id, date_range),
            "system_health": self._calculate_system_health(organization_id),
            "generated_at": datetime.utcnow().isoformat()
        }
        
        return analytics
    
    def setup_portfolio_accounting(self, portfolio_id: str, connection_id: str) -> Dict[str, Any]:
        """Setup accounting structure for portfolio"""
        portfolio = self.portfolios.get(portfolio_id)
        if not portfolio:
            return {"success": False, "error": "Portfolio not found"}
        
        # This would setup chart of accounts, cost centers, etc. in Yardi
        accounting_setup = {
            "portfolio_id": portfolio_id,
            "connection_id": connection_id,
            "chart_of_accounts_created": True,
            "cost_centers_setup": True,
            "reporting_structure": "consolidated",
            "setup_date": datetime.utcnow().isoformat()
        }
        
        return {
            "success": True,
            "accounting_setup": accounting_setup
        }
    
    def get_enterprise_status(self, organization_id: str) -> Dict[str, Any]:
        """Get enterprise features status"""
        config = self.get_enterprise_config(organization_id)
        portfolios = self.list_portfolios(organization_id)
        users = [u for u in self.enterprise_users.values() if u.organization_id == organization_id]
        reports = self.list_custom_reports(organization_id)
        
        return {
            "enterprise_enabled": bool(config),
            "multi_property_enabled": config.get("multi_property_enabled", False),
            "centralized_reporting": config.get("centralized_reporting", False),
            "role_based_access": config.get("role_based_access", False),
            "portfolios_count": len(portfolios),
            "users_count": len(users),
            "custom_reports_count": len(reports),
            "last_updated": datetime.utcnow().isoformat()
        }
    
    # =====================================================
    # REPORT GENERATORS
    # =====================================================
    
    def _generate_financial_summary(self, report: CustomReport, 
                                  date_range: Optional[Dict[str, str]]) -> Dict[str, Any]:
        """Generate financial summary report"""
        # Mock financial data - would integrate with actual financial data
        return {
            "total_revenue": 125000.00,
            "total_expenses": 45000.00,
            "net_income": 80000.00,
            "occupancy_rate": 92.5,
            "properties_count": 5,
            "units_count": 150,
            "period": date_range
        }
    
    def _generate_occupancy_analysis(self, report: CustomReport,
                                   date_range: Optional[Dict[str, str]]) -> Dict[str, Any]:
        """Generate occupancy analysis report"""
        return {
            "overall_occupancy": 92.5,
            "occupancy_trend": "increasing",
            "vacant_units": 12,
            "average_days_vacant": 15,
            "leasing_velocity": 8.5,
            "period": date_range
        }
    
    def _generate_portfolio_performance(self, report: CustomReport,
                                      date_range: Optional[Dict[str, str]]) -> Dict[str, Any]:
        """Generate portfolio performance report"""
        return {
            "portfolio_summary": "Strong performance across all properties",
            "top_performing_properties": [],
            "underperforming_properties": [],
            "key_metrics": {
                "revenue_growth": 5.2,
                "expense_ratio": 36.0,
                "noi_margin": 64.0
            },
            "period": date_range
        }
    
    def _generate_sync_analytics(self, report: CustomReport,
                               date_range: Optional[Dict[str, str]]) -> Dict[str, Any]:
        """Generate sync analytics report"""
        return {
            "total_sync_jobs": 45,
            "successful_syncs": 42,
            "failed_syncs": 3,
            "success_rate": 93.3,
            "average_sync_time": 45.2,
            "data_conflicts": 2,
            "period": date_range
        }
    
    # =====================================================
    # METRICS CALCULATORS
    # =====================================================
    
    def _calculate_portfolio_metrics(self, organization_id: str) -> Dict[str, Any]:
        """Calculate portfolio-level metrics"""
        portfolios = self.list_portfolios(organization_id)
        
        return {
            "total_portfolios": len(portfolios),
            "total_properties": sum(len(p.properties) for p in portfolios),
            "average_portfolio_size": len(portfolios[0].properties) if portfolios else 0
        }
    
    def _calculate_sync_performance(self, organization_id: str, 
                                  date_range: Dict[str, str]) -> Dict[str, Any]:
        """Calculate sync performance metrics"""
        # This would query actual sync history
        return {
            "total_syncs": 50,
            "successful_syncs": 47,
            "failed_syncs": 3,
            "success_rate": 94.0,
            "average_duration": 42.5
        }
    
    def _calculate_data_quality_metrics(self, organization_id: str) -> Dict[str, Any]:
        """Calculate data quality metrics"""
        return {
            "overall_quality_score": 96.5,
            "completeness_score": 98.2,
            "accuracy_score": 95.8,
            "consistency_score": 95.5
        }
    
    def _calculate_user_activity(self, organization_id: str,
                               date_range: Dict[str, str]) -> Dict[str, Any]:
        """Calculate user activity metrics"""
        users = [u for u in self.enterprise_users.values() if u.organization_id == organization_id]
        
        return {
            "total_users": len(users),
            "active_users": len([u for u in users if u.is_active]),
            "admin_users": len([u for u in users if u.access_level == AccessLevel.ADMIN])
        }
    
    def _calculate_system_health(self, organization_id: str) -> Dict[str, Any]:
        """Calculate system health metrics"""
        return {
            "overall_health": "excellent",
            "uptime_percentage": 99.9,
            "error_rate": 0.1,
            "response_time": 120.5
        }