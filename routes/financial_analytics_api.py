from flask import Blueprint, request, jsonify
from services.financial_analytics_service import financial_analytics_service, ReportType, TransactionType
from services.rbac_service import require_permission
import logging
from datetime import datetime
import json

financial_analytics_bp = Blueprint('financial_analytics', __name__, url_prefix='/api/financial-analytics')
logger = logging.getLogger(__name__)

@financial_analytics_bp.route('/transactions', methods=['POST'])
@require_permission('finance:write')
def record_transaction():
    """Record a new financial transaction"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'Request data is required'}), 400
        
        # Get user ID from session/token
        user_id = getattr(request, 'user_id', 1)  # Default to 1 for demo
        
        # Run async transaction recording
        import asyncio
        
        async def run_recording():
            return await financial_analytics_service.record_transaction(data, user_id)
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(run_recording())
        finally:
            loop.close()
        
        if result['success']:
            return jsonify(result), 201
        else:
            return jsonify({'error': result['error']}), 400
            
    except Exception as e:
        logger.error(f"Error recording transaction: {str(e)}")
        return jsonify({'error': 'Failed to record transaction'}), 500

@financial_analytics_bp.route('/reports/<report_type>', methods=['POST'])
@require_permission('finance:read')
def generate_report(report_type):
    """Generate financial report"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'Request data is required'}), 400
        
        # Validate required fields
        required_fields = ['period_start', 'period_end']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        period_start = data['period_start']
        period_end = data['period_end']
        properties = data.get('properties', [])
        user_id = getattr(request, 'user_id', 1)
        
        # Validate report type
        try:
            ReportType(report_type)
        except ValueError:
            return jsonify({'error': f'Invalid report type: {report_type}'}), 400
        
        # Run async report generation
        import asyncio
        
        async def run_generation():
            return await financial_analytics_service.generate_report(
                report_type, period_start, period_end, properties, user_id
            )
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(run_generation())
        finally:
            loop.close()
        
        if result['success']:
            return jsonify(result)
        else:
            return jsonify({'error': result['error']}), 400
            
    except Exception as e:
        logger.error(f"Error generating report: {str(e)}")
        return jsonify({'error': 'Failed to generate report'}), 500

@financial_analytics_bp.route('/dashboard', methods=['GET'])
@require_permission('finance:read')
def get_financial_dashboard():
    """Get financial dashboard data"""
    try:
        # Parse query parameters
        properties_param = request.args.get('properties')
        properties = None
        
        if properties_param:
            try:
                properties = [int(p) for p in properties_param.split(',')]
            except ValueError:
                return jsonify({'error': 'Invalid properties parameter'}), 400
        
        period_days = request.args.get('period_days', 30, type=int)
        
        if period_days < 1 or period_days > 365:
            return jsonify({'error': 'Period days must be between 1 and 365'}), 400
        
        # Run async dashboard data retrieval
        import asyncio
        
        async def get_dashboard():
            return await financial_analytics_service.get_financial_dashboard(properties, period_days)
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(get_dashboard())
        finally:
            loop.close()
        
        if result['success']:
            return jsonify(result)
        else:
            return jsonify({'error': result['error']}), 500
            
    except Exception as e:
        logger.error(f"Error getting dashboard data: {str(e)}")
        return jsonify({'error': 'Failed to get dashboard data'}), 500

@financial_analytics_bp.route('/budgets', methods=['POST'])
@require_permission('finance:write')
def create_budget():
    """Create annual budget for a property"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'Request data is required'}), 400
        
        # Validate required fields
        required_fields = ['property_id', 'year', 'budget_data']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        property_id = data['property_id']
        year = data['year']
        budget_data = data['budget_data']
        user_id = getattr(request, 'user_id', 1)
        
        # Validate data types
        if not isinstance(property_id, int) or not isinstance(year, int):
            return jsonify({'error': 'Property ID and year must be integers'}), 400
        
        if not isinstance(budget_data, dict):
            return jsonify({'error': 'Budget data must be an object'}), 400
        
        if year < 2020 or year > 2030:
            return jsonify({'error': 'Year must be between 2020 and 2030'}), 400
        
        # Run async budget creation
        import asyncio
        
        async def create_budget_async():
            return await financial_analytics_service.create_budget(property_id, year, budget_data, user_id)
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(create_budget_async())
        finally:
            loop.close()
        
        if result['success']:
            return jsonify(result), 201
        else:
            return jsonify({'error': result['error']}), 400
            
    except Exception as e:
        logger.error(f"Error creating budget: {str(e)}")
        return jsonify({'error': 'Failed to create budget'}), 500

@financial_analytics_bp.route('/budgets/<budget_id>/variance', methods=['GET'])
@require_permission('finance:read')
def get_budget_variance(budget_id):
    """Get budget variance analysis"""
    try:
        # Run async variance analysis
        import asyncio
        
        async def get_variance():
            return await financial_analytics_service.get_budget_variance_analysis(budget_id)
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(get_variance())
        finally:
            loop.close()
        
        if result['success']:
            return jsonify(result)
        else:
            return jsonify({'error': result['error']}), 404
            
    except Exception as e:
        logger.error(f"Error getting budget variance: {str(e)}")
        return jsonify({'error': 'Failed to get budget variance'}), 500

@financial_analytics_bp.route('/transactions', methods=['GET'])
@require_permission('finance:read')
def get_transactions():
    """Get transactions with filtering options"""
    try:
        # Parse query parameters
        property_id = request.args.get('property_id', type=int)
        transaction_type = request.args.get('transaction_type')
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        limit = request.args.get('limit', 50, type=int)
        
        # Validate limit
        if limit < 1 or limit > 1000:
            return jsonify({'error': 'Limit must be between 1 and 1000'}), 400
        
        # Filter transactions
        transactions = list(financial_analytics_service.transactions.values())
        
        # Apply filters
        if property_id:
            transactions = [tx for tx in transactions if tx.property_id == property_id]
        
        if transaction_type:
            try:
                tx_type = TransactionType(transaction_type)
                transactions = [tx for tx in transactions if tx.transaction_type == tx_type]
            except ValueError:
                return jsonify({'error': f'Invalid transaction type: {transaction_type}'}), 400
        
        if start_date:
            try:
                start_dt = datetime.fromisoformat(start_date)
                transactions = [tx for tx in transactions if tx.transaction_date >= start_dt]
            except ValueError:
                return jsonify({'error': 'Invalid start_date format. Use ISO format.'}), 400
        
        if end_date:
            try:
                end_dt = datetime.fromisoformat(end_date)
                transactions = [tx for tx in transactions if tx.transaction_date <= end_dt]
            except ValueError:
                return jsonify({'error': 'Invalid end_date format. Use ISO format.'}), 400
        
        # Sort by date (newest first)
        transactions.sort(key=lambda x: x.transaction_date, reverse=True)
        
        # Apply limit
        transactions = transactions[:limit]
        
        return jsonify({
            'success': True,
            'transactions': [tx.to_dict() for tx in transactions],
            'total_count': len(transactions),
            'filters_applied': {
                'property_id': property_id,
                'transaction_type': transaction_type,
                'start_date': start_date,
                'end_date': end_date,
                'limit': limit
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting transactions: {str(e)}")
        return jsonify({'error': 'Failed to get transactions'}), 500

@financial_analytics_bp.route('/reports', methods=['GET'])
@require_permission('finance:read')
def get_reports():
    """Get list of generated reports"""
    try:
        # Parse query parameters
        report_type = request.args.get('report_type')
        limit = request.args.get('limit', 50, type=int)
        
        # Get reports
        reports = list(financial_analytics_service.reports.values())
        
        # Filter by type if specified
        if report_type:
            try:
                ReportType(report_type)
                reports = [r for r in reports if r.report_type.value == report_type]
            except ValueError:
                return jsonify({'error': f'Invalid report type: {report_type}'}), 400
        
        # Sort by generation date (newest first)
        reports.sort(key=lambda x: x.generated_at, reverse=True)
        
        # Apply limit
        reports = reports[:limit]
        
        return jsonify({
            'success': True,
            'reports': [r.to_dict() for r in reports],
            'total_count': len(reports),
            'filters_applied': {
                'report_type': report_type,
                'limit': limit
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting reports: {str(e)}")
        return jsonify({'error': 'Failed to get reports'}), 500

@financial_analytics_bp.route('/reports/<report_id>', methods=['GET'])
@require_permission('finance:read')
def get_report(report_id):
    """Get specific report by ID"""
    try:
        if report_id not in financial_analytics_service.reports:
            return jsonify({'error': 'Report not found'}), 404
        
        report = financial_analytics_service.reports[report_id]
        
        return jsonify({
            'success': True,
            'report': report.to_dict()
        })
        
    except Exception as e:
        logger.error(f"Error getting report: {str(e)}")
        return jsonify({'error': 'Failed to get report'}), 500

@financial_analytics_bp.route('/budgets', methods=['GET'])
@require_permission('finance:read')
def get_budgets():
    """Get list of budgets"""
    try:
        property_id = request.args.get('property_id', type=int)
        year = request.args.get('year', type=int)
        
        # Get budgets
        budgets = list(financial_analytics_service.budgets.values())
        
        # Apply filters
        if property_id:
            budgets = [b for b in budgets if b.property_id == property_id]
        
        if year:
            budgets = [b for b in budgets if b.year == year]
        
        # Sort by creation date (newest first)
        budgets.sort(key=lambda x: x.created_at, reverse=True)
        
        return jsonify({
            'success': True,
            'budgets': [b.to_dict() for b in budgets],
            'total_count': len(budgets),
            'filters_applied': {
                'property_id': property_id,
                'year': year
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting budgets: {str(e)}")
        return jsonify({'error': 'Failed to get budgets'}), 500

@financial_analytics_bp.route('/summary', methods=['GET'])
@require_permission('finance:read')
def get_financial_summary():
    """Get high-level financial summary"""
    try:
        # Calculate summary metrics from transactions
        all_transactions = list(financial_analytics_service.transactions.values())
        
        total_income = sum(tx.amount for tx in all_transactions if tx.amount > 0)
        total_expenses = abs(sum(tx.amount for tx in all_transactions if tx.amount < 0))
        net_income = total_income - total_expenses
        
        # Transaction counts by type
        income_transactions = len([tx for tx in all_transactions if tx.amount > 0])
        expense_transactions = len([tx for tx in all_transactions if tx.amount < 0])
        
        # Recent activity
        recent_transactions = sorted(all_transactions, key=lambda x: x.transaction_date, reverse=True)[:5]
        
        summary = {
            'financial_overview': {
                'total_income': float(total_income),
                'total_expenses': float(total_expenses),
                'net_income': float(net_income),
                'profit_margin': float(net_income / total_income) if total_income > 0 else 0
            },
            'transaction_counts': {
                'total_transactions': len(all_transactions),
                'income_transactions': income_transactions,
                'expense_transactions': expense_transactions
            },
            'reports_summary': {
                'total_reports': len(financial_analytics_service.reports),
                'report_types': list(set(r.report_type.value for r in financial_analytics_service.reports.values()))
            },
            'budget_summary': {
                'total_budgets': len(financial_analytics_service.budgets),
                'budget_years': list(set(b.year for b in financial_analytics_service.budgets.values()))
            },
            'recent_activity': [tx.to_dict() for tx in recent_transactions]
        }
        
        return jsonify({
            'success': True,
            'summary': summary
        })
        
    except Exception as e:
        logger.error(f"Error getting financial summary: {str(e)}")
        return jsonify({'error': 'Failed to get financial summary'}), 500

# Health check endpoint
@financial_analytics_bp.route('/health', methods=['GET'])
def financial_analytics_health_check():
    """Financial analytics system health check"""
    try:
        health_status = {
            'status': 'healthy',
            'total_transactions': len(financial_analytics_service.transactions),
            'total_reports': len(financial_analytics_service.reports),
            'total_budgets': len(financial_analytics_service.budgets),
            'services': {
                'transaction_recording': 'operational',
                'report_generation': 'operational',
                'budget_management': 'operational',
                'dashboard_data': 'operational'
            }
        }
        
        return jsonify({
            'success': True,
            'health': health_status
        })
        
    except Exception as e:
        logger.error(f"Financial analytics health check failed: {str(e)}")
        return jsonify({
            'success': False,
            'status': 'unhealthy',
            'error': str(e)
        }), 500