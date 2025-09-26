"""
Smart Lease Renewal System - AI-Powered Lease Management
Enterprise-grade system for optimizing lease renewals through machine learning
"""

from .prediction_engine import SmartRenewalPredictionEngine
from .workflow_engine import AutomatedRenewalWorkflowEngine
from .pricing_intelligence import DynamicPricingIntelligence
from .risk_assessment import TenantRiskAssessment
from .portfolio_optimizer import PortfolioOptimizer
from .market_intelligence import MarketIntelligenceEngine
from .integration_manager import PlatformIntegrationManager
from .dashboard_service import RenewalDashboardService
from .ml_trainer import MLModelTrainer
from .continuous_learning import ContinuousLearningEngine

__version__ = "1.0.0"
__author__ = "EstateCore AI Team"

# Export main classes
__all__ = [
    'SmartRenewalPredictionEngine',
    'AutomatedRenewalWorkflowEngine', 
    'DynamicPricingIntelligence',
    'TenantRiskAssessment',
    'PortfolioOptimizer',
    'MarketIntelligenceEngine',
    'PlatformIntegrationManager',
    'RenewalDashboardService',
    'MLModelTrainer',
    'ContinuousLearningEngine'
]