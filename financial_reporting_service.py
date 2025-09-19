"""
Financial Reporting Service for EstateCore
Comprehensive financial analytics, reporting, and dashboard capabilities
"""

import os
import logging
from datetime import datetime, timedelta, date
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import calendar
import json
from decimal import Decimal
import uuid

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ReportType(Enum):
    """Report type enumeration"""
    INCOME_STATEMENT = "income_statement"
    CASH_FLOW = "cash_flow"
    BALANCE_SHEET = "balance_sheet"
    RENT_ROLL = "rent_roll"
    VACANCY_REPORT = "vacancy_report"
    EXPENSE_SUMMARY = "expense_summary"
    PROFIT_LOSS = "profit_loss"
    TAX_SUMMARY = "tax_summary"
    BUDGET_ANALYSIS = "budget_analysis"

class ReportPeriod(Enum):
    """Report period enumeration"""
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"
    CUSTOM = "custom"

class ExpenseCategory(Enum):
    """Expense category enumeration"""
    MAINTENANCE = "maintenance"
    UTILITIES = "utilities"
    INSURANCE = "insurance"
    PROPERTY_TAX = "property_tax"
    MANAGEMENT_FEE = "management_fee"
    MARKETING = "marketing"
    LEGAL = "legal"
    ACCOUNTING = "accounting"
    SUPPLIES = "supplies"
    LANDSCAPING = "landscaping"
    SECURITY = "security"
    OTHER = "other"

@dataclass
class FinancialMetric:
    """Financial metric data structure"""
    name: str
    value: Decimal
    previous_value: Optional[Decimal] = None
    change_percentage: Optional[float] = None
    period: str = ""
    unit: str = "currency"
    category: str = "general"

@dataclass
class RevenueStream:
    """Revenue stream data structure"""
    source: str
    amount: Decimal
    category: str
    property_id: Optional[int] = None
    tenant_id: Optional[int] = None
    date_recorded: datetime = field(default_factory=datetime.utcnow)
    description: str = ""

@dataclass
class ExpenseRecord:
    """Expense record data structure"""
    category: ExpenseCategory
    amount: Decimal
    description: str
    property_id: Optional[int] = None
    vendor: str = ""
    date_incurred: datetime = field(default_factory=datetime.utcnow)
    receipt_url: Optional[str] = None
    is_recurring: bool = False
    tax_deductible: bool = True

@dataclass
class FinancialReport:
    """Financial report data structure"""
    id: str
    report_type: ReportType
    period: ReportPeriod
    start_date: date
    end_date: date
    generated_at: datetime
    generated_by: str
    data: Dict
    summary: Dict
    charts_data: List[Dict] = field(default_factory=list)
    metadata: Dict = field(default_factory=dict)

class FinancialReportingService:
    def __init__(self):
        """Initialize financial reporting service"""
        self._database_service = None
        self._rent_service = None
        self._lease_service = None
        self._property_service = None
        
    def _initialize_services(self):
        """Initialize dependent services"""
        try:
            from database_service import get_database_service
            from rent_collection_service import get_rent_collection_service
            from lease_management_service import get_lease_management_service
            
            self._database_service = get_database_service()
            self._rent_service = get_rent_collection_service()
            self._lease_service = get_lease_management_service()
            
        except ImportError as e:
            logger.warning(f"Could not import service: {e}")
    
    def generate_financial_report(self, report_type: ReportType, period: ReportPeriod, 
                                start_date: date = None, end_date: date = None) -> Dict:
        """Generate comprehensive financial report"""
        try:
            self._initialize_services()
            
            # Set default dates if not provided
            if not start_date or not end_date:
                start_date, end_date = self._get_period_dates(period)
            
            # Generate report ID
            report_id = f"RPT-{report_type.value}-{datetime.now().strftime('%Y%m%d%H%M%S')}"
            
            logger.info(f"Generating {report_type.value} report for {start_date} to {end_date}")
            
            # Generate report data based on type
            if report_type == ReportType.INCOME_STATEMENT:
                report_data = self._generate_income_statement(start_date, end_date)
            elif report_type == ReportType.CASH_FLOW:
                report_data = self._generate_cash_flow_report(start_date, end_date)
            elif report_type == ReportType.RENT_ROLL:
                report_data = self._generate_rent_roll_report(start_date, end_date)
            elif report_type == ReportType.VACANCY_REPORT:
                report_data = self._generate_vacancy_report(start_date, end_date)
            elif report_type == ReportType.EXPENSE_SUMMARY:
                report_data = self._generate_expense_summary(start_date, end_date)
            elif report_type == ReportType.PROFIT_LOSS:
                report_data = self._generate_profit_loss_report(start_date, end_date)
            else:
                # Default comprehensive report
                report_data = self._generate_comprehensive_report(start_date, end_date)
            
            # Create financial report object
            report = FinancialReport(
                id=report_id,
                report_type=report_type,
                period=period,
                start_date=start_date,
                end_date=end_date,
                generated_at=datetime.utcnow(),
                generated_by="system",  # Would be actual user in production
                data=report_data,
                summary=self._generate_report_summary(report_data),
                charts_data=self._generate_charts_data(report_data),
                metadata={
                    'total_properties': self._get_property_count(),
                    'total_units': self._get_unit_count(),
                    'occupancy_rate': self._get_occupancy_rate(),
                    'generation_method': 'automated'
                }
            )
            
            # Save report
            self._save_report(report)
            
            return {
                'success': True,
                'report_id': report_id,
                'report_type': report_type.value,
                'period': f"{start_date} to {end_date}",
                'data': report_data,
                'summary': report.summary,
                'charts_data': report.charts_data,
                'metadata': report.metadata
            }
            
        except Exception as e:
            logger.error(f"Financial report generation failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _get_period_dates(self, period: ReportPeriod) -> Tuple[date, date]:
        """Get start and end dates for a given period"""
        today = date.today()
        
        if period == ReportPeriod.MONTHLY:
            start_date = date(today.year, today.month, 1)
            if today.month == 12:
                end_date = date(today.year + 1, 1, 1) - timedelta(days=1)
            else:
                end_date = date(today.year, today.month + 1, 1) - timedelta(days=1)
                
        elif period == ReportPeriod.QUARTERLY:
            quarter = (today.month - 1) // 3 + 1
            start_month = (quarter - 1) * 3 + 1
            start_date = date(today.year, start_month, 1)
            
            if quarter == 4:
                end_date = date(today.year + 1, 1, 1) - timedelta(days=1)
            else:
                end_month = quarter * 3 + 1
                end_date = date(today.year, end_month, 1) - timedelta(days=1)
                
        elif period == ReportPeriod.YEARLY:
            start_date = date(today.year, 1, 1)
            end_date = date(today.year, 12, 31)
            
        else:  # Custom or default to current month
            start_date = date(today.year, today.month, 1)
            end_date = today
            
        return start_date, end_date
    
    def _generate_income_statement(self, start_date: date, end_date: date) -> Dict:
        """Generate income statement report"""
        try:
            # Revenue calculations
            rental_income = self._calculate_rental_income(start_date, end_date)
            late_fees = self._calculate_late_fees_income(start_date, end_date)
            other_income = self._calculate_other_income(start_date, end_date)
            total_revenue = rental_income + late_fees + other_income
            
            # Expense calculations
            operating_expenses = self._calculate_operating_expenses(start_date, end_date)
            maintenance_expenses = self._calculate_maintenance_expenses(start_date, end_date)
            total_expenses = operating_expenses + maintenance_expenses
            
            # Net calculations
            net_operating_income = total_revenue - total_expenses
            
            return {
                'revenue': {
                    'rental_income': float(rental_income),
                    'late_fees': float(late_fees),
                    'other_income': float(other_income),
                    'total_revenue': float(total_revenue)
                },
                'expenses': {
                    'operating_expenses': float(operating_expenses),
                    'maintenance_expenses': float(maintenance_expenses),
                    'total_expenses': float(total_expenses)
                },
                'net_income': {
                    'net_operating_income': float(net_operating_income),
                    'profit_margin': float((net_operating_income / total_revenue * 100)) if total_revenue > 0 else 0
                },
                'period': f"{start_date} to {end_date}"
            }
            
        except Exception as e:
            logger.error(f"Income statement generation failed: {e}")
            return {}
    
    def _generate_cash_flow_report(self, start_date: date, end_date: date) -> Dict:
        """Generate cash flow statement"""
        try:
            # Operating cash flow
            rent_collected = self._calculate_rent_collected(start_date, end_date)
            expenses_paid = self._calculate_expenses_paid(start_date, end_date)
            operating_cash_flow = rent_collected - expenses_paid
            
            # Investment cash flow (property improvements, acquisitions)
            capital_expenditures = self._calculate_capital_expenditures(start_date, end_date)
            property_acquisitions = self._calculate_property_acquisitions(start_date, end_date)
            investing_cash_flow = -(capital_expenditures + property_acquisitions)
            
            # Financing cash flow (loans, owner contributions)
            loan_proceeds = self._calculate_loan_proceeds(start_date, end_date)
            loan_payments = self._calculate_loan_payments(start_date, end_date)
            owner_contributions = self._calculate_owner_contributions(start_date, end_date)
            financing_cash_flow = loan_proceeds - loan_payments + owner_contributions
            
            # Net cash flow
            net_cash_flow = operating_cash_flow + investing_cash_flow + financing_cash_flow
            
            return {
                'operating_activities': {
                    'rent_collected': float(rent_collected),
                    'expenses_paid': float(expenses_paid),
                    'net_operating_cash_flow': float(operating_cash_flow)
                },
                'investing_activities': {
                    'capital_expenditures': float(capital_expenditures),
                    'property_acquisitions': float(property_acquisitions),
                    'net_investing_cash_flow': float(investing_cash_flow)
                },
                'financing_activities': {
                    'loan_proceeds': float(loan_proceeds),
                    'loan_payments': float(loan_payments),
                    'owner_contributions': float(owner_contributions),
                    'net_financing_cash_flow': float(financing_cash_flow)
                },
                'net_cash_flow': float(net_cash_flow),
                'period': f"{start_date} to {end_date}"
            }
            
        except Exception as e:
            logger.error(f"Cash flow report generation failed: {e}")
            return {}
    
    def _generate_rent_roll_report(self, start_date: date, end_date: date) -> Dict:
        """Generate rent roll report"""
        try:
            # Mock rent roll data
            rent_roll_data = []
            total_potential_rent = Decimal('0')
            total_actual_rent = Decimal('0')
            vacant_units = 0
            total_units = 0
            
            # Mock data for demonstration
            properties = self._get_mock_properties()
            
            for prop in properties:
                for unit in prop.get('units', []):
                    total_units += 1
                    unit_rent = Decimal(str(unit.get('rent', 0)))
                    total_potential_rent += unit_rent
                    
                    if unit.get('is_occupied', False):
                        total_actual_rent += unit_rent
                        status = 'Occupied'
                    else:
                        vacant_units += 1
                        status = 'Vacant'
                    
                    rent_roll_data.append({
                        'property_name': prop.get('name', ''),
                        'unit_number': unit.get('unit_number', ''),
                        'tenant_name': unit.get('tenant_name', 'N/A'),
                        'rent_amount': float(unit_rent),
                        'lease_start': unit.get('lease_start', ''),
                        'lease_end': unit.get('lease_end', ''),
                        'status': status,
                        'security_deposit': float(unit.get('security_deposit', 0))
                    })
            
            occupancy_rate = ((total_units - vacant_units) / total_units * 100) if total_units > 0 else 0
            
            return {
                'rent_roll': rent_roll_data,
                'summary': {
                    'total_units': total_units,
                    'occupied_units': total_units - vacant_units,
                    'vacant_units': vacant_units,
                    'occupancy_rate': float(occupancy_rate),
                    'total_potential_rent': float(total_potential_rent),
                    'total_actual_rent': float(total_actual_rent),
                    'vacancy_loss': float(total_potential_rent - total_actual_rent)
                },
                'period': f"{start_date} to {end_date}"
            }
            
        except Exception as e:
            logger.error(f"Rent roll report generation failed: {e}")
            return {}
    
    def _generate_vacancy_report(self, start_date: date, end_date: date) -> Dict:
        """Generate vacancy analysis report"""
        try:
            # Mock vacancy data
            vacancy_data = {
                'current_vacancies': [
                    {
                        'property_name': 'Sunset Apartments',
                        'unit_number': '205',
                        'vacant_since': (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d'),
                        'days_vacant': 30,
                        'monthly_rent_loss': 1600.00,
                        'total_rent_loss': 1600.00,
                        'reason': 'Tenant moved out'
                    },
                    {
                        'property_name': 'Sunset Apartments',
                        'unit_number': '104',
                        'vacant_since': (datetime.now() - timedelta(days=15)).strftime('%Y-%m-%d'),
                        'days_vacant': 15,
                        'monthly_rent_loss': 1500.00,
                        'total_rent_loss': 750.00,
                        'reason': 'Lease expired'
                    }
                ],
                'vacancy_trends': {
                    'average_vacancy_days': 22.5,
                    'turnover_rate': 8.5,  # percentage
                    'seasonal_patterns': {
                        'Q1': 12.5,
                        'Q2': 8.0,
                        'Q3': 6.5,
                        'Q4': 10.5
                    }
                },
                'financial_impact': {
                    'total_vacancy_loss': 2350.00,
                    'annual_projected_loss': 28200.00,
                    'cost_per_vacant_day': 104.44
                }
            }
            
            return vacancy_data
            
        except Exception as e:
            logger.error(f"Vacancy report generation failed: {e}")
            return {}
    
    def _generate_expense_summary(self, start_date: date, end_date: date) -> Dict:
        """Generate expense summary report"""
        try:
            # Mock expense data by category
            expenses_by_category = {
                'maintenance': 3500.00,
                'utilities': 2100.00,
                'insurance': 1200.00,
                'property_tax': 4500.00,
                'management_fee': 1800.00,
                'marketing': 500.00,
                'legal': 800.00,
                'supplies': 300.00,
                'landscaping': 600.00,
                'other': 400.00
            }
            
            total_expenses = sum(expenses_by_category.values())
            
            # Calculate percentages
            expense_percentages = {
                category: (amount / total_expenses * 100) if total_expenses > 0 else 0
                for category, amount in expenses_by_category.items()
            }
            
            # Expense trends (mock data)
            expense_trends = {
                'monthly_comparison': {
                    'current_month': total_expenses,
                    'previous_month': total_expenses * 0.95,
                    'change_percentage': 5.0
                },
                'year_over_year': {
                    'current_year': total_expenses * 12,
                    'previous_year': total_expenses * 11.5,
                    'change_percentage': 4.3
                }
            }
            
            return {
                'expenses_by_category': expenses_by_category,
                'expense_percentages': expense_percentages,
                'total_expenses': total_expenses,
                'trends': expense_trends,
                'top_expenses': sorted(
                    expenses_by_category.items(), 
                    key=lambda x: x[1], 
                    reverse=True
                )[:5],
                'period': f"{start_date} to {end_date}"
            }
            
        except Exception as e:
            logger.error(f"Expense summary generation failed: {e}")
            return {}
    
    def _generate_profit_loss_report(self, start_date: date, end_date: date) -> Dict:
        """Generate profit and loss report"""
        try:
            # Get income statement data
            income_data = self._generate_income_statement(start_date, end_date)
            
            # Additional P&L specific calculations
            gross_rental_income = Decimal(str(income_data.get('revenue', {}).get('total_revenue', 0)))
            total_expenses = Decimal(str(income_data.get('expenses', {}).get('total_expenses', 0)))
            net_income = gross_rental_income - total_expenses
            
            # Calculate key metrics
            metrics = {
                'gross_rental_yield': float((gross_rental_income / Decimal('1000000')) * 100),  # Assuming $1M property value
                'expense_ratio': float((total_expenses / gross_rental_income) * 100) if gross_rental_income > 0 else 0,
                'net_yield': float((net_income / Decimal('1000000')) * 100),
                'cash_on_cash_return': 8.5  # Mock calculation
            }
            
            # Performance comparison
            performance = {
                'vs_budget': {
                    'income_variance': 2.5,  # percentage
                    'expense_variance': -1.8,
                    'net_income_variance': 4.2
                },
                'vs_previous_period': {
                    'income_growth': 3.1,
                    'expense_growth': 1.2,
                    'net_income_growth': 5.8
                }
            }
            
            return {
                **income_data,
                'key_metrics': metrics,
                'performance': performance,
                'period': f"{start_date} to {end_date}"
            }
            
        except Exception as e:
            logger.error(f"P&L report generation failed: {e}")
            return {}
    
    def _generate_comprehensive_report(self, start_date: date, end_date: date) -> Dict:
        """Generate comprehensive financial dashboard report"""
        try:
            return {
                'income_statement': self._generate_income_statement(start_date, end_date),
                'cash_flow': self._generate_cash_flow_report(start_date, end_date),
                'rent_roll': self._generate_rent_roll_report(start_date, end_date),
                'vacancy_analysis': self._generate_vacancy_report(start_date, end_date),
                'expense_summary': self._generate_expense_summary(start_date, end_date),
                'kpi_metrics': self._calculate_kpi_metrics(start_date, end_date)
            }
            
        except Exception as e:
            logger.error(f"Comprehensive report generation failed: {e}")
            return {}
    
    def _calculate_kpi_metrics(self, start_date: date, end_date: date) -> Dict:
        """Calculate key performance indicators"""
        try:
            return {
                'financial_kpis': {
                    'gross_rental_yield': 7.2,
                    'net_rental_yield': 5.8,
                    'cap_rate': 6.5,
                    'cash_on_cash_return': 8.3,
                    'debt_service_coverage_ratio': 1.45
                },
                'operational_kpis': {
                    'occupancy_rate': 95.5,
                    'tenant_retention_rate': 87.2,
                    'average_days_to_lease': 18,
                    'maintenance_cost_per_unit': 285.00,
                    'rent_growth_rate': 3.5
                },
                'efficiency_kpis': {
                    'expense_ratio': 35.2,
                    'revenue_per_unit': 1650.00,
                    'noi_per_unit': 1070.00,
                    'cost_per_square_foot': 12.50,
                    'revenue_per_square_foot': 19.30
                }
            }
            
        except Exception as e:
            logger.error(f"KPI calculation failed: {e}")
            return {}
    
    # Mock calculation methods (would be replaced with real database queries)
    def _calculate_rental_income(self, start_date: date, end_date: date) -> Decimal:
        return Decimal('45000.00')  # Mock value
    
    def _calculate_late_fees_income(self, start_date: date, end_date: date) -> Decimal:
        return Decimal('850.00')  # Mock value
    
    def _calculate_other_income(self, start_date: date, end_date: date) -> Decimal:
        return Decimal('500.00')  # Mock value
    
    def _calculate_operating_expenses(self, start_date: date, end_date: date) -> Decimal:
        return Decimal('12000.00')  # Mock value
    
    def _calculate_maintenance_expenses(self, start_date: date, end_date: date) -> Decimal:
        return Decimal('3500.00')  # Mock value
    
    def _calculate_rent_collected(self, start_date: date, end_date: date) -> Decimal:
        return Decimal('44200.00')  # Mock value
    
    def _calculate_expenses_paid(self, start_date: date, end_date: date) -> Decimal:
        return Decimal('14800.00')  # Mock value
    
    def _calculate_capital_expenditures(self, start_date: date, end_date: date) -> Decimal:
        return Decimal('5000.00')  # Mock value
    
    def _calculate_property_acquisitions(self, start_date: date, end_date: date) -> Decimal:
        return Decimal('0.00')  # Mock value
    
    def _calculate_loan_proceeds(self, start_date: date, end_date: date) -> Decimal:
        return Decimal('0.00')  # Mock value
    
    def _calculate_loan_payments(self, start_date: date, end_date: date) -> Decimal:
        return Decimal('8500.00')  # Mock value
    
    def _calculate_owner_contributions(self, start_date: date, end_date: date) -> Decimal:
        return Decimal('2000.00')  # Mock value
    
    def _get_property_count(self) -> int:
        return 3  # Mock value
    
    def _get_unit_count(self) -> int:
        return 28  # Mock value
    
    def _get_occupancy_rate(self) -> float:
        return 95.5  # Mock value
    
    def _get_mock_properties(self) -> List[Dict]:
        """Get mock property data for reports"""
        return [
            {
                'id': 1,
                'name': 'Sunset Apartments',
                'units': [
                    {
                        'unit_number': '101',
                        'rent': 1500,
                        'is_occupied': True,
                        'tenant_name': 'John Doe',
                        'lease_start': '2024-01-01',
                        'lease_end': '2024-12-31',
                        'security_deposit': 1500
                    },
                    {
                        'unit_number': '102',
                        'rent': 1600,
                        'is_occupied': True,
                        'tenant_name': 'Jane Smith',
                        'lease_start': '2024-02-01',
                        'lease_end': '2025-01-31',
                        'security_deposit': 1600
                    },
                    {
                        'unit_number': '103',
                        'rent': 1550,
                        'is_occupied': False,
                        'tenant_name': '',
                        'lease_start': '',
                        'lease_end': '',
                        'security_deposit': 0
                    }
                ]
            }
        ]
    
    def _generate_report_summary(self, report_data: Dict) -> Dict:
        """Generate executive summary for report"""
        try:
            if 'income_statement' in report_data:
                income_data = report_data['income_statement']
                return {
                    'total_revenue': income_data.get('revenue', {}).get('total_revenue', 0),
                    'total_expenses': income_data.get('expenses', {}).get('total_expenses', 0),
                    'net_income': income_data.get('net_income', {}).get('net_operating_income', 0),
                    'profit_margin': income_data.get('net_income', {}).get('profit_margin', 0),
                    'key_highlights': [
                        f"Total Revenue: ${income_data.get('revenue', {}).get('total_revenue', 0):,.2f}",
                        f"Net Income: ${income_data.get('net_income', {}).get('net_operating_income', 0):,.2f}",
                        f"Profit Margin: {income_data.get('net_income', {}).get('profit_margin', 0):.1f}%"
                    ]
                }
            else:
                return {
                    'status': 'Report generated successfully',
                    'data_points': len(report_data),
                    'key_highlights': ['Comprehensive financial analysis completed']
                }
                
        except Exception as e:
            logger.error(f"Report summary generation failed: {e}")
            return {'status': 'Summary generation failed'}
    
    def _generate_charts_data(self, report_data: Dict) -> List[Dict]:
        """Generate chart configuration data for frontend visualization"""
        try:
            charts = []
            
            # Revenue breakdown pie chart
            if 'income_statement' in report_data:
                income_data = report_data['income_statement']
                revenue_data = income_data.get('revenue', {})
                
                charts.append({
                    'type': 'pie',
                    'title': 'Revenue Breakdown',
                    'data': {
                        'labels': ['Rental Income', 'Late Fees', 'Other Income'],
                        'values': [
                            revenue_data.get('rental_income', 0),
                            revenue_data.get('late_fees', 0),
                            revenue_data.get('other_income', 0)
                        ]
                    }
                })
                
                # Income vs Expenses bar chart
                charts.append({
                    'type': 'bar',
                    'title': 'Income vs Expenses',
                    'data': {
                        'labels': ['Total Revenue', 'Total Expenses', 'Net Income'],
                        'values': [
                            revenue_data.get('total_revenue', 0),
                            income_data.get('expenses', {}).get('total_expenses', 0),
                            income_data.get('net_income', {}).get('net_operating_income', 0)
                        ]
                    }
                })
            
            # Expense breakdown chart
            if 'expense_summary' in report_data:
                expense_data = report_data['expense_summary']
                expenses_by_category = expense_data.get('expenses_by_category', {})
                
                charts.append({
                    'type': 'doughnut',
                    'title': 'Expense Breakdown by Category',
                    'data': {
                        'labels': list(expenses_by_category.keys()),
                        'values': list(expenses_by_category.values())
                    }
                })
            
            # Occupancy trend line chart
            charts.append({
                'type': 'line',
                'title': 'Occupancy Rate Trend',
                'data': {
                    'labels': ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
                    'values': [92.5, 94.0, 96.5, 95.0, 97.5, 95.5]
                }
            })
            
            return charts
            
        except Exception as e:
            logger.error(f"Charts data generation failed: {e}")
            return []
    
    def _save_report(self, report: FinancialReport) -> bool:
        """Save financial report to database"""
        try:
            if not self._database_service:
                logger.info(f"Mock: Saved financial report {report.id}")
                return True
            
            # Implementation would save to database
            return True
            
        except Exception as e:
            logger.error(f"Failed to save financial report: {e}")
            return False
    
    def get_dashboard_data(self) -> Dict:
        """Get financial dashboard overview data"""
        try:
            today = date.today()
            current_month_start = date(today.year, today.month, 1)
            
            # Generate key financial metrics
            income_data = self._generate_income_statement(current_month_start, today)
            cash_flow_data = self._generate_cash_flow_report(current_month_start, today)
            kpi_metrics = self._calculate_kpi_metrics(current_month_start, today)
            
            dashboard_data = {
                'overview_metrics': {
                    'total_revenue': income_data.get('revenue', {}).get('total_revenue', 0),
                    'total_expenses': income_data.get('expenses', {}).get('total_expenses', 0),
                    'net_income': income_data.get('net_income', {}).get('net_operating_income', 0),
                    'cash_flow': cash_flow_data.get('net_cash_flow', 0),
                    'occupancy_rate': self._get_occupancy_rate(),
                    'profit_margin': income_data.get('net_income', {}).get('profit_margin', 0)
                },
                'kpi_metrics': kpi_metrics,
                'recent_reports': self._get_recent_reports(),
                'alerts': self._get_financial_alerts(),
                'quick_stats': {
                    'properties_count': self._get_property_count(),
                    'units_count': self._get_unit_count(),
                    'tenants_count': 26,  # Mock
                    'maintenance_requests': 3  # Mock
                }
            }
            
            return dashboard_data
            
        except Exception as e:
            logger.error(f"Dashboard data generation failed: {e}")
            return {}
    
    def _get_recent_reports(self) -> List[Dict]:
        """Get list of recent financial reports"""
        return [
            {
                'id': 'RPT-income_statement-20241201120000',
                'type': 'Income Statement',
                'period': 'November 2024',
                'generated_at': '2024-12-01T12:00:00Z',
                'status': 'completed'
            },
            {
                'id': 'RPT-cash_flow-20241201100000',
                'type': 'Cash Flow',
                'period': 'Q4 2024',
                'generated_at': '2024-12-01T10:00:00Z',
                'status': 'completed'
            }
        ]
    
    def _get_financial_alerts(self) -> List[Dict]:
        """Get financial alerts and notifications"""
        return [
            {
                'type': 'warning',
                'title': 'High Vacancy Rate',
                'message': 'Property vacancy rate is above 10% threshold',
                'severity': 'medium'
            },
            {
                'type': 'info',
                'title': 'Rent Increase Due',
                'message': '3 leases eligible for rent increase next month',
                'severity': 'low'
            }
        ]

# Singleton instance
_financial_reporting_service = None

def get_financial_reporting_service() -> FinancialReportingService:
    """Get singleton financial reporting service instance"""
    global _financial_reporting_service
    if _financial_reporting_service is None:
        _financial_reporting_service = FinancialReportingService()
    return _financial_reporting_service

def create_financial_reporting_service() -> FinancialReportingService:
    """Create financial reporting service instance"""
    return FinancialReportingService()

if __name__ == "__main__":
    # Test the financial reporting service
    service = get_financial_reporting_service()
    
    print("💰 Financial Reporting Service Test")
    
    # Test income statement generation
    income_report = service.generate_financial_report(
        ReportType.INCOME_STATEMENT, 
        ReportPeriod.MONTHLY
    )
    print(f"Income Statement: {income_report.get('success', False)}")
    
    # Test cash flow report
    cash_flow_report = service.generate_financial_report(
        ReportType.CASH_FLOW,
        ReportPeriod.QUARTERLY
    )
    print(f"Cash Flow Report: {cash_flow_report.get('success', False)}")
    
    # Test dashboard data
    dashboard = service.get_dashboard_data()
    print(f"Dashboard Data: {len(dashboard)} sections")
    
    print("✅ Financial reporting service is ready!")