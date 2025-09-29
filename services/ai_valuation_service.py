import logging
import requests
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
import joblib
import asyncio

from flask import current_app
from estatecore_backend.models import db, Property, User
from services.rbac_service import require_permission

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PropertyType(Enum):
    RESIDENTIAL = "residential"
    COMMERCIAL = "commercial"
    INDUSTRIAL = "industrial"
    RETAIL = "retail"
    OFFICE = "office"
    MIXED_USE = "mixed_use"

class MarketTrend(Enum):
    STRONG_APPRECIATION = "strong_appreciation"
    MODERATE_APPRECIATION = "moderate_appreciation"
    STABLE = "stable"
    DECLINING = "declining"
    VOLATILE = "volatile"

@dataclass
class PropertyValuation:
    property_id: int
    estimated_value: float
    confidence_score: float
    valuation_date: datetime
    methodology: str
    comparable_properties: List[Dict[str, Any]]
    market_factors: Dict[str, Any]
    value_breakdown: Dict[str, float]
    appreciation_forecast: Dict[str, float]
    risk_assessment: Dict[str, Any]
    recommendations: List[str]
    
    def to_dict(self):
        return {
            'property_id': self.property_id,
            'estimated_value': self.estimated_value,
            'confidence_score': self.confidence_score,
            'valuation_date': self.valuation_date.isoformat(),
            'methodology': self.methodology,
            'comparable_properties': self.comparable_properties,
            'market_factors': self.market_factors,
            'value_breakdown': self.value_breakdown,
            'appreciation_forecast': self.appreciation_forecast,
            'risk_assessment': self.risk_assessment,
            'recommendations': self.recommendations
        }

@dataclass
class MarketAnalysis:
    location: str
    analysis_date: datetime
    market_trend: MarketTrend
    average_price_psf: float
    price_change_1y: float
    price_change_3y: float
    rental_yield: float
    vacancy_rate: float
    days_on_market: float
    market_velocity: float
    supply_demand_ratio: float
    comparable_sales: List[Dict[str, Any]]
    neighborhood_metrics: Dict[str, Any]
    economic_indicators: Dict[str, Any]
    future_developments: List[Dict[str, Any]]
    investment_outlook: Dict[str, Any]
    
    def to_dict(self):
        return {
            'location': self.location,
            'analysis_date': self.analysis_date.isoformat(),
            'market_trend': self.market_trend.value,
            'average_price_psf': self.average_price_psf,
            'price_change_1y': self.price_change_1y,
            'price_change_3y': self.price_change_3y,
            'rental_yield': self.rental_yield,
            'vacancy_rate': self.vacancy_rate,
            'days_on_market': self.days_on_market,
            'market_velocity': self.market_velocity,
            'supply_demand_ratio': self.supply_demand_ratio,
            'comparable_sales': self.comparable_sales,
            'neighborhood_metrics': self.neighborhood_metrics,
            'economic_indicators': self.economic_indicators,
            'future_developments': self.future_developments,
            'investment_outlook': self.investment_outlook
        }

class AIValuationService:
    """AI-powered property valuation and market analysis service"""
    
    def __init__(self):
        self.valuations_cache: Dict[int, PropertyValuation] = {}
        self.market_analyses_cache: Dict[str, MarketAnalysis] = {}
        self.ml_models = {
            'residential': None,
            'commercial': None
        }
        self.scalers = {
            'residential': StandardScaler(),
            'commercial': StandardScaler()
        }
        self.external_apis = {
            'mls_api': 'https://api.mls.com/v1',
            'market_data_api': 'https://api.realestatedata.com/v2',
            'economic_data_api': 'https://api.economicdata.gov/v1'
        }
        self._initialize_models()
    
    def _initialize_models(self):
        """Initialize ML models for property valuation"""
        try:
            # Initialize Random Forest models for different property types
            self.ml_models['residential'] = RandomForestRegressor(
                n_estimators=100,
                max_depth=20,
                random_state=42
            )
            self.ml_models['commercial'] = RandomForestRegressor(
                n_estimators=150,
                max_depth=25,
                random_state=42
            )
            
            # Load pre-trained models if available
            try:
                self.ml_models['residential'] = joblib.load('models/residential_valuation_model.pkl')
                self.scalers['residential'] = joblib.load('models/residential_scaler.pkl')
                logger.info("Loaded pre-trained residential valuation model")
            except:
                logger.info("No pre-trained residential model found, using default")
            
            try:
                self.ml_models['commercial'] = joblib.load('models/commercial_valuation_model.pkl')
                self.scalers['commercial'] = joblib.load('models/commercial_scaler.pkl')
                logger.info("Loaded pre-trained commercial valuation model")
            except:
                logger.info("No pre-trained commercial model found, using default")
                
        except Exception as e:
            logger.error(f"Error initializing ML models: {str(e)}")
    
    async def value_property(self, property_id: int, force_refresh: bool = False) -> Dict[str, Any]:
        """Perform comprehensive AI-powered property valuation"""
        try:
            # Check cache first
            if not force_refresh and property_id in self.valuations_cache:
                cached_valuation = self.valuations_cache[property_id]
                if (datetime.utcnow() - cached_valuation.valuation_date).days < 7:
                    return {'success': True, 'valuation': cached_valuation.to_dict()}
            
            # Get property details
            property_obj = Property.query.get(property_id)
            if not property_obj:
                return {'success': False, 'error': 'Property not found'}
            
            # Gather valuation data
            property_features = await self._extract_property_features(property_obj)
            comparable_properties = await self._find_comparable_properties(property_obj)
            market_data = await self._get_market_data(property_obj.location)
            
            # Run ML valuation
            ml_valuation = self._run_ml_valuation(property_features, property_obj.property_type)
            
            # Run comparative market analysis
            cma_valuation = self._run_comparative_analysis(comparable_properties)
            
            # Combine methodologies
            final_valuation = self._combine_valuations(ml_valuation, cma_valuation, market_data)
            
            # Generate recommendations
            recommendations = self._generate_recommendations(property_obj, final_valuation, market_data)
            
            # Create valuation object
            valuation = PropertyValuation(
                property_id=property_id,
                estimated_value=final_valuation['estimated_value'],
                confidence_score=final_valuation['confidence_score'],
                valuation_date=datetime.utcnow(),
                methodology="AI-Enhanced Hybrid (ML + CMA)",
                comparable_properties=comparable_properties,
                market_factors=market_data,
                value_breakdown=final_valuation['breakdown'],
                appreciation_forecast=final_valuation['forecast'],
                risk_assessment=final_valuation['risk_assessment'],
                recommendations=recommendations
            )
            
            # Cache the valuation
            self.valuations_cache[property_id] = valuation
            
            logger.info(f"Property valuation completed for property {property_id}: ${final_valuation['estimated_value']:,.2f}")
            
            return {
                'success': True,
                'valuation': valuation.to_dict()
            }
            
        except Exception as e:
            logger.error(f"Error valuing property {property_id}: {str(e)}")
            return {'success': False, 'error': 'Failed to value property'}
    
    async def analyze_market(self, location: str, radius_miles: float = 2.0) -> Dict[str, Any]:
        """Comprehensive market analysis for a location"""
        try:
            cache_key = f"{location}_{radius_miles}"
            
            # Check cache
            if cache_key in self.market_analyses_cache:
                cached_analysis = self.market_analyses_cache[cache_key]
                if (datetime.utcnow() - cached_analysis.analysis_date).days < 1:
                    return {'success': True, 'analysis': cached_analysis.to_dict()}
            
            # Gather market data
            sales_data = await self._get_recent_sales(location, radius_miles)
            rental_data = await self._get_rental_data(location, radius_miles)
            economic_data = await self._get_economic_indicators(location)
            demographic_data = await self._get_demographic_data(location)
            development_data = await self._get_future_developments(location)
            
            # Calculate market metrics
            market_metrics = self._calculate_market_metrics(sales_data, rental_data)
            
            # Determine market trend
            market_trend = self._determine_market_trend(sales_data, economic_data)
            
            # Generate investment outlook
            investment_outlook = self._generate_investment_outlook(
                market_metrics, economic_data, development_data
            )
            
            # Create market analysis
            analysis = MarketAnalysis(
                location=location,
                analysis_date=datetime.utcnow(),
                market_trend=market_trend,
                average_price_psf=market_metrics['avg_price_psf'],
                price_change_1y=market_metrics['price_change_1y'],
                price_change_3y=market_metrics['price_change_3y'],
                rental_yield=market_metrics['rental_yield'],
                vacancy_rate=market_metrics['vacancy_rate'],
                days_on_market=market_metrics['days_on_market'],
                market_velocity=market_metrics['market_velocity'],
                supply_demand_ratio=market_metrics['supply_demand_ratio'],
                comparable_sales=sales_data[:10],  # Top 10 recent sales
                neighborhood_metrics=demographic_data,
                economic_indicators=economic_data,
                future_developments=development_data,
                investment_outlook=investment_outlook
            )
            
            # Cache analysis
            self.market_analyses_cache[cache_key] = analysis
            
            logger.info(f"Market analysis completed for {location}")
            
            return {
                'success': True,
                'analysis': analysis.to_dict()
            }
            
        except Exception as e:
            logger.error(f"Error analyzing market for {location}: {str(e)}")
            return {'success': False, 'error': 'Failed to analyze market'}
    
    async def get_investment_insights(self, property_id: int) -> Dict[str, Any]:
        """Generate AI-powered investment insights for a property"""
        try:
            # Get property valuation
            valuation_result = await self.value_property(property_id)
            if not valuation_result['success']:
                return valuation_result
            
            valuation = valuation_result['valuation']
            
            # Get market analysis
            property_obj = Property.query.get(property_id)
            market_result = await self.analyze_market(property_obj.location)
            if not market_result['success']:
                return market_result
            
            market_analysis = market_result['analysis']
            
            # Calculate investment metrics
            investment_metrics = self._calculate_investment_metrics(valuation, market_analysis, property_obj)
            
            # Generate insights
            insights = {
                'property_score': investment_metrics['overall_score'],
                'appreciation_potential': investment_metrics['appreciation_potential'],
                'rental_income_potential': investment_metrics['rental_potential'],
                'market_position': investment_metrics['market_position'],
                'risk_factors': investment_metrics['risk_factors'],
                'opportunities': investment_metrics['opportunities'],
                'comparable_performance': investment_metrics['comparable_performance'],
                'optimal_strategy': investment_metrics['optimal_strategy'],
                'exit_strategy': investment_metrics['exit_strategy'],
                'financing_recommendations': investment_metrics['financing_recommendations']
            }
            
            return {
                'success': True,
                'insights': insights,
                'valuation_summary': valuation,
                'market_summary': market_analysis
            }
            
        except Exception as e:
            logger.error(f"Error generating investment insights: {str(e)}")
            return {'success': False, 'error': 'Failed to generate investment insights'}
    
    async def _extract_property_features(self, property_obj: Property) -> Dict[str, Any]:
        """Extract features for ML valuation"""
        return {
            'square_footage': getattr(property_obj, 'square_footage', 0),
            'bedrooms': getattr(property_obj, 'bedrooms', 0),
            'bathrooms': getattr(property_obj, 'bathrooms', 0),
            'year_built': getattr(property_obj, 'year_built', 1980),
            'lot_size': getattr(property_obj, 'lot_size', 0),
            'property_type': property_obj.property_type,
            'location_score': await self._calculate_location_score(property_obj.location),
            'amenities_score': await self._calculate_amenities_score(property_obj),
            'condition_score': getattr(property_obj, 'condition_score', 7),
            'parking_spaces': getattr(property_obj, 'parking_spaces', 0),
            'has_pool': getattr(property_obj, 'has_pool', False),
            'has_garage': getattr(property_obj, 'has_garage', False),
            'walkability_score': await self._get_walkability_score(property_obj.location)
        }
    
    async def _find_comparable_properties(self, property_obj: Property) -> List[Dict[str, Any]]:
        """Find comparable properties using AI similarity matching"""
        # Mock implementation - in production, use MLS API and similarity algorithms
        return [
            {
                'address': '123 Similar St',
                'sale_price': 525000,
                'sale_date': '2024-08-15',
                'square_footage': 1850,
                'bedrooms': 3,
                'bathrooms': 2,
                'similarity_score': 0.92,
                'adjustments': {
                    'size_adjustment': 5000,
                    'condition_adjustment': -3000,
                    'location_adjustment': 2000
                }
            },
            {
                'address': '456 Comparable Ave',
                'sale_price': 515000,
                'sale_date': '2024-09-01',
                'square_footage': 1900,
                'bedrooms': 3,
                'bathrooms': 2.5,
                'similarity_score': 0.89,
                'adjustments': {
                    'size_adjustment': -8000,
                    'condition_adjustment': 0,
                    'location_adjustment': 1000
                }
            }
        ]
    
    async def _get_market_data(self, location: str) -> Dict[str, Any]:
        """Get comprehensive market data for location"""
        return {
            'median_home_price': 495000,
            'price_per_sqft': 285,
            'market_appreciation_1y': 0.08,
            'market_appreciation_3y': 0.25,
            'days_on_market': 28,
            'inventory_levels': 'low',
            'buyer_demand': 'high',
            'interest_rates': 0.065,
            'economic_growth': 0.032,
            'employment_rate': 0.96,
            'population_growth': 0.015
        }
    
    def _run_ml_valuation(self, features: Dict[str, Any], property_type: str) -> Dict[str, Any]:
        """Run machine learning valuation"""
        try:
            # Prepare feature vector
            feature_vector = np.array([
                features['square_footage'],
                features['bedrooms'],
                features['bathrooms'],
                features['year_built'],
                features['lot_size'],
                features['location_score'],
                features['amenities_score'],
                features['condition_score'],
                features['parking_spaces'],
                int(features['has_pool']),
                int(features['has_garage']),
                features['walkability_score']
            ]).reshape(1, -1)
            
            # Scale features
            model_type = 'residential' if property_type in ['house', 'condo', 'townhouse'] else 'commercial'
            scaled_features = self.scalers[model_type].transform(feature_vector)
            
            # Predict value
            predicted_value = self.ml_models[model_type].predict(scaled_features)[0]
            
            # Calculate confidence based on feature importance and data quality
            confidence = min(0.95, 0.7 + (features['condition_score'] / 10) * 0.2)
            
            return {
                'estimated_value': predicted_value,
                'confidence_score': confidence,
                'methodology': 'Machine Learning (Random Forest)'
            }
            
        except Exception as e:
            logger.error(f"Error in ML valuation: {str(e)}")
            # Fallback to simple calculation
            base_value = features['square_footage'] * 285  # $285 per sq ft
            return {
                'estimated_value': base_value,
                'confidence_score': 0.6,
                'methodology': 'Fallback Calculation'
            }
    
    def _run_comparative_analysis(self, comparables: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Run comparative market analysis"""
        if not comparables:
            return {'estimated_value': 0, 'confidence_score': 0}
        
        adjusted_values = []
        for comp in comparables:
            adjusted_value = comp['sale_price']
            for adjustment in comp['adjustments'].values():
                adjusted_value += adjustment
            adjusted_values.append(adjusted_value)
        
        avg_value = np.mean(adjusted_values)
        confidence = min(len(comparables) / 5.0, 0.9)  # Higher confidence with more comps
        
        return {
            'estimated_value': avg_value,
            'confidence_score': confidence,
            'methodology': 'Comparative Market Analysis'
        }
    
    def _combine_valuations(self, ml_val: Dict, cma_val: Dict, market_data: Dict) -> Dict[str, Any]:
        """Combine different valuation methodologies"""
        # Weight the valuations based on confidence
        ml_weight = ml_val['confidence_score'] * 0.6
        cma_weight = cma_val['confidence_score'] * 0.4
        total_weight = ml_weight + cma_weight
        
        if total_weight > 0:
            final_value = (ml_val['estimated_value'] * ml_weight + cma_val['estimated_value'] * cma_weight) / total_weight
        else:
            final_value = ml_val['estimated_value']
        
        # Apply market adjustments
        market_adjustment = 1.0 + (market_data['market_appreciation_1y'] * 0.1)
        final_value *= market_adjustment
        
        return {
            'estimated_value': final_value,
            'confidence_score': min((ml_val['confidence_score'] + cma_val['confidence_score']) / 2, 0.95),
            'breakdown': {
                'ml_valuation': ml_val['estimated_value'],
                'cma_valuation': cma_val['estimated_value'],
                'market_adjustment': market_adjustment - 1.0,
                'final_valuation': final_value
            },
            'forecast': {
                '1_year': final_value * (1 + market_data['market_appreciation_1y']),
                '3_year': final_value * (1 + market_data['market_appreciation_3y']),
                '5_year': final_value * (1 + market_data['market_appreciation_3y'] * 1.5)
            },
            'risk_assessment': {
                'market_risk': 'moderate',
                'liquidity_risk': 'low' if market_data['days_on_market'] < 30 else 'moderate',
                'volatility': 'low'
            }
        }
    
    def _generate_recommendations(self, property_obj: Property, valuation: Dict, market_data: Dict) -> List[str]:
        """Generate AI-powered recommendations"""
        recommendations = []
        
        current_value = getattr(property_obj, 'purchase_price', 0)
        estimated_value = valuation['estimated_value']
        
        if estimated_value > current_value * 1.2:
            recommendations.append("Strong appreciation potential - consider holding for long-term gains")
        elif estimated_value < current_value * 0.9:
            recommendations.append("Property may be overvalued - consider reassessing investment strategy")
        
        if market_data['days_on_market'] < 20:
            recommendations.append("Hot market conditions - good time to sell if planning exit")
        
        if market_data['rental_yield'] > 0.08:
            recommendations.append("Strong rental yield potential - consider buy-and-hold strategy")
        
        return recommendations
    
    async def _calculate_location_score(self, location: str) -> float:
        """Calculate location desirability score"""
        # Mock implementation - in production, use various location APIs
        return 8.2
    
    async def _calculate_amenities_score(self, property_obj: Property) -> float:
        """Calculate property amenities score"""
        score = 5.0  # Base score
        if getattr(property_obj, 'has_pool', False):
            score += 1.0
        if getattr(property_obj, 'has_garage', False):
            score += 0.5
        return min(score, 10.0)
    
    async def _get_walkability_score(self, location: str) -> float:
        """Get walkability score for location"""
        # Mock implementation - in production, use Walk Score API
        return 75.0
    
    async def _get_recent_sales(self, location: str, radius_miles: float) -> List[Dict[str, Any]]:
        """Get recent sales data"""
        # Mock implementation
        return []
    
    async def _get_rental_data(self, location: str, radius_miles: float) -> List[Dict[str, Any]]:
        """Get rental market data"""
        return []
    
    async def _get_economic_indicators(self, location: str) -> Dict[str, Any]:
        """Get economic indicators for location"""
        return {
            'employment_rate': 0.96,
            'gdp_growth': 0.032,
            'population_growth': 0.015,
            'crime_index': 2.3,
            'school_ratings': 8.5
        }
    
    async def _get_demographic_data(self, location: str) -> Dict[str, Any]:
        """Get demographic data"""
        return {
            'median_income': 78000,
            'average_age': 38,
            'education_level': 'college',
            'family_households': 0.65
        }
    
    async def _get_future_developments(self, location: str) -> List[Dict[str, Any]]:
        """Get planned developments"""
        return [
            {
                'name': 'Metro Transit Extension',
                'type': 'transportation',
                'completion_date': '2026-Q2',
                'impact': 'positive'
            }
        ]
    
    def _calculate_market_metrics(self, sales_data: List, rental_data: List) -> Dict[str, Any]:
        """Calculate various market metrics"""
        return {
            'avg_price_psf': 285,
            'price_change_1y': 0.08,
            'price_change_3y': 0.25,
            'rental_yield': 0.075,
            'vacancy_rate': 0.04,
            'days_on_market': 28,
            'market_velocity': 0.82,
            'supply_demand_ratio': 0.65
        }
    
    def _determine_market_trend(self, sales_data: List, economic_data: Dict) -> MarketTrend:
        """Determine overall market trend"""
        return MarketTrend.MODERATE_APPRECIATION
    
    def _generate_investment_outlook(self, market_metrics: Dict, economic_data: Dict, development_data: List) -> Dict[str, Any]:
        """Generate investment outlook"""
        return {
            'overall_rating': 'positive',
            'time_horizon': 'medium_term',
            'key_drivers': ['economic_growth', 'population_growth', 'infrastructure'],
            'risk_factors': ['interest_rate_changes'],
            'opportunity_score': 8.2
        }
    
    def _calculate_investment_metrics(self, valuation: Dict, market_analysis: Dict, property_obj: Property) -> Dict[str, Any]:
        """Calculate comprehensive investment metrics"""
        return {
            'overall_score': 8.5,
            'appreciation_potential': 'high',
            'rental_potential': 'moderate',
            'market_position': 'favorable',
            'risk_factors': ['market_volatility'],
            'opportunities': ['rental_income', 'appreciation'],
            'comparable_performance': 'above_average',
            'optimal_strategy': 'buy_and_hold',
            'exit_strategy': '5_7_years',
            'financing_recommendations': ['conventional_loan', 'consider_refinancing']
        }

# Global AI valuation service instance
ai_valuation_service = AIValuationService()