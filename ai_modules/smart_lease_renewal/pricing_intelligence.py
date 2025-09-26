"""
Dynamic Pricing Intelligence Engine
Advanced market analysis and pricing optimization for lease renewals
"""

import asyncio
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from enum import Enum
import logging
import requests
import json
import statistics
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
import pickle
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MarketSegment(Enum):
    """Market segment classifications"""
    LUXURY = "luxury"
    PREMIUM = "premium"
    MARKET_RATE = "market_rate"
    AFFORDABLE = "affordable"
    SUBSIDIZED = "subsidized"

class PricingStrategy(Enum):
    """Pricing strategy types"""
    AGGRESSIVE = "aggressive"
    COMPETITIVE = "competitive"
    PREMIUM = "premium"
    VALUE_BASED = "value_based"
    RETENTION_FOCUSED = "retention_focused"

class SeasonalTrend(Enum):
    """Seasonal trend indicators"""
    PEAK = "peak"
    HIGH = "high"
    MODERATE = "moderate"
    LOW = "low"
    TROUGH = "trough"

@dataclass
class MarketComparable:
    """Market comparable property data"""
    property_id: str
    address: str
    rent_per_sqft: float
    total_rent: float
    bedrooms: int
    bathrooms: float
    square_feet: int
    amenities: List[str]
    distance_miles: float
    days_on_market: int
    occupancy_rate: float
    last_updated: datetime
    data_source: str
    confidence_score: float
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

@dataclass
class PricingRecommendation:
    """Pricing recommendation with analysis"""
    property_id: str
    tenant_id: str
    current_rent: float
    recommended_rent: float
    rent_change_percentage: float
    confidence_level: float
    strategy: PricingStrategy
    market_segment: MarketSegment
    seasonal_adjustment: float
    concessions_value: float
    total_effective_rent: float
    market_analysis: Dict[str, Any]
    risk_assessment: Dict[str, Any]
    competitive_position: Dict[str, Any]
    optimization_factors: Dict[str, Any]
    recommendation_timestamp: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

@dataclass
class MarketTrends:
    """Market trend analysis"""
    market_area: str
    average_rent_growth_12m: float
    average_rent_growth_6m: float
    vacancy_rate: float
    absorption_rate: float
    new_supply_units: int
    demand_indicators: Dict[str, float]
    seasonal_factors: Dict[str, float]
    economic_indicators: Dict[str, float]
    competitive_intensity: float
    market_maturity: str
    trend_timestamp: datetime

class DynamicPricingIntelligence:
    """
    Advanced dynamic pricing engine with market intelligence and ML optimization
    """
    
    def __init__(self, data_sources_config: Dict[str, Any] = None):
        self.data_sources = data_sources_config or {}
        
        # ML Models
        self.rent_prediction_model = None
        self.market_trend_model = None
        self.demand_forecasting_model = None
        self.scaler = StandardScaler()
        
        # Market data cache
        self.market_data_cache = {}
        self.comparable_properties = {}
        self.trend_analysis = {}
        
        # Pricing models and strategies
        self.pricing_models = {}
        self.strategy_weights = {
            PricingStrategy.AGGRESSIVE: {'rent_multiplier': 1.05, 'concession_reduction': 0.5},
            PricingStrategy.COMPETITIVE: {'rent_multiplier': 1.02, 'concession_reduction': 0.2},
            PricingStrategy.PREMIUM: {'rent_multiplier': 1.08, 'concession_reduction': 0.7},
            PricingStrategy.VALUE_BASED: {'rent_multiplier': 1.00, 'concession_reduction': 0.1},
            PricingStrategy.RETENTION_FOCUSED: {'rent_multiplier': 0.98, 'concession_reduction': -0.3}
        }
        
        # Market data sources
        self.external_data_sources = {
            'rentometer': {'enabled': False, 'api_key': None},
            'apartment_list': {'enabled': False, 'api_key': None},
            'costar': {'enabled': False, 'api_key': None},
            'realpage': {'enabled': False, 'api_key': None},
            'yardi_matrix': {'enabled': False, 'api_key': None}
        }
        
        # Load existing models
        self._load_pricing_models()
        
        # Initialize data collection
        self._initialize_data_sources()
    
    def analyze_market_pricing(self, 
                              property_data: Dict[str, Any],
                              tenant_data: Dict[str, Any],
                              lease_data: Dict[str, Any],
                              renewal_prediction: Dict[str, Any]) -> PricingRecommendation:
        """
        Comprehensive market pricing analysis and recommendation
        """
        try:
            logger.info(f"Starting pricing analysis for property {property_data.get('property_id')}")
            
            # Gather market intelligence
            market_comparables = self._get_market_comparables(property_data)
            market_trends = self._analyze_market_trends(property_data)
            competitive_analysis = self._perform_competitive_analysis(property_data, market_comparables)
            seasonal_factors = self._calculate_seasonal_factors()
            
            # Analyze current position
            current_rent = lease_data.get('monthly_rent', 0)
            market_position = self._assess_market_position(current_rent, market_comparables)
            
            # Generate ML-based rent prediction
            ml_prediction = self._predict_optimal_rent(property_data, tenant_data, market_trends)
            
            # Determine pricing strategy
            strategy = self._determine_pricing_strategy(
                renewal_prediction, tenant_data, market_position, market_trends
            )
            
            # Calculate base recommendation
            base_rent = self._calculate_base_rent(
                current_rent, market_comparables, market_trends, ml_prediction
            )
            
            # Apply strategy adjustments
            strategy_adjusted_rent = self._apply_strategy_adjustments(base_rent, strategy)
            
            # Apply seasonal adjustments
            seasonal_adjusted_rent = self._apply_seasonal_adjustments(
                strategy_adjusted_rent, seasonal_factors
            )
            
            # Apply tenant-specific adjustments
            final_rent = self._apply_tenant_adjustments(
                seasonal_adjusted_rent, tenant_data, renewal_prediction
            )
            
            # Calculate concessions
            concessions_value = self._calculate_optimal_concessions(
                final_rent, current_rent, strategy, renewal_prediction
            )
            
            # Risk assessment
            risk_assessment = self._assess_pricing_risks(
                final_rent, current_rent, market_trends, renewal_prediction
            )
            
            # Generate comprehensive recommendation
            recommendation = PricingRecommendation(
                property_id=property_data.get('property_id', ''),
                tenant_id=tenant_data.get('tenant_id', ''),
                current_rent=current_rent,
                recommended_rent=round(final_rent, 2),
                rent_change_percentage=round(((final_rent - current_rent) / current_rent) * 100, 2) if current_rent > 0 else 0,
                confidence_level=self._calculate_confidence_level(market_comparables, market_trends),
                strategy=strategy,
                market_segment=self._classify_market_segment(final_rent, market_comparables),
                seasonal_adjustment=round(seasonal_adjusted_rent - strategy_adjusted_rent, 2),
                concessions_value=concessions_value,
                total_effective_rent=round(final_rent - (concessions_value / 12), 2),
                market_analysis=self._summarize_market_analysis(market_trends, competitive_analysis),
                risk_assessment=risk_assessment,
                competitive_position=self._analyze_competitive_position(final_rent, market_comparables),
                optimization_factors=self._identify_optimization_factors(
                    property_data, market_trends, competitive_analysis
                ),
                recommendation_timestamp=datetime.now()
            )
            
            logger.info(f"Pricing analysis completed for property {property_data.get('property_id')}")
            return recommendation
            
        except Exception as e:
            logger.error(f"Error in pricing analysis: {str(e)}")
            return self._get_fallback_recommendation(property_data, tenant_data, lease_data)
    
    def get_market_intelligence_report(self, 
                                     market_area: str,
                                     property_type: str = "apartment") -> Dict[str, Any]:
        """
        Generate comprehensive market intelligence report
        """
        try:
            # Gather market data
            market_trends = self._analyze_area_market_trends(market_area)
            comparable_analysis = self._get_area_comparables(market_area, property_type)
            demand_analysis = self._analyze_demand_patterns(market_area)
            supply_analysis = self._analyze_supply_trends(market_area)
            economic_indicators = self._gather_economic_indicators(market_area)
            
            # Generate insights
            market_health_score = self._calculate_market_health_score(
                market_trends, demand_analysis, supply_analysis
            )
            
            pricing_recommendations = self._generate_area_pricing_guidance(
                market_trends, comparable_analysis
            )
            
            investment_outlook = self._assess_investment_outlook(
                market_trends, economic_indicators
            )
            
            return {
                'market_area': market_area,
                'property_type': property_type,
                'analysis_date': datetime.now().isoformat(),
                'market_health_score': market_health_score,
                'market_trends': market_trends,
                'comparable_analysis': comparable_analysis,
                'demand_analysis': demand_analysis,
                'supply_analysis': supply_analysis,
                'economic_indicators': economic_indicators,
                'pricing_recommendations': pricing_recommendations,
                'investment_outlook': investment_outlook,
                'key_insights': self._generate_key_insights(
                    market_trends, demand_analysis, supply_analysis
                ),
                'risk_factors': self._identify_market_risks(market_trends, economic_indicators)
            }
            
        except Exception as e:
            logger.error(f"Error generating market intelligence report: {str(e)}")
            return self._get_fallback_market_report(market_area)
    
    def optimize_portfolio_pricing(self, 
                                 portfolio_properties: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Optimize pricing across entire property portfolio
        """
        optimization_results = []
        portfolio_metrics = {
            'total_properties': len(portfolio_properties),
            'total_current_revenue': 0,
            'total_optimized_revenue': 0,
            'average_rent_increase': 0,
            'properties_with_increases': 0,
            'properties_with_decreases': 0,
            'risk_adjusted_return': 0
        }
        
        for property_data in portfolio_properties:
            try:
                # Get individual pricing recommendation
                tenant_data = property_data.get('tenant_data', {})
                lease_data = property_data.get('lease_data', {})
                renewal_prediction = property_data.get('renewal_prediction', {})
                
                pricing_rec = self.analyze_market_pricing(
                    property_data, tenant_data, lease_data, renewal_prediction
                )
                
                # Portfolio-level adjustments
                portfolio_adjusted_rent = self._apply_portfolio_adjustments(
                    pricing_rec.recommended_rent, property_data, portfolio_properties
                )
                
                pricing_rec.recommended_rent = portfolio_adjusted_rent
                pricing_rec.rent_change_percentage = round(
                    ((portfolio_adjusted_rent - pricing_rec.current_rent) / pricing_rec.current_rent) * 100, 2
                ) if pricing_rec.current_rent > 0 else 0
                
                optimization_results.append(pricing_rec.to_dict())
                
                # Update portfolio metrics
                portfolio_metrics['total_current_revenue'] += pricing_rec.current_rent
                portfolio_metrics['total_optimized_revenue'] += portfolio_adjusted_rent
                
                if portfolio_adjusted_rent > pricing_rec.current_rent:
                    portfolio_metrics['properties_with_increases'] += 1
                elif portfolio_adjusted_rent < pricing_rec.current_rent:
                    portfolio_metrics['properties_with_decreases'] += 1
                    
            except Exception as e:
                logger.error(f"Error optimizing property {property_data.get('property_id', 'unknown')}: {str(e)}")
                continue
        
        # Calculate portfolio-wide metrics
        if portfolio_metrics['total_current_revenue'] > 0:
            portfolio_metrics['average_rent_increase'] = round(
                ((portfolio_metrics['total_optimized_revenue'] - portfolio_metrics['total_current_revenue']) 
                 / portfolio_metrics['total_current_revenue']) * 100, 2
            )
        
        portfolio_metrics['risk_adjusted_return'] = self._calculate_portfolio_risk_adjusted_return(
            optimization_results
        )
        
        return {
            'optimization_results': optimization_results,
            'portfolio_metrics': portfolio_metrics,
            'optimization_summary': self._generate_portfolio_optimization_summary(
                optimization_results, portfolio_metrics
            ),
            'implementation_recommendations': self._generate_implementation_recommendations(
                optimization_results
            ),
            'analysis_timestamp': datetime.now().isoformat()
        }
    
    def track_pricing_performance(self, 
                                pricing_decisions: List[Dict[str, Any]],
                                actual_outcomes: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Track and analyze pricing decision performance
        """
        performance_metrics = {
            'total_decisions': len(pricing_decisions),
            'successful_renewals': 0,
            'failed_renewals': 0,
            'average_rent_achievement': 0,
            'prediction_accuracy': 0,
            'revenue_impact': 0,
            'strategy_performance': {}
        }
        
        decision_outcomes = []
        
        for i, decision in enumerate(pricing_decisions):
            if i < len(actual_outcomes):
                outcome = actual_outcomes[i]
                
                analysis = self._analyze_pricing_outcome(decision, outcome)
                decision_outcomes.append(analysis)
                
                # Update metrics
                if outcome.get('renewed', False):
                    performance_metrics['successful_renewals'] += 1
                else:
                    performance_metrics['failed_renewals'] += 1
                
                # Strategy performance tracking
                strategy = decision.get('strategy', 'unknown')
                if strategy not in performance_metrics['strategy_performance']:
                    performance_metrics['strategy_performance'][strategy] = {
                        'decisions': 0, 'successes': 0, 'avg_rent_achievement': 0
                    }
                
                performance_metrics['strategy_performance'][strategy]['decisions'] += 1
                if outcome.get('renewed', False):
                    performance_metrics['strategy_performance'][strategy]['successes'] += 1
        
        # Calculate aggregate metrics
        if performance_metrics['total_decisions'] > 0:
            performance_metrics['renewal_rate'] = round(
                (performance_metrics['successful_renewals'] / performance_metrics['total_decisions']) * 100, 2
            )
        
        return {
            'performance_metrics': performance_metrics,
            'decision_outcomes': decision_outcomes,
            'improvement_recommendations': self._generate_pricing_improvements(decision_outcomes),
            'model_retraining_needed': self._assess_retraining_need(decision_outcomes),
            'analysis_timestamp': datetime.now().isoformat()
        }
    
    # Private methods for data gathering and analysis
    
    def _get_market_comparables(self, property_data: Dict[str, Any]) -> List[MarketComparable]:
        """
        Gather market comparable properties
        """
        comparables = []
        
        # Try external data sources first
        for source, config in self.external_data_sources.items():
            if config.get('enabled', False):
                source_comparables = self._fetch_external_comparables(property_data, source)
                comparables.extend(source_comparables)
        
        # If no external data, use internal algorithms
        if not comparables:
            comparables = self._generate_synthetic_comparables(property_data)
        
        # Filter and rank comparables
        filtered_comparables = self._filter_comparables(comparables, property_data)
        
        return sorted(filtered_comparables, key=lambda x: x.confidence_score, reverse=True)[:10]
    
    def _fetch_external_comparables(self, property_data: Dict[str, Any], source: str) -> List[MarketComparable]:
        """
        Fetch comparables from external data source
        """
        comparables = []
        
        try:
            if source == 'rentometer':
                comparables = self._fetch_rentometer_data(property_data)
            elif source == 'apartment_list':
                comparables = self._fetch_apartment_list_data(property_data)
            # Add other sources as needed
                
        except Exception as e:
            logger.warning(f"Failed to fetch data from {source}: {str(e)}")
        
        return comparables
    
    def _fetch_rentometer_data(self, property_data: Dict[str, Any]) -> List[MarketComparable]:
        """
        Fetch data from Rentometer API
        """
        # This would implement actual API calls to Rentometer
        # For now, returning empty list as placeholder
        return []
    
    def _generate_synthetic_comparables(self, property_data: Dict[str, Any]) -> List[MarketComparable]:
        """
        Generate synthetic comparable data when external sources unavailable
        """
        base_rent = property_data.get('estimated_market_rent', 1500)
        bedrooms = property_data.get('bedrooms', 2)
        sqft = property_data.get('square_feet', 1000)
        
        comparables = []
        
        # Generate 5-10 synthetic comparables with variation
        for i in range(8):
            rent_variation = np.random.normal(0, 0.15)  # 15% standard deviation
            synthetic_rent = base_rent * (1 + rent_variation)
            
            comparable = MarketComparable(
                property_id=f"synthetic_{i+1}",
                address=f"Comparable Property {i+1}",
                rent_per_sqft=synthetic_rent / sqft,
                total_rent=synthetic_rent,
                bedrooms=bedrooms + np.random.randint(-1, 2),
                bathrooms=property_data.get('bathrooms', 1) + np.random.choice([-0.5, 0, 0.5]),
                square_feet=int(sqft * (1 + np.random.normal(0, 0.2))),
                amenities=property_data.get('amenities', []),
                distance_miles=np.random.uniform(0.1, 2.0),
                days_on_market=np.random.randint(5, 60),
                occupancy_rate=np.random.uniform(0.85, 0.98),
                last_updated=datetime.now() - timedelta(days=np.random.randint(1, 30)),
                data_source='synthetic',
                confidence_score=0.6 + np.random.uniform(-0.1, 0.1)
            )
            
            comparables.append(comparable)
        
        return comparables
    
    def _filter_comparables(self, comparables: List[MarketComparable], 
                           property_data: Dict[str, Any]) -> List[MarketComparable]:
        """
        Filter and validate comparable properties
        """
        filtered = []
        
        target_bedrooms = property_data.get('bedrooms', 2)
        target_sqft = property_data.get('square_feet', 1000)
        
        for comparable in comparables:
            # Filter criteria
            bedroom_diff = abs(comparable.bedrooms - target_bedrooms)
            sqft_diff_pct = abs(comparable.square_feet - target_sqft) / target_sqft if target_sqft > 0 else 0
            
            # Keep comparables that are reasonably similar
            if (bedroom_diff <= 1 and 
                sqft_diff_pct <= 0.3 and 
                comparable.distance_miles <= 3.0 and
                comparable.confidence_score >= 0.5):
                
                filtered.append(comparable)
        
        return filtered
    
    def _analyze_market_trends(self, property_data: Dict[str, Any]) -> MarketTrends:
        """
        Analyze market trends for the property area
        """
        market_area = property_data.get('market_area', property_data.get('zip_code', 'unknown'))
        
        # For now, generate synthetic trend data
        # In production, this would aggregate real market data
        
        current_month = datetime.now().month
        seasonal_factors = self._get_seasonal_factors_by_month(current_month)
        
        trends = MarketTrends(
            market_area=market_area,
            average_rent_growth_12m=np.random.uniform(0.02, 0.08),  # 2-8% annually
            average_rent_growth_6m=np.random.uniform(0.01, 0.04),  # 1-4% semi-annually
            vacancy_rate=np.random.uniform(0.03, 0.12),
            absorption_rate=np.random.uniform(0.6, 0.9),
            new_supply_units=np.random.randint(50, 500),
            demand_indicators={
                'job_growth': np.random.uniform(-0.02, 0.06),
                'population_growth': np.random.uniform(-0.01, 0.03),
                'household_formation': np.random.uniform(0.01, 0.04)
            },
            seasonal_factors=seasonal_factors,
            economic_indicators={
                'unemployment_rate': np.random.uniform(0.03, 0.08),
                'median_income_growth': np.random.uniform(0.02, 0.05),
                'inflation_rate': np.random.uniform(0.02, 0.06)
            },
            competitive_intensity=np.random.uniform(0.3, 0.8),
            market_maturity='mature' if np.random.random() > 0.3 else 'developing',
            trend_timestamp=datetime.now()
        )
        
        return trends
    
    def _perform_competitive_analysis(self, property_data: Dict[str, Any], 
                                    comparables: List[MarketComparable]) -> Dict[str, Any]:
        """
        Perform competitive analysis against market comparables
        """
        if not comparables:
            return {'status': 'insufficient_data'}
        
        current_rent = property_data.get('estimated_market_rent', 1500)
        comparable_rents = [comp.total_rent for comp in comparables]
        
        analysis = {
            'market_position': 'unknown',
            'percentile_rank': 50,
            'rent_vs_market_median': 0,
            'rent_vs_market_average': 0,
            'competitive_advantages': [],
            'competitive_disadvantages': [],
            'pricing_opportunities': []
        }
        
        if comparable_rents:
            market_median = statistics.median(comparable_rents)
            market_average = statistics.mean(comparable_rents)
            
            # Calculate position
            below_current = sum(1 for rent in comparable_rents if rent < current_rent)
            analysis['percentile_rank'] = (below_current / len(comparable_rents)) * 100
            
            analysis['rent_vs_market_median'] = current_rent - market_median
            analysis['rent_vs_market_average'] = current_rent - market_average
            
            # Determine market position
            if analysis['percentile_rank'] >= 75:
                analysis['market_position'] = 'premium'
            elif analysis['percentile_rank'] >= 60:
                analysis['market_position'] = 'above_market'
            elif analysis['percentile_rank'] >= 40:
                analysis['market_position'] = 'market_rate'
            else:
                analysis['market_position'] = 'below_market'
            
            # Identify advantages and opportunities
            property_amenities = set(property_data.get('amenities', []))
            
            for comparable in comparables:
                comp_amenities = set(comparable.amenities)
                unique_amenities = property_amenities - comp_amenities
                missing_amenities = comp_amenities - property_amenities
                
                if unique_amenities:
                    analysis['competitive_advantages'].extend(list(unique_amenities))
                if missing_amenities:
                    analysis['competitive_disadvantages'].extend(list(missing_amenities))
        
        return analysis
    
    def _calculate_seasonal_factors(self) -> Dict[str, float]:
        """
        Calculate seasonal adjustment factors
        """
        current_month = datetime.now().month
        return self._get_seasonal_factors_by_month(current_month)
    
    def _get_seasonal_factors_by_month(self, month: int) -> Dict[str, float]:
        """
        Get seasonal factors for specific month
        """
        # Seasonal rental market patterns (multipliers)
        monthly_factors = {
            1: 0.95,  # January - Low
            2: 0.97,  # February - Low
            3: 1.00,  # March - Moderate
            4: 1.03,  # April - High
            5: 1.08,  # May - Peak
            6: 1.12,  # June - Peak
            7: 1.10,  # July - High
            8: 1.05,  # August - High
            9: 1.02,  # September - Moderate
            10: 0.98,  # October - Low
            11: 0.93,  # November - Trough
            12: 0.95   # December - Low
        }
        
        return {
            'rent_multiplier': monthly_factors.get(month, 1.0),
            'demand_factor': monthly_factors.get(month, 1.0),
            'season': self._get_season_name(month),
            'trend': self._get_seasonal_trend(month)
        }
    
    def _get_season_name(self, month: int) -> str:
        """Get season name for month"""
        seasons = {
            (12, 1, 2): 'winter',
            (3, 4, 5): 'spring', 
            (6, 7, 8): 'summer',
            (9, 10, 11): 'fall'
        }
        
        for months, season in seasons.items():
            if month in months:
                return season
        return 'unknown'
    
    def _get_seasonal_trend(self, month: int) -> str:
        """Get seasonal trend direction"""
        if month in [5, 6]:
            return 'peak'
        elif month in [4, 7, 8]:
            return 'high'
        elif month in [3, 9]:
            return 'moderate'
        elif month in [1, 2, 10]:
            return 'low'
        else:  # 11, 12
            return 'trough'
    
    def _assess_market_position(self, current_rent: float, 
                              comparables: List[MarketComparable]) -> Dict[str, Any]:
        """
        Assess current market position
        """
        if not comparables:
            return {'position': 'unknown', 'percentile': 50}
        
        comparable_rents = [comp.total_rent for comp in comparables]
        below_current = sum(1 for rent in comparable_rents if rent < current_rent)
        percentile = (below_current / len(comparable_rents)) * 100
        
        if percentile >= 80:
            position = 'premium'
        elif percentile >= 60:
            position = 'above_market'
        elif percentile >= 40:
            position = 'market_rate'
        else:
            position = 'below_market'
        
        return {
            'position': position,
            'percentile': round(percentile, 1),
            'market_median': statistics.median(comparable_rents),
            'market_average': statistics.mean(comparable_rents)
        }
    
    def _predict_optimal_rent(self, property_data: Dict[str, Any],
                            tenant_data: Dict[str, Any],
                            market_trends: MarketTrends) -> float:
        """
        Use ML model to predict optimal rent
        """
        if self.rent_prediction_model is None:
            # Fallback to rule-based prediction
            return self._rule_based_rent_prediction(property_data, tenant_data, market_trends)
        
        try:
            # Extract features for ML model
            features = self._extract_pricing_features(property_data, tenant_data, market_trends)
            features_scaled = self.scaler.transform([features])
            
            predicted_rent = self.rent_prediction_model.predict(features_scaled)[0]
            return max(0, predicted_rent)
            
        except Exception as e:
            logger.warning(f"ML prediction failed, using rule-based approach: {str(e)}")
            return self._rule_based_rent_prediction(property_data, tenant_data, market_trends)
    
    def _rule_based_rent_prediction(self, property_data: Dict[str, Any],
                                  tenant_data: Dict[str, Any],
                                  market_trends: MarketTrends) -> float:
        """
        Rule-based rent prediction as fallback
        """
        base_rent = property_data.get('estimated_market_rent', 1500)
        
        # Apply market growth
        growth_adjusted = base_rent * (1 + market_trends.average_rent_growth_12m)
        
        # Apply supply/demand factors
        if market_trends.vacancy_rate < 0.05:  # Tight market
            growth_adjusted *= 1.02
        elif market_trends.vacancy_rate > 0.10:  # Loose market
            growth_adjusted *= 0.98
        
        # Apply property-specific factors
        amenity_count = len(property_data.get('amenities', []))
        if amenity_count > 5:
            growth_adjusted *= 1.01
        
        return growth_adjusted
    
    def _extract_pricing_features(self, property_data: Dict[str, Any],
                                tenant_data: Dict[str, Any],
                                market_trends: MarketTrends) -> List[float]:
        """
        Extract features for ML pricing model
        """
        return [
            property_data.get('bedrooms', 2),
            property_data.get('bathrooms', 1),
            property_data.get('square_feet', 1000),
            len(property_data.get('amenities', [])),
            property_data.get('property_age', 10),
            market_trends.average_rent_growth_12m,
            market_trends.vacancy_rate,
            market_trends.absorption_rate,
            tenant_data.get('tenancy_length_months', 12),
            tenant_data.get('payment_score', 80) / 100.0
        ]
    
    def _determine_pricing_strategy(self, renewal_prediction: Dict[str, Any],
                                  tenant_data: Dict[str, Any],
                                  market_position: Dict[str, Any],
                                  market_trends: MarketTrends) -> PricingStrategy:
        """
        Determine optimal pricing strategy
        """
        renewal_prob = renewal_prediction.get('renewal_probability', 0.5)
        risk_factors = renewal_prediction.get('risk_factors', [])
        
        # Retention-focused for at-risk tenants
        if renewal_prob < 0.4 or len(risk_factors) > 3:
            return PricingStrategy.RETENTION_FOCUSED
        
        # Value-based for moderate risk
        if renewal_prob < 0.6:
            return PricingStrategy.VALUE_BASED
        
        # Consider market position for high-probability renewals
        if market_position.get('percentile', 50) < 40:
            # Below market, can be more aggressive
            return PricingStrategy.COMPETITIVE
        elif market_position.get('percentile', 50) > 70:
            # Already premium, maintain position
            return PricingStrategy.PREMIUM
        else:
            # Standard competitive approach
            return PricingStrategy.COMPETITIVE
    
    def _calculate_base_rent(self, current_rent: float,
                           comparables: List[MarketComparable],
                           market_trends: MarketTrends,
                           ml_prediction: float) -> float:
        """
        Calculate base rent recommendation
        """
        weights = {
            'current_rent': 0.3,
            'market_comparables': 0.4,
            'market_trends': 0.2,
            'ml_prediction': 0.1
        }
        
        # Current rent component
        rent_components = [current_rent * weights['current_rent']]
        
        # Market comparables component
        if comparables:
            market_median = statistics.median([comp.total_rent for comp in comparables])
            rent_components.append(market_median * weights['market_comparables'])
        else:
            rent_components.append(current_rent * weights['market_comparables'])
        
        # Market trends component
        trend_adjusted_rent = current_rent * (1 + market_trends.average_rent_growth_12m)
        rent_components.append(trend_adjusted_rent * weights['market_trends'])
        
        # ML prediction component
        rent_components.append(ml_prediction * weights['ml_prediction'])
        
        return sum(rent_components)
    
    def _apply_strategy_adjustments(self, base_rent: float, strategy: PricingStrategy) -> float:
        """
        Apply pricing strategy adjustments
        """
        strategy_config = self.strategy_weights.get(strategy, {'rent_multiplier': 1.0})
        return base_rent * strategy_config['rent_multiplier']
    
    def _apply_seasonal_adjustments(self, rent: float, seasonal_factors: Dict[str, float]) -> float:
        """
        Apply seasonal adjustments to rent
        """
        seasonal_multiplier = seasonal_factors.get('rent_multiplier', 1.0)
        return rent * seasonal_multiplier
    
    def _apply_tenant_adjustments(self, rent: float,
                                tenant_data: Dict[str, Any],
                                renewal_prediction: Dict[str, Any]) -> float:
        """
        Apply tenant-specific adjustments
        """
        adjusted_rent = rent
        
        # Loyalty discount for long-term tenants
        tenancy_months = tenant_data.get('total_tenancy_months', 0)
        if tenancy_months >= 36:  # 3+ years
            adjusted_rent *= 0.99
        elif tenancy_months >= 24:  # 2+ years
            adjusted_rent *= 0.995
        
        # Payment history adjustment
        payment_score = tenant_data.get('payment_score', 80)
        if payment_score >= 95:
            adjusted_rent *= 1.005  # Small premium for excellent payers
        elif payment_score < 70:
            adjusted_rent *= 0.995  # Discount for payment risk
        
        # Maintenance history adjustment
        maintenance_score = tenant_data.get('maintenance_cooperation_score', 80)
        if maintenance_score >= 90:
            adjusted_rent *= 1.002  # Small premium for cooperative tenants
        
        return adjusted_rent
    
    def _calculate_optimal_concessions(self, recommended_rent: float,
                                     current_rent: float,
                                     strategy: PricingStrategy,
                                     renewal_prediction: Dict[str, Any]) -> float:
        """
        Calculate optimal concession value
        """
        renewal_prob = renewal_prediction.get('renewal_probability', 0.5)
        
        # Base concession calculation
        if renewal_prob < 0.3:
            base_concession = current_rent * 2.0  # Two months
        elif renewal_prob < 0.5:
            base_concession = current_rent * 1.0  # One month
        elif renewal_prob < 0.7:
            base_concession = current_rent * 0.5  # Half month
        else:
            base_concession = 0.0  # No concessions needed
        
        # Strategy adjustments
        strategy_config = self.strategy_weights.get(strategy, {'concession_reduction': 0})
        concession_multiplier = 1.0 + strategy_config['concession_reduction']
        
        return max(0, base_concession * concession_multiplier)
    
    def _assess_pricing_risks(self, recommended_rent: float,
                            current_rent: float,
                            market_trends: MarketTrends,
                            renewal_prediction: Dict[str, Any]) -> Dict[str, Any]:
        """
        Assess risks associated with pricing recommendation
        """
        rent_increase_pct = ((recommended_rent - current_rent) / current_rent) * 100 if current_rent > 0 else 0
        
        risks = {
            'rent_shock_risk': 'low',
            'market_resistance_risk': 'low',
            'competitive_risk': 'low',
            'renewal_risk': 'low',
            'overall_risk_score': 0.2
        }
        
        # Rent shock risk
        if rent_increase_pct > 10:
            risks['rent_shock_risk'] = 'high'
        elif rent_increase_pct > 5:
            risks['rent_shock_risk'] = 'medium'
        
        # Market resistance risk
        if market_trends.vacancy_rate > 0.08:
            risks['market_resistance_risk'] = 'medium'
        if market_trends.vacancy_rate > 0.12:
            risks['market_resistance_risk'] = 'high'
        
        # Renewal risk based on prediction
        renewal_prob = renewal_prediction.get('renewal_probability', 0.5)
        if renewal_prob < 0.4:
            risks['renewal_risk'] = 'high'
        elif renewal_prob < 0.6:
            risks['renewal_risk'] = 'medium'
        
        # Calculate overall risk score
        risk_scores = {
            'low': 0.2,
            'medium': 0.5, 
            'high': 0.8
        }
        
        avg_risk = statistics.mean([
            risk_scores[risks['rent_shock_risk']],
            risk_scores[risks['market_resistance_risk']], 
            risk_scores[risks['competitive_risk']],
            risk_scores[risks['renewal_risk']]
        ])
        
        risks['overall_risk_score'] = round(avg_risk, 2)
        
        return risks
    
    def _calculate_confidence_level(self, comparables: List[MarketComparable],
                                  market_trends: MarketTrends) -> float:
        """
        Calculate confidence level in pricing recommendation
        """
        confidence = 0.5  # Base confidence
        
        # Data quality factors
        if len(comparables) >= 5:
            confidence += 0.2
        elif len(comparables) >= 3:
            confidence += 0.1
        
        # Market trend data recency
        trend_age_days = (datetime.now() - market_trends.trend_timestamp).days
        if trend_age_days <= 7:
            confidence += 0.1
        elif trend_age_days <= 30:
            confidence += 0.05
        
        # Market stability
        if market_trends.vacancy_rate < 0.08 and market_trends.vacancy_rate > 0.03:
            confidence += 0.1  # Stable market
        
        # Comparable data quality
        if comparables:
            avg_confidence = statistics.mean([comp.confidence_score for comp in comparables])
            confidence += (avg_confidence - 0.5) * 0.2
        
        return max(0.3, min(1.0, confidence))
    
    def _classify_market_segment(self, recommended_rent: float,
                               comparables: List[MarketComparable]) -> MarketSegment:
        """
        Classify property into market segment
        """
        if not comparables:
            return MarketSegment.MARKET_RATE
        
        comparable_rents = [comp.total_rent for comp in comparables]
        percentile_90 = np.percentile(comparable_rents, 90)
        percentile_75 = np.percentile(comparable_rents, 75)
        percentile_25 = np.percentile(comparable_rents, 25)
        percentile_10 = np.percentile(comparable_rents, 10)
        
        if recommended_rent >= percentile_90:
            return MarketSegment.LUXURY
        elif recommended_rent >= percentile_75:
            return MarketSegment.PREMIUM
        elif recommended_rent >= percentile_25:
            return MarketSegment.MARKET_RATE
        elif recommended_rent >= percentile_10:
            return MarketSegment.AFFORDABLE
        else:
            return MarketSegment.SUBSIDIZED
    
    def _summarize_market_analysis(self, market_trends: MarketTrends,
                                 competitive_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        Summarize market analysis findings
        """
        return {
            'market_health': self._assess_market_health(market_trends),
            'rent_growth_trend': market_trends.average_rent_growth_12m,
            'vacancy_trend': market_trends.vacancy_rate,
            'competitive_position': competitive_analysis.get('market_position', 'unknown'),
            'demand_strength': self._assess_demand_strength(market_trends),
            'supply_pressure': self._assess_supply_pressure(market_trends)
        }
    
    def _assess_market_health(self, market_trends: MarketTrends) -> str:
        """Assess overall market health"""
        health_score = 0
        
        # Vacancy rate factor
        if market_trends.vacancy_rate < 0.05:
            health_score += 2
        elif market_trends.vacancy_rate < 0.08:
            health_score += 1
        elif market_trends.vacancy_rate > 0.12:
            health_score -= 1
        
        # Rent growth factor
        if market_trends.average_rent_growth_12m > 0.05:
            health_score += 1
        elif market_trends.average_rent_growth_12m < 0.02:
            health_score -= 1
        
        # Absorption rate
        if market_trends.absorption_rate > 0.8:
            health_score += 1
        elif market_trends.absorption_rate < 0.6:
            health_score -= 1
        
        if health_score >= 3:
            return 'excellent'
        elif health_score >= 1:
            return 'good'
        elif health_score >= -1:
            return 'fair'
        else:
            return 'poor'
    
    def _assess_demand_strength(self, market_trends: MarketTrends) -> str:
        """Assess demand strength"""
        demand_indicators = market_trends.demand_indicators
        avg_demand = statistics.mean(demand_indicators.values())
        
        if avg_demand > 0.03:
            return 'strong'
        elif avg_demand > 0.01:
            return 'moderate'
        else:
            return 'weak'
    
    def _assess_supply_pressure(self, market_trends: MarketTrends) -> str:
        """Assess supply pressure"""
        # This would analyze new supply relative to demand
        # Simplified implementation
        if market_trends.new_supply_units > 1000:
            return 'high'
        elif market_trends.new_supply_units > 200:
            return 'moderate'
        else:
            return 'low'
    
    def _analyze_competitive_position(self, recommended_rent: float,
                                    comparables: List[MarketComparable]) -> Dict[str, Any]:
        """
        Analyze competitive position of recommended rent
        """
        if not comparables:
            return {'status': 'insufficient_data'}
        
        comparable_rents = [comp.total_rent for comp in comparables]
        below_recommended = sum(1 for rent in comparable_rents if rent < recommended_rent)
        percentile = (below_recommended / len(comparable_rents)) * 100
        
        return {
            'percentile_rank': round(percentile, 1),
            'premium_to_median': recommended_rent - statistics.median(comparable_rents),
            'premium_to_average': recommended_rent - statistics.mean(comparable_rents),
            'competitive_tier': self._get_competitive_tier(percentile)
        }
    
    def _get_competitive_tier(self, percentile: float) -> str:
        """Get competitive tier based on percentile"""
        if percentile >= 80:
            return 'premium'
        elif percentile >= 60:
            return 'above_average'
        elif percentile >= 40:
            return 'average'
        elif percentile >= 20:
            return 'below_average'
        else:
            return 'value'
    
    def _identify_optimization_factors(self, property_data: Dict[str, Any],
                                     market_trends: MarketTrends,
                                     competitive_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        Identify factors that can optimize rent
        """
        factors = {
            'property_improvements': [],
            'market_timing': [],
            'competitive_advantages': [],
            'pricing_levers': []
        }
        
        # Property improvement opportunities
        amenities = property_data.get('amenities', [])
        high_value_amenities = ['parking', 'laundry', 'dishwasher', 'air_conditioning', 'balcony']
        missing_amenities = [amenity for amenity in high_value_amenities if amenity not in amenities]
        factors['property_improvements'] = missing_amenities[:3]  # Top 3
        
        # Market timing factors
        if market_trends.vacancy_rate < 0.05:
            factors['market_timing'].append('tight_market_advantage')
        
        current_month = datetime.now().month
        if current_month in [4, 5, 6]:  # Peak season
            factors['market_timing'].append('peak_season_opportunity')
        
        # Competitive advantages
        competitive_pos = competitive_analysis.get('market_position', 'unknown')
        if competitive_pos == 'below_market':
            factors['competitive_advantages'].append('pricing_upside')
        
        # Pricing levers
        factors['pricing_levers'] = [
            'seasonal_adjustments',
            'concession_optimization',
            'lease_term_flexibility'
        ]
        
        return factors
    
    # Additional helper methods...
    
    def _load_pricing_models(self):
        """Load existing ML models"""
        try:
            model_path = Path("ai_models/pricing_models")
            
            if (model_path / "rent_prediction_model.pkl").exists():
                with open(model_path / "rent_prediction_model.pkl", 'rb') as f:
                    self.rent_prediction_model = pickle.load(f)
            
            if (model_path / "feature_scaler.pkl").exists():
                with open(model_path / "feature_scaler.pkl", 'rb') as f:
                    self.scaler = pickle.load(f)
                    
        except Exception as e:
            logger.warning(f"Could not load existing pricing models: {str(e)}")
    
    def _initialize_data_sources(self):
        """Initialize external data source connections"""
        # This would set up connections to external APIs
        pass
    
    # Portfolio optimization methods
    
    def _apply_portfolio_adjustments(self, recommended_rent: float,
                                   property_data: Dict[str, Any],
                                   portfolio_properties: List[Dict[str, Any]]) -> float:
        """
        Apply portfolio-level pricing adjustments
        """
        # This would implement portfolio-wide optimization logic
        # For now, return the recommended rent unchanged
        return recommended_rent
    
    def _calculate_portfolio_risk_adjusted_return(self, optimization_results: List[Dict[str, Any]]) -> float:
        """
        Calculate portfolio-wide risk-adjusted return
        """
        if not optimization_results:
            return 0.0
        
        returns = []
        risks = []
        
        for result in optimization_results:
            rent_change_pct = result.get('rent_change_percentage', 0) / 100.0
            risk_score = result.get('risk_assessment', {}).get('overall_risk_score', 0.5)
            
            returns.append(rent_change_pct)
            risks.append(risk_score)
        
        avg_return = statistics.mean(returns)
        avg_risk = statistics.mean(risks)
        
        # Simple Sharpe-like ratio
        if avg_risk > 0:
            return avg_return / avg_risk
        else:
            return avg_return
    
    # Fallback methods
    
    def _get_fallback_recommendation(self, property_data: Dict[str, Any],
                                   tenant_data: Dict[str, Any],
                                   lease_data: Dict[str, Any]) -> PricingRecommendation:
        """
        Generate fallback pricing recommendation when main analysis fails
        """
        current_rent = lease_data.get('monthly_rent', 1500)
        
        return PricingRecommendation(
            property_id=property_data.get('property_id', ''),
            tenant_id=tenant_data.get('tenant_id', ''),
            current_rent=current_rent,
            recommended_rent=current_rent * 1.03,  # 3% increase
            rent_change_percentage=3.0,
            confidence_level=0.3,
            strategy=PricingStrategy.COMPETITIVE,
            market_segment=MarketSegment.MARKET_RATE,
            seasonal_adjustment=0.0,
            concessions_value=0.0,
            total_effective_rent=current_rent * 1.03,
            market_analysis={'status': 'limited_data'},
            risk_assessment={'overall_risk_score': 0.5},
            competitive_position={'status': 'unknown'},
            optimization_factors={},
            recommendation_timestamp=datetime.now()
        )
    
    def _get_fallback_market_report(self, market_area: str) -> Dict[str, Any]:
        """Generate fallback market report"""
        return {
            'market_area': market_area,
            'status': 'limited_data',
            'analysis_date': datetime.now().isoformat(),
            'message': 'Insufficient market data for comprehensive analysis'
        }
    
    # Analysis and reporting methods (placeholders for additional functionality)
    
    def _analyze_area_market_trends(self, market_area: str):
        """Analyze market trends for specific area"""
        return self._analyze_market_trends({'market_area': market_area})
    
    def _get_area_comparables(self, market_area: str, property_type: str):
        """Get comparables for specific market area"""
        return []
    
    def _analyze_demand_patterns(self, market_area: str):
        """Analyze demand patterns for market area"""
        return {}
    
    def _analyze_supply_trends(self, market_area: str):
        """Analyze supply trends for market area"""
        return {}
    
    def _gather_economic_indicators(self, market_area: str):
        """Gather economic indicators for market area"""
        return {}
    
    def _calculate_market_health_score(self, market_trends, demand_analysis, supply_analysis):
        """Calculate overall market health score"""
        return 7.5  # Out of 10
    
    def _generate_area_pricing_guidance(self, market_trends, comparable_analysis):
        """Generate pricing guidance for market area"""
        return {}
    
    def _assess_investment_outlook(self, market_trends, economic_indicators):
        """Assess investment outlook for market area"""
        return {}
    
    def _generate_key_insights(self, market_trends, demand_analysis, supply_analysis):
        """Generate key market insights"""
        return []
    
    def _identify_market_risks(self, market_trends, economic_indicators):
        """Identify market risks"""
        return []
    
    def _generate_portfolio_optimization_summary(self, optimization_results, portfolio_metrics):
        """Generate portfolio optimization summary"""
        return {
            'total_properties_analyzed': portfolio_metrics['total_properties'],
            'average_rent_increase': portfolio_metrics['average_rent_increase'],
            'estimated_revenue_impact': portfolio_metrics['total_optimized_revenue'] - portfolio_metrics['total_current_revenue']
        }
    
    def _generate_implementation_recommendations(self, optimization_results):
        """Generate implementation recommendations"""
        return [
            'Implement rent increases gradually over 90-day period',
            'Prioritize high-confidence recommendations first',
            'Monitor tenant response and adjust as needed'
        ]
    
    def _analyze_pricing_outcome(self, decision, outcome):
        """Analyze individual pricing decision outcome"""
        return {
            'decision_id': decision.get('id', 'unknown'),
            'predicted_renewal': decision.get('predicted_renewal_probability', 0),
            'actual_renewal': outcome.get('renewed', False),
            'predicted_rent': decision.get('recommended_rent', 0),
            'achieved_rent': outcome.get('final_rent', 0)
        }
    
    def _generate_pricing_improvements(self, decision_outcomes):
        """Generate pricing improvement recommendations"""
        return [
            'Improve tenant retention prediction accuracy',
            'Refine market comparable selection criteria',
            'Enhance seasonal adjustment factors'
        ]
    
    def _assess_retraining_need(self, decision_outcomes):
        """Assess whether model retraining is needed"""
        return len(decision_outcomes) > 100  # Simple threshold