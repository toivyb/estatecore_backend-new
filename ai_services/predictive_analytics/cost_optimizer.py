#!/usr/bin/env python3
"""
Maintenance Cost Optimization System for EstateCore Phase 6
Advanced algorithms for optimizing maintenance costs and scheduling
"""

import os
import json
import logging
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from enum import Enum

# Import maintenance predictor components
from .maintenance_predictor import (
    MaintenancePrediction, MaintenanceType, MaintenancePriority,
    EquipmentData, MaintenanceRecord
)

class OptimizationStrategy(Enum):
    COST_MINIMIZATION = "cost_minimization"
    TIME_EFFICIENCY = "time_efficiency"
    RESOURCE_BALANCING = "resource_balancing"
    TENANT_IMPACT_MINIMIZATION = "tenant_impact_minimization"
    SEASONAL_OPTIMIZATION = "seasonal_optimization"

class ContractorType(Enum):
    IN_HOUSE = "in_house"
    PREFERRED_VENDOR = "preferred_vendor"
    MARKET_BID = "market_bid"
    EMERGENCY_SERVICE = "emergency_service"
    SPECIALTY_CONTRACTOR = "specialty_contractor"

@dataclass
class ContractorProfile:
    """Contractor information for optimization"""
    contractor_id: str
    name: str
    contractor_type: ContractorType
    specializations: List[MaintenanceType]
    hourly_rate: float
    availability_schedule: Dict[str, List[Tuple[str, str]]]  # day: [(start, end)]
    quality_rating: float  # 1-5 scale
    reliability_score: float  # 1-5 scale
    response_time_hours: int
    min_job_cost: float
    bulk_discount_threshold: float
    bulk_discount_rate: float
    travel_cost_per_mile: float
    emergency_surcharge: float
    seasonal_adjustments: Dict[str, float]  # season: multiplier

@dataclass
class OptimizationConstraint:
    """Constraints for maintenance scheduling optimization"""
    max_daily_cost: Optional[float] = None
    max_weekly_cost: Optional[float] = None
    max_monthly_cost: Optional[float] = None
    excluded_dates: List[datetime] = None
    preferred_time_slots: Dict[str, List[Tuple[str, str]]] = None
    max_tenant_disruption_hours: int = 8
    required_advance_notice_days: int = 7
    max_concurrent_jobs: int = 3
    preferred_contractors: List[str] = None
    avoid_contractors: List[str] = None

@dataclass
class CostOptimizationResult:
    """Result of cost optimization analysis"""
    property_id: int
    optimization_strategy: OptimizationStrategy
    original_total_cost: float
    optimized_total_cost: float
    cost_savings: float
    savings_percentage: float
    
    # Scheduling details
    optimized_schedule: List[Dict[str, Any]]
    contractor_assignments: Dict[str, List[str]]  # contractor_id: [maintenance_ids]
    
    # Impact analysis
    tenant_disruption_hours: int
    total_project_duration_days: int
    risk_mitigation_actions: List[str]
    
    # Resource utilization
    contractor_utilization: Dict[str, float]
    equipment_sharing_opportunities: List[Dict[str, Any]]
    bulk_purchase_savings: float
    
    # Recommendations
    recommendations: List[str]
    alternative_strategies: List[Dict[str, Any]]
    
    optimization_timestamp: datetime

class MaintenanceCostOptimizer:
    """Advanced cost optimization system for maintenance scheduling"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Contractor database
        self.contractors = {}
        
        # Historical cost data
        self.cost_history = []
        
        # Optimization parameters
        self.optimization_config = self._load_optimization_config()
        
        self.logger.info("MaintenanceCostOptimizer initialized")

    def _load_optimization_config(self) -> Dict:
        """Load optimization configuration"""
        return {
            'bulk_discount_thresholds': {
                'hvac': 3,
                'plumbing': 5,
                'electrical': 4,
                'general': 2
            },
            'seasonal_factors': {
                'spring': {'hvac': 0.9, 'landscaping': 1.2, 'roofing': 1.1},
                'summer': {'hvac': 1.3, 'landscaping': 1.0, 'roofing': 1.2},
                'fall': {'hvac': 0.95, 'landscaping': 1.1, 'roofing': 0.9},
                'winter': {'hvac': 1.1, 'landscaping': 0.7, 'roofing': 0.8}
            },
            'priority_cost_multipliers': {
                MaintenancePriority.LOW: 0.8,
                MaintenancePriority.MEDIUM: 1.0,
                MaintenancePriority.HIGH: 1.2,
                MaintenancePriority.CRITICAL: 1.5,
                MaintenancePriority.EMERGENCY: 2.0
            },
            'contractor_efficiency_bonuses': {
                ContractorType.IN_HOUSE: 0.85,
                ContractorType.PREFERRED_VENDOR: 0.9,
                ContractorType.MARKET_BID: 1.0,
                ContractorType.EMERGENCY_SERVICE: 1.8,
                ContractorType.SPECIALTY_CONTRACTOR: 1.2
            },
            'time_slot_preferences': {
                'business_hours': {'start': '09:00', 'end': '17:00', 'multiplier': 1.0},
                'after_hours': {'start': '17:00', 'end': '22:00', 'multiplier': 1.25},
                'weekend': {'multiplier': 1.4},
                'holiday': {'multiplier': 1.8}
            }
        }

    def add_contractor(self, contractor: ContractorProfile) -> bool:
        """Add contractor to optimization database"""
        try:
            self.contractors[contractor.contractor_id] = contractor
            self.logger.info(f"Added contractor: {contractor.name}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to add contractor: {str(e)}")
            return False

    def optimize_maintenance_costs(self, predictions: List[MaintenancePrediction],
                                 property_id: int,
                                 strategy: OptimizationStrategy = OptimizationStrategy.COST_MINIMIZATION,
                                 constraints: OptimizationConstraint = None) -> CostOptimizationResult:
        """Optimize maintenance costs using specified strategy"""
        try:
            self.logger.info(f"Optimizing costs for property {property_id} using {strategy.value}")
            
            if not predictions:
                return self._create_empty_result(property_id, strategy)
            
            constraints = constraints or OptimizationConstraint()
            
            # Calculate original costs
            original_cost = sum((p.estimated_cost[0] + p.estimated_cost[1]) / 2 for p in predictions)
            
            # Apply optimization strategy
            if strategy == OptimizationStrategy.COST_MINIMIZATION:
                result = self._optimize_for_cost_minimization(predictions, property_id, constraints)
            elif strategy == OptimizationStrategy.TIME_EFFICIENCY:
                result = self._optimize_for_time_efficiency(predictions, property_id, constraints)
            elif strategy == OptimizationStrategy.RESOURCE_BALANCING:
                result = self._optimize_for_resource_balancing(predictions, property_id, constraints)
            elif strategy == OptimizationStrategy.TENANT_IMPACT_MINIMIZATION:
                result = self._optimize_for_tenant_impact(predictions, property_id, constraints)
            else:
                result = self._optimize_for_seasonal_factors(predictions, property_id, constraints)
            
            # Calculate savings
            optimized_cost = result.optimized_total_cost
            savings = original_cost - optimized_cost
            savings_percentage = (savings / original_cost * 100) if original_cost > 0 else 0
            
            result.original_total_cost = original_cost
            result.cost_savings = savings
            result.savings_percentage = savings_percentage
            result.optimization_strategy = strategy
            
            self.logger.info(f"Optimization completed: ${savings:.2f} savings ({savings_percentage:.1f}%)")
            return result
            
        except Exception as e:
            self.logger.error(f"Cost optimization failed: {str(e)}")
            return self._create_empty_result(property_id, strategy)

    def _optimize_for_cost_minimization(self, predictions: List[MaintenancePrediction],
                                      property_id: int, constraints: OptimizationConstraint) -> CostOptimizationResult:
        """Optimize purely for lowest cost"""
        try:
            optimized_schedule = []
            contractor_assignments = {}
            total_cost = 0
            
            # Group maintenance tasks by type for bulk discounts
            grouped_tasks = self._group_tasks_for_bulk_pricing(predictions)
            
            for group in grouped_tasks:
                # Find most cost-effective contractor for this group
                best_contractor = self._find_best_cost_contractor(group, constraints)
                
                if best_contractor:
                    group_cost = self._calculate_group_cost(group, best_contractor, apply_bulk_discount=True)
                    total_cost += group_cost
                    
                    # Schedule optimization within group
                    optimal_dates = self._optimize_dates_for_cost(group, best_contractor)
                    
                    for i, prediction in enumerate(group):
                        schedule_item = {
                            'maintenance_id': f"{prediction.property_id}_{prediction.maintenance_type.value}_{i}",
                            'maintenance_type': prediction.maintenance_type.value,
                            'scheduled_date': optimal_dates[i].isoformat(),
                            'contractor_id': best_contractor.contractor_id,
                            'estimated_cost': group_cost / len(group),
                            'estimated_duration': prediction.estimated_duration,
                            'cost_optimization_applied': ['bulk_discount', 'contractor_selection', 'date_optimization']
                        }
                        optimized_schedule.append(schedule_item)
                    
                    # Track contractor assignments
                    if best_contractor.contractor_id not in contractor_assignments:
                        contractor_assignments[best_contractor.contractor_id] = []
                    contractor_assignments[best_contractor.contractor_id].extend(
                        [item['maintenance_id'] for item in optimized_schedule[-len(group):]]
                    )
            
            # Calculate additional optimization metrics
            tenant_disruption = self._calculate_tenant_disruption(optimized_schedule)
            project_duration = self._calculate_project_duration(optimized_schedule)
            contractor_utilization = self._calculate_contractor_utilization(contractor_assignments)
            bulk_savings = self._calculate_bulk_savings(grouped_tasks)
            
            return CostOptimizationResult(
                property_id=property_id,
                optimization_strategy=OptimizationStrategy.COST_MINIMIZATION,
                original_total_cost=0,  # Will be set by caller
                optimized_total_cost=total_cost,
                cost_savings=0,  # Will be calculated by caller
                savings_percentage=0,  # Will be calculated by caller
                optimized_schedule=optimized_schedule,
                contractor_assignments=contractor_assignments,
                tenant_disruption_hours=tenant_disruption,
                total_project_duration_days=project_duration,
                risk_mitigation_actions=self._generate_risk_mitigation_actions(optimized_schedule),
                contractor_utilization=contractor_utilization,
                equipment_sharing_opportunities=self._identify_equipment_sharing(optimized_schedule),
                bulk_purchase_savings=bulk_savings,
                recommendations=self._generate_cost_recommendations(optimized_schedule),
                alternative_strategies=self._suggest_alternative_strategies(predictions),
                optimization_timestamp=datetime.now()
            )
            
        except Exception as e:
            self.logger.error(f"Cost minimization optimization failed: {str(e)}")
            return self._create_empty_result(property_id, OptimizationStrategy.COST_MINIMIZATION)

    def _optimize_for_time_efficiency(self, predictions: List[MaintenancePrediction],
                                    property_id: int, constraints: OptimizationConstraint) -> CostOptimizationResult:
        """Optimize for fastest completion time"""
        try:
            # Sort by urgency and try to parallelize compatible tasks
            sorted_predictions = sorted(predictions, key=lambda x: (
                x.recommended_priority.value,
                x.predicted_date
            ))
            
            # Find tasks that can be done simultaneously
            parallel_groups = self._identify_parallel_tasks(sorted_predictions)
            
            optimized_schedule = []
            contractor_assignments = {}
            total_cost = 0
            
            current_date = datetime.now()
            
            for group in parallel_groups:
                # Assign multiple contractors if needed for parallel execution
                contractors_needed = self._assign_parallel_contractors(group, constraints)
                
                for prediction, contractor in zip(group, contractors_needed):
                    cost = self._calculate_single_task_cost(prediction, contractor, current_date)
                    total_cost += cost
                    
                    schedule_item = {
                        'maintenance_id': f"{prediction.property_id}_{prediction.maintenance_type.value}",
                        'maintenance_type': prediction.maintenance_type.value,
                        'scheduled_date': current_date.isoformat(),
                        'contractor_id': contractor.contractor_id,
                        'estimated_cost': cost,
                        'estimated_duration': prediction.estimated_duration,
                        'optimization_applied': ['parallel_scheduling', 'multi_contractor']
                    }
                    optimized_schedule.append(schedule_item)
                    
                    if contractor.contractor_id not in contractor_assignments:
                        contractor_assignments[contractor.contractor_id] = []
                    contractor_assignments[contractor.contractor_id].append(schedule_item['maintenance_id'])
                
                # Advance date for next group
                max_duration = max(p.estimated_duration for p in group)
                current_date += timedelta(hours=max_duration)
            
            return CostOptimizationResult(
                property_id=property_id,
                optimization_strategy=OptimizationStrategy.TIME_EFFICIENCY,
                original_total_cost=0,
                optimized_total_cost=total_cost,
                cost_savings=0,
                savings_percentage=0,
                optimized_schedule=optimized_schedule,
                contractor_assignments=contractor_assignments,
                tenant_disruption_hours=self._calculate_tenant_disruption(optimized_schedule),
                total_project_duration_days=self._calculate_project_duration(optimized_schedule),
                risk_mitigation_actions=self._generate_risk_mitigation_actions(optimized_schedule),
                contractor_utilization=self._calculate_contractor_utilization(contractor_assignments),
                equipment_sharing_opportunities=self._identify_equipment_sharing(optimized_schedule),
                bulk_purchase_savings=0,  # Time optimization may not achieve bulk savings
                recommendations=self._generate_time_efficiency_recommendations(optimized_schedule),
                alternative_strategies=self._suggest_alternative_strategies(predictions),
                optimization_timestamp=datetime.now()
            )
            
        except Exception as e:
            self.logger.error(f"Time efficiency optimization failed: {str(e)}")
            return self._create_empty_result(property_id, OptimizationStrategy.TIME_EFFICIENCY)

    def get_cost_analysis_report(self, property_id: int, 
                               predictions: List[MaintenancePrediction]) -> Dict[str, Any]:
        """Generate comprehensive cost analysis report"""
        try:
            # Run multiple optimization strategies
            strategies = [
                OptimizationStrategy.COST_MINIMIZATION,
                OptimizationStrategy.TIME_EFFICIENCY,
                OptimizationStrategy.RESOURCE_BALANCING
            ]
            
            optimization_results = {}
            for strategy in strategies:
                result = self.optimize_maintenance_costs(predictions, property_id, strategy)
                optimization_results[strategy.value] = {
                    'total_cost': result.optimized_total_cost,
                    'savings': result.cost_savings,
                    'savings_percentage': result.savings_percentage,
                    'project_duration': result.total_project_duration_days,
                    'tenant_disruption': result.tenant_disruption_hours
                }
            
            # Cost breakdown analysis
            cost_breakdown = self._analyze_cost_breakdown(predictions)
            
            # Seasonal cost analysis
            seasonal_analysis = self._analyze_seasonal_costs(predictions)
            
            # Contractor comparison
            contractor_comparison = self._compare_contractor_options(predictions)
            
            report = {
                'property_id': property_id,
                'analysis_date': datetime.now().isoformat(),
                'total_predictions': len(predictions),
                
                'optimization_strategies': optimization_results,
                'cost_breakdown': cost_breakdown,
                'seasonal_analysis': seasonal_analysis,
                'contractor_comparison': contractor_comparison,
                
                'recommendations': {
                    'best_overall_strategy': self._recommend_best_strategy(optimization_results),
                    'cost_saving_opportunities': self._identify_cost_saving_opportunities(predictions),
                    'risk_factors': self._identify_cost_risk_factors(predictions),
                    'budget_planning_tips': self._generate_budget_planning_tips(predictions)
                },
                
                'executive_summary': {
                    'total_expected_costs': sum((p.estimated_cost[0] + p.estimated_cost[1]) / 2 for p in predictions),
                    'optimization_potential': max(r['savings'] for r in optimization_results.values()),
                    'critical_items_count': len([p for p in predictions if p.recommended_priority == MaintenancePriority.CRITICAL]),
                    'timeline_span_days': (max(p.predicted_date for p in predictions) - min(p.predicted_date for p in predictions)).days if predictions else 0
                }
            }
            
            return report
            
        except Exception as e:
            self.logger.error(f"Cost analysis report generation failed: {str(e)}")
            return {'error': str(e)}

    # Helper methods for optimization logic
    def _group_tasks_for_bulk_pricing(self, predictions: List[MaintenancePrediction]) -> List[List[MaintenancePrediction]]:
        """Group tasks to take advantage of bulk pricing"""
        groups = {}
        
        for prediction in predictions:
            maintenance_type = prediction.maintenance_type
            if maintenance_type not in groups:
                groups[maintenance_type] = []
            groups[maintenance_type].append(prediction)
        
        # Only create bulk groups if threshold is met
        bulk_groups = []
        for maintenance_type, group in groups.items():
            threshold = self.optimization_config['bulk_discount_thresholds'].get(
                maintenance_type.value, 2
            )
            
            if len(group) >= threshold:
                bulk_groups.append(group)
            else:
                # Add individual tasks
                for task in group:
                    bulk_groups.append([task])
        
        return bulk_groups

    def _find_best_cost_contractor(self, tasks: List[MaintenancePrediction], 
                                 constraints: OptimizationConstraint) -> Optional[ContractorProfile]:
        """Find the most cost-effective contractor for a group of tasks"""
        if not tasks:
            return None
            
        maintenance_type = tasks[0].maintenance_type
        suitable_contractors = [
            c for c in self.contractors.values()
            if maintenance_type in c.specializations
        ]
        
        if not suitable_contractors:
            return None
        
        # Calculate cost for each contractor
        best_contractor = None
        best_cost = float('inf')
        
        for contractor in suitable_contractors:
            if constraints.avoid_contractors and contractor.contractor_id in constraints.avoid_contractors:
                continue
            
            total_cost = self._calculate_group_cost(tasks, contractor)
            
            # Apply quality and reliability adjustments
            adjusted_cost = total_cost * (2.0 - contractor.quality_rating / 5.0)
            
            if adjusted_cost < best_cost:
                best_cost = adjusted_cost
                best_contractor = contractor
        
        return best_contractor

    def _calculate_group_cost(self, tasks: List[MaintenancePrediction], 
                            contractor: ContractorProfile, 
                            apply_bulk_discount: bool = False) -> float:
        """Calculate total cost for a group of tasks with one contractor"""
        total_cost = 0
        
        for task in tasks:
            base_cost = (task.estimated_cost[0] + task.estimated_cost[1]) / 2
            
            # Apply contractor efficiency
            contractor_multiplier = self.optimization_config['contractor_efficiency_bonuses'][contractor.contractor_type]
            task_cost = base_cost * contractor_multiplier
            
            # Apply seasonal adjustments
            season = self._get_season(task.predicted_date)
            seasonal_factor = contractor.seasonal_adjustments.get(season, 1.0)
            task_cost *= seasonal_factor
            
            total_cost += task_cost
        
        # Apply bulk discount if applicable
        if apply_bulk_discount and len(tasks) >= contractor.bulk_discount_threshold:
            total_cost *= (1.0 - contractor.bulk_discount_rate)
        
        return total_cost

    def _create_empty_result(self, property_id: int, strategy: OptimizationStrategy) -> CostOptimizationResult:
        """Create empty optimization result for error cases"""
        return CostOptimizationResult(
            property_id=property_id,
            optimization_strategy=strategy,
            original_total_cost=0,
            optimized_total_cost=0,
            cost_savings=0,
            savings_percentage=0,
            optimized_schedule=[],
            contractor_assignments={},
            tenant_disruption_hours=0,
            total_project_duration_days=0,
            risk_mitigation_actions=[],
            contractor_utilization={},
            equipment_sharing_opportunities=[],
            bulk_purchase_savings=0,
            recommendations=[],
            alternative_strategies=[],
            optimization_timestamp=datetime.now()
        )

    def _get_season(self, date: datetime) -> str:
        """Get season for date"""
        month = date.month
        if month in [12, 1, 2]:
            return 'winter'
        elif month in [3, 4, 5]:
            return 'spring'
        elif month in [6, 7, 8]:
            return 'summer'
        else:
            return 'fall'

# Global cost optimizer instance
_cost_optimizer = None

def get_cost_optimizer():
    """Get the global cost optimizer instance"""
    global _cost_optimizer
    if _cost_optimizer is None:
        _cost_optimizer = MaintenanceCostOptimizer()
    return _cost_optimizer