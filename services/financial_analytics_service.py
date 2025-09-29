import logging
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
import uuid
import calendar
import numpy as np
from decimal import Decimal, ROUND_HALF_UP

from flask import current_app
from estatecore_backend.models import db, Property, User
from services.rbac_service import require_permission

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ReportType(Enum):
    INCOME_STATEMENT = "income_statement"
    CASH_FLOW = "cash_flow"
    PROFIT_LOSS = "profit_loss"
    RENT_ROLL = "rent_roll"
    OCCUPANCY_REPORT = "occupancy_report"
    EXPENSE_ANALYSIS = "expense_analysis"
    PORTFOLIO_PERFORMANCE = "portfolio_performance"
    TAX_REPORT = "tax_report"

class TransactionType(Enum):
    RENT_INCOME = "rent_income"
    LATE_FEES = "late_fees"
    SECURITY_DEPOSIT = "security_deposit"
    UTILITIES = "utilities"
    MAINTENANCE = "maintenance"
    PROPERTY_MANAGEMENT = "property_management"
    INSURANCE = "insurance"
    PROPERTY_TAX = "property_tax"
    MORTGAGE_PAYMENT = "mortgage_payment"
    CAPITAL_IMPROVEMENT = "capital_improvement"
    VACANCY_LOSS = "vacancy_loss"
    OTHER_INCOME = "other_income"
    OTHER_EXPENSE = "other_expense"

class AccountingPeriod(Enum):
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"

@dataclass
class FinancialTransaction:
    transaction_id: str
    property_id: int
    unit_id: Optional[int]
    tenant_id: Optional[int]
    transaction_type: TransactionType
    amount: Decimal
    description: str
    transaction_date: datetime
    due_date: Optional[datetime] = None
    payment_method: Optional[str] = None
    reference_number: Optional[str] = None
    is_recurring: bool = False
    recurring_frequency: Optional[str] = None
    category: Optional[str] = None
    subcategory: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)
    created_by: Optional[int] = None
    
    def to_dict(self):
        return {
            'transaction_id': self.transaction_id,
            'property_id': self.property_id,
            'unit_id': self.unit_id,
            'tenant_id': self.tenant_id,
            'transaction_type': self.transaction_type.value,
            'amount': float(self.amount),
            'description': self.description,
            'transaction_date': self.transaction_date.isoformat(),
            'due_date': self.due_date.isoformat() if self.due_date else None,
            'payment_method': self.payment_method,
            'reference_number': self.reference_number,
            'is_recurring': self.is_recurring,
            'recurring_frequency': self.recurring_frequency,
            'category': self.category,
            'subcategory': self.subcategory,
            'tags': self.tags,
            'created_at': self.created_at.isoformat(),
            'created_by': self.created_by
        }

@dataclass
class FinancialReport:
    report_id: str
    report_type: ReportType
    period_start: datetime
    period_end: datetime
    properties: List[int]
    data: Dict[str, Any]
    summary: Dict[str, Decimal]
    generated_at: datetime = field(default_factory=datetime.utcnow)
    generated_by: Optional[int] = None
    
    def to_dict(self):
        return {
            'report_id': self.report_id,
            'report_type': self.report_type.value,
            'period_start': self.period_start.isoformat(),
            'period_end': self.period_end.isoformat(),
            'properties': self.properties,
            'data': self._serialize_data(self.data),
            'summary': {k: float(v) for k, v in self.summary.items()},
            'generated_at': self.generated_at.isoformat(),
            'generated_by': self.generated_by
        }
    
    def _serialize_data(self, data):
        """Convert Decimal objects to float for JSON serialization"""
        if isinstance(data, dict):
            return {k: self._serialize_data(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [self._serialize_data(item) for item in data]
        elif isinstance(data, Decimal):
            return float(data)
        else:
            return data

@dataclass
class BudgetPlan:
    budget_id: str
    property_id: int
    year: int
    budget_data: Dict[str, Decimal]
    actual_data: Dict[str, Decimal] = field(default_factory=dict)
    variance_data: Dict[str, Decimal] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None
    
    def to_dict(self):
        return {
            'budget_id': self.budget_id,
            'property_id': self.property_id,
            'year': self.year,
            'budget_data': {k: float(v) for k, v in self.budget_data.items()},
            'actual_data': {k: float(v) for k, v in self.actual_data.items()},
            'variance_data': {k: float(v) for k, v in self.variance_data.items()},
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class FinancialAnalyticsService:
    """Comprehensive financial reporting and analytics service"""
    
    def __init__(self):
        self.transactions: Dict[str, FinancialTransaction] = {}
        self.reports: Dict[str, FinancialReport] = {}
        self.budgets: Dict[str, BudgetPlan] = {}
        
        # Initialize with sample data
        self._initialize_sample_data()
    
    def _initialize_sample_data(self):
        """Initialize with sample financial data"""
        # Sample transactions for the last 12 months
        sample_transactions = [
            # Rent income
            {
                'property_id': 123,
                'unit_id': 1,
                'tenant_id': 101,
                'transaction_type': TransactionType.RENT_INCOME,
                'amount': Decimal('2500.00'),
                'description': 'Monthly rent - Unit 1A',
                'transaction_date': datetime(2024, 9, 1),
                'payment_method': 'ACH'
            },
            {
                'property_id': 123,
                'unit_id': 2,
                'tenant_id': 102,
                'transaction_type': TransactionType.RENT_INCOME,
                'amount': Decimal('2200.00'),
                'description': 'Monthly rent - Unit 2B',
                'transaction_date': datetime(2024, 9, 1),
                'payment_method': 'Check'
            },
            # Expenses
            {
                'property_id': 123,
                'transaction_type': TransactionType.MAINTENANCE,
                'amount': Decimal('-450.00'),
                'description': 'HVAC repair - Unit 1A',
                'transaction_date': datetime(2024, 9, 5),
                'category': 'Repairs'
            },
            {
                'property_id': 123,
                'transaction_type': TransactionType.PROPERTY_TAX,
                'amount': Decimal('-1200.00'),
                'description': 'Q3 Property Tax',
                'transaction_date': datetime(2024, 9, 15),
                'category': 'Taxes'
            },
            {
                'property_id': 123,
                'transaction_type': TransactionType.INSURANCE,
                'amount': Decimal('-380.00'),
                'description': 'Property Insurance Premium',
                'transaction_date': datetime(2024, 9, 1),
                'category': 'Insurance'
            }
        ]
        
        for i, tx_data in enumerate(sample_transactions):
            transaction_id = str(uuid.uuid4())
            transaction = FinancialTransaction(
                transaction_id=transaction_id,
                **tx_data
            )
            self.transactions[transaction_id] = transaction
    
    async def record_transaction(self, transaction_data: Dict[str, Any], user_id: int) -> Dict[str, Any]:
        """Record a new financial transaction"""
        try:
            # Validate required fields
            required_fields = ['property_id', 'transaction_type', 'amount', 'description', 'transaction_date']
            for field in required_fields:
                if field not in transaction_data:
                    return {'success': False, 'error': f'Missing required field: {field}'}
            
            # Create transaction
            transaction_id = str(uuid.uuid4())
            
            transaction = FinancialTransaction(
                transaction_id=transaction_id,
                property_id=transaction_data['property_id'],
                unit_id=transaction_data.get('unit_id'),
                tenant_id=transaction_data.get('tenant_id'),
                transaction_type=TransactionType(transaction_data['transaction_type']),
                amount=Decimal(str(transaction_data['amount'])),
                description=transaction_data['description'],
                transaction_date=datetime.fromisoformat(transaction_data['transaction_date']),
                due_date=datetime.fromisoformat(transaction_data['due_date']) if transaction_data.get('due_date') else None,
                payment_method=transaction_data.get('payment_method'),
                reference_number=transaction_data.get('reference_number'),
                is_recurring=transaction_data.get('is_recurring', False),
                recurring_frequency=transaction_data.get('recurring_frequency'),
                category=transaction_data.get('category'),
                subcategory=transaction_data.get('subcategory'),
                tags=transaction_data.get('tags', []),
                created_by=user_id
            )
            
            # Store transaction
            self.transactions[transaction_id] = transaction
            
            logger.info(f"Financial transaction recorded: {transaction_id}")
            
            return {
                'success': True,
                'transaction_id': transaction_id,
                'transaction': transaction.to_dict(),
                'message': 'Transaction recorded successfully'
            }
            
        except Exception as e:
            logger.error(f"Error recording transaction: {str(e)}")
            return {'success': False, 'error': 'Failed to record transaction'}
    
    async def generate_report(self, report_type: str, period_start: str, period_end: str,
                            properties: List[int], user_id: int) -> Dict[str, Any]:
        """Generate comprehensive financial report"""
        try:
            report_type_enum = ReportType(report_type)
            start_date = datetime.fromisoformat(period_start)
            end_date = datetime.fromisoformat(period_end)
            
            # Generate report based on type
            if report_type_enum == ReportType.INCOME_STATEMENT:
                report_data, summary = await self._generate_income_statement(start_date, end_date, properties)
            elif report_type_enum == ReportType.CASH_FLOW:
                report_data, summary = await self._generate_cash_flow_report(start_date, end_date, properties)
            elif report_type_enum == ReportType.RENT_ROLL:
                report_data, summary = await self._generate_rent_roll(start_date, end_date, properties)
            elif report_type_enum == ReportType.EXPENSE_ANALYSIS:
                report_data, summary = await self._generate_expense_analysis(start_date, end_date, properties)
            elif report_type_enum == ReportType.PORTFOLIO_PERFORMANCE:
                report_data, summary = await self._generate_portfolio_performance(start_date, end_date, properties)
            else:
                return {'success': False, 'error': f'Report type {report_type} not implemented'}
            
            # Create report object
            report_id = str(uuid.uuid4())
            report = FinancialReport(
                report_id=report_id,
                report_type=report_type_enum,
                period_start=start_date,
                period_end=end_date,
                properties=properties,
                data=report_data,
                summary=summary,
                generated_by=user_id
            )
            
            # Store report
            self.reports[report_id] = report
            
            logger.info(f"Financial report generated: {report_id} ({report_type})")
            
            return {
                'success': True,
                'report_id': report_id,
                'report': report.to_dict(),
                'message': f'{report_type} report generated successfully'
            }
            
        except Exception as e:
            logger.error(f"Error generating report: {str(e)}")
            return {'success': False, 'error': 'Failed to generate report'}
    
    async def get_financial_dashboard(self, properties: Optional[List[int]] = None,
                                    period_days: int = 30) -> Dict[str, Any]:
        """Get financial dashboard data"""
        try:
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=period_days)
            
            # Filter transactions
            transactions = self._filter_transactions(start_date, end_date, properties)
            
            # Calculate key metrics
            total_income = sum(tx.amount for tx in transactions if tx.amount > 0)
            total_expenses = abs(sum(tx.amount for tx in transactions if tx.amount < 0))
            net_income = total_income - total_expenses
            
            # Income breakdown
            income_breakdown = self._calculate_income_breakdown(transactions)
            
            # Expense breakdown
            expense_breakdown = self._calculate_expense_breakdown(transactions)
            
            # Monthly trends
            monthly_trends = self._calculate_monthly_trends(start_date, end_date, properties)
            
            # Occupancy metrics
            occupancy_metrics = self._calculate_occupancy_metrics(properties)
            
            # Key performance indicators
            kpis = self._calculate_kpis(transactions, properties)
            
            dashboard_data = {
                'period': {
                    'start_date': start_date.isoformat(),
                    'end_date': end_date.isoformat(),
                    'days': period_days
                },
                'summary': {
                    'total_income': float(total_income),
                    'total_expenses': float(total_expenses),
                    'net_income': float(net_income),
                    'net_margin': float(net_income / total_income) if total_income > 0 else 0
                },
                'income_breakdown': income_breakdown,
                'expense_breakdown': expense_breakdown,
                'monthly_trends': monthly_trends,
                'occupancy_metrics': occupancy_metrics,
                'kpis': kpis,
                'properties_included': properties or 'all'
            }
            
            return {
                'success': True,
                'dashboard': dashboard_data
            }
            
        except Exception as e:
            logger.error(f"Error getting financial dashboard: {str(e)}")
            return {'success': False, 'error': 'Failed to get dashboard data'}
    
    async def create_budget(self, property_id: int, year: int, budget_data: Dict[str, float],
                          user_id: int) -> Dict[str, Any]:
        """Create annual budget for a property"""
        try:
            budget_id = str(uuid.uuid4())
            
            # Convert to Decimal for precision
            budget_decimal = {k: Decimal(str(v)) for k, v in budget_data.items()}
            
            budget = BudgetPlan(
                budget_id=budget_id,
                property_id=property_id,
                year=year,
                budget_data=budget_decimal
            )
            
            # Store budget
            self.budgets[budget_id] = budget
            
            logger.info(f"Budget created: {budget_id} for property {property_id} year {year}")
            
            return {
                'success': True,
                'budget_id': budget_id,
                'budget': budget.to_dict(),
                'message': 'Budget created successfully'
            }
            
        except Exception as e:
            logger.error(f"Error creating budget: {str(e)}")
            return {'success': False, 'error': 'Failed to create budget'}
    
    async def get_budget_variance_analysis(self, budget_id: str) -> Dict[str, Any]:
        """Analyze budget vs actual performance"""
        try:
            if budget_id not in self.budgets:
                return {'success': False, 'error': 'Budget not found'}
            
            budget = self.budgets[budget_id]
            
            # Get actual data for the budget year
            start_date = datetime(budget.year, 1, 1)
            end_date = datetime(budget.year, 12, 31)
            
            actual_data = self._calculate_actual_vs_budget(budget.property_id, start_date, end_date)
            
            # Calculate variances
            variance_data = {}
            for category, budgeted in budget.budget_data.items():
                actual = actual_data.get(category, Decimal('0'))
                variance = actual - budgeted
                variance_percentage = (variance / budgeted * 100) if budgeted != 0 else 0
                
                variance_data[category] = {
                    'budgeted': float(budgeted),
                    'actual': float(actual),
                    'variance': float(variance),
                    'variance_percentage': float(variance_percentage),
                    'status': 'over' if variance > 0 else 'under' if variance < 0 else 'on_target'
                }
            
            # Update budget with actual data
            budget.actual_data = actual_data
            budget.variance_data = {k: Decimal(str(v['variance'])) for k, v in variance_data.items()}
            budget.updated_at = datetime.utcnow()
            
            return {
                'success': True,
                'budget_id': budget_id,
                'analysis': variance_data,
                'summary': {
                    'total_budgeted': float(sum(budget.budget_data.values())),
                    'total_actual': float(sum(actual_data.values())),
                    'total_variance': float(sum(budget.variance_data.values())),
                    'categories_over_budget': len([v for v in variance_data.values() if v['status'] == 'over']),
                    'categories_under_budget': len([v for v in variance_data.values() if v['status'] == 'under'])
                }
            }
            
        except Exception as e:
            logger.error(f"Error analyzing budget variance: {str(e)}")
            return {'success': False, 'error': 'Failed to analyze budget variance'}
    
    def _filter_transactions(self, start_date: datetime, end_date: datetime,
                           properties: Optional[List[int]] = None) -> List[FinancialTransaction]:
        """Filter transactions by date range and properties"""
        filtered = []
        for transaction in self.transactions.values():
            # Date filter
            if not (start_date <= transaction.transaction_date <= end_date):
                continue
            
            # Property filter
            if properties and transaction.property_id not in properties:
                continue
            
            filtered.append(transaction)
        
        return filtered
    
    def _calculate_income_breakdown(self, transactions: List[FinancialTransaction]) -> Dict[str, float]:
        """Calculate income breakdown by type"""
        income_types = {}
        
        for tx in transactions:
            if tx.amount > 0:  # Income transactions
                tx_type = tx.transaction_type.value
                income_types[tx_type] = income_types.get(tx_type, 0) + float(tx.amount)
        
        return income_types
    
    def _calculate_expense_breakdown(self, transactions: List[FinancialTransaction]) -> Dict[str, float]:
        """Calculate expense breakdown by type"""
        expense_types = {}
        
        for tx in transactions:
            if tx.amount < 0:  # Expense transactions
                tx_type = tx.transaction_type.value
                expense_types[tx_type] = expense_types.get(tx_type, 0) + abs(float(tx.amount))
        
        return expense_types
    
    def _calculate_monthly_trends(self, start_date: datetime, end_date: datetime,
                                properties: Optional[List[int]]) -> List[Dict[str, Any]]:
        """Calculate monthly income/expense trends"""
        trends = []
        
        current_date = start_date.replace(day=1)
        while current_date <= end_date:
            month_start = current_date
            month_end = datetime(current_date.year, current_date.month, 
                               calendar.monthrange(current_date.year, current_date.month)[1])
            
            month_transactions = self._filter_transactions(month_start, month_end, properties)
            
            monthly_income = sum(tx.amount for tx in month_transactions if tx.amount > 0)
            monthly_expenses = abs(sum(tx.amount for tx in month_transactions if tx.amount < 0))
            
            trends.append({
                'month': current_date.strftime('%Y-%m'),
                'income': float(monthly_income),
                'expenses': float(monthly_expenses),
                'net_income': float(monthly_income - monthly_expenses)
            })
            
            # Move to next month
            if current_date.month == 12:
                current_date = current_date.replace(year=current_date.year + 1, month=1)
            else:
                current_date = current_date.replace(month=current_date.month + 1)
        
        return trends
    
    def _calculate_occupancy_metrics(self, properties: Optional[List[int]]) -> Dict[str, Any]:
        """Calculate occupancy-related metrics"""
        # Mock occupancy data - in production, get from property/lease data
        return {
            'occupancy_rate': 92.5,
            'average_rent': 2350,
            'vacancy_loss': 1200,
            'total_units': 156,
            'occupied_units': 144,
            'vacant_units': 12
        }
    
    def _calculate_kpis(self, transactions: List[FinancialTransaction],
                       properties: Optional[List[int]]) -> Dict[str, float]:
        """Calculate key performance indicators"""
        total_income = sum(tx.amount for tx in transactions if tx.amount > 0)
        total_expenses = abs(sum(tx.amount for tx in transactions if tx.amount < 0))
        
        return {
            'gross_rental_yield': 8.5,  # Mock data
            'net_operating_income': float(total_income - total_expenses),
            'cap_rate': 6.2,  # Mock data
            'cash_on_cash_return': 12.8,  # Mock data
            'expense_ratio': float(total_expenses / total_income) if total_income > 0 else 0,
            'rent_growth_rate': 3.2  # Mock data
        }
    
    async def _generate_income_statement(self, start_date: datetime, end_date: datetime,
                                       properties: List[int]) -> Tuple[Dict[str, Any], Dict[str, Decimal]]:
        """Generate income statement report"""
        transactions = self._filter_transactions(start_date, end_date, properties)
        
        # Income
        rental_income = sum(tx.amount for tx in transactions 
                          if tx.transaction_type == TransactionType.RENT_INCOME)
        late_fees = sum(tx.amount for tx in transactions 
                       if tx.transaction_type == TransactionType.LATE_FEES)
        other_income = sum(tx.amount for tx in transactions 
                         if tx.transaction_type == TransactionType.OTHER_INCOME)
        
        total_income = rental_income + late_fees + other_income
        
        # Expenses
        maintenance = abs(sum(tx.amount for tx in transactions 
                            if tx.transaction_type == TransactionType.MAINTENANCE and tx.amount < 0))
        utilities = abs(sum(tx.amount for tx in transactions 
                          if tx.transaction_type == TransactionType.UTILITIES and tx.amount < 0))
        insurance = abs(sum(tx.amount for tx in transactions 
                          if tx.transaction_type == TransactionType.INSURANCE and tx.amount < 0))
        property_tax = abs(sum(tx.amount for tx in transactions 
                             if tx.transaction_type == TransactionType.PROPERTY_TAX and tx.amount < 0))
        
        total_expenses = maintenance + utilities + insurance + property_tax
        net_income = total_income - total_expenses
        
        data = {
            'income': {
                'rental_income': float(rental_income),
                'late_fees': float(late_fees),
                'other_income': float(other_income),
                'total_income': float(total_income)
            },
            'expenses': {
                'maintenance': float(maintenance),
                'utilities': float(utilities),
                'insurance': float(insurance),
                'property_tax': float(property_tax),
                'total_expenses': float(total_expenses)
            },
            'net_income': float(net_income)
        }
        
        summary = {
            'total_income': total_income,
            'total_expenses': total_expenses,
            'net_income': net_income
        }
        
        return data, summary
    
    async def _generate_cash_flow_report(self, start_date: datetime, end_date: datetime,
                                       properties: List[int]) -> Tuple[Dict[str, Any], Dict[str, Decimal]]:
        """Generate cash flow report"""
        transactions = self._filter_transactions(start_date, end_date, properties)
        
        # Operating cash flows
        operating_inflows = sum(tx.amount for tx in transactions if tx.amount > 0)
        operating_outflows = abs(sum(tx.amount for tx in transactions if tx.amount < 0))
        net_operating_cash_flow = operating_inflows - operating_outflows
        
        # Mock data for other cash flow categories
        financing_cash_flow = Decimal('-2500.00')  # Mortgage payments
        investing_cash_flow = Decimal('-5000.00')  # Capital improvements
        
        net_cash_flow = net_operating_cash_flow + financing_cash_flow + investing_cash_flow
        
        data = {
            'operating_activities': {
                'cash_inflows': float(operating_inflows),
                'cash_outflows': float(operating_outflows),
                'net_operating_cash_flow': float(net_operating_cash_flow)
            },
            'financing_activities': {
                'net_financing_cash_flow': float(financing_cash_flow)
            },
            'investing_activities': {
                'net_investing_cash_flow': float(investing_cash_flow)
            },
            'net_cash_flow': float(net_cash_flow)
        }
        
        summary = {
            'net_operating_cash_flow': net_operating_cash_flow,
            'net_cash_flow': net_cash_flow
        }
        
        return data, summary
    
    async def _generate_rent_roll(self, start_date: datetime, end_date: datetime,
                                properties: List[int]) -> Tuple[Dict[str, Any], Dict[str, Decimal]]:
        """Generate rent roll report"""
        # Mock rent roll data
        rent_roll_data = [
            {
                'property_name': 'Sunset Apartments',
                'unit': '1A',
                'tenant': 'Sarah Johnson',
                'lease_start': '2024-01-01',
                'lease_end': '2024-12-31',
                'monthly_rent': 2500,
                'security_deposit': 2500,
                'status': 'occupied'
            },
            {
                'property_name': 'Sunset Apartments',
                'unit': '2B',
                'tenant': 'Michael Chen',
                'lease_start': '2024-03-01',
                'lease_end': '2025-02-28',
                'monthly_rent': 2200,
                'security_deposit': 2200,
                'status': 'occupied'
            },
            {
                'property_name': 'Oak Street Complex',
                'unit': '3C',
                'tenant': None,
                'lease_start': None,
                'lease_end': None,
                'monthly_rent': 2300,
                'security_deposit': 0,
                'status': 'vacant'
            }
        ]
        
        total_units = len(rent_roll_data)
        occupied_units = len([unit for unit in rent_roll_data if unit['status'] == 'occupied'])
        total_monthly_rent = sum(unit['monthly_rent'] for unit in rent_roll_data if unit['status'] == 'occupied')
        
        data = {
            'rent_roll': rent_roll_data,
            'summary': {
                'total_units': total_units,
                'occupied_units': occupied_units,
                'vacant_units': total_units - occupied_units,
                'occupancy_rate': occupied_units / total_units * 100,
                'total_monthly_rent': total_monthly_rent
            }
        }
        
        summary = {
            'total_monthly_rent': Decimal(str(total_monthly_rent)),
            'occupancy_rate': Decimal(str(occupied_units / total_units * 100))
        }
        
        return data, summary
    
    async def _generate_expense_analysis(self, start_date: datetime, end_date: datetime,
                                       properties: List[int]) -> Tuple[Dict[str, Any], Dict[str, Decimal]]:
        """Generate expense analysis report"""
        transactions = self._filter_transactions(start_date, end_date, properties)
        expense_transactions = [tx for tx in transactions if tx.amount < 0]
        
        # Group expenses by category
        expense_categories = {}
        for tx in expense_transactions:
            category = tx.transaction_type.value
            expense_categories[category] = expense_categories.get(category, Decimal('0')) + abs(tx.amount)
        
        total_expenses = sum(expense_categories.values())
        
        # Calculate percentages
        expense_percentages = {
            category: float(amount / total_expenses * 100) if total_expenses > 0 else 0
            for category, amount in expense_categories.items()
        }
        
        data = {
            'expense_categories': {k: float(v) for k, v in expense_categories.items()},
            'expense_percentages': expense_percentages,
            'total_expenses': float(total_expenses),
            'average_monthly_expenses': float(total_expenses / 3) if total_expenses > 0 else 0  # Assuming 3-month period
        }
        
        summary = {
            'total_expenses': total_expenses,
            'largest_expense_category': max(expense_categories.keys(), key=lambda k: expense_categories[k]) if expense_categories else 'none'
        }
        
        return data, summary
    
    async def _generate_portfolio_performance(self, start_date: datetime, end_date: datetime,
                                            properties: List[int]) -> Tuple[Dict[str, Any], Dict[str, Decimal]]:
        """Generate portfolio performance report"""
        # Mock portfolio performance data
        portfolio_data = {
            'total_properties': len(properties) if properties else 24,
            'total_units': 156,
            'occupied_units': 144,
            'occupancy_rate': 92.3,
            'total_portfolio_value': 12500000,
            'total_monthly_income': 285600,
            'total_monthly_expenses': 142800,
            'net_operating_income': 142800,
            'cap_rate': 6.8,
            'cash_on_cash_return': 12.5
        }
        
        # Property-level performance
        property_performance = [
            {
                'property_id': 123,
                'property_name': 'Sunset Apartments',
                'units': 24,
                'occupied_units': 22,
                'monthly_income': 52500,
                'monthly_expenses': 18400,
                'noi': 34100,
                'cap_rate': 7.2
            },
            {
                'property_id': 456,
                'property_name': 'Oak Street Complex',
                'units': 48,
                'occupied_units': 45,
                'monthly_income': 98750,
                'monthly_expenses': 31200,
                'noi': 67550,
                'cap_rate': 6.9
            }
        ]
        
        data = {
            'portfolio_summary': portfolio_data,
            'property_performance': property_performance
        }
        
        summary = {
            'total_noi': Decimal(str(portfolio_data['net_operating_income'])),
            'average_cap_rate': Decimal(str(portfolio_data['cap_rate']))
        }
        
        return data, summary
    
    def _calculate_actual_vs_budget(self, property_id: int, start_date: datetime,
                                  end_date: datetime) -> Dict[str, Decimal]:
        """Calculate actual financial performance vs budget"""
        transactions = self._filter_transactions(start_date, end_date, [property_id])
        
        actual_data = {
            'rental_income': Decimal('0'),
            'maintenance': Decimal('0'),
            'utilities': Decimal('0'),
            'insurance': Decimal('0'),
            'property_tax': Decimal('0')
        }
        
        for tx in transactions:
            if tx.transaction_type == TransactionType.RENT_INCOME:
                actual_data['rental_income'] += tx.amount
            elif tx.transaction_type == TransactionType.MAINTENANCE:
                actual_data['maintenance'] += abs(tx.amount)
            elif tx.transaction_type == TransactionType.UTILITIES:
                actual_data['utilities'] += abs(tx.amount)
            elif tx.transaction_type == TransactionType.INSURANCE:
                actual_data['insurance'] += abs(tx.amount)
            elif tx.transaction_type == TransactionType.PROPERTY_TAX:
                actual_data['property_tax'] += abs(tx.amount)
        
        return actual_data

# Global financial analytics service instance
financial_analytics_service = FinancialAnalyticsService()