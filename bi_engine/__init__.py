"""
Advanced Reporting and Business Intelligence Engine for EstateCore
================================================================

This module provides comprehensive business intelligence capabilities including:
- Unified data warehouse with normalized schemas
- Real-time data ingestion from integrated platforms  
- Custom report builder with drag-and-drop interface
- Executive dashboards with KPIs and analytics
- Predictive analytics and AI-powered insights
- Cross-platform analytics and comparison tools
- Enterprise features (RBAC, multi-tenancy, white-labeling)
"""

from .data_warehouse import DataWarehouseManager, DataWarehouseSchema
from .ingestion_engine import DataIngestionEngine, PlatformConnector
from .report_builder import ReportBuilder, CustomReport
from .dashboard_engine import DashboardEngine, ExecutiveDashboard
from .predictive_analytics import PredictiveAnalyticsEngine, AIInsights
from .cross_platform_analytics import CrossPlatformAnalytics
from .bi_api import BIAPIManager
from .performance_optimizer import PerformanceOptimizer
from .enterprise_features import EnterpriseFeatureManager

__version__ = "1.0.0"
__author__ = "EstateCore Development Team"

# Export main classes
__all__ = [
    'DataWarehouseManager',
    'DataIngestionEngine', 
    'ReportBuilder',
    'DashboardEngine',
    'PredictiveAnalyticsEngine',
    'CrossPlatformAnalytics',
    'BIAPIManager',
    'PerformanceOptimizer',
    'EnterpriseFeatureManager'
]