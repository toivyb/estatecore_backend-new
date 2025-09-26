"""
Renewal Dashboard Service
Comprehensive management dashboard with AI insights for lease renewal operations
"""

import asyncio
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any, Union
from dataclasses import dataclass, asdict
from enum import Enum
import logging
import json
import statistics
from collections import defaultdict
import plotly.graph_objs as go
import plotly.utils
from dateutil.relativedelta import relativedelta

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DashboardModule(Enum):
    """Dashboard module types"""
    OVERVIEW = "overview"
    RENEWAL_PIPELINE = "renewal_pipeline"
    RISK_ASSESSMENT = "risk_assessment"
    PRICING_INTELLIGENCE = "pricing_intelligence"
    PORTFOLIO_OPTIMIZATION = "portfolio_optimization"
    MARKET_INTELLIGENCE = "market_intelligence"
    PERFORMANCE_ANALYTICS = "performance_analytics"
    WORKFLOW_MANAGEMENT = "workflow_management"

class MetricTimeframe(Enum):
    """Timeframe options for metrics"""
    LAST_7_DAYS = "7d"
    LAST_30_DAYS = "30d"
    LAST_90_DAYS = "90d"
    LAST_6_MONTHS = "6m"
    LAST_12_MONTHS = "12m"
    YTD = "ytd"
    CUSTOM = "custom"

@dataclass
class DashboardMetric:
    """Dashboard metric definition"""
    metric_id: str
    name: str
    value: Union[float, int, str]
    previous_value: Optional[Union[float, int, str]]
    change_percentage: Optional[float]
    trend: str  # 'up', 'down', 'stable'
    format_type: str  # 'number', 'percentage', 'currency', 'text'
    description: str
    category: str
    importance: str  # 'critical', 'important', 'informational'
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

@dataclass
class DashboardWidget:
    """Dashboard widget configuration"""
    widget_id: str
    widget_type: str  # 'metric', 'chart', 'table', 'map', 'alert'
    title: str
    module: DashboardModule
    position: Dict[str, int]  # x, y, width, height
    data: Any
    config: Dict[str, Any]
    refresh_interval: int  # seconds
    last_updated: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

@dataclass
class AlertRule:
    """Dashboard alert rule"""
    rule_id: str
    name: str
    metric_id: str
    condition: str  # 'greater_than', 'less_than', 'equals', 'change_greater_than'
    threshold: Union[float, int]
    severity: str  # 'low', 'medium', 'high', 'critical'
    enabled: bool
    last_triggered: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

class RenewalDashboardService:
    """
    Comprehensive dashboard service for lease renewal management
    """
    
    def __init__(self):
        # Dashboard configuration
        self.dashboard_config = {
            'refresh_intervals': {
                'real_time': 30,      # 30 seconds
                'frequent': 300,      # 5 minutes
                'standard': 900,      # 15 minutes
                'periodic': 3600      # 1 hour
            },
            'data_retention_days': 365,
            'max_alerts_per_user': 50
        }
        
        # Cached data for performance
        self.metric_cache = {}
        self.widget_cache = {}
        self.alert_cache = {}
        
        # Alert rules
        self.alert_rules = []
        
        # Dashboard layouts for different user types
        self.dashboard_layouts = {
            'executive': self._get_executive_layout(),
            'property_manager': self._get_property_manager_layout(),
            'leasing_agent': self._get_leasing_agent_layout(),
            'analyst': self._get_analyst_layout()
        }
    
    async def get_dashboard_data(self, 
                               user_type: str = 'property_manager',
                               timeframe: MetricTimeframe = MetricTimeframe.LAST_30_DAYS,
                               filters: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Get complete dashboard data for specified user type
        """
        try:
            logger.info(f"Generating dashboard data for {user_type} with timeframe {timeframe.value}")
            
            # Get dashboard layout
            layout = self.dashboard_layouts.get(user_type, self.dashboard_layouts['property_manager'])
            
            # Generate core metrics
            metrics = await self._generate_core_metrics(timeframe, filters)
            
            # Generate widgets based on layout
            widgets = await self._generate_widgets(layout, timeframe, filters)
            
            # Get active alerts
            alerts = await self._get_active_alerts(filters)
            
            # Generate insights
            insights = await self._generate_ai_insights(metrics, timeframe, filters)
            
            # Performance summary
            performance = await self._generate_performance_summary(timeframe, filters)
            
            return {
                'dashboard_type': user_type,
                'timeframe': timeframe.value,
                'last_updated': datetime.now().isoformat(),
                'metrics': metrics,
                'widgets': widgets,
                'alerts': alerts,
                'insights': insights,
                'performance_summary': performance,
                'layout': layout,
                'filters_applied': filters or {},
                'refresh_intervals': self.dashboard_config['refresh_intervals']
            }
            
        except Exception as e:
            logger.error(f"Error generating dashboard data: {str(e)}")
            return self._get_fallback_dashboard(user_type)
    
    async def _generate_core_metrics(self, 
                                   timeframe: MetricTimeframe,
                                   filters: Dict[str, Any] = None) -> List[DashboardMetric]:
        """
        Generate core renewal metrics
        """
        metrics = []
        
        # Simulate data - in production, this would query actual databases
        base_data = self._generate_sample_data(timeframe)
        
        # Renewal Rate
        renewal_rate = self._calculate_renewal_rate(base_data, timeframe)
        metrics.append(DashboardMetric(
            metric_id='renewal_rate',
            name='Renewal Rate',
            value=renewal_rate['current'],
            previous_value=renewal_rate['previous'],
            change_percentage=renewal_rate['change'],
            trend=renewal_rate['trend'],
            format_type='percentage',
            description='Percentage of leases successfully renewed',
            category='performance',
            importance='critical'
        ))
        
        # Average Rent Increase
        avg_increase = self._calculate_avg_rent_increase(base_data, timeframe)
        metrics.append(DashboardMetric(
            metric_id='avg_rent_increase',
            name='Average Rent Increase',
            value=avg_increase['current'],
            previous_value=avg_increase['previous'],
            change_percentage=avg_increase['change'],
            trend=avg_increase['trend'],
            format_type='percentage',
            description='Average rent increase across renewed leases',
            category='pricing',
            importance='important'
        ))
        
        # Revenue Impact
        revenue_impact = self._calculate_revenue_impact(base_data, timeframe)
        metrics.append(DashboardMetric(
            metric_id='revenue_impact',
            name='Revenue Impact',
            value=revenue_impact['current'],
            previous_value=revenue_impact['previous'],
            change_percentage=revenue_impact['change'],
            trend=revenue_impact['trend'],
            format_type='currency',
            description='Additional revenue from lease renewals',
            category='financial',
            importance='critical'
        ))
        
        # Portfolio Risk Score
        risk_score = self._calculate_portfolio_risk_score(base_data)
        metrics.append(DashboardMetric(
            metric_id='portfolio_risk_score',
            name='Portfolio Risk Score',
            value=risk_score['current'],
            previous_value=risk_score['previous'],
            change_percentage=risk_score['change'],
            trend=risk_score['trend'],
            format_type='number',
            description='Overall portfolio risk assessment (0-100)',
            category='risk',
            importance='important'
        ))
        
        # Active Workflows
        active_workflows = self._count_active_workflows(base_data)
        metrics.append(DashboardMetric(
            metric_id='active_workflows',
            name='Active Workflows',
            value=active_workflows['current'],
            previous_value=active_workflows['previous'],
            change_percentage=active_workflows['change'],
            trend=active_workflows['trend'],
            format_type='number',
            description='Number of active renewal workflows',
            category='operations',
            importance='informational'
        ))
        
        # Lease Expirations (Next 90 Days)
        expirations = self._count_upcoming_expirations(base_data)
        metrics.append(DashboardMetric(
            metric_id='upcoming_expirations',
            name='Upcoming Expirations',
            value=expirations['current'],
            previous_value=None,
            change_percentage=None,
            trend='stable',
            format_type='number',
            description='Leases expiring in the next 90 days',
            category='pipeline',
            importance='important'
        ))
        
        # Market Competitiveness
        market_score = self._calculate_market_competitiveness(base_data)
        metrics.append(DashboardMetric(
            metric_id='market_competitiveness',
            name='Market Competitiveness',
            value=market_score['current'],
            previous_value=market_score['previous'],
            change_percentage=market_score['change'],
            trend=market_score['trend'],
            format_type='percentage',
            description='Portfolio competitiveness vs market rates',
            category='market',
            importance='important'
        ))
        
        return metrics
    
    async def _generate_widgets(self, 
                              layout: List[Dict[str, Any]],
                              timeframe: MetricTimeframe,
                              filters: Dict[str, Any] = None) -> List[DashboardWidget]:
        """
        Generate dashboard widgets based on layout
        """
        widgets = []
        
        for widget_config in layout:
            try:
                widget = await self._create_widget(widget_config, timeframe, filters)
                if widget:
                    widgets.append(widget)
            except Exception as e:
                logger.error(f"Error creating widget {widget_config.get('widget_id')}: {str(e)}")
        
        return widgets
    
    async def _create_widget(self, 
                           config: Dict[str, Any],
                           timeframe: MetricTimeframe,
                           filters: Dict[str, Any] = None) -> Optional[DashboardWidget]:
        """
        Create individual dashboard widget
        """
        widget_type = config.get('widget_type')
        widget_id = config.get('widget_id')
        
        if widget_type == 'renewal_pipeline_chart':
            data = await self._generate_renewal_pipeline_chart(timeframe, filters)
        elif widget_type == 'risk_heatmap':
            data = await self._generate_risk_heatmap(filters)
        elif widget_type == 'pricing_trends_chart':
            data = await self._generate_pricing_trends_chart(timeframe, filters)
        elif widget_type == 'workflow_status_table':
            data = await self._generate_workflow_status_table(filters)
        elif widget_type == 'market_comparison_chart':
            data = await self._generate_market_comparison_chart(timeframe, filters)
        elif widget_type == 'performance_gauge':
            data = await self._generate_performance_gauge(timeframe, filters)
        elif widget_type == 'alert_list':
            data = await self._generate_alert_list(filters)
        elif widget_type == 'ai_recommendations':
            data = await self._generate_ai_recommendations(filters)
        else:
            logger.warning(f"Unknown widget type: {widget_type}")
            return None
        
        return DashboardWidget(
            widget_id=widget_id,
            widget_type=widget_type,
            title=config.get('title', 'Untitled Widget'),
            module=DashboardModule(config.get('module', 'overview')),
            position=config.get('position', {'x': 0, 'y': 0, 'width': 4, 'height': 4}),
            data=data,
            config=config.get('widget_config', {}),
            refresh_interval=config.get('refresh_interval', 900),
            last_updated=datetime.now()
        )
    
    async def _generate_renewal_pipeline_chart(self, 
                                             timeframe: MetricTimeframe,
                                             filters: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Generate renewal pipeline visualization
        """
        # Simulate pipeline data
        pipeline_stages = [
            'Upcoming (90+ days)',
            'Due Soon (30-90 days)',
            'Due Now (0-30 days)',
            'In Progress',
            'Awaiting Decision',
            'Renewed',
            'Not Renewed'
        ]
        
        # Sample data - would be actual counts from database
        stage_counts = [45, 78, 23, 15, 8, 67, 12]
        colors = ['#f39c12', '#e74c3c', '#e74c3c', '#3498db', '#f39c12', '#27ae60', '#95a5a6']
        
        # Create funnel chart
        chart_data = {
            'chart_type': 'funnel',
            'data': {
                'labels': pipeline_stages,
                'values': stage_counts,
                'colors': colors
            },
            'layout': {
                'title': 'Lease Renewal Pipeline',
                'showlegend': True,
                'annotations': [
                    {
                        'text': f'Total Properties: {sum(stage_counts)}',
                        'x': 0.5,
                        'y': -0.1,
                        'showarrow': False
                    }
                ]
            }
        }
        
        # Add summary statistics
        total_properties = sum(stage_counts)
        completed_renewals = stage_counts[5]  # Renewed
        completion_rate = (completed_renewals / total_properties * 100) if total_properties > 0 else 0
        
        chart_data['summary'] = {
            'total_properties': total_properties,
            'completed_renewals': completed_renewals,
            'completion_rate': round(completion_rate, 1),
            'properties_at_risk': stage_counts[1] + stage_counts[2],  # Due soon + Due now
            'in_progress': stage_counts[3] + stage_counts[4]  # In progress + Awaiting
        }
        
        return chart_data
    
    async def _generate_risk_heatmap(self, filters: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Generate risk assessment heatmap
        """
        # Simulate risk data by property
        properties = [f'Property {i}' for i in range(1, 21)]  # 20 properties
        risk_categories = ['Payment Risk', 'Behavioral Risk', 'Financial Risk', 'Market Risk']
        
        # Generate risk scores (0-100)
        risk_data = []
        for prop in properties:
            prop_risks = []
            for category in risk_categories:
                # Simulate varying risk levels
                risk_score = np.random.uniform(10, 90)
                prop_risks.append(risk_score)
            risk_data.append(prop_risks)
        
        # Create heatmap data
        heatmap_data = {
            'chart_type': 'heatmap',
            'data': {
                'z': risk_data,
                'x': risk_categories,
                'y': properties,
                'colorscale': [
                    [0, '#27ae60'],    # Low risk - green
                    [0.5, '#f39c12'],  # Medium risk - orange
                    [1, '#e74c3c']     # High risk - red
                ],
                'zmin': 0,
                'zmax': 100
            },
            'layout': {
                'title': 'Portfolio Risk Assessment Heatmap',
                'xaxis': {'title': 'Risk Categories'},
                'yaxis': {'title': 'Properties'},
                'annotations': []
            }
        }
        
        # Add risk level annotations
        for i, prop_risks in enumerate(risk_data):
            for j, risk_score in enumerate(prop_risks):
                color = 'white' if risk_score > 50 else 'black'
                heatmap_data['layout']['annotations'].append({
                    'x': risk_categories[j],
                    'y': properties[i],
                    'text': f'{risk_score:.0f}',
                    'showarrow': False,
                    'font': {'color': color, 'size': 10}
                })
        
        # Calculate summary statistics
        avg_risk_by_category = [np.mean([row[j] for row in risk_data]) for j in range(len(risk_categories))]
        highest_risk_property = properties[np.argmax([np.mean(row) for row in risk_data])]
        
        heatmap_data['summary'] = {
            'average_risk_by_category': {
                cat: round(score, 1) for cat, score in zip(risk_categories, avg_risk_by_category)
            },
            'highest_risk_property': highest_risk_property,
            'properties_high_risk': len([prop for i, prop in enumerate(properties) if np.mean(risk_data[i]) > 70]),
            'overall_portfolio_risk': round(np.mean([np.mean(row) for row in risk_data]), 1)
        }
        
        return heatmap_data
    
    async def _generate_pricing_trends_chart(self, 
                                           timeframe: MetricTimeframe,
                                           filters: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Generate pricing trends visualization
        """
        # Generate time series data
        end_date = datetime.now()
        if timeframe == MetricTimeframe.LAST_30_DAYS:
            start_date = end_date - timedelta(days=30)
            freq = 'D'
        elif timeframe == MetricTimeframe.LAST_90_DAYS:
            start_date = end_date - timedelta(days=90)
            freq = 'W'
        elif timeframe == MetricTimeframe.LAST_6_MONTHS:
            start_date = end_date - relativedelta(months=6)
            freq = 'W'
        else:
            start_date = end_date - relativedelta(months=12)
            freq = 'M'
        
        # Generate date range
        dates = pd.date_range(start=start_date, end=end_date, freq=freq)
        
        # Simulate pricing trends
        portfolio_avg = []
        market_avg = []
        base_portfolio = 1800
        base_market = 1850
        
        for i, date in enumerate(dates):
            # Simulate gradual increase with some volatility
            portfolio_rent = base_portfolio + (i * 15) + np.random.normal(0, 20)
            market_rent = base_market + (i * 12) + np.random.normal(0, 25)
            
            portfolio_avg.append(portfolio_rent)
            market_avg.append(market_rent)
        
        chart_data = {
            'chart_type': 'line',
            'data': {
                'x': [date.strftime('%Y-%m-%d') for date in dates],
                'series': [
                    {
                        'name': 'Portfolio Average Rent',
                        'y': [round(rent, 2) for rent in portfolio_avg],
                        'color': '#3498db',
                        'type': 'line'
                    },
                    {
                        'name': 'Market Average Rent',
                        'y': [round(rent, 2) for rent in market_avg],
                        'color': '#e74c3c',
                        'type': 'line'
                    }
                ]
            },
            'layout': {
                'title': 'Portfolio vs Market Rent Trends',
                'xaxis': {'title': 'Date'},
                'yaxis': {'title': 'Average Rent ($)'},
                'showlegend': True
            }
        }
        
        # Calculate trend statistics
        portfolio_growth = ((portfolio_avg[-1] - portfolio_avg[0]) / portfolio_avg[0]) * 100
        market_growth = ((market_avg[-1] - market_avg[0]) / market_avg[0]) * 100
        gap_percentage = ((market_avg[-1] - portfolio_avg[-1]) / market_avg[-1]) * 100
        
        chart_data['summary'] = {
            'portfolio_growth_percentage': round(portfolio_growth, 2),
            'market_growth_percentage': round(market_growth, 2),
            'current_gap_percentage': round(gap_percentage, 2),
            'current_portfolio_avg': round(portfolio_avg[-1], 2),
            'current_market_avg': round(market_avg[-1], 2),
            'trend_analysis': 'Portfolio rents tracking below market' if gap_percentage > 0 else 'Portfolio rents above market'
        }
        
        return chart_data
    
    async def _generate_workflow_status_table(self, filters: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Generate workflow status table
        """
        # Simulate active workflows
        workflows = []
        workflow_types = ['standard_renewal', 'retention_renewal', 'intensive_retention', 'early_renewal']
        statuses = ['pending', 'in_progress', 'awaiting_response', 'completed', 'failed']
        
        for i in range(1, 26):  # 25 workflows
            workflow = {
                'workflow_id': f'WF{i:04d}',
                'tenant_name': f'Tenant {i}',
                'property': f'Property {(i % 10) + 1}',
                'workflow_type': np.random.choice(workflow_types),
                'status': np.random.choice(statuses, p=[0.2, 0.3, 0.2, 0.25, 0.05]),
                'renewal_probability': round(np.random.uniform(0.3, 0.9), 2),
                'current_rent': round(np.random.uniform(1200, 2800), 2),
                'recommended_rent': 0,
                'lease_expiration': (datetime.now() + timedelta(days=np.random.randint(1, 180))).strftime('%Y-%m-%d'),
                'days_in_workflow': np.random.randint(1, 45),
                'next_action': '',
                'priority': np.random.choice(['low', 'medium', 'high'], p=[0.4, 0.4, 0.2])
            }
            
            # Calculate recommended rent
            increase_factor = np.random.uniform(1.0, 1.08)
            workflow['recommended_rent'] = round(workflow['current_rent'] * increase_factor, 2)
            
            # Set next action based on status
            if workflow['status'] == 'pending':
                workflow['next_action'] = 'Send initial notice'
            elif workflow['status'] == 'in_progress':
                workflow['next_action'] = 'Follow up with tenant'
            elif workflow['status'] == 'awaiting_response':
                workflow['next_action'] = 'Wait for tenant decision'
            elif workflow['status'] == 'completed':
                workflow['next_action'] = 'Archive workflow'
            else:
                workflow['next_action'] = 'Review and retry'
            
            workflows.append(workflow)
        
        # Sort by priority and days in workflow
        priority_order = {'high': 3, 'medium': 2, 'low': 1}
        workflows.sort(key=lambda x: (priority_order[x['priority']], -x['days_in_workflow']), reverse=True)
        
        table_data = {
            'table_type': 'workflow_status',
            'columns': [
                {'key': 'workflow_id', 'title': 'Workflow ID', 'sortable': True},
                {'key': 'tenant_name', 'title': 'Tenant', 'sortable': True},
                {'key': 'property', 'title': 'Property', 'sortable': True},
                {'key': 'status', 'title': 'Status', 'sortable': True, 'type': 'badge'},
                {'key': 'priority', 'title': 'Priority', 'sortable': True, 'type': 'badge'},
                {'key': 'renewal_probability', 'title': 'Renewal Prob.', 'sortable': True, 'type': 'percentage'},
                {'key': 'current_rent', 'title': 'Current Rent', 'sortable': True, 'type': 'currency'},
                {'key': 'recommended_rent', 'title': 'Recommended Rent', 'sortable': True, 'type': 'currency'},
                {'key': 'lease_expiration', 'title': 'Lease Expiration', 'sortable': True, 'type': 'date'},
                {'key': 'days_in_workflow', 'title': 'Days Active', 'sortable': True},
                {'key': 'next_action', 'title': 'Next Action', 'sortable': False}
            ],
            'data': workflows,
            'pagination': {
                'total_records': len(workflows),
                'page_size': 10,
                'current_page': 1
            }
        }
        
        # Add summary statistics
        status_counts = defaultdict(int)
        priority_counts = defaultdict(int)
        for workflow in workflows:
            status_counts[workflow['status']] += 1
            priority_counts[workflow['priority']] += 1
        
        table_data['summary'] = {
            'total_workflows': len(workflows),
            'status_breakdown': dict(status_counts),
            'priority_breakdown': dict(priority_counts),
            'avg_days_active': round(statistics.mean([w['days_in_workflow'] for w in workflows]), 1),
            'high_priority_count': priority_counts['high']
        }
        
        return table_data
    
    async def _generate_market_comparison_chart(self, 
                                              timeframe: MetricTimeframe,
                                              filters: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Generate market comparison visualization
        """
        # Simulate market comparison data
        property_types = ['1 Bed', '2 Bed', '3 Bed', '4+ Bed']
        portfolio_rents = [1450, 1850, 2350, 2950]
        market_rents = [1520, 1920, 2420, 3100]
        competitor_rents = [1480, 1890, 2380, 3020]
        
        chart_data = {
            'chart_type': 'grouped_bar',
            'data': {
                'categories': property_types,
                'series': [
                    {
                        'name': 'Portfolio Average',
                        'data': portfolio_rents,
                        'color': '#3498db'
                    },
                    {
                        'name': 'Market Average',
                        'data': market_rents,
                        'color': '#e74c3c'
                    },
                    {
                        'name': 'Competitor Average',
                        'data': competitor_rents,
                        'color': '#f39c12'
                    }
                ]
            },
            'layout': {
                'title': 'Rent Comparison by Property Type',
                'xaxis': {'title': 'Property Type'},
                'yaxis': {'title': 'Average Rent ($)'},
                'showlegend': True,
                'bargap': 0.2
            }
        }
        
        # Calculate positioning metrics
        below_market_count = sum(1 for i in range(len(portfolio_rents)) if portfolio_rents[i] < market_rents[i])
        avg_market_gap = statistics.mean([(market_rents[i] - portfolio_rents[i]) / market_rents[i] * 100 
                                        for i in range(len(portfolio_rents))])
        
        chart_data['summary'] = {
            'property_types_below_market': below_market_count,
            'average_market_gap_percentage': round(avg_market_gap, 1),
            'total_revenue_opportunity': sum(market_rents[i] - portfolio_rents[i] for i in range(len(portfolio_rents))),
            'competitive_position': 'Below Market' if avg_market_gap > 0 else 'Above Market',
            'recommendation': 'Consider selective rent increases' if avg_market_gap > 2 else 'Monitor market trends'
        }
        
        return chart_data
    
    async def _generate_performance_gauge(self, 
                                        timeframe: MetricTimeframe,
                                        filters: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Generate performance gauge widget
        """
        # Simulate performance score calculation
        renewal_rate = 0.87  # 87%
        revenue_growth = 0.045  # 4.5%
        risk_score = 35  # 35/100
        efficiency_score = 0.92  # 92%
        
        # Calculate composite performance score
        performance_score = (
            renewal_rate * 30 +
            min(revenue_growth * 10, 0.5) * 25 +
            (100 - risk_score) / 100 * 25 +
            efficiency_score * 20
        )
        
        # Performance level
        if performance_score >= 90:
            performance_level = 'Excellent'
            color = '#27ae60'
        elif performance_score >= 75:
            performance_level = 'Good'
            color = '#3498db'
        elif performance_score >= 60:
            performance_level = 'Fair'
            color = '#f39c12'
        else:
            performance_level = 'Poor'
            color = '#e74c3c'
        
        gauge_data = {
            'widget_type': 'gauge',
            'data': {
                'value': round(performance_score, 1),
                'min_value': 0,
                'max_value': 100,
                'color': color,
                'ranges': [
                    {'from': 0, 'to': 60, 'color': '#e74c3c'},
                    {'from': 60, 'to': 75, 'color': '#f39c12'},
                    {'from': 75, 'to': 90, 'color': '#3498db'},
                    {'from': 90, 'to': 100, 'color': '#27ae60'}
                ]
            },
            'layout': {
                'title': f'Overall Performance Score: {performance_level}',
                'annotations': [
                    {
                        'text': f'{performance_score:.1f}/100',
                        'x': 0.5,
                        'y': 0.3,
                        'font': {'size': 24, 'color': color}
                    }
                ]
            }
        }
        
        # Add performance breakdown
        gauge_data['breakdown'] = {
            'renewal_rate_contribution': round(renewal_rate * 30, 1),
            'revenue_growth_contribution': round(min(revenue_growth * 10, 0.5) * 25, 1),
            'risk_management_contribution': round((100 - risk_score) / 100 * 25, 1),
            'efficiency_contribution': round(efficiency_score * 20, 1),
            'improvement_areas': []
        }
        
        # Identify improvement areas
        if renewal_rate < 0.85:
            gauge_data['breakdown']['improvement_areas'].append('Focus on tenant retention')
        if revenue_growth < 0.03:
            gauge_data['breakdown']['improvement_areas'].append('Optimize pricing strategy')
        if risk_score > 45:
            gauge_data['breakdown']['improvement_areas'].append('Reduce portfolio risk')
        if efficiency_score < 0.90:
            gauge_data['breakdown']['improvement_areas'].append('Improve operational efficiency')
        
        return gauge_data
    
    async def _generate_alert_list(self, filters: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Generate active alerts list
        """
        # Simulate active alerts
        alerts = [
            {
                'alert_id': 'ALT001',
                'title': 'High Churn Risk - Property 5',
                'message': '3 tenants in Property 5 have churn risk > 80%',
                'severity': 'high',
                'category': 'risk',
                'created_at': datetime.now() - timedelta(hours=2),
                'status': 'active',
                'action_required': True,
                'recommended_action': 'Schedule tenant retention meetings'
            },
            {
                'alert_id': 'ALT002',
                'title': 'Pricing Opportunity',
                'message': 'Unit 2B rent is 15% below market rate',
                'severity': 'medium',
                'category': 'pricing',
                'created_at': datetime.now() - timedelta(hours=6),
                'status': 'active',
                'action_required': False,
                'recommended_action': 'Review for next renewal cycle'
            },
            {
                'alert_id': 'ALT003',
                'title': 'Workflow Overdue',
                'message': 'Renewal workflow WF0042 has been active for 35 days',
                'severity': 'medium',
                'category': 'workflow',
                'created_at': datetime.now() - timedelta(hours=12),
                'status': 'active',
                'action_required': True,
                'recommended_action': 'Escalate to property manager'
            },
            {
                'alert_id': 'ALT004',
                'title': 'Market Trend Alert',
                'message': 'Local vacancy rate increased to 12% (up from 8%)',
                'severity': 'low',
                'category': 'market',
                'created_at': datetime.now() - timedelta(days=1),
                'status': 'active',
                'action_required': False,
                'recommended_action': 'Monitor for competitive pressure'
            }
        ]
        
        # Sort by severity and creation time
        severity_order = {'high': 3, 'medium': 2, 'low': 1}
        alerts.sort(key=lambda x: (severity_order[x['severity']], x['created_at']), reverse=True)
        
        alert_data = {
            'widget_type': 'alert_list',
            'alerts': alerts,
            'summary': {
                'total_alerts': len(alerts),
                'high_severity': len([a for a in alerts if a['severity'] == 'high']),
                'action_required': len([a for a in alerts if a['action_required']]),
                'categories': list(set([a['category'] for a in alerts]))
            }
        }
        
        return alert_data
    
    async def _generate_ai_recommendations(self, filters: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Generate AI-powered recommendations
        """
        recommendations = [
            {
                'recommendation_id': 'REC001',
                'title': 'Optimize Lease Staggering',
                'description': 'Consider adjusting lease terms to better distribute expiration dates throughout the year',
                'category': 'portfolio_optimization',
                'impact_level': 'medium',
                'confidence': 0.85,
                'estimated_benefit': '$12,500 annual revenue protection',
                'implementation_effort': 'low',
                'timeline': '30-60 days',
                'details': [
                    '23% of leases expire in June-August',
                    'Target 8-10% per month for optimal distribution',
                    'Offer 14-month leases for Q2 expirations'
                ]
            },
            {
                'recommendation_id': 'REC002',
                'title': 'Implement Predictive Maintenance',
                'description': 'Use tenant satisfaction patterns to predict and prevent maintenance issues',
                'category': 'risk_management',
                'impact_level': 'high',
                'confidence': 0.92,
                'estimated_benefit': '15% reduction in tenant churn',
                'implementation_effort': 'medium',
                'timeline': '60-90 days',
                'details': [
                    'Properties with 4+ maintenance requests show 40% higher churn',
                    'Proactive maintenance reduces complaints by 60%',
                    'Focus on HVAC and plumbing preventive care'
                ]
            },
            {
                'recommendation_id': 'REC003',
                'title': 'Market-Based Pricing Strategy',
                'description': 'Implement dynamic pricing based on real-time market conditions',
                'category': 'pricing_optimization',
                'impact_level': 'high',
                'confidence': 0.78,
                'estimated_benefit': '$45,000 annual revenue increase',
                'implementation_effort': 'high',
                'timeline': '90-120 days',
                'details': [
                    'Current rents average 5.2% below market',
                    '67% of tenants would accept 3-5% increases',
                    'Gradual implementation reduces churn risk'
                ]
            }
        ]
        
        recommendation_data = {
            'widget_type': 'ai_recommendations',
            'recommendations': recommendations,
            'summary': {
                'total_recommendations': len(recommendations),
                'high_impact': len([r for r in recommendations if r['impact_level'] == 'high']),
                'estimated_total_benefit': '$57,500',
                'avg_confidence': round(statistics.mean([r['confidence'] for r in recommendations]), 2)
            }
        }
        
        return recommendation_data
    
    async def _get_active_alerts(self, filters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """
        Get active dashboard alerts
        """
        # This would query the actual alert system
        active_alerts = [
            {
                'alert_id': 'DASH001',
                'type': 'threshold_breach',
                'message': 'Renewal rate dropped below 85% threshold',
                'severity': 'high',
                'triggered_at': datetime.now() - timedelta(minutes=15),
                'acknowledged': False
            },
            {
                'alert_id': 'DASH002',
                'type': 'trend_alert',
                'message': 'Revenue growth trending downward for 3 consecutive weeks',
                'severity': 'medium',
                'triggered_at': datetime.now() - timedelta(hours=2),
                'acknowledged': False
            }
        ]
        
        return active_alerts
    
    async def _generate_ai_insights(self, 
                                  metrics: List[DashboardMetric],
                                  timeframe: MetricTimeframe,
                                  filters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """
        Generate AI-powered insights from dashboard data
        """
        insights = []
        
        # Analyze renewal rate trends
        renewal_metric = next((m for m in metrics if m.metric_id == 'renewal_rate'), None)
        if renewal_metric and renewal_metric.change_percentage:
            if renewal_metric.change_percentage < -5:
                insights.append({
                    'insight_id': 'INS001',
                    'type': 'trend_analysis',
                    'title': 'Declining Renewal Rates',
                    'description': f'Renewal rates have decreased by {abs(renewal_metric.change_percentage):.1f}% - investigate tenant satisfaction and market conditions',
                    'severity': 'high',
                    'confidence': 0.87,
                    'recommended_actions': [
                        'Conduct tenant satisfaction survey',
                        'Review competitive positioning',
                        'Assess recent policy changes'
                    ]
                })
        
        # Analyze pricing opportunities
        pricing_metric = next((m for m in metrics if m.metric_id == 'market_competitiveness'), None)
        if pricing_metric and pricing_metric.value < 95:  # Below 95% of market
            insights.append({
                'insight_id': 'INS002',
                'type': 'opportunity_analysis',
                'title': 'Pricing Optimization Opportunity',
                'description': f'Portfolio rents are {100 - pricing_metric.value:.1f}% below market - potential for selective increases',
                'severity': 'medium',
                'confidence': 0.73,
                'recommended_actions': [
                    'Analyze tenant-by-tenant pricing sensitivity',
                    'Implement gradual increase strategy',
                    'Monitor competitor actions'
                ]
            })
        
        # Risk pattern analysis
        risk_metric = next((m for m in metrics if m.metric_id == 'portfolio_risk_score'), None)
        if risk_metric and risk_metric.value > 60:
            insights.append({
                'insight_id': 'INS003',
                'type': 'risk_analysis',
                'title': 'Elevated Portfolio Risk',
                'description': f'Portfolio risk score of {risk_metric.value} indicates need for proactive risk management',
                'severity': 'medium',
                'confidence': 0.91,
                'recommended_actions': [
                    'Focus on high-risk tenant retention',
                    'Implement enhanced screening',
                    'Diversify tenant mix'
                ]
            })
        
        return insights
    
    async def _generate_performance_summary(self, 
                                          timeframe: MetricTimeframe,
                                          filters: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Generate performance summary
        """
        return {
            'overall_score': 82.5,
            'score_change': 3.2,
            'key_achievements': [
                'Renewal rate improved by 4.2%',
                'Revenue increased by $23,500',
                'Risk score reduced by 8 points'
            ],
            'areas_for_improvement': [
                'Lease expiration clustering',
                'Market competitiveness',
                'Workflow efficiency'
            ],
            'period_comparison': {
                'current_period': timeframe.value,
                'metrics_improved': 6,
                'metrics_declined': 2,
                'metrics_stable': 4
            }
        }
    
    # Dashboard layout configurations
    
    def _get_executive_layout(self) -> List[Dict[str, Any]]:
        """Executive dashboard layout"""
        return [
            {
                'widget_id': 'exec_overview',
                'widget_type': 'performance_gauge',
                'title': 'Portfolio Performance',
                'module': 'overview',
                'position': {'x': 0, 'y': 0, 'width': 6, 'height': 4},
                'refresh_interval': 900
            },
            {
                'widget_id': 'exec_revenue',
                'widget_type': 'pricing_trends_chart',
                'title': 'Revenue Trends',
                'module': 'pricing_intelligence',
                'position': {'x': 6, 'y': 0, 'width': 6, 'height': 4},
                'refresh_interval': 3600
            },
            {
                'widget_id': 'exec_pipeline',
                'widget_type': 'renewal_pipeline_chart',
                'title': 'Renewal Pipeline',
                'module': 'renewal_pipeline',
                'position': {'x': 0, 'y': 4, 'width': 8, 'height': 4},
                'refresh_interval': 1800
            },
            {
                'widget_id': 'exec_insights',
                'widget_type': 'ai_recommendations',
                'title': 'AI Insights',
                'module': 'performance_analytics',
                'position': {'x': 8, 'y': 4, 'width': 4, 'height': 4},
                'refresh_interval': 3600
            }
        ]
    
    def _get_property_manager_layout(self) -> List[Dict[str, Any]]:
        """Property manager dashboard layout"""
        return [
            {
                'widget_id': 'pm_pipeline',
                'widget_type': 'renewal_pipeline_chart',
                'title': 'Renewal Pipeline',
                'module': 'renewal_pipeline',
                'position': {'x': 0, 'y': 0, 'width': 8, 'height': 4},
                'refresh_interval': 300
            },
            {
                'widget_id': 'pm_alerts',
                'widget_type': 'alert_list',
                'title': 'Active Alerts',
                'module': 'overview',
                'position': {'x': 8, 'y': 0, 'width': 4, 'height': 4},
                'refresh_interval': 300
            },
            {
                'widget_id': 'pm_workflows',
                'widget_type': 'workflow_status_table',
                'title': 'Active Workflows',
                'module': 'workflow_management',
                'position': {'x': 0, 'y': 4, 'width': 12, 'height': 6},
                'refresh_interval': 300
            },
            {
                'widget_id': 'pm_risk',
                'widget_type': 'risk_heatmap',
                'title': 'Risk Assessment',
                'module': 'risk_assessment',
                'position': {'x': 0, 'y': 10, 'width': 12, 'height': 4},
                'refresh_interval': 1800
            }
        ]
    
    def _get_leasing_agent_layout(self) -> List[Dict[str, Any]]:
        """Leasing agent dashboard layout"""
        return [
            {
                'widget_id': 'la_workflows',
                'widget_type': 'workflow_status_table',
                'title': 'My Active Renewals',
                'module': 'workflow_management',
                'position': {'x': 0, 'y': 0, 'width': 12, 'height': 6},
                'refresh_interval': 300
            },
            {
                'widget_id': 'la_pipeline',
                'widget_type': 'renewal_pipeline_chart',
                'title': 'Renewal Pipeline',
                'module': 'renewal_pipeline',
                'position': {'x': 0, 'y': 6, 'width': 6, 'height': 4},
                'refresh_interval': 900
            },
            {
                'widget_id': 'la_market',
                'widget_type': 'market_comparison_chart',
                'title': 'Market Comparison',
                'module': 'market_intelligence',
                'position': {'x': 6, 'y': 6, 'width': 6, 'height': 4},
                'refresh_interval': 3600
            }
        ]
    
    def _get_analyst_layout(self) -> List[Dict[str, Any]]:
        """Analyst dashboard layout"""
        return [
            {
                'widget_id': 'analyst_trends',
                'widget_type': 'pricing_trends_chart',
                'title': 'Pricing Trends Analysis',
                'module': 'pricing_intelligence',
                'position': {'x': 0, 'y': 0, 'width': 8, 'height': 4},
                'refresh_interval': 1800
            },
            {
                'widget_id': 'analyst_performance',
                'widget_type': 'performance_gauge',
                'title': 'Performance Score',
                'module': 'performance_analytics',
                'position': {'x': 8, 'y': 0, 'width': 4, 'height': 4},
                'refresh_interval': 1800
            },
            {
                'widget_id': 'analyst_market',
                'widget_type': 'market_comparison_chart',
                'title': 'Market Position Analysis',
                'module': 'market_intelligence',
                'position': {'x': 0, 'y': 4, 'width': 6, 'height': 4},
                'refresh_interval': 3600
            },
            {
                'widget_id': 'analyst_risk',
                'widget_type': 'risk_heatmap',
                'title': 'Portfolio Risk Heatmap',
                'module': 'risk_assessment',
                'position': {'x': 6, 'y': 4, 'width': 6, 'height': 4},
                'refresh_interval': 1800
            },
            {
                'widget_id': 'analyst_insights',
                'widget_type': 'ai_recommendations',
                'title': 'AI Recommendations',
                'module': 'portfolio_optimization',
                'position': {'x': 0, 'y': 8, 'width': 12, 'height': 4},
                'refresh_interval': 3600
            }
        ]
    
    # Utility methods for data generation
    
    def _generate_sample_data(self, timeframe: MetricTimeframe) -> Dict[str, Any]:
        """Generate sample data for calculations"""
        # This would be replaced with actual database queries
        return {
            'total_properties': 150,
            'total_leases': 148,
            'renewed_leases_current': 89,
            'renewed_leases_previous': 82,
            'avg_rent_increase_current': 0.043,
            'avg_rent_increase_previous': 0.038,
            'revenue_impact_current': 125000,
            'revenue_impact_previous': 108000,
            'portfolio_risk_current': 42,
            'portfolio_risk_previous': 46,
            'active_workflows_current': 23,
            'active_workflows_previous': 28,
            'market_competitiveness_current': 0.923,
            'market_competitiveness_previous': 0.931
        }
    
    def _calculate_renewal_rate(self, data: Dict[str, Any], timeframe: MetricTimeframe) -> Dict[str, Any]:
        """Calculate renewal rate metrics"""
        current = data['renewed_leases_current'] / data['total_leases']
        previous = data['renewed_leases_previous'] / data['total_leases']
        change = ((current - previous) / previous) * 100 if previous > 0 else 0
        
        return {
            'current': round(current * 100, 1),
            'previous': round(previous * 100, 1),
            'change': round(change, 1),
            'trend': 'up' if change > 0 else 'down' if change < 0 else 'stable'
        }
    
    def _calculate_avg_rent_increase(self, data: Dict[str, Any], timeframe: MetricTimeframe) -> Dict[str, Any]:
        """Calculate average rent increase metrics"""
        current = data['avg_rent_increase_current']
        previous = data['avg_rent_increase_previous']
        change = ((current - previous) / previous) * 100 if previous > 0 else 0
        
        return {
            'current': round(current * 100, 1),
            'previous': round(previous * 100, 1),
            'change': round(change, 1),
            'trend': 'up' if change > 0 else 'down' if change < 0 else 'stable'
        }
    
    def _calculate_revenue_impact(self, data: Dict[str, Any], timeframe: MetricTimeframe) -> Dict[str, Any]:
        """Calculate revenue impact metrics"""
        current = data['revenue_impact_current']
        previous = data['revenue_impact_previous']
        change = ((current - previous) / previous) * 100 if previous > 0 else 0
        
        return {
            'current': current,
            'previous': previous,
            'change': round(change, 1),
            'trend': 'up' if change > 0 else 'down' if change < 0 else 'stable'
        }
    
    def _calculate_portfolio_risk_score(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate portfolio risk score"""
        current = data['portfolio_risk_current']
        previous = data['portfolio_risk_previous']
        change = ((current - previous) / previous) * 100 if previous > 0 else 0
        
        return {
            'current': current,
            'previous': previous,
            'change': round(change, 1),
            'trend': 'down' if change < 0 else 'up' if change > 0 else 'stable'  # Lower risk is better
        }
    
    def _count_active_workflows(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Count active workflows"""
        current = data['active_workflows_current']
        previous = data['active_workflows_previous']
        change = ((current - previous) / previous) * 100 if previous > 0 else 0
        
        return {
            'current': current,
            'previous': previous,
            'change': round(change, 1),
            'trend': 'up' if change > 0 else 'down' if change < 0 else 'stable'
        }
    
    def _count_upcoming_expirations(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Count upcoming lease expirations"""
        # Simulate upcoming expirations
        current = 34  # Leases expiring in next 90 days
        
        return {
            'current': current,
            'previous': None,
            'change': None,
            'trend': 'stable'
        }
    
    def _calculate_market_competitiveness(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate market competitiveness"""
        current = data['market_competitiveness_current']
        previous = data['market_competitiveness_previous']
        change = ((current - previous) / previous) * 100 if previous > 0 else 0
        
        return {
            'current': round(current * 100, 1),
            'previous': round(previous * 100, 1),
            'change': round(change, 1),
            'trend': 'up' if change > 0 else 'down' if change < 0 else 'stable'
        }
    
    def _get_fallback_dashboard(self, user_type: str) -> Dict[str, Any]:
        """Generate fallback dashboard when main generation fails"""
        return {
            'dashboard_type': user_type,
            'status': 'error',
            'message': 'Unable to load dashboard data. Please try again.',
            'metrics': [],
            'widgets': [],
            'alerts': [],
            'insights': [],
            'performance_summary': {'overall_score': 0, 'status': 'unavailable'},
            'last_updated': datetime.now().isoformat()
        }