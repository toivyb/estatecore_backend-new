"""
Portfolio Analytics Service for EstateCore Enterprise
Advanced analytics, aggregation, and reporting for multi-property portfolios
"""

import logging
from datetime import datetime, timedelta, date
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum
import pandas as pd
import numpy as np
from sqlalchemy import func, text, and_, or_, desc, asc
from sqlalchemy.orm import sessionmaker
from flask import current_app

from models.portfolio import (
    Portfolio, PortfolioMetric, PortfolioReport, PortfolioAlert,
    PropertyComparison, PortfolioStatus, PortfolioType
)
from models.property import Property, Unit, PropertyType, UnitStatus
from models.lease import Lease, LeaseStatus
from models.tenant import Tenant
from models.base import db

logger = logging.getLogger(__name__)


class AnalyticsTimeframe(Enum):
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"
    YTD = "ytd"
    CUSTOM = "custom"


class MetricType(Enum):
    FINANCIAL = "financial"
    OPERATIONAL = "operational"
    MARKET = "market"
    PERFORMANCE = "performance"
    RISK = "risk"


@dataclass
class AnalyticsQuery:
    """Query parameters for analytics operations"""
    portfolio_ids: List[int] = None
    property_ids: List[int] = None
    timeframe: AnalyticsTimeframe = AnalyticsTimeframe.MONTHLY
    start_date: date = None
    end_date: date = None
    metric_types: List[MetricType] = None
    group_by: str = None  # 'property', 'portfolio', 'location', 'property_type'
    compare_to: str = None  # 'previous_period', 'same_period_last_year', 'baseline'


class PortfolioAnalyticsService:
    """Comprehensive portfolio analytics and reporting service"""
    
    def __init__(self):
        self.db = db
    
    def get_portfolio_overview(self, organization_id: int, portfolio_ids: List[int] = None) -> Dict[str, Any]:
        """Get comprehensive portfolio overview with key metrics"""
        try:
            # Build base query
            query = Portfolio.query.filter_by(organization_id=organization_id, deleted_at=None)
            if portfolio_ids:
                query = query.filter(Portfolio.id.in_(portfolio_ids))
            
            portfolios = query.all()
            
            if not portfolios:
                return {"error": "No portfolios found"}
            
            # Aggregate metrics across all portfolios
            total_properties = 0
            total_units = 0
            occupied_units = 0
            total_value = 0
            total_acquisition_cost = 0
            property_types = set()
            locations = set()
            portfolios_data = []
            
            for portfolio in portfolios:
                metrics = portfolio.calculate_portfolio_metrics()
                
                total_properties += metrics['total_properties']
                total_units += metrics['total_units']
                occupied_units += metrics['occupied_units']
                total_value += metrics['total_value']
                total_acquisition_cost += metrics['total_acquisition_cost']
                property_types.update(metrics['property_types'])
                locations.update(metrics['locations'])
                
                portfolios_data.append({
                    'id': portfolio.id,
                    'name': portfolio.name,
                    'type': portfolio.portfolio_type.value,
                    'status': portfolio.status.value,
                    'properties': metrics['total_properties'],
                    'units': metrics['total_units'],
                    'occupancy_rate': metrics['portfolio_occupancy_rate'],
                    'value': metrics['total_value'],
                    'appreciation': metrics['portfolio_appreciation']
                })
            
            # Calculate overall metrics
            overall_occupancy = (occupied_units / total_units * 100) if total_units > 0 else 0
            overall_appreciation = ((total_value - total_acquisition_cost) / total_acquisition_cost * 100) if total_acquisition_cost > 0 else 0
            
            # Get recent performance trends
            performance_trends = self._get_performance_trends(portfolio_ids or [p.id for p in portfolios])
            
            # Get alerts and notifications
            alerts = self._get_active_alerts(portfolio_ids or [p.id for p in portfolios])
            
            return {
                'summary': {
                    'total_portfolios': len(portfolios),
                    'total_properties': total_properties,
                    'total_units': total_units,
                    'occupied_units': occupied_units,
                    'overall_occupancy_rate': round(overall_occupancy, 2),
                    'total_value': float(total_value),
                    'total_acquisition_cost': float(total_acquisition_cost),
                    'overall_appreciation': round(overall_appreciation, 2),
                    'property_types': list(property_types),
                    'locations': list(locations),
                    'location_count': len(locations)
                },
                'portfolios': portfolios_data,
                'performance_trends': performance_trends,
                'alerts': alerts,
                'last_updated': datetime.utcnow().isoformat()
            }
        
        except Exception as e:
            logger.error(f"Error getting portfolio overview: {str(e)}")
            return {"error": "Failed to retrieve portfolio overview"}
    
    def get_property_management_grid(self, organization_id: int, filters: Dict = None) -> Dict[str, Any]:
        """Get comprehensive property grid with all key metrics for management"""
        try:
            # Build base query
            query = db.session.query(Property).filter_by(organization_id=organization_id, deleted_at=None)
            
            # Apply filters
            if filters:
                if filters.get('portfolio_ids'):
                    query = query.filter(Property.portfolio_id.in_(filters['portfolio_ids']))
                if filters.get('property_types'):
                    query = query.filter(Property.property_type.in_(filters['property_types']))
                if filters.get('cities'):
                    query = query.filter(Property.city.in_(filters['cities']))
                if filters.get('occupancy_min'):
                    query = query.filter(Property.occupancy_rate >= filters['occupancy_min'])
                if filters.get('occupancy_max'):
                    query = query.filter(Property.occupancy_rate <= filters['occupancy_max'])
                if filters.get('value_min'):
                    query = query.filter(Property.current_value >= filters['value_min'])
                if filters.get('value_max'):
                    query = query.filter(Property.current_value <= filters['value_max'])
            
            # Apply sorting
            sort_by = filters.get('sort_by', 'name') if filters else 'name'
            sort_order = filters.get('sort_order', 'asc') if filters else 'asc'
            
            if hasattr(Property, sort_by):
                if sort_order == 'desc':
                    query = query.order_by(desc(getattr(Property, sort_by)))
                else:
                    query = query.order_by(asc(getattr(Property, sort_by)))
            
            properties = query.all()
            
            properties_data = []
            for property_obj in properties:
                # Calculate property metrics
                property_metrics = self._calculate_property_metrics(property_obj)
                
                # Get recent financial data
                recent_financial = self._get_recent_financial_data(property_obj.id)
                
                # Calculate health score
                health_score = self._calculate_property_health_score(property_obj)
                
                properties_data.append({
                    'id': property_obj.id,
                    'name': property_obj.name,
                    'type': property_obj.property_type.value,
                    'address': property_obj.full_address,
                    'city': property_obj.city,
                    'state': property_obj.state,
                    'portfolio_id': property_obj.portfolio_id,
                    'portfolio_name': property_obj.portfolio.name if property_obj.portfolio else None,
                    
                    # Basic metrics
                    'total_units': property_obj.total_units,
                    'occupied_units': property_metrics['occupied_units'],
                    'vacant_units': property_metrics['vacant_units'],
                    'occupancy_rate': round(property_obj.occupancy_rate or 0, 2),
                    'vacancy_rate': round(property_obj.vacancy_rate or 0, 2),
                    
                    # Financial metrics
                    'current_value': float(property_obj.current_value or 0),
                    'purchase_price': float(property_obj.purchase_price or 0),
                    'monthly_revenue': recent_financial.get('monthly_revenue', 0),
                    'monthly_expenses': recent_financial.get('monthly_expenses', 0),
                    'net_operating_income': recent_financial.get('noi', 0),
                    'cap_rate': recent_financial.get('cap_rate', 0),
                    
                    # Operational metrics
                    'maintenance_requests': property_metrics['active_maintenance_requests'],
                    'avg_lease_term': property_metrics['avg_lease_term'],
                    'tenant_satisfaction': property_metrics['tenant_satisfaction'],
                    'rent_collection_rate': property_metrics['rent_collection_rate'],
                    
                    # Performance indicators
                    'health_score': health_score,
                    'performance_rating': self._get_performance_rating(health_score),
                    'alerts_count': property_metrics['alerts_count'],
                    'last_inspection': property_metrics['last_inspection'],
                    
                    # Management info
                    'manager_id': property_obj.manager_id,
                    'year_built': property_obj.year_built,
                    'acquisition_date': property_obj.acquisition_date.isoformat() if property_obj.acquisition_date else None,
                    'is_active': property_obj.is_active
                })
            
            # Calculate summary statistics
            summary_stats = self._calculate_grid_summary_stats(properties_data)
            
            return {
                'properties': properties_data,
                'summary': summary_stats,
                'total_count': len(properties_data),
                'filters_applied': filters or {},
                'last_updated': datetime.utcnow().isoformat()
            }
        
        except Exception as e:
            logger.error(f"Error getting property management grid: {str(e)}")
            return {"error": "Failed to retrieve property management grid"}
    
    def get_financial_analytics(self, query: AnalyticsQuery) -> Dict[str, Any]:
        """Get comprehensive financial analytics and comparisons"""
        try:
            # Get portfolios based on query
            portfolios = self._get_portfolios_for_query(query)
            
            # Calculate financial metrics for each portfolio
            financial_data = []
            for portfolio in portfolios:
                portfolio_financials = self._calculate_portfolio_financials(portfolio, query)
                financial_data.append(portfolio_financials)
            
            # Aggregate metrics across portfolios
            aggregated_metrics = self._aggregate_financial_metrics(financial_data)
            
            # Generate comparison charts data
            comparison_data = self._generate_financial_comparisons(portfolios, query)
            
            # Calculate performance benchmarks
            benchmarks = self._calculate_financial_benchmarks(portfolios, query)
            
            # Generate cash flow analysis
            cash_flow_analysis = self._generate_cash_flow_analysis(portfolios, query)
            
            # ROI and CAP rate analysis
            roi_analysis = self._calculate_roi_analysis(portfolios, query)
            
            return {
                'aggregated_metrics': aggregated_metrics,
                'portfolio_financials': financial_data,
                'comparison_data': comparison_data,
                'benchmarks': benchmarks,
                'cash_flow_analysis': cash_flow_analysis,
                'roi_analysis': roi_analysis,
                'timeframe': query.timeframe.value,
                'query_params': {
                    'portfolio_ids': query.portfolio_ids,
                    'start_date': query.start_date.isoformat() if query.start_date else None,
                    'end_date': query.end_date.isoformat() if query.end_date else None
                },
                'generated_at': datetime.utcnow().isoformat()
            }
        
        except Exception as e:
            logger.error(f"Error getting financial analytics: {str(e)}")
            return {"error": "Failed to retrieve financial analytics"}
    
    def get_operational_analytics(self, query: AnalyticsQuery) -> Dict[str, Any]:
        """Get comprehensive operational analytics"""
        try:
            portfolios = self._get_portfolios_for_query(query)
            
            operational_data = []
            for portfolio in portfolios:
                portfolio_operations = self._calculate_operational_metrics(portfolio, query)
                operational_data.append(portfolio_operations)
            
            # Aggregate operational metrics
            aggregated_operations = self._aggregate_operational_metrics(operational_data)
            
            # Maintenance analytics
            maintenance_analytics = self._generate_maintenance_analytics(portfolios, query)
            
            # Tenant analytics
            tenant_analytics = self._generate_tenant_analytics(portfolios, query)
            
            # Lease analytics
            lease_analytics = self._generate_lease_analytics(portfolios, query)
            
            # Vendor performance
            vendor_analytics = self._generate_vendor_analytics(portfolios, query)
            
            # Energy and sustainability metrics
            sustainability_metrics = self._generate_sustainability_metrics(portfolios, query)
            
            return {
                'aggregated_operations': aggregated_operations,
                'portfolio_operations': operational_data,
                'maintenance_analytics': maintenance_analytics,
                'tenant_analytics': tenant_analytics,
                'lease_analytics': lease_analytics,
                'vendor_analytics': vendor_analytics,
                'sustainability_metrics': sustainability_metrics,
                'timeframe': query.timeframe.value,
                'generated_at': datetime.utcnow().isoformat()
            }
        
        except Exception as e:
            logger.error(f"Error getting operational analytics: {str(e)}")
            return {"error": "Failed to retrieve operational analytics"}
    
    def generate_portfolio_report(self, portfolio_id: int, report_type: str, 
                                report_period: str, user_id: int) -> Dict[str, Any]:
        """Generate comprehensive portfolio report"""
        try:
            portfolio = Portfolio.query.get(portfolio_id)
            if not portfolio:
                return {"error": "Portfolio not found"}
            
            # Create analytics query based on report period
            query = self._create_query_for_report(portfolio_id, report_period)
            
            # Generate report data based on type
            if report_type == 'financial':
                report_data = self.get_financial_analytics(query)
            elif report_type == 'operational':
                report_data = self.get_operational_analytics(query)
            elif report_type == 'performance':
                report_data = self._generate_performance_report(portfolio, query)
            elif report_type == 'compliance':
                report_data = self._generate_compliance_report(portfolio, query)
            else:
                report_data = self._generate_comprehensive_report(portfolio, query)
            
            # Create report record
            report = PortfolioReport(
                portfolio_id=portfolio_id,
                report_type=report_type,
                report_period=report_period,
                report_date=date.today(),
                title=f"{portfolio.name} {report_type.title()} Report - {report_period.title()}",
                description=f"Generated {report_type} report for {portfolio.name}",
                generated_by_id=user_id,
                report_data=report_data,
                status='generated'
            )
            
            db.session.add(report)
            db.session.commit()
            
            return {
                'report_id': report.id,
                'report_data': report_data,
                'generated_at': datetime.utcnow().isoformat()
            }
        
        except Exception as e:
            logger.error(f"Error generating portfolio report: {str(e)}")
            return {"error": "Failed to generate portfolio report"}
    
    def process_bulk_operations(self, operation_type: str, entity_type: str,
                              entity_ids: List[int], operation_data: Dict) -> Dict[str, Any]:
        """Process bulk operations across multiple properties/portfolios"""
        try:
            results = []
            errors = []
            
            for entity_id in entity_ids:
                try:
                    if entity_type == 'property':
                        result = self._process_property_bulk_operation(entity_id, operation_type, operation_data)
                    elif entity_type == 'portfolio':
                        result = self._process_portfolio_bulk_operation(entity_id, operation_type, operation_data)
                    else:
                        result = {"error": f"Unknown entity type: {entity_type}"}
                    
                    results.append({
                        'entity_id': entity_id,
                        'success': 'error' not in result,
                        'result': result
                    })
                
                except Exception as e:
                    errors.append({
                        'entity_id': entity_id,
                        'error': str(e)
                    })
            
            return {
                'total_processed': len(entity_ids),
                'successful': len([r for r in results if r['success']]),
                'failed': len(errors),
                'results': results,
                'errors': errors,
                'processed_at': datetime.utcnow().isoformat()
            }
        
        except Exception as e:
            logger.error(f"Error processing bulk operations: {str(e)}")
            return {"error": "Failed to process bulk operations"}
    
    # Helper methods
    
    def _get_performance_trends(self, portfolio_ids: List[int]) -> Dict[str, Any]:
        """Get performance trends for portfolios"""
        # Query recent metrics for trend analysis
        recent_metrics = db.session.query(PortfolioMetric).filter(
            PortfolioMetric.portfolio_id.in_(portfolio_ids),
            PortfolioMetric.metric_date >= date.today() - timedelta(days=90)
        ).order_by(PortfolioMetric.metric_date.desc()).all()
        
        # Calculate trends
        trends = {
            'occupancy_trend': self._calculate_trend([m.occupancy_rate for m in recent_metrics if m.occupancy_rate]),
            'revenue_trend': self._calculate_trend([float(m.gross_revenue) for m in recent_metrics if m.gross_revenue]),
            'noi_trend': self._calculate_trend([float(m.net_operating_income) for m in recent_metrics if m.net_operating_income]),
            'maintenance_trend': self._calculate_trend([float(m.maintenance_costs) for m in recent_metrics if m.maintenance_costs])
        }
        
        return trends
    
    def _get_active_alerts(self, portfolio_ids: List[int]) -> List[Dict]:
        """Get active alerts for portfolios"""
        alerts = PortfolioAlert.query.filter(
            PortfolioAlert.portfolio_id.in_(portfolio_ids),
            PortfolioAlert.status == 'active'
        ).order_by(PortfolioAlert.severity.desc(), PortfolioAlert.created_at.desc()).limit(10).all()
        
        return [{
            'id': alert.id,
            'portfolio_id': alert.portfolio_id,
            'title': alert.title,
            'message': alert.message,
            'severity': alert.severity,
            'created_at': alert.created_at.isoformat()
        } for alert in alerts]
    
    def _calculate_property_metrics(self, property_obj: Property) -> Dict[str, Any]:
        """Calculate comprehensive metrics for a property"""
        occupied_units = len([unit for unit in property_obj.units if unit.is_occupied])
        total_units = property_obj.total_units or len(property_obj.units)
        vacant_units = total_units - occupied_units
        
        # Get maintenance requests count
        active_maintenance = len([mr for mr in property_obj.maintenance_requests if mr.status in ['open', 'in_progress']])
        
        # Calculate average lease term
        active_leases = [lease for lease in property_obj.leases if lease.status == LeaseStatus.ACTIVE]
        avg_lease_term = sum([(lease.end_date - lease.start_date).days for lease in active_leases]) / len(active_leases) / 30 if active_leases else 0
        
        return {
            'occupied_units': occupied_units,
            'vacant_units': vacant_units,
            'active_maintenance_requests': active_maintenance,
            'avg_lease_term': round(avg_lease_term, 1),
            'tenant_satisfaction': 4.2,  # Placeholder - would come from surveys
            'rent_collection_rate': 95.5,  # Placeholder - would be calculated from payments
            'alerts_count': 0,  # Placeholder - would come from alerts
            'last_inspection': None  # Placeholder - would come from inspection records
        }
    
    def _get_recent_financial_data(self, property_id: int) -> Dict[str, float]:
        """Get recent financial data for a property"""
        # This would integrate with payment and expense tracking
        # For now, returning placeholder data
        return {
            'monthly_revenue': 25000.0,
            'monthly_expenses': 8000.0,
            'noi': 17000.0,
            'cap_rate': 6.8
        }
    
    def _calculate_property_health_score(self, property_obj: Property) -> float:
        """Calculate property health score based on multiple factors"""
        score = 100.0
        
        # Occupancy impact (30% weight)
        occupancy_rate = property_obj.occupancy_rate or 0
        if occupancy_rate < 85:
            score -= (85 - occupancy_rate) * 0.5
        
        # Age impact (20% weight)
        if property_obj.year_built:
            age = datetime.now().year - property_obj.year_built
            if age > 30:
                score -= (age - 30) * 0.3
        
        # Maintenance impact (25% weight)
        # This would be calculated based on maintenance requests and costs
        
        # Financial performance impact (25% weight)
        # This would be calculated based on NOI, cap rate, etc.
        
        return max(0, min(100, round(score, 1)))
    
    def _get_performance_rating(self, health_score: float) -> str:
        """Get performance rating based on health score"""
        if health_score >= 90:
            return "Excellent"
        elif health_score >= 80:
            return "Good"
        elif health_score >= 70:
            return "Fair"
        elif health_score >= 60:
            return "Poor"
        else:
            return "Critical"
    
    def _calculate_grid_summary_stats(self, properties_data: List[Dict]) -> Dict[str, Any]:
        """Calculate summary statistics for property grid"""
        if not properties_data:
            return {}
        
        total_properties = len(properties_data)
        total_units = sum(p['total_units'] for p in properties_data)
        total_occupied = sum(p['occupied_units'] for p in properties_data)
        total_value = sum(p['current_value'] for p in properties_data)
        
        avg_occupancy = sum(p['occupancy_rate'] for p in properties_data) / total_properties
        avg_health_score = sum(p['health_score'] for p in properties_data) / total_properties
        
        return {
            'total_properties': total_properties,
            'total_units': total_units,
            'total_occupied_units': total_occupied,
            'overall_occupancy_rate': round((total_occupied / total_units * 100) if total_units > 0 else 0, 2),
            'average_occupancy_rate': round(avg_occupancy, 2),
            'total_portfolio_value': total_value,
            'average_property_value': round(total_value / total_properties if total_properties > 0 else 0, 2),
            'average_health_score': round(avg_health_score, 1),
            'properties_by_rating': {
                'excellent': len([p for p in properties_data if p['performance_rating'] == 'Excellent']),
                'good': len([p for p in properties_data if p['performance_rating'] == 'Good']),
                'fair': len([p for p in properties_data if p['performance_rating'] == 'Fair']),
                'poor': len([p for p in properties_data if p['performance_rating'] == 'Poor']),
                'critical': len([p for p in properties_data if p['performance_rating'] == 'Critical'])
            }
        }
    
    def _calculate_trend(self, values: List[float]) -> Dict[str, Any]:
        """Calculate trend from a series of values"""
        if len(values) < 2:
            return {'direction': 'stable', 'percentage': 0.0}
        
        # Calculate percentage change from first to last value
        first_val = values[-1]  # Most recent
        last_val = values[0]   # Oldest
        
        if last_val == 0:
            return {'direction': 'stable', 'percentage': 0.0}
        
        percentage_change = ((first_val - last_val) / last_val) * 100
        
        if percentage_change > 2:
            direction = 'increasing'
        elif percentage_change < -2:
            direction = 'decreasing'
        else:
            direction = 'stable'
        
        return {
            'direction': direction,
            'percentage': round(percentage_change, 2)
        }
    
    def _get_portfolios_for_query(self, query: AnalyticsQuery) -> List[Portfolio]:
        """Get portfolios based on analytics query"""
        base_query = Portfolio.query.filter_by(deleted_at=None)
        
        if query.portfolio_ids:
            base_query = base_query.filter(Portfolio.id.in_(query.portfolio_ids))
        
        return base_query.all()
    
    def _calculate_portfolio_financials(self, portfolio: Portfolio, query: AnalyticsQuery) -> Dict[str, Any]:
        """Calculate financial metrics for a portfolio"""
        # This would involve complex financial calculations
        # For now, returning structured placeholder data
        return {
            'portfolio_id': portfolio.id,
            'portfolio_name': portfolio.name,
            'gross_revenue': 150000.0,
            'operating_expenses': 45000.0,
            'net_operating_income': 105000.0,
            'cash_flow': 95000.0,
            'cap_rate': 6.8,
            'roi': 12.5,
            'expense_ratio': 30.0,
            'debt_service_coverage': 1.45
        }
    
    def _aggregate_financial_metrics(self, financial_data: List[Dict]) -> Dict[str, Any]:
        """Aggregate financial metrics across portfolios"""
        if not financial_data:
            return {}
        
        total_revenue = sum(p['gross_revenue'] for p in financial_data)
        total_expenses = sum(p['operating_expenses'] for p in financial_data)
        total_noi = sum(p['net_operating_income'] for p in financial_data)
        avg_cap_rate = sum(p['cap_rate'] for p in financial_data) / len(financial_data)
        avg_roi = sum(p['roi'] for p in financial_data) / len(financial_data)
        
        return {
            'total_gross_revenue': total_revenue,
            'total_operating_expenses': total_expenses,
            'total_net_operating_income': total_noi,
            'average_cap_rate': round(avg_cap_rate, 2),
            'average_roi': round(avg_roi, 2),
            'profit_margin': round((total_noi / total_revenue * 100) if total_revenue > 0 else 0, 2),
            'expense_ratio': round((total_expenses / total_revenue * 100) if total_revenue > 0 else 0, 2)
        }
    
    # Additional helper methods would be implemented here for:
    # - _generate_financial_comparisons
    # - _calculate_financial_benchmarks  
    # - _generate_cash_flow_analysis
    # - _calculate_roi_analysis
    # - _calculate_operational_metrics
    # - _aggregate_operational_metrics
    # - _generate_maintenance_analytics
    # - _generate_tenant_analytics
    # - _generate_lease_analytics
    # - _generate_vendor_analytics
    # - _generate_sustainability_metrics
    # - And other specialized analytics methods


# Create service instance
portfolio_analytics_service = PortfolioAnalyticsService()


def get_portfolio_analytics_service() -> PortfolioAnalyticsService:
    """Get portfolio analytics service instance"""
    return portfolio_analytics_service