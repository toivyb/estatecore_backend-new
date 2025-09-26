"""
Automated Compliance Reporting System
Generate comprehensive compliance reports and analytics
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.units import inch
import io
import base64
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict
from enum import Enum
from sqlalchemy import func, and_, or_, desc
import json
import asyncio
from pathlib import Path

from models.base import db
from models.compliance import (
    ComplianceViolation, ComplianceRequirement, ComplianceMetrics,
    ComplianceAudit, ComplianceTraining, RegulatoryKnowledgeBase,
    ViolationSeverity, ComplianceStatus, RegulationType
)


logger = logging.getLogger(__name__)


class ReportType(Enum):
    """Types of compliance reports"""
    EXECUTIVE_DASHBOARD = "executive_dashboard"
    PROPERTY_COMPLIANCE = "property_compliance"
    VIOLATION_ANALYSIS = "violation_analysis"
    RISK_ASSESSMENT = "risk_assessment"
    REGULATORY_COMPLIANCE = "regulatory_compliance"
    TRAINING_COMPLIANCE = "training_compliance"
    AUDIT_REPORT = "audit_report"
    TREND_ANALYSIS = "trend_analysis"
    PORTFOLIO_OVERVIEW = "portfolio_overview"
    REGULATORY_CHANGES = "regulatory_changes"


class ReportFormat(Enum):
    """Report output formats"""
    PDF = "pdf"
    HTML = "html"
    EXCEL = "excel"
    JSON = "json"
    CSV = "csv"


@dataclass
class ReportConfig:
    """Configuration for report generation"""
    report_type: ReportType
    title: str
    description: str
    property_ids: Optional[List[str]] = None
    date_range: Optional[Dict[str, datetime]] = None
    include_charts: bool = True
    include_recommendations: bool = True
    format: ReportFormat = ReportFormat.PDF
    template_path: Optional[str] = None


@dataclass
class ReportData:
    """Structured report data"""
    metadata: Dict[str, Any]
    summary: Dict[str, Any]
    sections: List[Dict[str, Any]]
    charts: List[Dict[str, Any]]
    recommendations: List[Dict[str, Any]]
    raw_data: Optional[Dict[str, Any]] = None


class ComplianceDataAnalyzer:
    """Analyzer for compliance data and statistics"""
    
    def __init__(self):
        self.session = db.session
    
    def analyze_violation_trends(
        self,
        property_ids: List[str] = None,
        days_back: int = 365
    ) -> Dict[str, Any]:
        """Analyze violation trends over time"""
        try:
            cutoff_date = datetime.now() - timedelta(days=days_back)
            
            query = self.session.query(ComplianceViolation).filter(
                ComplianceViolation.detected_date >= cutoff_date
            )
            
            if property_ids:
                query = query.filter(ComplianceViolation.property_id.in_(property_ids))
            
            violations = query.all()
            
            # Convert to DataFrame for analysis
            violation_data = []
            for v in violations:
                violation_data.append({
                    'date': v.detected_date,
                    'property_id': v.property_id,
                    'violation_type': v.violation_type,
                    'severity': v.severity.value,
                    'is_resolved': v.is_resolved,
                    'resolution_days': (v.resolved_date - v.detected_date).days if v.resolved_date else None
                })
            
            if not violation_data:
                return {'total_violations': 0, 'trends': {}, 'analysis': {}}
            
            df = pd.DataFrame(violation_data)
            
            # Time series analysis
            df['month'] = df['date'].dt.to_period('M')
            monthly_counts = df.groupby('month').size()
            
            # Severity analysis
            severity_counts = df['severity'].value_counts()
            
            # Type analysis
            type_counts = df['violation_type'].value_counts()
            
            # Resolution analysis
            resolved_df = df[df['is_resolved'] == True]
            avg_resolution_time = resolved_df['resolution_days'].mean() if not resolved_df.empty else 0
            
            # Trend calculation
            recent_period = df[df['date'] >= datetime.now() - timedelta(days=90)]
            previous_period = df[
                (df['date'] >= datetime.now() - timedelta(days=180)) &
                (df['date'] < datetime.now() - timedelta(days=90))
            ]
            
            trend_direction = 'stable'
            if len(recent_period) > len(previous_period) * 1.1:
                trend_direction = 'increasing'
            elif len(recent_period) < len(previous_period) * 0.9:
                trend_direction = 'decreasing'
            
            return {
                'total_violations': len(violations),
                'monthly_trends': monthly_counts.to_dict(),
                'severity_distribution': severity_counts.to_dict(),
                'violation_types': type_counts.to_dict(),
                'average_resolution_days': avg_resolution_time,
                'trend_direction': trend_direction,
                'recent_vs_previous': {
                    'recent_count': len(recent_period),
                    'previous_count': len(previous_period),
                    'change_percent': ((len(recent_period) - len(previous_period)) / max(len(previous_period), 1)) * 100
                }
            }
            
        except Exception as e:
            logger.error(f"Error analyzing violation trends: {e}")
            return {}
    
    def analyze_compliance_scores(
        self,
        property_ids: List[str] = None,
        days_back: int = 90
    ) -> Dict[str, Any]:
        """Analyze compliance scores and performance"""
        try:
            cutoff_date = datetime.now() - timedelta(days=days_back)
            
            query = self.session.query(ComplianceMetrics).filter(
                ComplianceMetrics.metric_date >= cutoff_date
            )
            
            if property_ids:
                query = query.filter(ComplianceMetrics.property_id.in_(property_ids))
            
            metrics = query.all()
            
            if not metrics:
                return {'overall_score': 0, 'trends': {}, 'analysis': {}}
            
            # Convert to DataFrame
            metrics_data = []
            for m in metrics:
                metrics_data.append({
                    'date': m.metric_date,
                    'property_id': m.property_id,
                    'overall_score': m.overall_compliance_score,
                    'risk_score': m.risk_score,
                    'violations': m.total_violations,
                    'fair_housing_score': m.fair_housing_score,
                    'safety_score': m.safety_compliance_score,
                    'building_code_score': m.building_code_score
                })
            
            df = pd.DataFrame(metrics_data)
            
            # Overall analysis
            current_avg_score = df['overall_score'].mean()
            current_avg_risk = df['risk_score'].mean()
            
            # Trend analysis
            df['week'] = df['date'].dt.to_period('W')
            weekly_scores = df.groupby('week')['overall_score'].mean()
            
            # Property performance
            property_scores = df.groupby('property_id')['overall_score'].mean().sort_values(ascending=False)
            
            # Category performance
            category_scores = {
                'fair_housing': df['fair_housing_score'].mean(),
                'safety': df['safety_score'].mean(),
                'building_code': df['building_code_score'].mean()
            }
            
            return {
                'overall_average_score': current_avg_score,
                'average_risk_score': current_avg_risk,
                'weekly_trends': weekly_scores.to_dict(),
                'property_performance': property_scores.to_dict(),
                'category_performance': category_scores,
                'total_properties_analyzed': len(property_scores)
            }
            
        except Exception as e:
            logger.error(f"Error analyzing compliance scores: {e}")
            return {}
    
    def analyze_regulatory_compliance(
        self,
        property_ids: List[str] = None
    ) -> Dict[str, Any]:
        """Analyze compliance by regulation type"""
        try:
            query = self.session.query(ComplianceRequirement)
            
            if property_ids:
                query = query.filter(ComplianceRequirement.property_id.in_(property_ids))
            
            requirements = query.all()
            
            # Group by regulation type
            regulation_analysis = {}
            
            for req in requirements:
                reg_type = req.regulation.regulation_type.value
                if reg_type not in regulation_analysis:
                    regulation_analysis[reg_type] = {
                        'total_requirements': 0,
                        'compliant': 0,
                        'non_compliant': 0,
                        'at_risk': 0,
                        'under_review': 0,
                        'average_risk_score': 0,
                        'overdue_count': 0
                    }
                
                analysis = regulation_analysis[reg_type]
                analysis['total_requirements'] += 1
                
                if req.compliance_status == ComplianceStatus.COMPLIANT:
                    analysis['compliant'] += 1
                elif req.compliance_status == ComplianceStatus.NON_COMPLIANT:
                    analysis['non_compliant'] += 1
                elif req.compliance_status == ComplianceStatus.AT_RISK:
                    analysis['at_risk'] += 1
                elif req.compliance_status == ComplianceStatus.UNDER_REVIEW:
                    analysis['under_review'] += 1
                
                analysis['average_risk_score'] += req.risk_score or 0
                
                if req.next_review_date < datetime.now():
                    analysis['overdue_count'] += 1
            
            # Calculate averages
            for reg_type, analysis in regulation_analysis.items():
                if analysis['total_requirements'] > 0:
                    analysis['compliance_rate'] = (analysis['compliant'] / analysis['total_requirements']) * 100
                    analysis['average_risk_score'] = analysis['average_risk_score'] / analysis['total_requirements']
                else:
                    analysis['compliance_rate'] = 100
                    analysis['average_risk_score'] = 0
            
            return regulation_analysis
            
        except Exception as e:
            logger.error(f"Error analyzing regulatory compliance: {e}")
            return {}
    
    def analyze_training_compliance(self) -> Dict[str, Any]:
        """Analyze training compliance status"""
        try:
            trainings = self.session.query(ComplianceTraining).all()
            
            if not trainings:
                return {'total_trainings': 0, 'analysis': {}}
            
            # Convert to DataFrame
            training_data = []
            for t in trainings:
                training_data.append({
                    'user_id': t.user_id,
                    'training_module': t.training_module,
                    'status': t.status.value,
                    'completed_date': t.completed_date,
                    'required_by': t.required_by,
                    'score': t.score,
                    'certification_expires': t.certification_expires
                })
            
            df = pd.DataFrame(training_data)
            
            # Overall statistics
            total_trainings = len(trainings)
            completed_trainings = len(df[df['status'] == 'completed'])
            completion_rate = (completed_trainings / total_trainings) * 100 if total_trainings > 0 else 0
            
            # Overdue trainings
            now = datetime.now()
            overdue_trainings = len(df[
                (df['required_by'].notna()) & 
                (pd.to_datetime(df['required_by']) < now) & 
                (df['status'] != 'completed')
            ])
            
            # Expiring certifications
            expiring_soon = len(df[
                (df['certification_expires'].notna()) &
                (pd.to_datetime(df['certification_expires']) < now + timedelta(days=30)) &
                (pd.to_datetime(df['certification_expires']) > now)
            ])
            
            # Module analysis
            module_stats = df.groupby('training_module').agg({
                'status': lambda x: (x == 'completed').sum(),
                'score': 'mean'
            }).to_dict()
            
            return {
                'total_trainings': total_trainings,
                'completed_trainings': completed_trainings,
                'completion_rate': completion_rate,
                'overdue_trainings': overdue_trainings,
                'expiring_certifications': expiring_soon,
                'module_statistics': module_stats,
                'users_analyzed': len(df['user_id'].unique())
            }
            
        except Exception as e:
            logger.error(f"Error analyzing training compliance: {e}")
            return {}


class ChartGenerator:
    """Generate charts for compliance reports"""
    
    def __init__(self):
        # Set style
        plt.style.use('seaborn-v0_8')
        sns.set_palette("husl")
    
    def create_violation_trend_chart(self, trend_data: Dict[str, Any]) -> str:
        """Create violation trend chart"""
        try:
            fig, ax = plt.subplots(figsize=(12, 6))
            
            monthly_trends = trend_data.get('monthly_trends', {})
            if monthly_trends:
                periods = list(monthly_trends.keys())
                values = list(monthly_trends.values())
                
                ax.plot(range(len(periods)), values, marker='o', linewidth=2, markersize=6)
                ax.set_title('Compliance Violations Over Time', fontsize=16, fontweight='bold')
                ax.set_xlabel('Month', fontsize=12)
                ax.set_ylabel('Number of Violations', fontsize=12)
                ax.grid(True, alpha=0.3)
                
                # Set x-axis labels
                ax.set_xticks(range(len(periods)))
                ax.set_xticklabels([str(p) for p in periods], rotation=45)
                
            plt.tight_layout()
            
            # Save to base64 string
            buffer = io.BytesIO()
            plt.savefig(buffer, format='png', dpi=300, bbox_inches='tight')
            buffer.seek(0)
            chart_data = base64.b64encode(buffer.getvalue()).decode()
            plt.close()
            
            return chart_data
            
        except Exception as e:
            logger.error(f"Error creating violation trend chart: {e}")
            return ""
    
    def create_severity_distribution_chart(self, trend_data: Dict[str, Any]) -> str:
        """Create severity distribution pie chart"""
        try:
            fig, ax = plt.subplots(figsize=(10, 8))
            
            severity_data = trend_data.get('severity_distribution', {})
            if severity_data:
                labels = list(severity_data.keys())
                sizes = list(severity_data.values())
                
                colors = ['#ff4444', '#ff8800', '#ffcc00', '#88cc00', '#44aaff']
                
                ax.pie(sizes, labels=labels, autopct='%1.1f%%', colors=colors, startangle=90)
                ax.set_title('Violations by Severity', fontsize=16, fontweight='bold')
                
            plt.tight_layout()
            
            # Save to base64 string
            buffer = io.BytesIO()
            plt.savefig(buffer, format='png', dpi=300, bbox_inches='tight')
            buffer.seek(0)
            chart_data = base64.b64encode(buffer.getvalue()).decode()
            plt.close()
            
            return chart_data
            
        except Exception as e:
            logger.error(f"Error creating severity distribution chart: {e}")
            return ""
    
    def create_compliance_scores_chart(self, scores_data: Dict[str, Any]) -> str:
        """Create compliance scores bar chart"""
        try:
            fig, ax = plt.subplots(figsize=(12, 8))
            
            property_performance = scores_data.get('property_performance', {})
            if property_performance:
                properties = list(property_performance.keys())[:10]  # Top 10 properties
                scores = [property_performance[p] for p in properties]
                
                bars = ax.bar(range(len(properties)), scores, 
                            color=['green' if s >= 80 else 'orange' if s >= 60 else 'red' for s in scores])
                
                ax.set_title('Property Compliance Scores', fontsize=16, fontweight='bold')
                ax.set_xlabel('Properties', fontsize=12)
                ax.set_ylabel('Compliance Score', fontsize=12)
                ax.set_ylim(0, 100)
                
                # Add value labels on bars
                for i, bar in enumerate(bars):
                    height = bar.get_height()
                    ax.text(bar.get_x() + bar.get_width()/2., height + 1,
                           f'{height:.1f}', ha='center', va='bottom')
                
                # Set x-axis labels
                ax.set_xticks(range(len(properties)))
                ax.set_xticklabels([p[:8] + '...' if len(p) > 8 else p for p in properties], 
                                 rotation=45)
                
                # Add horizontal line for target score
                ax.axhline(y=80, color='green', linestyle='--', alpha=0.7, label='Target Score')
                ax.legend()
                
            plt.tight_layout()
            
            # Save to base64 string
            buffer = io.BytesIO()
            plt.savefig(buffer, format='png', dpi=300, bbox_inches='tight')
            buffer.seek(0)
            chart_data = base64.b64encode(buffer.getvalue()).decode()
            plt.close()
            
            return chart_data
            
        except Exception as e:
            logger.error(f"Error creating compliance scores chart: {e}")
            return ""
    
    def create_regulatory_compliance_chart(self, regulatory_data: Dict[str, Any]) -> str:
        """Create regulatory compliance heatmap"""
        try:
            if not regulatory_data:
                return ""
            
            fig, ax = plt.subplots(figsize=(14, 8))
            
            # Prepare data for heatmap
            regulation_types = list(regulatory_data.keys())
            metrics = ['compliance_rate', 'average_risk_score']
            
            data_matrix = []
            for reg_type in regulation_types:
                row = [
                    regulatory_data[reg_type]['compliance_rate'],
                    100 - regulatory_data[reg_type]['average_risk_score']  # Invert risk score
                ]
                data_matrix.append(row)
            
            # Create heatmap
            sns.heatmap(data_matrix, 
                       annot=True, 
                       fmt='.1f',
                       xticklabels=['Compliance Rate', 'Risk Score (Inverted)'],
                       yticklabels=regulation_types,
                       cmap='RdYlGn',
                       vmin=0, vmax=100,
                       ax=ax)
            
            ax.set_title('Regulatory Compliance Overview', fontsize=16, fontweight='bold')
            
            plt.tight_layout()
            
            # Save to base64 string
            buffer = io.BytesIO()
            plt.savefig(buffer, format='png', dpi=300, bbox_inches='tight')
            buffer.seek(0)
            chart_data = base64.b64encode(buffer.getvalue()).decode()
            plt.close()
            
            return chart_data
            
        except Exception as e:
            logger.error(f"Error creating regulatory compliance chart: {e}")
            return ""


class ReportGenerator:
    """Generate compliance reports in various formats"""
    
    def __init__(self):
        self.analyzer = ComplianceDataAnalyzer()
        self.chart_generator = ChartGenerator()
        self.session = db.session
    
    async def generate_report(self, config: ReportConfig) -> Dict[str, Any]:
        """Generate a compliance report based on configuration"""
        try:
            logger.info(f"Generating {config.report_type.value} report")
            
            # Collect data based on report type
            report_data = await self._collect_report_data(config)
            
            # Generate charts if requested
            if config.include_charts:
                charts = await self._generate_charts(report_data, config)
                report_data.charts = charts
            
            # Generate recommendations if requested
            if config.include_recommendations:
                recommendations = await self._generate_recommendations(report_data, config)
                report_data.recommendations = recommendations
            
            # Format report based on requested format
            formatted_report = await self._format_report(report_data, config)
            
            logger.info(f"Successfully generated {config.report_type.value} report")
            return {
                'success': True,
                'report_data': formatted_report,
                'metadata': report_data.metadata,
                'generated_at': datetime.now()
            }
            
        except Exception as e:
            logger.error(f"Error generating report: {e}")
            return {
                'success': False,
                'error': str(e),
                'generated_at': datetime.now()
            }
    
    async def _collect_report_data(self, config: ReportConfig) -> ReportData:
        """Collect data for the report"""
        metadata = {
            'report_type': config.report_type.value,
            'title': config.title,
            'description': config.description,
            'generated_at': datetime.now(),
            'property_ids': config.property_ids,
            'date_range': config.date_range
        }
        
        summary = {}
        sections = []
        
        # Collect data based on report type
        if config.report_type == ReportType.EXECUTIVE_DASHBOARD:
            summary, sections = await self._collect_executive_data(config)
        
        elif config.report_type == ReportType.VIOLATION_ANALYSIS:
            summary, sections = await self._collect_violation_data(config)
        
        elif config.report_type == ReportType.PROPERTY_COMPLIANCE:
            summary, sections = await self._collect_property_data(config)
        
        elif config.report_type == ReportType.REGULATORY_COMPLIANCE:
            summary, sections = await self._collect_regulatory_data(config)
        
        elif config.report_type == ReportType.TRAINING_COMPLIANCE:
            summary, sections = await self._collect_training_data(config)
        
        # Add more report types as needed
        
        return ReportData(
            metadata=metadata,
            summary=summary,
            sections=sections,
            charts=[],
            recommendations=[]
        )
    
    async def _collect_executive_data(self, config: ReportConfig) -> Tuple[Dict, List]:
        """Collect data for executive dashboard"""
        summary = {}
        sections = []
        
        try:
            # Overall compliance metrics
            violation_trends = self.analyzer.analyze_violation_trends(config.property_ids)
            compliance_scores = self.analyzer.analyze_compliance_scores(config.property_ids)
            regulatory_analysis = self.analyzer.analyze_regulatory_compliance(config.property_ids)
            training_analysis = self.analyzer.analyze_training_compliance()
            
            # Summary metrics
            summary = {
                'total_violations': violation_trends.get('total_violations', 0),
                'average_compliance_score': compliance_scores.get('overall_average_score', 0),
                'properties_analyzed': compliance_scores.get('total_properties_analyzed', 0),
                'high_risk_properties': len([p for p, s in compliance_scores.get('property_performance', {}).items() if s < 60]),
                'training_completion_rate': training_analysis.get('completion_rate', 0),
                'overdue_trainings': training_analysis.get('overdue_trainings', 0)
            }
            
            # Detailed sections
            sections = [
                {
                    'title': 'Violation Trends',
                    'type': 'analysis',
                    'data': violation_trends
                },
                {
                    'title': 'Compliance Scores',
                    'type': 'analysis',
                    'data': compliance_scores
                },
                {
                    'title': 'Regulatory Compliance',
                    'type': 'analysis',
                    'data': regulatory_analysis
                },
                {
                    'title': 'Training Status',
                    'type': 'analysis',
                    'data': training_analysis
                }
            ]
            
        except Exception as e:
            logger.error(f"Error collecting executive data: {e}")
        
        return summary, sections
    
    async def _collect_violation_data(self, config: ReportConfig) -> Tuple[Dict, List]:
        """Collect data for violation analysis report"""
        summary = {}
        sections = []
        
        try:
            violation_trends = self.analyzer.analyze_violation_trends(config.property_ids)
            
            summary = {
                'total_violations': violation_trends.get('total_violations', 0),
                'trend_direction': violation_trends.get('trend_direction', 'stable'),
                'average_resolution_days': violation_trends.get('average_resolution_days', 0),
                'most_common_violation': max(violation_trends.get('violation_types', {}).items(), 
                                          key=lambda x: x[1], default=('None', 0))[0]
            }
            
            sections = [
                {
                    'title': 'Violation Trends Analysis',
                    'type': 'detailed_analysis',
                    'data': violation_trends
                }
            ]
            
        except Exception as e:
            logger.error(f"Error collecting violation data: {e}")
        
        return summary, sections
    
    async def _collect_property_data(self, config: ReportConfig) -> Tuple[Dict, List]:
        """Collect data for property compliance report"""
        # Implementation for property-specific compliance data
        return {}, []
    
    async def _collect_regulatory_data(self, config: ReportConfig) -> Tuple[Dict, List]:
        """Collect data for regulatory compliance report"""
        summary = {}
        sections = []
        
        try:
            regulatory_analysis = self.analyzer.analyze_regulatory_compliance(config.property_ids)
            
            # Calculate overall statistics
            total_requirements = sum(data['total_requirements'] for data in regulatory_analysis.values())
            total_compliant = sum(data['compliant'] for data in regulatory_analysis.values())
            overall_compliance_rate = (total_compliant / total_requirements * 100) if total_requirements > 0 else 0
            
            summary = {
                'total_requirements': total_requirements,
                'overall_compliance_rate': overall_compliance_rate,
                'regulation_types_covered': len(regulatory_analysis),
                'highest_compliance_area': max(regulatory_analysis.items(), 
                                            key=lambda x: x[1]['compliance_rate'], 
                                            default=('None', {'compliance_rate': 0}))[0],
                'lowest_compliance_area': min(regulatory_analysis.items(), 
                                           key=lambda x: x[1]['compliance_rate'], 
                                           default=('None', {'compliance_rate': 100}))[0]
            }
            
            sections = [
                {
                    'title': 'Regulatory Compliance Analysis',
                    'type': 'regulatory_breakdown',
                    'data': regulatory_analysis
                }
            ]
            
        except Exception as e:
            logger.error(f"Error collecting regulatory data: {e}")
        
        return summary, sections
    
    async def _collect_training_data(self, config: ReportConfig) -> Tuple[Dict, List]:
        """Collect data for training compliance report"""
        summary = {}
        sections = []
        
        try:
            training_analysis = self.analyzer.analyze_training_compliance()
            
            summary = training_analysis
            
            sections = [
                {
                    'title': 'Training Compliance Analysis',
                    'type': 'training_analysis',
                    'data': training_analysis
                }
            ]
            
        except Exception as e:
            logger.error(f"Error collecting training data: {e}")
        
        return summary, sections
    
    async def _generate_charts(self, report_data: ReportData, config: ReportConfig) -> List[Dict[str, Any]]:
        """Generate charts for the report"""
        charts = []
        
        try:
            # Generate charts based on report type and available data
            for section in report_data.sections:
                if section['type'] == 'analysis' and 'violation_trends' in section.get('title', '').lower():
                    chart_data = self.chart_generator.create_violation_trend_chart(section['data'])
                    if chart_data:
                        charts.append({
                            'title': 'Violation Trends Over Time',
                            'type': 'line_chart',
                            'data': chart_data,
                            'description': 'Monthly violation trends showing compliance performance over time'
                        })
                    
                    severity_chart = self.chart_generator.create_severity_distribution_chart(section['data'])
                    if severity_chart:
                        charts.append({
                            'title': 'Violation Severity Distribution',
                            'type': 'pie_chart',
                            'data': severity_chart,
                            'description': 'Distribution of violations by severity level'
                        })
                
                elif section['type'] == 'analysis' and 'compliance scores' in section.get('title', '').lower():
                    chart_data = self.chart_generator.create_compliance_scores_chart(section['data'])
                    if chart_data:
                        charts.append({
                            'title': 'Property Compliance Scores',
                            'type': 'bar_chart',
                            'data': chart_data,
                            'description': 'Compliance scores by property showing performance comparison'
                        })
                
                elif section['type'] == 'regulatory_breakdown':
                    chart_data = self.chart_generator.create_regulatory_compliance_chart(section['data'])
                    if chart_data:
                        charts.append({
                            'title': 'Regulatory Compliance Overview',
                            'type': 'heatmap',
                            'data': chart_data,
                            'description': 'Compliance rates and risk scores by regulation type'
                        })
            
        except Exception as e:
            logger.error(f"Error generating charts: {e}")
        
        return charts
    
    async def _generate_recommendations(self, report_data: ReportData, config: ReportConfig) -> List[Dict[str, Any]]:
        """Generate recommendations based on report data"""
        recommendations = []
        
        try:
            # Analyze data and generate actionable recommendations
            summary = report_data.summary
            
            # Violation-based recommendations
            if summary.get('total_violations', 0) > 10:
                recommendations.append({
                    'priority': 'high',
                    'category': 'violation_reduction',
                    'title': 'Implement Enhanced Violation Prevention Program',
                    'description': 'High violation count detected. Recommend implementing proactive monitoring and prevention measures.',
                    'action_items': [
                        'Review and strengthen compliance monitoring procedures',
                        'Increase staff training frequency',
                        'Implement automated compliance alerts'
                    ],
                    'estimated_impact': 'Could reduce violations by 30-40%',
                    'timeline': '60-90 days'
                })
            
            # Compliance score recommendations
            avg_score = summary.get('average_compliance_score', 0)
            if avg_score < 75:
                recommendations.append({
                    'priority': 'high',
                    'category': 'compliance_improvement',
                    'title': 'Improve Overall Compliance Scores',
                    'description': f'Average compliance score of {avg_score:.1f}% is below target of 80%.',
                    'action_items': [
                        'Conduct comprehensive compliance audit',
                        'Address identified compliance gaps',
                        'Implement compliance improvement action plans'
                    ],
                    'estimated_impact': f'Target: Increase scores to 80%+',
                    'timeline': '90-120 days'
                })
            
            # Training recommendations
            completion_rate = summary.get('training_completion_rate', 0)
            if completion_rate < 90:
                recommendations.append({
                    'priority': 'medium',
                    'category': 'training',
                    'title': 'Improve Training Completion Rates',
                    'description': f'Training completion rate of {completion_rate:.1f}% is below target of 95%.',
                    'action_items': [
                        'Send training reminders to overdue staff',
                        'Review training scheduling and accessibility',
                        'Implement training tracking and follow-up procedures'
                    ],
                    'estimated_impact': 'Target: 95%+ completion rate',
                    'timeline': '30-45 days'
                })
            
            # High-risk property recommendations
            high_risk_count = summary.get('high_risk_properties', 0)
            if high_risk_count > 0:
                recommendations.append({
                    'priority': 'high',
                    'category': 'risk_management',
                    'title': 'Address High-Risk Properties',
                    'description': f'{high_risk_count} properties identified as high-risk for compliance violations.',
                    'action_items': [
                        'Conduct immediate compliance assessments',
                        'Implement enhanced monitoring for high-risk properties',
                        'Develop property-specific improvement plans'
                    ],
                    'estimated_impact': 'Reduce violation risk by 50%+',
                    'timeline': '30-60 days'
                })
            
        except Exception as e:
            logger.error(f"Error generating recommendations: {e}")
        
        return recommendations
    
    async def _format_report(self, report_data: ReportData, config: ReportConfig) -> Any:
        """Format report based on requested format"""
        try:
            if config.format == ReportFormat.JSON:
                return asdict(report_data)
            
            elif config.format == ReportFormat.PDF:
                return await self._generate_pdf_report(report_data, config)
            
            elif config.format == ReportFormat.HTML:
                return await self._generate_html_report(report_data, config)
            
            elif config.format == ReportFormat.EXCEL:
                return await self._generate_excel_report(report_data, config)
            
            else:
                return asdict(report_data)
                
        except Exception as e:
            logger.error(f"Error formatting report: {e}")
            return asdict(report_data)
    
    async def _generate_pdf_report(self, report_data: ReportData, config: ReportConfig) -> str:
        """Generate PDF report"""
        try:
            buffer = io.BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=letter)
            styles = getSampleStyleSheet()
            story = []
            
            # Title
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=18,
                textColor=colors.darkblue,
                spaceAfter=30
            )
            story.append(Paragraph(report_data.metadata['title'], title_style))
            story.append(Spacer(1, 12))
            
            # Summary section
            story.append(Paragraph("Executive Summary", styles['Heading2']))
            story.append(Spacer(1, 12))
            
            # Create summary table
            summary_data = [['Metric', 'Value']]
            for key, value in report_data.summary.items():
                formatted_key = key.replace('_', ' ').title()
                formatted_value = f"{value:.1f}%" if 'rate' in key or 'score' in key else str(value)
                summary_data.append([formatted_key, formatted_value])
            
            if len(summary_data) > 1:
                summary_table = Table(summary_data, colWidths=[3*inch, 2*inch])
                summary_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 14),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black)
                ]))
                story.append(summary_table)
                story.append(Spacer(1, 20))
            
            # Sections
            for section in report_data.sections:
                story.append(Paragraph(section['title'], styles['Heading2']))
                story.append(Spacer(1, 12))
                
                # Add section content (simplified for this example)
                section_text = f"Analysis of {section['title'].lower()} shows various trends and patterns in compliance data."
                story.append(Paragraph(section_text, styles['Normal']))
                story.append(Spacer(1, 20))
            
            # Recommendations
            if report_data.recommendations:
                story.append(Paragraph("Recommendations", styles['Heading2']))
                story.append(Spacer(1, 12))
                
                for i, rec in enumerate(report_data.recommendations):
                    rec_title = f"{i+1}. {rec['title']} ({rec['priority'].upper()})"
                    story.append(Paragraph(rec_title, styles['Heading3']))
                    story.append(Paragraph(rec['description'], styles['Normal']))
                    
                    # Action items
                    if rec.get('action_items'):
                        story.append(Paragraph("Action Items:", styles['Normal']))
                        for item in rec['action_items']:
                            story.append(Paragraph(f"• {item}", styles['Normal']))
                    
                    story.append(Spacer(1, 15))
            
            # Build PDF
            doc.build(story)
            
            # Return base64 encoded PDF
            buffer.seek(0)
            pdf_data = base64.b64encode(buffer.getvalue()).decode()
            buffer.close()
            
            return pdf_data
            
        except Exception as e:
            logger.error(f"Error generating PDF report: {e}")
            return ""
    
    async def _generate_html_report(self, report_data: ReportData, config: ReportConfig) -> str:
        """Generate HTML report"""
        try:
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>{report_data.metadata['title']}</title>
                <style>
                    body {{ font-family: Arial, sans-serif; margin: 40px; }}
                    h1 {{ color: #2c3e50; border-bottom: 3px solid #3498db; padding-bottom: 10px; }}
                    h2 {{ color: #34495e; margin-top: 30px; }}
                    .summary {{ background: #ecf0f1; padding: 20px; border-radius: 5px; margin: 20px 0; }}
                    .metric {{ display: inline-block; margin: 10px; padding: 15px; background: white; border-radius: 5px; text-align: center; }}
                    .metric-value {{ font-size: 24px; font-weight: bold; color: #3498db; }}
                    .metric-label {{ font-size: 14px; color: #7f8c8d; }}
                    .recommendation {{ background: #f8f9fa; border-left: 4px solid #28a745; padding: 15px; margin: 10px 0; }}
                    .recommendation.high {{ border-left-color: #dc3545; }}
                    .recommendation.medium {{ border-left-color: #ffc107; }}
                    .chart {{ text-align: center; margin: 20px 0; }}
                    .chart img {{ max-width: 100%; height: auto; }}
                </style>
            </head>
            <body>
                <h1>{report_data.metadata['title']}</h1>
                <p><strong>Generated:</strong> {report_data.metadata['generated_at'].strftime('%Y-%m-%d %H:%M:%S')}</p>
                <p>{report_data.metadata['description']}</p>
                
                <div class="summary">
                    <h2>Executive Summary</h2>
            """
            
            # Add summary metrics
            for key, value in report_data.summary.items():
                formatted_key = key.replace('_', ' ').title()
                formatted_value = f"{value:.1f}%" if 'rate' in key or 'score' in key else str(value)
                html_content += f"""
                    <div class="metric">
                        <div class="metric-value">{formatted_value}</div>
                        <div class="metric-label">{formatted_key}</div>
                    </div>
                """
            
            html_content += "</div>"
            
            # Add charts
            for chart in report_data.charts:
                html_content += f"""
                <div class="chart">
                    <h3>{chart['title']}</h3>
                    <img src="data:image/png;base64,{chart['data']}" alt="{chart['title']}">
                    <p><em>{chart['description']}</em></p>
                </div>
                """
            
            # Add recommendations
            if report_data.recommendations:
                html_content += "<h2>Recommendations</h2>"
                for rec in report_data.recommendations:
                    html_content += f"""
                    <div class="recommendation {rec['priority']}">
                        <h3>{rec['title']} ({rec['priority'].upper()})</h3>
                        <p>{rec['description']}</p>
                    """
                    
                    if rec.get('action_items'):
                        html_content += "<ul>"
                        for item in rec['action_items']:
                            html_content += f"<li>{item}</li>"
                        html_content += "</ul>"
                    
                    html_content += "</div>"
            
            html_content += """
            </body>
            </html>
            """
            
            return html_content
            
        except Exception as e:
            logger.error(f"Error generating HTML report: {e}")
            return ""
    
    async def _generate_excel_report(self, report_data: ReportData, config: ReportConfig) -> str:
        """Generate Excel report"""
        try:
            buffer = io.BytesIO()
            
            with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                # Summary sheet
                summary_df = pd.DataFrame(list(report_data.summary.items()), 
                                        columns=['Metric', 'Value'])
                summary_df.to_excel(writer, sheet_name='Summary', index=False)
                
                # Data sheets for each section
                for i, section in enumerate(report_data.sections):
                    sheet_name = section['title'][:30]  # Excel sheet name limit
                    
                    if isinstance(section['data'], dict):
                        # Convert dict data to DataFrame
                        section_df = pd.DataFrame([section['data']]).T
                        section_df.columns = ['Value']
                        section_df.to_excel(writer, sheet_name=sheet_name)
                
                # Recommendations sheet
                if report_data.recommendations:
                    rec_data = []
                    for rec in report_data.recommendations:
                        rec_data.append({
                            'Priority': rec['priority'],
                            'Category': rec['category'],
                            'Title': rec['title'],
                            'Description': rec['description'],
                            'Timeline': rec.get('timeline', 'TBD'),
                            'Impact': rec.get('estimated_impact', 'TBD')
                        })
                    
                    rec_df = pd.DataFrame(rec_data)
                    rec_df.to_excel(writer, sheet_name='Recommendations', index=False)
            
            # Return base64 encoded Excel file
            buffer.seek(0)
            excel_data = base64.b64encode(buffer.getvalue()).decode()
            buffer.close()
            
            return excel_data
            
        except Exception as e:
            logger.error(f"Error generating Excel report: {e}")
            return ""


class ComplianceReportingService:
    """Main service for compliance reporting"""
    
    def __init__(self):
        self.report_generator = ReportGenerator()
        self.session = db.session
        
        # Report templates
        self.report_templates = {
            ReportType.EXECUTIVE_DASHBOARD: {
                'title': 'Executive Compliance Dashboard',
                'description': 'High-level overview of compliance status across all properties',
                'include_charts': True,
                'include_recommendations': True
            },
            ReportType.VIOLATION_ANALYSIS: {
                'title': 'Compliance Violation Analysis',
                'description': 'Detailed analysis of compliance violations and trends',
                'include_charts': True,
                'include_recommendations': True
            },
            ReportType.PROPERTY_COMPLIANCE: {
                'title': 'Property Compliance Report',
                'description': 'Comprehensive compliance status for specific properties',
                'include_charts': True,
                'include_recommendations': True
            }
        }
    
    async def generate_standard_report(
        self,
        report_type: ReportType,
        property_ids: List[str] = None,
        date_range: Dict[str, datetime] = None,
        format: ReportFormat = ReportFormat.PDF
    ) -> Dict[str, Any]:
        """Generate a standard compliance report"""
        try:
            template = self.report_templates.get(report_type, {})
            
            config = ReportConfig(
                report_type=report_type,
                title=template.get('title', f'{report_type.value.title()} Report'),
                description=template.get('description', f'Report for {report_type.value}'),
                property_ids=property_ids,
                date_range=date_range,
                include_charts=template.get('include_charts', True),
                include_recommendations=template.get('include_recommendations', True),
                format=format
            )
            
            return await self.report_generator.generate_report(config)
            
        except Exception as e:
            logger.error(f"Error generating standard report: {e}")
            return {'success': False, 'error': str(e)}
    
    async def generate_custom_report(self, config: ReportConfig) -> Dict[str, Any]:
        """Generate a custom compliance report"""
        return await self.report_generator.generate_report(config)
    
    async def schedule_automated_reports(
        self,
        report_configs: List[ReportConfig],
        schedule: Dict[str, Any]
    ) -> bool:
        """Schedule automated report generation"""
        try:
            # This would integrate with your task scheduler (Celery, etc.)
            logger.info(f"Scheduled {len(report_configs)} automated reports")
            return True
            
        except Exception as e:
            logger.error(f"Error scheduling automated reports: {e}")
            return False
    
    def get_available_report_types(self) -> List[Dict[str, Any]]:
        """Get list of available report types"""
        return [
            {
                'type': report_type.value,
                'name': template['title'],
                'description': template['description']
            }
            for report_type, template in self.report_templates.items()
        ]


# Global service instance
_compliance_reporting_service = None


def get_compliance_reporting_service() -> ComplianceReportingService:
    """Get or create the compliance reporting service instance"""
    global _compliance_reporting_service
    if _compliance_reporting_service is None:
        _compliance_reporting_service = ComplianceReportingService()
    return _compliance_reporting_service