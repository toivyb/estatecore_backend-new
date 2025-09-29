from flask import Blueprint, request, jsonify, g
from estatecore_backend.models import db, Property
from services.ai_valuation_service import ai_valuation_service
from services.rbac_service import require_permission
import logging
import asyncio

ai_valuation_bp = Blueprint('ai_valuation', __name__, url_prefix='/api/ai-valuation')
logger = logging.getLogger(__name__)

@ai_valuation_bp.route('/property/<int:property_id>/value', methods=['GET'])
@require_permission('properties:read')
def get_property_valuation(property_id):
    """Get AI-powered property valuation"""
    try:
        force_refresh = request.args.get('force_refresh', 'false').lower() == 'true'
        
        # Run async valuation
        async def run_valuation():
            return await ai_valuation_service.value_property(property_id, force_refresh)
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(run_valuation())
        finally:
            loop.close()
        
        if result['success']:
            return jsonify({
                'success': True,
                'valuation': result['valuation'],
                'message': 'Property valuation completed successfully'
            })
        else:
            return jsonify({'error': result['error']}), 404 if 'not found' in result['error'] else 500
            
    except Exception as e:
        logger.error(f"Error getting property valuation: {str(e)}")
        return jsonify({'error': 'Failed to get property valuation'}), 500

@ai_valuation_bp.route('/market-analysis', methods=['POST'])
@require_permission('properties:read')
def analyze_market():
    """Perform comprehensive market analysis"""
    try:
        data = request.get_json()
        
        if not data or 'location' not in data:
            return jsonify({'error': 'Location is required'}), 400
        
        location = data['location']
        radius_miles = data.get('radius_miles', 2.0)
        
        # Run async market analysis
        async def run_analysis():
            return await ai_valuation_service.analyze_market(location, radius_miles)
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(run_analysis())
        finally:
            loop.close()
        
        if result['success']:
            return jsonify({
                'success': True,
                'analysis': result['analysis'],
                'message': 'Market analysis completed successfully'
            })
        else:
            return jsonify({'error': result['error']}), 500
            
    except Exception as e:
        logger.error(f"Error analyzing market: {str(e)}")
        return jsonify({'error': 'Failed to analyze market'}), 500

@ai_valuation_bp.route('/property/<int:property_id>/investment-insights', methods=['GET'])
@require_permission('properties:read')
def get_investment_insights(property_id):
    """Get AI-powered investment insights"""
    try:
        # Run async insights generation
        async def run_insights():
            return await ai_valuation_service.get_investment_insights(property_id)
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(run_insights())
        finally:
            loop.close()
        
        if result['success']:
            return jsonify({
                'success': True,
                'insights': result['insights'],
                'valuation_summary': result['valuation_summary'],
                'market_summary': result['market_summary'],
                'message': 'Investment insights generated successfully'
            })
        else:
            return jsonify({'error': result['error']}), 404 if 'not found' in result['error'] else 500
            
    except Exception as e:
        logger.error(f"Error getting investment insights: {str(e)}")
        return jsonify({'error': 'Failed to get investment insights'}), 500

@ai_valuation_bp.route('/batch-valuation', methods=['POST'])
@require_permission('properties:read')
def batch_property_valuation():
    """Perform batch valuation for multiple properties"""
    try:
        data = request.get_json()
        
        if not data or 'property_ids' not in data:
            return jsonify({'error': 'Property IDs are required'}), 400
        
        property_ids = data['property_ids']
        
        if not isinstance(property_ids, list) or len(property_ids) > 50:
            return jsonify({'error': 'Invalid property IDs list (max 50 properties)'}), 400
        
        results = []
        
        async def run_batch_valuation():
            batch_results = []
            for property_id in property_ids:
                try:
                    result = await ai_valuation_service.value_property(property_id)
                    batch_results.append({
                        'property_id': property_id,
                        'success': result['success'],
                        'valuation': result.get('valuation'),
                        'error': result.get('error')
                    })
                except Exception as e:
                    batch_results.append({
                        'property_id': property_id,
                        'success': False,
                        'error': str(e)
                    })
            return batch_results
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            results = loop.run_until_complete(run_batch_valuation())
        finally:
            loop.close()
        
        successful_valuations = [r for r in results if r['success']]
        failed_valuations = [r for r in results if not r['success']]
        
        return jsonify({
            'success': True,
            'total_properties': len(property_ids),
            'successful_valuations': len(successful_valuations),
            'failed_valuations': len(failed_valuations),
            'results': results,
            'message': f'Batch valuation completed: {len(successful_valuations)}/{len(property_ids)} successful'
        })
        
    except Exception as e:
        logger.error(f"Error in batch valuation: {str(e)}")
        return jsonify({'error': 'Failed to perform batch valuation'}), 500

@ai_valuation_bp.route('/comparative-analysis', methods=['POST'])
@require_permission('properties:read')
def comparative_analysis():
    """Compare multiple properties for investment potential"""
    try:
        data = request.get_json()
        
        if not data or 'property_ids' not in data:
            return jsonify({'error': 'Property IDs are required'}), 400
        
        property_ids = data['property_ids']
        
        if not isinstance(property_ids, list) or len(property_ids) < 2 or len(property_ids) > 10:
            return jsonify({'error': 'Please provide 2-10 properties for comparison'}), 400
        
        async def run_comparison():
            comparisons = []
            for property_id in property_ids:
                try:
                    insights_result = await ai_valuation_service.get_investment_insights(property_id)
                    if insights_result['success']:
                        comparisons.append({
                            'property_id': property_id,
                            'insights': insights_result['insights'],
                            'valuation': insights_result['valuation_summary']
                        })
                except Exception as e:
                    logger.error(f"Error getting insights for property {property_id}: {str(e)}")
            
            return comparisons
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            comparisons = loop.run_until_complete(run_comparison())
        finally:
            loop.close()
        
        if not comparisons:
            return jsonify({'error': 'No valid properties found for comparison'}), 400
        
        # Rank properties by investment score
        ranked_properties = sorted(
            comparisons,
            key=lambda x: x['insights']['property_score'],
            reverse=True
        )
        
        # Generate comparison summary
        comparison_summary = {
            'best_investment': ranked_properties[0]['property_id'] if ranked_properties else None,
            'highest_value': max(c['valuation']['estimated_value'] for c in comparisons),
            'average_value': sum(c['valuation']['estimated_value'] for c in comparisons) / len(comparisons),
            'best_appreciation': max(c['insights']['appreciation_potential'] for c in comparisons),
            'best_rental_yield': max(c['insights']['rental_income_potential'] for c in comparisons)
        }
        
        return jsonify({
            'success': True,
            'comparison_summary': comparison_summary,
            'ranked_properties': ranked_properties,
            'total_compared': len(comparisons),
            'message': 'Property comparison completed successfully'
        })
        
    except Exception as e:
        logger.error(f"Error in comparative analysis: {str(e)}")
        return jsonify({'error': 'Failed to perform comparative analysis'}), 500

@ai_valuation_bp.route('/market-trends', methods=['GET'])
@require_permission('properties:read')
def get_market_trends():
    """Get market trends and forecasts"""
    try:
        location = request.args.get('location')
        
        if not location:
            return jsonify({'error': 'Location parameter is required'}), 400
        
        async def get_trends():
            return await ai_valuation_service.analyze_market(location)
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(get_trends())
        finally:
            loop.close()
        
        if result['success']:
            analysis = result['analysis']
            
            # Extract trend data
            trends = {
                'current_trend': analysis['market_trend'],
                'price_trends': {
                    '1_year_change': analysis['price_change_1y'],
                    '3_year_change': analysis['price_change_3y']
                },
                'market_indicators': {
                    'days_on_market': analysis['days_on_market'],
                    'inventory_levels': analysis['supply_demand_ratio'],
                    'market_velocity': analysis['market_velocity']
                },
                'investment_outlook': analysis['investment_outlook'],
                'key_drivers': analysis['economic_indicators']
            }
            
            return jsonify({
                'success': True,
                'trends': trends,
                'location': location,
                'analysis_date': analysis['analysis_date'],
                'message': 'Market trends retrieved successfully'
            })
        else:
            return jsonify({'error': result['error']}), 500
            
    except Exception as e:
        logger.error(f"Error getting market trends: {str(e)}")
        return jsonify({'error': 'Failed to get market trends'}), 500

@ai_valuation_bp.route('/portfolio-analysis', methods=['POST'])
@require_permission('properties:read')
def analyze_portfolio():
    """Analyze entire property portfolio performance"""
    try:
        data = request.get_json()
        
        if not data or 'property_ids' not in data:
            return jsonify({'error': 'Property IDs are required'}), 400
        
        property_ids = data['property_ids']
        
        async def run_portfolio_analysis():
            portfolio_data = []
            total_value = 0
            total_appreciation = 0
            
            for property_id in property_ids:
                try:
                    valuation_result = await ai_valuation_service.value_property(property_id)
                    if valuation_result['success']:
                        valuation = valuation_result['valuation']
                        portfolio_data.append({
                            'property_id': property_id,
                            'current_value': valuation['estimated_value'],
                            'confidence': valuation['confidence_score'],
                            'appreciation_1y': valuation['appreciation_forecast']['1_year'] - valuation['estimated_value']
                        })
                        total_value += valuation['estimated_value']
                        total_appreciation += valuation['appreciation_forecast']['1_year'] - valuation['estimated_value']
                except Exception as e:
                    logger.error(f"Error analyzing property {property_id}: {str(e)}")
            
            return portfolio_data, total_value, total_appreciation
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            portfolio_data, total_value, total_appreciation = loop.run_until_complete(run_portfolio_analysis())
        finally:
            loop.close()
        
        if not portfolio_data:
            return jsonify({'error': 'No valid properties found in portfolio'}), 400
        
        # Calculate portfolio metrics
        avg_confidence = sum(p['confidence'] for p in portfolio_data) / len(portfolio_data)
        appreciation_rate = total_appreciation / total_value if total_value > 0 else 0
        
        portfolio_summary = {
            'total_properties': len(portfolio_data),
            'total_portfolio_value': total_value,
            'projected_appreciation_1y': total_appreciation,
            'appreciation_rate': appreciation_rate,
            'average_confidence': avg_confidence,
            'strongest_performer': max(portfolio_data, key=lambda x: x['appreciation_1y'])['property_id'],
            'portfolio_diversification': self._calculate_diversification_score(portfolio_data)
        }
        
        return jsonify({
            'success': True,
            'portfolio_summary': portfolio_summary,
            'property_details': portfolio_data,
            'message': 'Portfolio analysis completed successfully'
        })
        
    except Exception as e:
        logger.error(f"Error in portfolio analysis: {str(e)}")
        return jsonify({'error': 'Failed to analyze portfolio'}), 500

def _calculate_diversification_score(portfolio_data):
    """Calculate portfolio diversification score"""
    # Simple diversification metric based on value distribution
    values = [p['current_value'] for p in portfolio_data]
    if not values:
        return 0
    
    avg_value = sum(values) / len(values)
    variance = sum((v - avg_value) ** 2 for v in values) / len(values)
    coefficient_of_variation = (variance ** 0.5) / avg_value if avg_value > 0 else 0
    
    # Convert to 0-10 scale (lower variance = higher diversification score)
    diversification_score = max(0, 10 - (coefficient_of_variation * 10))
    return round(diversification_score, 1)

# Health check endpoint
@ai_valuation_bp.route('/health', methods=['GET'])
def ai_valuation_health_check():
    """AI valuation system health check"""
    try:
        health_status = {
            'status': 'healthy',
            'ml_models_loaded': len(ai_valuation_service.ml_models),
            'cached_valuations': len(ai_valuation_service.valuations_cache),
            'cached_market_analyses': len(ai_valuation_service.market_analyses_cache)
        }
        
        return jsonify({
            'success': True,
            'health': health_status
        })
        
    except Exception as e:
        logger.error(f"AI valuation health check failed: {str(e)}")
        return jsonify({
            'success': False,
            'status': 'unhealthy',
            'error': str(e)
        }), 500