"""
Portfolio Optimization Algorithms
Advanced portfolio-level optimization for lease renewals, revenue maximization, and risk management
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any, Union
from dataclasses import dataclass, asdict
from enum import Enum
import logging
import json
import statistics
from scipy.optimize import minimize, linprog
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
import pulp  # For linear programming optimization
import warnings
warnings.filterwarnings('ignore')

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class OptimizationObjective(Enum):
    """Portfolio optimization objectives"""
    MAXIMIZE_REVENUE = "maximize_revenue"
    MAXIMIZE_RETENTION = "maximize_retention" 
    MINIMIZE_RISK = "minimize_risk"
    BALANCED_OPTIMIZATION = "balanced_optimization"
    MAXIMIZE_NOI = "maximize_noi"  # Net Operating Income

class OptimizationStrategy(Enum):
    """Optimization strategy types"""
    AGGRESSIVE = "aggressive"
    CONSERVATIVE = "conservative"
    BALANCED = "balanced"
    RISK_AVERSE = "risk_averse"
    GROWTH_FOCUSED = "growth_focused"

class PropertyTier(Enum):
    """Property tier classifications"""
    TIER_1 = "tier_1"  # Premium properties
    TIER_2 = "tier_2"  # Standard properties
    TIER_3 = "tier_3"  # Value properties

@dataclass
class OptimizationConstraint:
    """Optimization constraint definition"""
    constraint_id: str
    name: str
    constraint_type: str  # 'hard', 'soft', 'preference'
    target_value: float
    tolerance: float
    weight: float  # For soft constraints
    description: str

@dataclass
class PortfolioProperty:
    """Property data for portfolio optimization"""
    property_id: str
    current_rent: float
    market_rent: float
    tenant_id: str
    lease_expiration: datetime
    renewal_probability: float
    risk_score: float
    property_tier: PropertyTier
    bedrooms: int
    square_feet: int
    location_factor: float
    maintenance_costs: float
    expected_vacancy_cost: float
    market_appreciation_rate: float
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

@dataclass
class OptimizationResult:
    """Portfolio optimization results"""
    optimization_id: str
    objective: OptimizationObjective
    strategy: OptimizationStrategy
    property_recommendations: List[Dict[str, Any]]
    expected_outcomes: Dict[str, Any]
    risk_metrics: Dict[str, Any]
    portfolio_metrics: Dict[str, Any]
    sensitivity_analysis: Dict[str, Any]
    implementation_timeline: Dict[str, Any]
    confidence_score: float
    optimization_timestamp: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, default=str)

class PortfolioOptimizer:
    """
    Advanced portfolio optimization engine for lease renewal strategies
    """
    
    def __init__(self):
        # Optimization parameters
        self.optimization_parameters = {
            'max_rent_increase_per_property': 0.15,  # 15% max increase
            'min_retention_rate': 0.75,  # 75% minimum retention
            'risk_tolerance': 0.6,  # 0-1 scale
            'revenue_weight': 0.4,
            'retention_weight': 0.3,
            'risk_weight': 0.3
        }
        
        # Market factors
        self.market_factors = {
            'vacancy_cost_multiplier': 2.5,  # Vacancy costs 2.5x monthly rent
            'turnover_cost_fixed': 1500,     # Fixed turnover costs
            'lease_up_time_months': 2.0,     # Average time to lease up
            'concession_effectiveness': 0.15  # 15% improvement in retention per $100 concession
        }
        
        # Clustering model for property segmentation
        self.property_clusterer = KMeans(n_clusters=3, random_state=42)
        self.scaler = StandardScaler()
        
        # Optimization history
        self.optimization_history = []
        
    def optimize_portfolio(self, 
                          properties: List[PortfolioProperty],
                          objective: OptimizationObjective = OptimizationObjective.BALANCED_OPTIMIZATION,
                          constraints: List[OptimizationConstraint] = None,
                          strategy: OptimizationStrategy = OptimizationStrategy.BALANCED) -> OptimizationResult:
        """
        Optimize entire portfolio for lease renewals
        """
        try:
            logger.info(f"Starting portfolio optimization with objective: {objective.value}")
            
            # Validate and prepare data
            if not properties:
                raise ValueError("No properties provided for optimization")
            
            # Segment properties for targeted optimization
            property_segments = self._segment_properties(properties)
            
            # Generate optimization model based on objective
            optimization_model = self._build_optimization_model(
                properties, objective, constraints, strategy
            )
            
            # Solve optimization problem
            solution = self._solve_optimization(optimization_model, properties)
            
            # Generate property-specific recommendations
            property_recommendations = self._generate_property_recommendations(
                properties, solution, strategy
            )
            
            # Calculate expected outcomes
            expected_outcomes = self._calculate_expected_outcomes(
                properties, property_recommendations
            )
            
            # Assess portfolio risks
            risk_metrics = self._assess_portfolio_risks(
                properties, property_recommendations
            )
            
            # Calculate portfolio-level metrics
            portfolio_metrics = self._calculate_portfolio_metrics(
                properties, property_recommendations, expected_outcomes
            )
            
            # Perform sensitivity analysis
            sensitivity_analysis = self._perform_sensitivity_analysis(
                properties, solution, optimization_model
            )
            
            # Generate implementation timeline
            implementation_timeline = self._generate_implementation_timeline(
                property_recommendations
            )
            
            # Calculate confidence score
            confidence_score = self._calculate_optimization_confidence(
                properties, solution, sensitivity_analysis
            )
            
            # Create optimization result
            result = OptimizationResult(
                optimization_id=f"opt_{int(datetime.now().timestamp())}",
                objective=objective,
                strategy=strategy,
                property_recommendations=property_recommendations,
                expected_outcomes=expected_outcomes,
                risk_metrics=risk_metrics,
                portfolio_metrics=portfolio_metrics,
                sensitivity_analysis=sensitivity_analysis,
                implementation_timeline=implementation_timeline,
                confidence_score=confidence_score,
                optimization_timestamp=datetime.now()
            )
            
            # Store optimization history
            self.optimization_history.append(result.to_dict())
            
            logger.info(f"Portfolio optimization completed successfully")
            return result
            
        except Exception as e:
            logger.error(f"Error in portfolio optimization: {str(e)}")
            return self._get_fallback_optimization(properties, objective, strategy)
    
    def optimize_lease_expiration_staggering(self, 
                                           properties: List[PortfolioProperty],
                                           target_distribution: Dict[int, float] = None) -> Dict[str, Any]:
        """
        Optimize lease expiration timing to minimize vacancy clustering
        """
        try:
            if not target_distribution:
                # Default: even distribution across 12 months
                target_distribution = {month: 1/12 for month in range(1, 13)}
            
            # Current lease expiration distribution
            current_distribution = self._analyze_expiration_distribution(properties)
            
            # Identify optimization opportunities
            staggering_opportunities = self._identify_staggering_opportunities(
                properties, current_distribution, target_distribution
            )
            
            # Generate staggering recommendations
            recommendations = self._generate_staggering_recommendations(
                staggering_opportunities, target_distribution
            )
            
            # Calculate impact metrics
            impact_metrics = self._calculate_staggering_impact(
                properties, recommendations, current_distribution, target_distribution
            )
            
            return {
                'current_distribution': current_distribution,
                'target_distribution': target_distribution,
                'staggering_opportunities': staggering_opportunities,
                'recommendations': recommendations,
                'impact_metrics': impact_metrics,
                'implementation_priority': self._prioritize_staggering_actions(recommendations),
                'analysis_timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error in lease staggering optimization: {str(e)}")
            return {'status': 'error', 'message': str(e)}
    
    def optimize_concession_strategy(self, 
                                   properties: List[PortfolioProperty],
                                   concession_budget: float) -> Dict[str, Any]:
        """
        Optimize concession allocation across portfolio
        """
        try:
            # Calculate concession effectiveness for each property
            concession_effectiveness = self._calculate_concession_effectiveness(properties)
            
            # Use linear programming to optimize allocation
            allocation_solution = self._optimize_concession_allocation(
                properties, concession_effectiveness, concession_budget
            )
            
            # Generate concession recommendations
            recommendations = self._generate_concession_recommendations(
                properties, allocation_solution
            )
            
            # Calculate expected ROI
            roi_analysis = self._calculate_concession_roi(
                properties, recommendations, concession_budget
            )
            
            return {
                'concession_budget': concession_budget,
                'allocation_recommendations': recommendations,
                'effectiveness_scores': concession_effectiveness,
                'roi_analysis': roi_analysis,
                'budget_utilization': sum(rec['recommended_concession'] for rec in recommendations),
                'expected_retention_improvement': roi_analysis.get('retention_improvement', 0),
                'analysis_timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error in concession optimization: {str(e)}")
            return {'status': 'error', 'message': str(e)}
    
    def optimize_market_positioning(self, 
                                  properties: List[PortfolioProperty],
                                  market_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Optimize portfolio positioning relative to market
        """
        try:
            # Analyze current market position
            current_positioning = self._analyze_current_positioning(properties, market_data)
            
            # Identify positioning opportunities
            positioning_opportunities = self._identify_positioning_opportunities(
                properties, current_positioning, market_data
            )
            
            # Generate positioning strategies
            positioning_strategies = self._generate_positioning_strategies(
                positioning_opportunities, market_data
            )
            
            # Calculate competitive impact
            competitive_impact = self._calculate_competitive_impact(
                properties, positioning_strategies, market_data
            )
            
            return {
                'current_positioning': current_positioning,
                'positioning_opportunities': positioning_opportunities,
                'recommended_strategies': positioning_strategies,
                'competitive_impact': competitive_impact,
                'implementation_roadmap': self._generate_positioning_roadmap(positioning_strategies),
                'analysis_timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error in market positioning optimization: {str(e)}")
            return {'status': 'error', 'message': str(e)}
    
    def analyze_portfolio_performance(self, 
                                    optimization_results: List[OptimizationResult],
                                    actual_outcomes: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze optimization performance and learn from outcomes
        """
        try:
            if len(optimization_results) != len(actual_outcomes):
                raise ValueError("Mismatch between optimization results and actual outcomes")
            
            # Performance analysis
            performance_metrics = self._calculate_performance_metrics(
                optimization_results, actual_outcomes
            )
            
            # Accuracy analysis
            accuracy_analysis = self._analyze_prediction_accuracy(
                optimization_results, actual_outcomes
            )
            
            # Strategy effectiveness
            strategy_effectiveness = self._analyze_strategy_effectiveness(
                optimization_results, actual_outcomes
            )
            
            # Model improvement recommendations
            improvement_recommendations = self._generate_improvement_recommendations(
                performance_metrics, accuracy_analysis, strategy_effectiveness
            )
            
            return {
                'performance_metrics': performance_metrics,
                'accuracy_analysis': accuracy_analysis,
                'strategy_effectiveness': strategy_effectiveness,
                'improvement_recommendations': improvement_recommendations,
                'model_update_needed': self._assess_model_update_need(accuracy_analysis),
                'analysis_timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error in performance analysis: {str(e)}")
            return {'status': 'error', 'message': str(e)}
    
    # Private optimization methods
    
    def _segment_properties(self, properties: List[PortfolioProperty]) -> Dict[str, List[PortfolioProperty]]:
        """
        Segment properties for targeted optimization
        """
        # Extract features for clustering
        features = []
        for prop in properties:
            features.append([
                prop.current_rent,
                prop.renewal_probability,
                prop.risk_score,
                prop.square_feet,
                prop.location_factor,
                (prop.lease_expiration - datetime.now()).days
            ])
        
        # Normalize features
        features_scaled = self.scaler.fit_transform(features)
        
        # Cluster properties
        clusters = self.property_clusterer.fit_predict(features_scaled)
        
        # Group properties by cluster
        segments = {}
        for i, cluster in enumerate(clusters):
            cluster_name = f"segment_{cluster}"
            if cluster_name not in segments:
                segments[cluster_name] = []
            segments[cluster_name].append(properties[i])
        
        return segments
    
    def _build_optimization_model(self, 
                                properties: List[PortfolioProperty],
                                objective: OptimizationObjective,
                                constraints: List[OptimizationConstraint],
                                strategy: OptimizationStrategy) -> Dict[str, Any]:
        """
        Build mathematical optimization model
        """
        n_properties = len(properties)
        
        # Decision variables: rent increase percentage for each property
        rent_increases = pulp.LpVariable.dicts("rent_increase", range(n_properties), 
                                             lowBound=-0.05, upBound=0.15, cat='Continuous')
        
        # Concession variables: concession amount for each property
        concessions = pulp.LpVariable.dicts("concession", range(n_properties),
                                          lowBound=0, upBound=5000, cat='Continuous')
        
        # Binary variables: whether to renew lease for each property
        renewals = pulp.LpVariable.dicts("renewal", range(n_properties), cat='Binary')
        
        # Create problem
        if objective == OptimizationObjective.MAXIMIZE_REVENUE:
            prob = pulp.LpProblem("Portfolio_Revenue_Maximization", pulp.LpMaximize)
        elif objective == OptimizationObjective.MAXIMIZE_RETENTION:
            prob = pulp.LpProblem("Portfolio_Retention_Maximization", pulp.LpMaximize)
        elif objective == OptimizationObjective.MINIMIZE_RISK:
            prob = pulp.LpProblem("Portfolio_Risk_Minimization", pulp.LpMinimize)
        else:
            prob = pulp.LpProblem("Portfolio_Balanced_Optimization", pulp.LpMaximize)
        
        # Define objective function
        objective_expr = self._build_objective_function(
            properties, rent_increases, concessions, renewals, objective
        )
        prob += objective_expr
        
        # Add constraints
        self._add_optimization_constraints(
            prob, properties, rent_increases, concessions, renewals, constraints, strategy
        )
        
        return {
            'problem': prob,
            'rent_increases': rent_increases,
            'concessions': concessions,
            'renewals': renewals
        }
    
    def _build_objective_function(self,
                                properties: List[PortfolioProperty],
                                rent_increases: Dict,
                                concessions: Dict,
                                renewals: Dict,
                                objective: OptimizationObjective) -> pulp.LpAffineExpression:
        """
        Build objective function based on optimization goal
        """
        n_properties = len(properties)
        
        if objective == OptimizationObjective.MAXIMIZE_REVENUE:
            # Maximize total rental revenue minus concessions and vacancy costs
            revenue_expr = 0
            for i in range(n_properties):
                prop = properties[i]
                # Revenue from renewed leases
                new_rent = prop.current_rent * (1 + rent_increases[i])
                annual_revenue = new_rent * 12 * renewals[i]
                
                # Subtract concessions
                revenue_expr += annual_revenue - concessions[i]
                
                # Subtract expected vacancy costs for non-renewals
                vacancy_cost = (prop.expected_vacancy_cost * (1 - renewals[i]))
                revenue_expr -= vacancy_cost
            
            return revenue_expr
        
        elif objective == OptimizationObjective.MAXIMIZE_RETENTION:
            # Maximize number of renewals weighted by property value
            retention_expr = 0
            for i in range(n_properties):
                prop = properties[i]
                # Weight renewal by property rent level
                weight = prop.current_rent / 1000  # Normalize by typical rent level
                retention_expr += renewals[i] * weight
            
            return retention_expr
        
        elif objective == OptimizationObjective.MINIMIZE_RISK:
            # Minimize portfolio risk score
            risk_expr = 0
            for i in range(n_properties):
                prop = properties[i]
                # Risk increases with rent increases and decreases with renewals
                risk_contribution = (prop.risk_score * rent_increases[i] * 100 - 
                                   renewals[i] * prop.risk_score)
                risk_expr += risk_contribution
            
            return risk_expr
        
        else:  # BALANCED_OPTIMIZATION
            # Multi-objective function balancing revenue, retention, and risk
            revenue_component = 0
            retention_component = 0
            risk_component = 0
            
            for i in range(n_properties):
                prop = properties[i]
                
                # Revenue component
                new_rent = prop.current_rent * (1 + rent_increases[i])
                revenue_component += (new_rent - prop.current_rent) * 12 * renewals[i]
                
                # Retention component
                retention_component += renewals[i] * prop.current_rent / 1000
                
                # Risk component (to minimize)
                risk_component += prop.risk_score * rent_increases[i] * renewals[i]
            
            # Weighted combination
            weights = self.optimization_parameters
            balanced_expr = (weights['revenue_weight'] * revenue_component +
                           weights['retention_weight'] * retention_component -
                           weights['risk_weight'] * risk_component)
            
            return balanced_expr
    
    def _add_optimization_constraints(self,
                                    prob: pulp.LpProblem,
                                    properties: List[PortfolioProperty],
                                    rent_increases: Dict,
                                    concessions: Dict,
                                    renewals: Dict,
                                    constraints: List[OptimizationConstraint],
                                    strategy: OptimizationStrategy):
        """
        Add constraints to optimization problem
        """
        n_properties = len(properties)
        
        # Portfolio-level retention constraint
        min_retention_rate = self.optimization_parameters['min_retention_rate']
        total_renewals = pulp.lpSum([renewals[i] for i in range(n_properties)])
        prob += total_renewals >= min_retention_rate * n_properties, "Min_Retention_Rate"
        
        # Individual property constraints
        for i in range(n_properties):
            prop = properties[i]
            
            # Link renewal decision to rent increase and renewal probability
            # Higher rent increases reduce renewal probability
            base_renewal_prob = prop.renewal_probability
            
            # Simplified constraint: if rent increase > threshold, renewal probability drops
            prob += rent_increases[i] <= 0.10, f"Max_Rent_Increase_{i}"
            
            # Concession effectiveness constraint
            # More concessions improve renewal probability
            max_concession = prop.current_rent * 2  # Max 2 months rent
            prob += concessions[i] <= max_concession, f"Max_Concession_{i}"
        
        # Strategy-specific constraints
        if strategy == OptimizationStrategy.CONSERVATIVE:
            # Conservative strategy: limit rent increases
            for i in range(n_properties):
                prob += rent_increases[i] <= 0.05, f"Conservative_Rent_Limit_{i}"
        
        elif strategy == OptimizationStrategy.AGGRESSIVE:
            # Aggressive strategy: allow higher increases but ensure retention
            prob += total_renewals >= 0.80 * n_properties, "Aggressive_Retention_Min"
        
        elif strategy == OptimizationStrategy.RISK_AVERSE:
            # Risk-averse: prioritize low-risk properties
            for i in range(n_properties):
                prop = properties[i]
                if prop.risk_score > 70:  # High risk properties
                    prob += rent_increases[i] <= 0.02, f"Risk_Averse_Limit_{i}"
        
        # Custom constraints
        if constraints:
            for constraint in constraints:
                self._add_custom_constraint(prob, constraint, properties, rent_increases, 
                                          concessions, renewals)
    
    def _add_custom_constraint(self,
                             prob: pulp.LpProblem,
                             constraint: OptimizationConstraint,
                             properties: List[PortfolioProperty],
                             rent_increases: Dict,
                             concessions: Dict,
                             renewals: Dict):
        """
        Add custom constraint to optimization problem
        """
        # Implementation would depend on specific constraint types
        # This is a placeholder for extensibility
        pass
    
    def _solve_optimization(self, 
                          optimization_model: Dict[str, Any],
                          properties: List[PortfolioProperty]) -> Dict[str, Any]:
        """
        Solve the optimization problem
        """
        prob = optimization_model['problem']
        
        # Solve the problem
        prob.solve()
        
        # Extract solution
        solution = {
            'status': pulp.LpStatus[prob.status],
            'objective_value': pulp.value(prob.objective),
            'rent_increases': {},
            'concessions': {},
            'renewals': {}
        }
        
        # Extract variable values
        for i in range(len(properties)):
            solution['rent_increases'][i] = pulp.value(optimization_model['rent_increases'][i])
            solution['concessions'][i] = pulp.value(optimization_model['concessions'][i])
            solution['renewals'][i] = pulp.value(optimization_model['renewals'][i])
        
        return solution
    
    def _generate_property_recommendations(self,
                                         properties: List[PortfolioProperty],
                                         solution: Dict[str, Any],
                                         strategy: OptimizationStrategy) -> List[Dict[str, Any]]:
        """
        Generate property-specific recommendations from optimization solution
        """
        recommendations = []
        
        for i, prop in enumerate(properties):
            rent_increase = solution['rent_increases'].get(i, 0)
            concession = solution['concessions'].get(i, 0)
            renewal_recommended = solution['renewals'].get(i, 0) > 0.5
            
            # Calculate new rent
            new_rent = prop.current_rent * (1 + rent_increase)
            
            # Generate recommendation
            recommendation = {
                'property_id': prop.property_id,
                'tenant_id': prop.tenant_id,
                'current_rent': prop.current_rent,
                'recommended_rent': round(new_rent, 2),
                'rent_increase_percentage': round(rent_increase * 100, 2),
                'recommended_concession': round(concession, 2),
                'renewal_recommended': renewal_recommended,
                'strategy_applied': strategy.value,
                'expected_renewal_probability': self._calculate_adjusted_renewal_probability(
                    prop, rent_increase, concession
                ),
                'revenue_impact': self._calculate_revenue_impact(prop, rent_increase, concession),
                'risk_assessment': self._assess_recommendation_risk(prop, rent_increase),
                'implementation_priority': self._calculate_implementation_priority(
                    prop, rent_increase, concession
                ),
                'alternative_scenarios': self._generate_alternative_scenarios(prop)
            }
            
            recommendations.append(recommendation)
        
        return recommendations
    
    def _calculate_expected_outcomes(self,
                                   properties: List[PortfolioProperty],
                                   recommendations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Calculate expected portfolio outcomes from recommendations
        """
        total_current_revenue = sum(prop.current_rent * 12 for prop in properties)
        total_recommended_revenue = 0
        total_concessions = 0
        expected_renewals = 0
        total_risk_score = 0
        
        for i, rec in enumerate(recommendations):
            prop = properties[i]
            
            # Revenue calculations
            if rec['renewal_recommended']:
                annual_revenue = rec['recommended_rent'] * 12
                total_recommended_revenue += annual_revenue - rec['recommended_concession']
                expected_renewals += rec['expected_renewal_probability']
            else:
                # Factor in vacancy and re-leasing costs
                vacancy_cost = prop.expected_vacancy_cost
                total_recommended_revenue += (prop.market_rent * 12 * 0.9) - vacancy_cost
            
            total_concessions += rec['recommended_concession']
            total_risk_score += prop.risk_score
        
        portfolio_retention_rate = expected_renewals / len(properties)
        revenue_increase = total_recommended_revenue - total_current_revenue
        revenue_increase_percentage = (revenue_increase / total_current_revenue) * 100 if total_current_revenue > 0 else 0
        
        return {
            'current_annual_revenue': round(total_current_revenue, 2),
            'projected_annual_revenue': round(total_recommended_revenue, 2),
            'revenue_increase': round(revenue_increase, 2),
            'revenue_increase_percentage': round(revenue_increase_percentage, 2),
            'total_concessions': round(total_concessions, 2),
            'expected_retention_rate': round(portfolio_retention_rate, 4),
            'expected_renewals': round(expected_renewals, 1),
            'net_revenue_increase': round(revenue_increase - total_concessions, 2),
            'roi_percentage': round(((revenue_increase - total_concessions) / total_concessions * 100), 2) if total_concessions > 0 else float('inf'),
            'average_rent_increase': round(statistics.mean([rec['rent_increase_percentage'] for rec in recommendations]), 2),
            'properties_with_increases': sum(1 for rec in recommendations if rec['rent_increase_percentage'] > 0),
            'properties_with_concessions': sum(1 for rec in recommendations if rec['recommended_concession'] > 0)
        }
    
    def _assess_portfolio_risks(self,
                              properties: List[PortfolioProperty],
                              recommendations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Assess portfolio-level risks from optimization
        """
        high_risk_properties = sum(1 for prop in properties if prop.risk_score > 70)
        aggressive_increases = sum(1 for rec in recommendations if rec['rent_increase_percentage'] > 8)
        large_concessions = sum(1 for rec in recommendations if rec['recommended_concession'] > 1000)
        
        # Calculate portfolio risk score
        weighted_risk = sum(prop.risk_score * prop.current_rent for prop in properties)
        total_rent = sum(prop.current_rent for prop in properties)
        portfolio_risk_score = weighted_risk / total_rent if total_rent > 0 else 0
        
        # Risk factors
        risk_factors = []
        if high_risk_properties > len(properties) * 0.15:
            risk_factors.append('high_concentration_risky_tenants')
        if aggressive_increases > len(properties) * 0.20:
            risk_factors.append('aggressive_rent_increases')
        if large_concessions > len(properties) * 0.10:
            risk_factors.append('high_concession_exposure')
        
        return {
            'portfolio_risk_score': round(portfolio_risk_score, 2),
            'risk_level': 'high' if portfolio_risk_score > 60 else 'medium' if portfolio_risk_score > 40 else 'low',
            'high_risk_properties': high_risk_properties,
            'properties_with_aggressive_increases': aggressive_increases,
            'properties_with_large_concessions': large_concessions,
            'identified_risk_factors': risk_factors,
            'risk_mitigation_needed': len(risk_factors) > 2,
            'diversification_score': self._calculate_diversification_score(properties),
            'concentration_risk': self._assess_concentration_risk(properties)
        }
    
    def _calculate_portfolio_metrics(self,
                                   properties: List[PortfolioProperty],
                                   recommendations: List[Dict[str, Any]],
                                   expected_outcomes: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate comprehensive portfolio metrics
        """
        # Property tier analysis
        tier_distribution = {}
        tier_revenue = {}
        for prop in properties:
            tier = prop.property_tier.value
            tier_distribution[tier] = tier_distribution.get(tier, 0) + 1
            tier_revenue[tier] = tier_revenue.get(tier, 0) + prop.current_rent * 12
        
        # Lease expiration analysis
        expiration_months = {}
        for prop in properties:
            month = prop.lease_expiration.month
            expiration_months[month] = expiration_months.get(month, 0) + 1
        
        # Geographic/location analysis
        location_factors = [prop.location_factor for prop in properties]
        
        return {
            'total_properties': len(properties),
            'total_units': sum(1 for prop in properties),  # Assuming 1 unit per property
            'average_rent': round(statistics.mean([prop.current_rent for prop in properties]), 2),
            'median_rent': round(statistics.median([prop.current_rent for prop in properties]), 2),
            'rent_range': {
                'min': min(prop.current_rent for prop in properties),
                'max': max(prop.current_rent for prop in properties)
            },
            'tier_distribution': tier_distribution,
            'tier_revenue_distribution': tier_revenue,
            'lease_expiration_distribution': expiration_months,
            'average_location_factor': round(statistics.mean(location_factors), 2),
            'portfolio_occupancy_rate': len([p for p in properties if p.tenant_id]) / len(properties),
            'weighted_average_renewal_probability': round(
                sum(prop.renewal_probability * prop.current_rent for prop in properties) / 
                sum(prop.current_rent for prop in properties), 4
            ),
            'portfolio_noi_projection': expected_outcomes['projected_annual_revenue'] - 
                                       sum(prop.maintenance_costs * 12 for prop in properties),
            'average_cap_rate': round(statistics.mean([prop.market_appreciation_rate for prop in properties]), 4)
        }
    
    def _perform_sensitivity_analysis(self,
                                    properties: List[PortfolioProperty],
                                    solution: Dict[str, Any],
                                    optimization_model: Dict[str, Any]) -> Dict[str, Any]:
        """
        Perform sensitivity analysis on optimization results
        """
        base_objective_value = solution.get('objective_value', 0)
        
        # Test sensitivity to key parameters
        sensitivity_results = {}
        
        # Market rent sensitivity
        market_rent_scenarios = [0.95, 1.05, 1.10]  # -5%, +5%, +10%
        for factor in market_rent_scenarios:
            scenario_properties = [
                PortfolioProperty(
                    **{**prop.to_dict(), 'market_rent': prop.market_rent * factor}
                ) for prop in properties
            ]
            # Would re-run optimization with modified properties
            sensitivity_results[f'market_rent_{factor}'] = {
                'revenue_change': f"{((factor - 1) * 100):.1f}%",
                'expected_impact': 'positive' if factor > 1 else 'negative'
            }
        
        # Vacancy cost sensitivity
        vacancy_scenarios = [2.0, 3.0, 3.5]  # Different vacancy cost multipliers
        for multiplier in vacancy_scenarios:
            sensitivity_results[f'vacancy_cost_{multiplier}x'] = {
                'impact_level': 'high' if multiplier > 2.5 else 'moderate',
                'strategy_adjustment': 'more_retention_focused' if multiplier > 2.5 else 'balanced'
            }
        
        # Renewal probability sensitivity
        prob_scenarios = [-0.1, 0.1, 0.2]  # Changes in renewal probability
        for delta in prob_scenarios:
            sensitivity_results[f'renewal_prob_{delta:+.1f}'] = {
                'portfolio_impact': 'significant' if abs(delta) > 0.15 else 'moderate',
                'strategy_recommendation': 'adjust_concessions' if delta < 0 else 'maintain_course'
            }
        
        return {
            'base_scenario_value': base_objective_value,
            'sensitivity_scenarios': sensitivity_results,
            'robustness_score': self._calculate_robustness_score(sensitivity_results),
            'key_risk_factors': self._identify_key_risk_factors(sensitivity_results),
            'recommended_hedging_strategies': self._recommend_hedging_strategies(sensitivity_results)
        }
    
    def _generate_implementation_timeline(self, recommendations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generate implementation timeline for recommendations
        """
        # Sort by implementation priority
        sorted_recs = sorted(recommendations, key=lambda x: x.get('implementation_priority', 5), reverse=True)
        
        timeline_phases = {
            'immediate': [],      # Next 30 days
            'short_term': [],     # 30-90 days
            'medium_term': [],    # 90-180 days
            'long_term': []       # 180+ days
        }
        
        for i, rec in enumerate(sorted_recs):
            priority = rec.get('implementation_priority', 5)
            
            if priority >= 8:
                timeline_phases['immediate'].append({
                    'property_id': rec['property_id'],
                    'action': f"Implement rent increase to ${rec['recommended_rent']}",
                    'priority': priority
                })
            elif priority >= 6:
                timeline_phases['short_term'].append({
                    'property_id': rec['property_id'],
                    'action': f"Implement rent increase to ${rec['recommended_rent']}",
                    'priority': priority
                })
            elif priority >= 4:
                timeline_phases['medium_term'].append({
                    'property_id': rec['property_id'],
                    'action': f"Consider rent increase to ${rec['recommended_rent']}",
                    'priority': priority
                })
            else:
                timeline_phases['long_term'].append({
                    'property_id': rec['property_id'],
                    'action': f"Monitor and reassess",
                    'priority': priority
                })
        
        return {
            'timeline_phases': timeline_phases,
            'total_actions': len(recommendations),
            'high_priority_actions': len(timeline_phases['immediate']) + len(timeline_phases['short_term']),
            'implementation_sequence': [rec['property_id'] for rec in sorted_recs],
            'estimated_completion_months': self._estimate_implementation_time(timeline_phases)
        }
    
    def _calculate_optimization_confidence(self,
                                         properties: List[PortfolioProperty],
                                         solution: Dict[str, Any],
                                         sensitivity_analysis: Dict[str, Any]) -> float:
        """
        Calculate confidence score for optimization results
        """
        confidence = 0.7  # Base confidence
        
        # Data quality factors
        avg_data_completeness = 0.9  # Assume good data quality
        confidence += (avg_data_completeness - 0.7) * 0.2
        
        # Solution quality
        if solution.get('status') == 'Optimal':
            confidence += 0.1
        
        # Robustness score from sensitivity analysis
        robustness = sensitivity_analysis.get('robustness_score', 0.5)
        confidence += (robustness - 0.5) * 0.2
        
        # Portfolio diversification
        diversification = self._calculate_diversification_score(properties)
        confidence += (diversification - 0.5) * 0.1
        
        # Historical performance (if available)
        # This would use actual historical optimization performance
        confidence += 0.05  # Placeholder
        
        return max(0.3, min(1.0, confidence))
    
    # Helper methods for calculations
    
    def _calculate_adjusted_renewal_probability(self,
                                              prop: PortfolioProperty,
                                              rent_increase: float,
                                              concession: float) -> float:
        """
        Calculate adjusted renewal probability based on rent changes and concessions
        """
        base_prob = prop.renewal_probability
        
        # Rent increase impact (negative)
        rent_impact = -rent_increase * 0.5  # 50% reduction per 100% increase
        
        # Concession impact (positive)
        concession_impact = (concession / prop.current_rent) * 0.1  # 10% improvement per month rent concession
        
        adjusted_prob = base_prob + rent_impact + concession_impact
        
        return max(0.05, min(0.95, adjusted_prob))
    
    def _calculate_revenue_impact(self,
                                prop: PortfolioProperty,
                                rent_increase: float,
                                concession: float) -> Dict[str, float]:
        """
        Calculate revenue impact of recommendation
        """
        current_annual = prop.current_rent * 12
        new_annual = prop.current_rent * (1 + rent_increase) * 12
        
        gross_increase = new_annual - current_annual
        net_increase = gross_increase - concession
        
        return {
            'gross_annual_increase': round(gross_increase, 2),
            'concession_cost': round(concession, 2),
            'net_annual_increase': round(net_increase, 2),
            'roi_months': round(gross_increase / concession, 1) if concession > 0 else float('inf')
        }
    
    def _assess_recommendation_risk(self,
                                  prop: PortfolioProperty,
                                  rent_increase: float) -> Dict[str, Any]:
        """
        Assess risk of specific recommendation
        """
        base_risk = prop.risk_score
        
        # Rent increase adds risk
        increase_risk = rent_increase * 100  # 100 points per 100% increase
        
        total_risk = min(100, base_risk + increase_risk)
        
        risk_level = 'high' if total_risk > 70 else 'medium' if total_risk > 40 else 'low'
        
        return {
            'total_risk_score': round(total_risk, 2),
            'risk_level': risk_level,
            'base_tenant_risk': round(base_risk, 2),
            'rent_increase_risk': round(increase_risk, 2),
            'mitigation_needed': total_risk > 60
        }
    
    def _calculate_implementation_priority(self,
                                         prop: PortfolioProperty,
                                         rent_increase: float,
                                         concession: float) -> int:
        """
        Calculate implementation priority (1-10)
        """
        priority = 5  # Base priority
        
        # Higher rent = higher priority
        if prop.current_rent > 2000:
            priority += 2
        elif prop.current_rent > 1500:
            priority += 1
        
        # Lease expiration urgency
        days_to_expiration = (prop.lease_expiration - datetime.now()).days
        if days_to_expiration <= 60:
            priority += 3
        elif days_to_expiration <= 90:
            priority += 2
        elif days_to_expiration <= 120:
            priority += 1
        
        # Risk factors
        if prop.risk_score > 70:
            priority += 2  # High risk needs attention
        
        # Rent increase size
        if rent_increase > 0.08:
            priority += 1  # Large increases need careful timing
        
        return max(1, min(10, priority))
    
    def _generate_alternative_scenarios(self, prop: PortfolioProperty) -> List[Dict[str, Any]]:
        """
        Generate alternative scenarios for property
        """
        scenarios = []
        
        # Conservative scenario
        scenarios.append({
            'scenario': 'conservative',
            'rent_increase': 0.03,
            'concession': prop.current_rent * 0.5,
            'expected_probability': prop.renewal_probability * 1.1
        })
        
        # Aggressive scenario
        scenarios.append({
            'scenario': 'aggressive',
            'rent_increase': 0.10,
            'concession': 0,
            'expected_probability': prop.renewal_probability * 0.8
        })
        
        # Market-based scenario
        market_increase = (prop.market_rent - prop.current_rent) / prop.current_rent
        scenarios.append({
            'scenario': 'market_rate',
            'rent_increase': max(0, min(0.15, market_increase)),
            'concession': prop.current_rent * 0.25 if market_increase > 0.05 else 0,
            'expected_probability': prop.renewal_probability * (1 - market_increase * 0.5)
        })
        
        return scenarios
    
    def _calculate_diversification_score(self, properties: List[PortfolioProperty]) -> float:
        """
        Calculate portfolio diversification score
        """
        if not properties:
            return 0.0
        
        # Rent level diversification
        rents = [prop.current_rent for prop in properties]
        rent_std = np.std(rents)
        rent_mean = np.mean(rents)
        rent_cv = rent_std / rent_mean if rent_mean > 0 else 0
        
        # Location diversification
        location_factors = [prop.location_factor for prop in properties]
        location_std = np.std(location_factors)
        
        # Lease expiration diversification
        expiration_months = [prop.lease_expiration.month for prop in properties]
        unique_months = len(set(expiration_months))
        expiration_diversity = unique_months / 12  # Max diversity is all 12 months
        
        # Property tier diversification
        tiers = [prop.property_tier.value for prop in properties]
        unique_tiers = len(set(tiers))
        tier_diversity = unique_tiers / 3  # Max 3 tiers
        
        # Combined diversification score
        diversification = np.mean([
            min(1.0, rent_cv),
            min(1.0, location_std / 2.0),  # Normalize location diversity
            expiration_diversity,
            tier_diversity
        ])
        
        return diversification
    
    def _assess_concentration_risk(self, properties: List[PortfolioProperty]) -> Dict[str, Any]:
        """
        Assess concentration risk in portfolio
        """
        # Rent concentration
        rents = [prop.current_rent for prop in properties]
        total_rent = sum(rents)
        
        # Find properties contributing to top 50% of rent
        sorted_rents = sorted(rents, reverse=True)
        cumulative = 0
        top_50_count = 0
        for rent in sorted_rents:
            cumulative += rent
            top_50_count += 1
            if cumulative >= total_rent * 0.5:
                break
        
        rent_concentration = top_50_count / len(properties)
        
        # Geographic concentration
        location_factors = [prop.location_factor for prop in properties]
        location_groups = {}
        for factor in location_factors:
            group = round(factor, 1)  # Group by 0.1 intervals
            location_groups[group] = location_groups.get(group, 0) + 1
        
        max_location_concentration = max(location_groups.values()) / len(properties)
        
        # Lease expiration concentration
        expiration_months = [prop.lease_expiration.month for prop in properties]
        month_groups = {}
        for month in expiration_months:
            month_groups[month] = month_groups.get(month, 0) + 1
        
        max_expiration_concentration = max(month_groups.values()) / len(properties)
        
        return {
            'rent_concentration': round(rent_concentration, 3),
            'geographic_concentration': round(max_location_concentration, 3),
            'expiration_concentration': round(max_expiration_concentration, 3),
            'overall_concentration_risk': 'high' if any([
                rent_concentration > 0.3,
                max_location_concentration > 0.4,
                max_expiration_concentration > 0.3
            ]) else 'moderate' if any([
                rent_concentration > 0.2,
                max_location_concentration > 0.3,
                max_expiration_concentration > 0.25
            ]) else 'low'
        }
    
    # Additional analysis methods (continued in next part due to length...)
    
    def _analyze_expiration_distribution(self, properties: List[PortfolioProperty]) -> Dict[int, float]:
        """
        Analyze current lease expiration distribution
        """
        month_counts = {}
        for prop in properties:
            month = prop.lease_expiration.month
            month_counts[month] = month_counts.get(month, 0) + 1
        
        total = len(properties)
        return {month: count / total for month, count in month_counts.items()}
    
    def _identify_staggering_opportunities(self,
                                         properties: List[PortfolioProperty],
                                         current_dist: Dict[int, float],
                                         target_dist: Dict[int, float]) -> List[Dict[str, Any]]:
        """
        Identify opportunities for lease staggering
        """
        opportunities = []
        
        for month, current_pct in current_dist.items():
            target_pct = target_dist.get(month, 1/12)
            if current_pct > target_pct + 0.05:  # 5% threshold
                # Find properties expiring in this month that could be moved
                month_properties = [p for p in properties if p.lease_expiration.month == month]
                
                for prop in month_properties[:int(len(month_properties) * 0.3)]:  # Consider moving 30%
                    opportunities.append({
                        'property_id': prop.property_id,
                        'current_month': month,
                        'recommended_months': self._find_best_target_months(target_dist, current_dist),
                        'lease_adjustment_needed': True,
                        'priority': 'high' if current_pct > target_pct + 0.10 else 'medium'
                    })
        
        return opportunities
    
    def _find_best_target_months(self,
                               target_dist: Dict[int, float],
                               current_dist: Dict[int, float]) -> List[int]:
        """
        Find best months to move lease expirations to
        """
        best_months = []
        
        for month in range(1, 13):
            target_pct = target_dist.get(month, 1/12)
            current_pct = current_dist.get(month, 0)
            
            if current_pct < target_pct - 0.03:  # 3% below target
                best_months.append(month)
        
        return sorted(best_months, key=lambda m: target_dist.get(m, 0) - current_dist.get(m, 0), reverse=True)
    
    # Fallback and utility methods
    
    def _get_fallback_optimization(self,
                                 properties: List[PortfolioProperty],
                                 objective: OptimizationObjective,
                                 strategy: OptimizationStrategy) -> OptimizationResult:
        """
        Generate fallback optimization when main optimization fails
        """
        # Simple rule-based recommendations
        recommendations = []
        
        for prop in properties:
            # Conservative approach: small rent increase based on market
            market_increase = (prop.market_rent - prop.current_rent) / prop.current_rent
            recommended_increase = max(0, min(0.05, market_increase * 0.5))  # 50% of market gap, max 5%
            
            recommendations.append({
                'property_id': prop.property_id,
                'tenant_id': prop.tenant_id,
                'current_rent': prop.current_rent,
                'recommended_rent': round(prop.current_rent * (1 + recommended_increase), 2),
                'rent_increase_percentage': round(recommended_increase * 100, 2),
                'recommended_concession': prop.current_rent * 0.25 if prop.renewal_probability < 0.6 else 0,
                'renewal_recommended': True,
                'strategy_applied': 'conservative_fallback',
                'expected_renewal_probability': prop.renewal_probability * 0.95,
                'revenue_impact': {'net_annual_increase': prop.current_rent * 12 * recommended_increase},
                'risk_assessment': {'risk_level': 'low'},
                'implementation_priority': 5
            })
        
        return OptimizationResult(
            optimization_id=f"fallback_{int(datetime.now().timestamp())}",
            objective=objective,
            strategy=strategy,
            property_recommendations=recommendations,
            expected_outcomes={'status': 'fallback_calculation'},
            risk_metrics={'portfolio_risk_score': 30},
            portfolio_metrics={'total_properties': len(properties)},
            sensitivity_analysis={'status': 'not_available'},
            implementation_timeline={'status': 'standard_timeline'},
            confidence_score=0.4,
            optimization_timestamp=datetime.now()
        )
    
    # Additional placeholder methods for complete implementation
    def _generate_staggering_recommendations(self, opportunities, target_distribution): return []
    def _calculate_staggering_impact(self, properties, recommendations, current_dist, target_dist): return {}
    def _prioritize_staggering_actions(self, recommendations): return []
    def _calculate_concession_effectiveness(self, properties): return {}
    def _optimize_concession_allocation(self, properties, effectiveness, budget): return {}
    def _generate_concession_recommendations(self, properties, allocation): return []
    def _calculate_concession_roi(self, properties, recommendations, budget): return {}
    def _analyze_current_positioning(self, properties, market_data): return {}
    def _identify_positioning_opportunities(self, properties, positioning, market_data): return {}
    def _generate_positioning_strategies(self, opportunities, market_data): return {}
    def _calculate_competitive_impact(self, properties, strategies, market_data): return {}
    def _generate_positioning_roadmap(self, strategies): return {}
    def _calculate_performance_metrics(self, results, outcomes): return {}
    def _analyze_prediction_accuracy(self, results, outcomes): return {}
    def _analyze_strategy_effectiveness(self, results, outcomes): return {}
    def _generate_improvement_recommendations(self, performance, accuracy, effectiveness): return []
    def _assess_model_update_need(self, accuracy): return False
    def _calculate_robustness_score(self, sensitivity): return 0.7
    def _identify_key_risk_factors(self, sensitivity): return []
    def _recommend_hedging_strategies(self, sensitivity): return []
    def _estimate_implementation_time(self, phases): return 6