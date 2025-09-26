"""
Main QuickBooks Integration Service

Provides a unified interface to all QuickBooks integration functionality
including OAuth, API operations, synchronization, automation, and enterprise features.
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict
from enum import Enum
import asyncio
import uuid

from .quickbooks_oauth_service import QuickBooksOAuthService, QuickBooksConnection
from .quickbooks_api_client import QuickBooksAPIClient, QBOEntityType, QBOOperationType, QBORequest
from .financial_sync_service import FinancialSyncService, SyncDirection, SyncStatus
from .data_mapping_service import DataMappingService
from .automation_engine import QuickBooksAutomationEngine, WorkflowType
from .reconciliation_service import ReconciliationService
from .enterprise_features import EnterpriseQuickBooksService, AccessLevel, ReportType

logger = logging.getLogger(__name__)

class IntegrationStatus(Enum):
    """Overall integration status"""
    NOT_CONNECTED = "not_connected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    SYNCING = "syncing"
    ERROR = "error"
    MAINTENANCE = "maintenance"

@dataclass
class IntegrationHealth:
    """Health status of QuickBooks integration"""
    status: IntegrationStatus
    connection_health: Dict[str, Any]
    sync_health: Dict[str, Any]
    automation_health: Dict[str, Any]
    data_quality: Dict[str, Any]
    last_check: datetime
    issues: List[str] = None
    recommendations: List[str] = None
    
    def __post_init__(self):
        if self.issues is None:
            self.issues = []
        if self.recommendations is None:
            self.recommendations = []

class QuickBooksIntegrationService:
    """
    Main service class that provides unified access to all QuickBooks integration features
    """
    
    def __init__(self):
        # Initialize all service components
        self.oauth_service = QuickBooksOAuthService()
        self.api_client = QuickBooksAPIClient(self.oauth_service)
        self.mapping_service = DataMappingService()
        self.sync_service = FinancialSyncService(
            self.api_client, self.mapping_service, self.oauth_service
        )
        self.automation_engine = QuickBooksAutomationEngine(
            self.sync_service, self.api_client, self.oauth_service
        )
        self.reconciliation_service = ReconciliationService(
            self.api_client, self.oauth_service
        )
        self.enterprise_service = EnterpriseQuickBooksService(
            self.api_client, self.sync_service, self.mapping_service, self.reconciliation_service
        )
        
        # Integration state
        self.integration_health_cache: Dict[str, IntegrationHealth] = {}
        self.last_health_check: Dict[str, datetime] = {}
        
        logger.info("QuickBooks Integration Service initialized")
    
    # Connection Management
    
    def start_oauth_flow(self, organization_id: str) -> Dict[str, str]:
        """
        Start OAuth authentication flow for QuickBooks Online
        
        Returns:
            Dict with 'authorization_url' and 'state' for the OAuth flow
        """
        try:
            auth_url, state = self.oauth_service.generate_authorization_url(organization_id)
            
            return {
                "success": True,
                "authorization_url": auth_url,
                "state": state,
                "instructions": "Redirect user to authorization_url to complete QuickBooks connection"
            }
            
        except Exception as e:
            logger.error(f"Failed to start OAuth flow: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def complete_oauth_flow(self, code: str, state: str, realm_id: str) -> Dict[str, Any]:
        """
        Complete OAuth authentication flow
        
        Args:
            code: Authorization code from QuickBooks callback
            state: OAuth state parameter
            realm_id: QuickBooks Company ID
            
        Returns:
            Dict with connection details
        """
        try:
            connection = self.oauth_service.exchange_code_for_tokens(code, state, realm_id)
            
            # Test the connection
            test_result = self.api_client.test_connection(connection.connection_id)
            
            # Log the connection establishment
            self.reconciliation_service.log_operation(
                organization_id=connection.organization_id,
                connection_id=connection.connection_id,
                operation_type="connection_established",
                entity_type="connection",
                entity_id=connection.connection_id,
                success=True
            )
            
            return {
                "success": True,
                "connection_id": connection.connection_id,
                "company_name": connection.company_info.get("Name", "Unknown"),
                "company_id": connection.company_id,
                "connection_status": test_result,
                "message": "QuickBooks connection established successfully"
            }
            
        except Exception as e:
            logger.error(f"Failed to complete OAuth flow: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_connection_status(self, organization_id: str) -> Dict[str, Any]:
        """Get QuickBooks connection status for organization"""
        try:
            connection = self.oauth_service.get_organization_connection(organization_id)
            
            if not connection:
                return {
                    "connected": False,
                    "status": "not_connected",
                    "message": "No QuickBooks connection found"
                }
            
            # Test connection
            test_result = self.api_client.test_connection(connection.connection_id)
            
            return {
                "connected": True,
                "connection_id": connection.connection_id,
                "company_name": connection.company_info.get("Name", "Unknown"),
                "company_id": connection.company_id,
                "status": test_result["status"],
                "last_sync": connection.last_sync_at.isoformat() if connection.last_sync_at else None,
                "token_expires": connection.token_expires_at.isoformat(),
                "test_result": test_result
            }
            
        except Exception as e:
            logger.error(f"Error getting connection status: {e}")
            return {
                "connected": False,
                "status": "error",
                "error": str(e)
            }
    
    def disconnect_quickbooks(self, organization_id: str) -> Dict[str, Any]:
        """Disconnect QuickBooks integration"""
        try:
            connection = self.oauth_service.get_organization_connection(organization_id)
            
            if not connection:
                return {
                    "success": False,
                    "error": "No connection found"
                }
            
            # Revoke connection
            success = self.oauth_service.revoke_connection(connection.connection_id)
            
            if success:
                # Log disconnection
                self.reconciliation_service.log_operation(
                    organization_id=organization_id,
                    connection_id=connection.connection_id,
                    operation_type="connection_revoked",
                    entity_type="connection",
                    entity_id=connection.connection_id,
                    success=True
                )
                
                return {
                    "success": True,
                    "message": "QuickBooks connection disconnected successfully"
                }
            else:
                return {
                    "success": False,
                    "error": "Failed to revoke connection"
                }
                
        except Exception as e:
            logger.error(f"Error disconnecting QuickBooks: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    # Data Synchronization
    
    async def sync_all_data(self, organization_id: str, 
                          direction: str = "both") -> Dict[str, Any]:
        """
        Synchronize all data between EstateCore and QuickBooks
        
        Args:
            organization_id: Organization to sync
            direction: 'to_qb', 'from_qb', or 'both'
            
        Returns:
            Comprehensive sync results
        """
        try:
            connection = self.oauth_service.get_organization_connection(organization_id)
            if not connection:
                return {
                    "success": False,
                    "error": "No QuickBooks connection found"
                }
            
            results = {
                "sync_id": str(uuid.uuid4()),
                "organization_id": organization_id,
                "direction": direction,
                "started_at": datetime.now().isoformat(),
                "results": {}
            }
            
            # Sync to QuickBooks
            if direction in ["to_qb", "both"]:
                # Sync tenants to customers
                tenant_data = self._get_organization_tenants(organization_id)
                if tenant_data:
                    tenant_result = await self.sync_service.sync_tenants_to_customers(
                        organization_id, tenant_data
                    )
                    results["results"]["tenants_to_customers"] = asdict(tenant_result)
                
                # Sync payments
                payment_data = self._get_organization_payments(organization_id)
                if payment_data:
                    payment_result = await self.sync_service.sync_payments_to_quickbooks(
                        organization_id, payment_data
                    )
                    results["results"]["payments"] = asdict(payment_result)
                
                # Sync expenses
                expense_data = self._get_organization_expenses(organization_id)
                if expense_data:
                    expense_result = await self.sync_service.sync_expenses_to_quickbooks(
                        organization_id, expense_data
                    )
                    results["results"]["expenses"] = asdict(expense_result)
            
            # Sync from QuickBooks
            if direction in ["from_qb", "both"]:
                qb_sync_result = await self.sync_service.sync_from_quickbooks(
                    organization_id, ["customers", "invoices", "payments"]
                )
                results["results"]["from_quickbooks"] = asdict(qb_sync_result)
            
            # Update connection last sync time
            connection.last_sync_at = datetime.now()
            
            results["completed_at"] = datetime.now().isoformat()
            results["success"] = True
            
            return results
            
        except Exception as e:
            logger.error(f"Sync failed for organization {organization_id}: {e}")
            return {
                "success": False,
                "error": str(e),
                "organization_id": organization_id
            }
    
    def sync_entity_manual(self, organization_id: str, entity_type: str, 
                          entity_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Manually sync specific entities"""
        try:
            if entity_type == "tenants":
                result = asyncio.run(
                    self.sync_service.sync_tenants_to_customers(organization_id, entity_data)
                )
            elif entity_type == "payments":
                result = asyncio.run(
                    self.sync_service.sync_payments_to_quickbooks(organization_id, entity_data)
                )
            elif entity_type == "expenses":
                result = asyncio.run(
                    self.sync_service.sync_expenses_to_quickbooks(organization_id, entity_data)
                )
            else:
                return {
                    "success": False,
                    "error": f"Unsupported entity type: {entity_type}"
                }
            
            return {
                "success": True,
                "entity_type": entity_type,
                "sync_result": asdict(result)
            }
            
        except Exception as e:
            logger.error(f"Manual sync failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    # Automation Management
    
    def enable_automation(self, organization_id: str, 
                         workflow_types: Optional[List[str]] = None) -> Dict[str, Any]:
        """Enable automated workflows"""
        try:
            if workflow_types is None:
                workflow_types = ["rent_invoice_generation", "payment_sync", "late_fee_processing"]
            
            enabled_workflows = []
            
            for workflow_type in workflow_types:
                try:
                    wf_type = WorkflowType(workflow_type)
                    
                    # Create or update workflow schedule
                    workflow = self.automation_engine.create_workflow_schedule(
                        workflow_type=wf_type,
                        frequency="daily",
                        time_of_day="09:00",
                        enabled=True
                    )
                    
                    enabled_workflows.append({
                        "workflow_type": workflow_type,
                        "schedule_id": workflow.schedule_id,
                        "enabled": True
                    })
                    
                except ValueError:
                    logger.warning(f"Unknown workflow type: {workflow_type}")
            
            # Start the automation scheduler if not already running
            self.automation_engine.start_scheduler()
            
            return {
                "success": True,
                "enabled_workflows": enabled_workflows,
                "scheduler_running": True
            }
            
        except Exception as e:
            logger.error(f"Failed to enable automation: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def execute_workflow_manual(self, organization_id: str, workflow_type: str,
                               parameters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Manually execute a workflow"""
        try:
            wf_type = WorkflowType(workflow_type)
            
            execution_id = self.automation_engine.execute_workflow_manually(
                workflow_type=wf_type,
                organization_id=organization_id,
                parameters=parameters
            )
            
            return {
                "success": True,
                "execution_id": execution_id,
                "workflow_type": workflow_type,
                "status": "started"
            }
            
        except ValueError:
            return {
                "success": False,
                "error": f"Unknown workflow type: {workflow_type}"
            }
        except Exception as e:
            logger.error(f"Failed to execute workflow: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_automation_status(self, organization_id: str) -> Dict[str, Any]:
        """Get automation status and history"""
        try:
            # Get workflow schedules
            workflows = self.automation_engine.list_workflow_schedules()
            
            # Get execution history
            history = self.automation_engine.get_execution_history(limit=20)
            
            # Filter for organization
            org_history = [
                h for h in history 
                if h.get("organization_id") == organization_id
            ]
            
            return {
                "success": True,
                "scheduler_running": self.automation_engine.scheduler_running,
                "workflows": workflows,
                "recent_executions": org_history,
                "automation_enabled": len(workflows) > 0
            }
            
        except Exception as e:
            logger.error(f"Error getting automation status: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    # Data Quality and Reconciliation
    
    def perform_reconciliation(self, organization_id: str, 
                             entity_types: Optional[List[str]] = None,
                             period_days: int = 30) -> Dict[str, Any]:
        """Perform data reconciliation"""
        try:
            period_start = datetime.now() - timedelta(days=period_days)
            period_end = datetime.now()
            
            report = self.reconciliation_service.reconcile_data(
                organization_id=organization_id,
                entity_types=entity_types,
                period_start=period_start,
                period_end=period_end
            )
            
            return {
                "success": True,
                "reconciliation_report": asdict(report)
            }
            
        except Exception as e:
            logger.error(f"Reconciliation failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_data_quality_score(self, organization_id: str) -> Dict[str, Any]:
        """Get data quality and integrity score"""
        try:
            score_data = self.reconciliation_service.get_data_integrity_score(organization_id)
            
            # Get discrepancies
            discrepancies = self.reconciliation_service.get_discrepancies(
                organization_id=organization_id,
                status="unresolved"
            )
            
            return {
                "success": True,
                "data_quality": score_data,
                "unresolved_discrepancies": len(discrepancies),
                "discrepancies": discrepancies[:10]  # Latest 10
            }
            
        except Exception as e:
            logger.error(f"Error getting data quality score: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_audit_trail(self, organization_id: str, limit: int = 50) -> Dict[str, Any]:
        """Get audit trail for organization"""
        try:
            audit_logs = self.reconciliation_service.get_audit_trail(
                organization_id=organization_id,
                limit=limit
            )
            
            return {
                "success": True,
                "audit_logs": audit_logs,
                "total_entries": len(audit_logs)
            }
            
        except Exception as e:
            logger.error(f"Error getting audit trail: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    # Enterprise Features
    
    def setup_multi_property(self, organization_id: str, portfolio_name: str,
                           properties: List[str]) -> Dict[str, Any]:
        """Setup multi-property portfolio"""
        try:
            portfolio = self.enterprise_service.create_property_portfolio(
                organization_id=organization_id,
                portfolio_name=portfolio_name,
                properties=properties,
                consolidated_reporting=True
            )
            
            # Setup QuickBooks accounting structure
            connection = self.oauth_service.get_organization_connection(organization_id)
            if connection:
                setup_result = self.enterprise_service.setup_portfolio_accounting(
                    portfolio.portfolio_id, connection.connection_id
                )
                
                return {
                    "success": True,
                    "portfolio_id": portfolio.portfolio_id,
                    "portfolio_name": portfolio_name,
                    "properties_count": len(properties),
                    "accounting_setup": setup_result
                }
            else:
                return {
                    "success": True,
                    "portfolio_id": portfolio.portfolio_id,
                    "portfolio_name": portfolio_name,
                    "properties_count": len(properties),
                    "warning": "Portfolio created but QuickBooks accounting setup skipped (no connection)"
                }
                
        except Exception as e:
            logger.error(f"Failed to setup multi-property: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def create_custom_report(self, organization_id: str, report_name: str,
                           report_type: str, **kwargs) -> Dict[str, Any]:
        """Create custom financial report"""
        try:
            rpt_type = ReportType(report_type)
            
            report = self.enterprise_service.create_custom_report(
                organization_id=organization_id,
                report_name=report_name,
                report_type=rpt_type,
                **kwargs
            )
            
            return {
                "success": True,
                "report_id": report.report_id,
                "report_name": report_name,
                "report_type": report_type
            }
            
        except ValueError:
            return {
                "success": False,
                "error": f"Unknown report type: {report_type}"
            }
        except Exception as e:
            logger.error(f"Failed to create custom report: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def generate_report(self, report_id: str, 
                       date_range: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """Generate a custom report"""
        try:
            result = self.enterprise_service.generate_custom_report(
                report_id=report_id,
                date_range=date_range
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to generate report: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    # Health and Monitoring
    
    def get_integration_health(self, organization_id: str, 
                             force_refresh: bool = False) -> IntegrationHealth:
        """Get comprehensive integration health status"""
        
        # Check cache
        if not force_refresh and organization_id in self.integration_health_cache:
            cached_health = self.integration_health_cache[organization_id]
            last_check = self.last_health_check.get(organization_id, datetime.min)
            
            # Use cache if less than 5 minutes old
            if datetime.now() - last_check < timedelta(minutes=5):
                return cached_health
        
        try:
            # Check connection health
            connection_status = self.get_connection_status(organization_id)
            
            # Check sync health
            sync_config = self.sync_service.get_sync_configuration(organization_id)
            sync_history = self.sync_service.get_sync_history(organization_id, limit=10)
            
            # Check automation health
            automation_status = self.get_automation_status(organization_id)
            
            # Check data quality
            data_quality = self.get_data_quality_score(organization_id)
            
            # Determine overall status
            overall_status = IntegrationStatus.CONNECTED
            issues = []
            recommendations = []
            
            if not connection_status.get("connected"):
                overall_status = IntegrationStatus.NOT_CONNECTED
                issues.append("QuickBooks not connected")
                recommendations.append("Connect to QuickBooks Online to enable integration")
            
            elif connection_status.get("status") == "error":
                overall_status = IntegrationStatus.ERROR
                issues.append("QuickBooks connection error")
                recommendations.append("Check QuickBooks connection and refresh tokens")
            
            elif data_quality.get("success") and data_quality["data_quality"]["integrity_score"] < 90:
                overall_status = IntegrationStatus.ERROR
                issues.append("Low data quality score")
                recommendations.append("Perform data reconciliation to resolve discrepancies")
            
            # Create health object
            health = IntegrationHealth(
                status=overall_status,
                connection_health=connection_status,
                sync_health={
                    "configuration": asdict(sync_config) if sync_config else None,
                    "recent_syncs": sync_history
                },
                automation_health=automation_status,
                data_quality=data_quality,
                last_check=datetime.now(),
                issues=issues,
                recommendations=recommendations
            )
            
            # Cache result
            self.integration_health_cache[organization_id] = health
            self.last_health_check[organization_id] = datetime.now()
            
            return health
            
        except Exception as e:
            logger.error(f"Error checking integration health: {e}")
            return IntegrationHealth(
                status=IntegrationStatus.ERROR,
                connection_health={},
                sync_health={},
                automation_health={},
                data_quality={},
                last_check=datetime.now(),
                issues=[f"Health check failed: {str(e)}"],
                recommendations=["Contact support for assistance"]
            )
    
    def get_integration_summary(self, organization_id: str) -> Dict[str, Any]:
        """Get comprehensive integration summary"""
        try:
            health = self.get_integration_health(organization_id)
            connection_status = self.get_connection_status(organization_id)
            automation_status = self.get_automation_status(organization_id)
            data_quality = self.get_data_quality_score(organization_id)
            
            # Get enterprise features status
            portfolios = self.enterprise_service.list_portfolios(organization_id)
            custom_reports = self.enterprise_service.list_custom_reports(organization_id)
            
            return {
                "organization_id": organization_id,
                "overall_status": health.status.value,
                "connection": {
                    "connected": connection_status.get("connected", False),
                    "company_name": connection_status.get("company_name"),
                    "last_sync": connection_status.get("last_sync")
                },
                "automation": {
                    "enabled": automation_status.get("automation_enabled", False),
                    "scheduler_running": automation_status.get("scheduler_running", False),
                    "active_workflows": len(automation_status.get("workflows", []))
                },
                "data_quality": {
                    "score": data_quality.get("data_quality", {}).get("integrity_score", 0),
                    "unresolved_issues": data_quality.get("unresolved_discrepancies", 0)
                },
                "enterprise_features": {
                    "portfolios_count": len(portfolios),
                    "custom_reports_count": len(custom_reports)
                },
                "issues": health.issues,
                "recommendations": health.recommendations,
                "last_updated": health.last_check.isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting integration summary: {e}")
            return {
                "organization_id": organization_id,
                "overall_status": "error",
                "error": str(e)
            }
    
    # Private helper methods
    
    def _get_organization_tenants(self, organization_id: str) -> List[Dict[str, Any]]:
        """Get tenants for organization"""
        # This would query the EstateCore database
        # For now, return empty list
        return []
    
    def _get_organization_payments(self, organization_id: str) -> List[Dict[str, Any]]:
        """Get payments for organization"""
        # This would query the EstateCore database
        return []
    
    def _get_organization_expenses(self, organization_id: str) -> List[Dict[str, Any]]:
        """Get expenses for organization"""
        # This would query the EstateCore database
        return []

# Service instance
_integration_service = None

def get_quickbooks_integration_service() -> QuickBooksIntegrationService:
    """Get singleton integration service instance"""
    global _integration_service
    if _integration_service is None:
        _integration_service = QuickBooksIntegrationService()
    return _integration_service