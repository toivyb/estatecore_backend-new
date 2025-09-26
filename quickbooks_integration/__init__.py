"""
EstateCore QuickBooks Online Integration

A comprehensive enterprise-grade QuickBooks Online integration for automated
accounting and financial management for property management companies.

Features:
- OAuth 2.0 authentication with QuickBooks Online
- Complete financial data synchronization
- Automated rent payment processing
- Expense categorization and tracking
- Invoice generation and management
- Multi-property accounting separation
- Enterprise-level error handling and reconciliation
"""

from .quickbooks_oauth_service import QuickBooksOAuthService
from .quickbooks_api_client import QuickBooksAPIClient
from .financial_sync_service import FinancialSyncService
from .automation_engine import QuickBooksAutomationEngine
from .data_mapping_service import DataMappingService
from .reconciliation_service import ReconciliationService
from .enterprise_features import EnterpriseQuickBooksService

__version__ = "1.0.0"
__author__ = "EstateCore Development Team"

# Main integration class for easy import
from .quickbooks_integration_service import QuickBooksIntegrationService

__all__ = [
    'QuickBooksOAuthService',
    'QuickBooksAPIClient', 
    'FinancialSyncService',
    'QuickBooksAutomationEngine',
    'DataMappingService',
    'ReconciliationService',
    'EnterpriseQuickBooksService',
    'QuickBooksIntegrationService'
]