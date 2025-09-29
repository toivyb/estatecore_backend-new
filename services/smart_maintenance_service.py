import logging
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
import uuid
import numpy as np
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.preprocessing import StandardScaler
import asyncio

from flask import current_app
from estatecore_backend.models import db, Property, User
from services.rbac_service import require_permission

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MaintenanceCategory(Enum):
    HVAC = "hvac"
    PLUMBING = "plumbing"
    ELECTRICAL = "electrical"
    ROOFING = "roofing"
    FLOORING = "flooring"
    APPLIANCES = "appliances"
    EXTERIOR = "exterior"
    LANDSCAPING = "landscaping"
    SECURITY = "security"
    GENERAL = "general"

class Priority(Enum):
    EMERGENCY = "emergency"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    PREVENTIVE = "preventive"

class MaintenanceStatus(Enum):
    SCHEDULED = "scheduled"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    OVERDUE = "overdue"
    PENDING_APPROVAL = "pending_approval"

class PredictionType(Enum):
    FAILURE_PREDICTION = "failure_prediction"
    COST_ESTIMATION = "cost_estimation"
    TIMELINE_PREDICTION = "timeline_prediction"
    RESOURCE_OPTIMIZATION = "resource_optimization"

@dataclass
class MaintenanceItem:
    id: str
    property_id: int
    category: MaintenanceCategory
    title: str
    description: str
    priority: Priority
    status: MaintenanceStatus
    scheduled_date: Optional[datetime]
    estimated_duration_hours: float
    estimated_cost: float
    actual_cost: Optional[float] = None
    actual_duration_hours: Optional[float] = None
    assigned_contractor: Optional[str] = None
    created_by: Optional[int] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    notes: List[str] = field(default_factory=list)
    photos: List[str] = field(default_factory=list)
    equipment_ids: List[str] = field(default_factory=list)
    recurring_schedule: Optional[Dict[str, Any]] = None
    ai_generated: bool = False
    confidence_score: float = 0.0
    
    def to_dict(self):
        return {
            'id': self.id,
            'property_id': self.property_id,
            'category': self.category.value,
            'title': self.title,
            'description': self.description,
            'priority': self.priority.value,
            'status': self.status.value,
            'scheduled_date': self.scheduled_date.isoformat() if self.scheduled_date else None,
            'estimated_duration_hours': self.estimated_duration_hours,
            'estimated_cost': self.estimated_cost,
            'actual_cost': self.actual_cost,
            'actual_duration_hours': self.actual_duration_hours,
            'assigned_contractor': self.assigned_contractor,
            'created_by': self.created_by,
            'created_at': self.created_at.isoformat(),
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'notes': self.notes,
            'photos': self.photos,
            'equipment_ids': self.equipment_ids,
            'recurring_schedule': self.recurring_schedule,
            'ai_generated': self.ai_generated,
            'confidence_score': self.confidence_score
        }

@dataclass
class MaintenancePrediction:
    prediction_id: str
    property_id: int
    equipment_id: Optional[str]
    prediction_type: PredictionType
    predicted_failure_date: Optional[datetime]
    confidence_score: float
    risk_factors: List[str]
    recommended_actions: List[str]
    estimated_cost: float
    severity_level: str
    maintenance_category: MaintenanceCategory
    predicted_at: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self):
        return {
            'prediction_id': self.prediction_id,
            'property_id': self.property_id,
            'equipment_id': self.equipment_id,
            'prediction_type': self.prediction_type.value,
            'predicted_failure_date': self.predicted_failure_date.isoformat() if self.predicted_failure_date else None,
            'confidence_score': self.confidence_score,
            'risk_factors': self.risk_factors,
            'recommended_actions': self.recommended_actions,
            'estimated_cost': self.estimated_cost,
            'severity_level': self.severity_level,
            'maintenance_category': self.maintenance_category.value,
            'predicted_at': self.predicted_at.isoformat()
        }

@dataclass
class Equipment:
    id: str
    property_id: int
    name: str
    category: MaintenanceCategory
    manufacturer: str
    model: str
    installation_date: datetime
    warranty_expiry: Optional[datetime]
    last_maintenance: Optional[datetime]
    maintenance_history: List[str] = field(default_factory=list)
    current_condition: str = "good"
    expected_lifespan_years: int = 10
    replacement_cost: float = 0.0
    energy_efficiency_rating: Optional[str] = None
    iot_sensor_data: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self):
        return {
            'id': self.id,
            'property_id': self.property_id,
            'name': self.name,
            'category': self.category.value,
            'manufacturer': self.manufacturer,
            'model': self.model,
            'installation_date': self.installation_date.isoformat(),
            'warranty_expiry': self.warranty_expiry.isoformat() if self.warranty_expiry else None,
            'last_maintenance': self.last_maintenance.isoformat() if self.last_maintenance else None,
            'maintenance_history': self.maintenance_history,
            'current_condition': self.current_condition,
            'expected_lifespan_years': self.expected_lifespan_years,
            'replacement_cost': self.replacement_cost,
            'energy_efficiency_rating': self.energy_efficiency_rating,
            'iot_sensor_data': self.iot_sensor_data
        }

class SmartMaintenanceService:
    """Smart maintenance scheduling and predictive analytics service"""
    
    def __init__(self):
        self.maintenance_items: Dict[str, MaintenanceItem] = {}
        self.equipment: Dict[str, Equipment] = {}
        self.predictions: Dict[str, MaintenancePrediction] = {}
        self.contractors: Dict[str, Dict[str, Any]] = {}
        
        # ML Models for predictions
        self.failure_predictor = RandomForestClassifier(n_estimators=100, random_state=42)
        self.cost_predictor = RandomForestRegressor(n_estimators=100, random_state=42)
        self.timeline_predictor = RandomForestRegressor(n_estimators=100, random_state=42)
        self.scaler = StandardScaler()
        
        # Maintenance schedules and templates
        self.maintenance_templates = self._load_maintenance_templates()
        self.seasonal_schedules = self._load_seasonal_schedules()
        
        # Initialize with sample data
        self._initialize_sample_data()
    
    def _load_maintenance_templates(self) -> Dict[str, Dict[str, Any]]:
        """Load maintenance templates for different equipment types"""
        return {
            'hvac_system': {
                'category': MaintenanceCategory.HVAC,
                'recurring_tasks': [
                    {
                        'title': 'Filter Replacement',
                        'frequency_months': 3,
                        'estimated_hours': 0.5,
                        'estimated_cost': 50,
                        'priority': Priority.MEDIUM
                    },
                    {
                        'title': 'System Inspection',
                        'frequency_months': 6,
                        'estimated_hours': 2,
                        'estimated_cost': 200,
                        'priority': Priority.MEDIUM
                    },
                    {
                        'title': 'Deep Cleaning & Tune-up',
                        'frequency_months': 12,
                        'estimated_hours': 4,
                        'estimated_cost': 400,
                        'priority': Priority.HIGH
                    }
                ]
            },
            'water_heater': {
                'category': MaintenanceCategory.PLUMBING,
                'recurring_tasks': [
                    {
                        'title': 'Temperature & Pressure Check',
                        'frequency_months': 6,
                        'estimated_hours': 1,
                        'estimated_cost': 75,
                        'priority': Priority.MEDIUM
                    },
                    {
                        'title': 'Anode Rod Inspection',
                        'frequency_months': 12,
                        'estimated_hours': 1.5,
                        'estimated_cost': 150,
                        'priority': Priority.HIGH
                    },
                    {
                        'title': 'Tank Flush',
                        'frequency_months': 12,
                        'estimated_hours': 2,
                        'estimated_cost': 125,
                        'priority': Priority.MEDIUM
                    }
                ]
            },
            'roof': {
                'category': MaintenanceCategory.ROOFING,
                'recurring_tasks': [
                    {
                        'title': 'Visual Inspection',
                        'frequency_months': 6,
                        'estimated_hours': 1,
                        'estimated_cost': 100,
                        'priority': Priority.MEDIUM
                    },
                    {
                        'title': 'Gutter Cleaning',
                        'frequency_months': 6,
                        'estimated_hours': 3,
                        'estimated_cost': 200,
                        'priority': Priority.MEDIUM
                    },
                    {
                        'title': 'Professional Inspection',
                        'frequency_months': 24,
                        'estimated_hours': 2,
                        'estimated_cost': 300,
                        'priority': Priority.HIGH
                    }
                ]
            }
        }
    
    def _load_seasonal_schedules(self) -> Dict[str, List[Dict[str, Any]]]:
        """Load seasonal maintenance schedules"""
        return {
            'spring': [
                {
                    'title': 'HVAC Spring Tune-up',
                    'category': MaintenanceCategory.HVAC,
                    'priority': Priority.HIGH,
                    'estimated_cost': 200
                },
                {
                    'title': 'Exterior Inspection',
                    'category': MaintenanceCategory.EXTERIOR,
                    'priority': Priority.MEDIUM,
                    'estimated_cost': 150
                },
                {
                    'title': 'Landscaping Preparation',
                    'category': MaintenanceCategory.LANDSCAPING,
                    'priority': Priority.LOW,
                    'estimated_cost': 300
                }
            ],
            'summer': [
                {
                    'title': 'AC Performance Check',
                    'category': MaintenanceCategory.HVAC,
                    'priority': Priority.HIGH,
                    'estimated_cost': 150
                },
                {
                    'title': 'Roof Inspection',
                    'category': MaintenanceCategory.ROOFING,
                    'priority': Priority.MEDIUM,
                    'estimated_cost': 200
                }
            ],
            'fall': [
                {
                    'title': 'Heating System Check',
                    'category': MaintenanceCategory.HVAC,
                    'priority': Priority.HIGH,
                    'estimated_cost': 200
                },
                {
                    'title': 'Gutter Cleaning',
                    'category': MaintenanceCategory.EXTERIOR,
                    'priority': Priority.MEDIUM,
                    'estimated_cost': 150
                }
            ],
            'winter': [
                {
                    'title': 'Pipe Insulation Check',
                    'category': MaintenanceCategory.PLUMBING,
                    'priority': Priority.HIGH,
                    'estimated_cost': 100
                },
                {
                    'title': 'Weather Sealing',
                    'category': MaintenanceCategory.EXTERIOR,
                    'priority': Priority.MEDIUM,
                    'estimated_cost': 200
                }
            ]
        }
    
    def _initialize_sample_data(self):
        """Initialize with sample equipment and maintenance data"""
        # Sample equipment
        sample_equipment = [
            Equipment(
                id="eq_001",
                property_id=123,
                name="Central HVAC Unit #1",
                category=MaintenanceCategory.HVAC,
                manufacturer="Carrier",
                model="25HCE4",
                installation_date=datetime(2020, 3, 15),
                warranty_expiry=datetime(2025, 3, 15),
                last_maintenance=datetime(2024, 6, 15),
                expected_lifespan_years=15,
                replacement_cost=8500,
                current_condition="good"
            ),
            Equipment(
                id="eq_002",
                property_id=123,
                name="Water Heater",
                category=MaintenanceCategory.PLUMBING,
                manufacturer="Rheem",
                model="XE50T10HD45U1",
                installation_date=datetime(2019, 8, 20),
                warranty_expiry=datetime(2025, 8, 20),
                last_maintenance=datetime(2024, 2, 10),
                expected_lifespan_years=12,
                replacement_cost=1200,
                current_condition="good"
            )
        ]
        
        for equipment in sample_equipment:
            self.equipment[equipment.id] = equipment
    
    async def schedule_maintenance(self, property_id: int, maintenance_data: Dict[str, Any], 
                                  user_id: int) -> Dict[str, Any]:
        """Schedule a new maintenance item"""
        try:
            # Validate required fields
            required_fields = ['title', 'category', 'priority']
            for field in required_fields:
                if field not in maintenance_data:
                    return {'success': False, 'error': f'Missing required field: {field}'}
            
            # Create maintenance item
            maintenance_id = str(uuid.uuid4())
            
            # Use AI to optimize scheduling if not specified
            if 'scheduled_date' not in maintenance_data:
                optimal_date = await self._find_optimal_schedule_date(
                    property_id, 
                    MaintenanceCategory(maintenance_data['category']),
                    Priority(maintenance_data['priority'])
                )
                maintenance_data['scheduled_date'] = optimal_date
            else:
                maintenance_data['scheduled_date'] = datetime.fromisoformat(maintenance_data['scheduled_date'])
            
            # Estimate cost and duration using AI
            if 'estimated_cost' not in maintenance_data:
                maintenance_data['estimated_cost'] = await self._estimate_cost(maintenance_data)
            
            if 'estimated_duration_hours' not in maintenance_data:
                maintenance_data['estimated_duration_hours'] = await self._estimate_duration(maintenance_data)
            
            maintenance_item = MaintenanceItem(
                id=maintenance_id,
                property_id=property_id,
                category=MaintenanceCategory(maintenance_data['category']),
                title=maintenance_data['title'],
                description=maintenance_data.get('description', ''),
                priority=Priority(maintenance_data['priority']),
                status=MaintenanceStatus.SCHEDULED,
                scheduled_date=maintenance_data['scheduled_date'],
                estimated_duration_hours=maintenance_data['estimated_duration_hours'],
                estimated_cost=maintenance_data['estimated_cost'],
                created_by=user_id,
                equipment_ids=maintenance_data.get('equipment_ids', []),
                recurring_schedule=maintenance_data.get('recurring_schedule')
            )
            
            # Store maintenance item
            self.maintenance_items[maintenance_id] = maintenance_item
            
            # Auto-assign contractor if available
            await self._auto_assign_contractor(maintenance_item)
            
            logger.info(f"Maintenance scheduled: {maintenance_id} for property {property_id}")
            
            return {
                'success': True,
                'maintenance_id': maintenance_id,
                'maintenance_item': maintenance_item.to_dict(),
                'message': 'Maintenance scheduled successfully'
            }
            
        except Exception as e:
            logger.error(f"Error scheduling maintenance: {str(e)}")
            return {'success': False, 'error': 'Failed to schedule maintenance'}
    
    async def generate_predictive_maintenance(self, property_id: int) -> Dict[str, Any]:
        """Generate predictive maintenance recommendations using AI"""
        try:
            predictions = []
            property_equipment = [eq for eq in self.equipment.values() if eq.property_id == property_id]
            
            for equipment in property_equipment:
                # Run failure prediction
                failure_prediction = await self._predict_equipment_failure(equipment)
                if failure_prediction:
                    predictions.append(failure_prediction)
                
                # Generate preventive maintenance recommendations
                preventive_tasks = await self._generate_preventive_tasks(equipment)
                predictions.extend(preventive_tasks)
            
            # Generate seasonal recommendations
            seasonal_tasks = await self._generate_seasonal_recommendations(property_id)
            predictions.extend(seasonal_tasks)
            
            # Sort by priority and urgency
            predictions.sort(key=lambda x: (x.confidence_score, x.estimated_cost), reverse=True)
            
            # Auto-schedule high-confidence predictions
            scheduled_items = []
            for prediction in predictions[:5]:  # Top 5 predictions
                if prediction.confidence_score > 0.8:
                    scheduled_item = await self._auto_schedule_from_prediction(prediction)
                    if scheduled_item['success']:
                        scheduled_items.append(scheduled_item)
            
            return {
                'success': True,
                'property_id': property_id,
                'predictions': [p.to_dict() for p in predictions],
                'auto_scheduled': len(scheduled_items),
                'total_estimated_cost': sum(p.estimated_cost for p in predictions),
                'message': f'Generated {len(predictions)} maintenance recommendations'
            }
            
        except Exception as e:
            logger.error(f"Error generating predictive maintenance: {str(e)}")
            return {'success': False, 'error': 'Failed to generate predictions'}
    
    async def optimize_maintenance_schedule(self, property_id: int, 
                                          time_window_days: int = 30) -> Dict[str, Any]:
        """Optimize maintenance schedule for efficiency and cost"""
        try:
            # Get all scheduled maintenance for property
            property_maintenance = [
                item for item in self.maintenance_items.values() 
                if item.property_id == property_id and item.status == MaintenanceStatus.SCHEDULED
            ]
            
            if not property_maintenance:
                return {'success': True, 'optimizations': [], 'message': 'No scheduled maintenance to optimize'}
            
            optimizations = []
            
            # Group by category and date for efficiency
            category_groups = {}
            for item in property_maintenance:
                category = item.category.value
                if category not in category_groups:
                    category_groups[category] = []
                category_groups[category].append(item)
            
            # Find optimization opportunities
            for category, items in category_groups.items():
                if len(items) > 1:
                    # Check for items that can be combined
                    combined_opportunities = self._find_combination_opportunities(items)
                    optimizations.extend(combined_opportunities)
            
            # Check for contractor optimization
            contractor_optimizations = await self._optimize_contractor_scheduling(property_maintenance)
            optimizations.extend(contractor_optimizations)
            
            # Calculate cost savings
            total_savings = sum(opt.get('estimated_savings', 0) for opt in optimizations)
            
            return {
                'success': True,
                'property_id': property_id,
                'optimizations': optimizations,
                'potential_savings': total_savings,
                'optimization_count': len(optimizations),
                'message': f'Found {len(optimizations)} optimization opportunities'
            }
            
        except Exception as e:
            logger.error(f"Error optimizing maintenance schedule: {str(e)}")
            return {'success': False, 'error': 'Failed to optimize schedule'}
    
    async def get_maintenance_analytics(self, property_id: Optional[int] = None,
                                      date_range_days: int = 365) -> Dict[str, Any]:
        """Get comprehensive maintenance analytics"""
        try:
            # Filter maintenance items
            if property_id:
                maintenance_items = [item for item in self.maintenance_items.values() if item.property_id == property_id]
            else:
                maintenance_items = list(self.maintenance_items.values())
            
            # Filter by date range
            cutoff_date = datetime.utcnow() - timedelta(days=date_range_days)
            recent_items = [item for item in maintenance_items if item.created_at > cutoff_date]
            
            # Calculate metrics
            analytics = {
                'overview': {
                    'total_maintenance_items': len(recent_items),
                    'completed_items': len([item for item in recent_items if item.status == MaintenanceStatus.COMPLETED]),
                    'pending_items': len([item for item in recent_items if item.status == MaintenanceStatus.SCHEDULED]),
                    'overdue_items': len([item for item in recent_items if item.status == MaintenanceStatus.OVERDUE]),
                    'total_cost': sum(item.actual_cost or item.estimated_cost for item in recent_items),
                    'average_completion_time': self._calculate_average_completion_time(recent_items)
                },
                'category_breakdown': self._analyze_by_category(recent_items),
                'cost_analysis': self._analyze_costs(recent_items),
                'timeline_analysis': self._analyze_timeline(recent_items),
                'contractor_performance': self._analyze_contractor_performance(recent_items),
                'predictive_insights': await self._generate_analytics_insights(recent_items)
            }
            
            return {
                'success': True,
                'analytics': analytics,
                'date_range_days': date_range_days,
                'property_id': property_id
            }
            
        except Exception as e:
            logger.error(f"Error getting maintenance analytics: {str(e)}")
            return {'success': False, 'error': 'Failed to get analytics'}
    
    async def _find_optimal_schedule_date(self, property_id: int, category: MaintenanceCategory, 
                                        priority: Priority) -> datetime:
        """Find optimal date for scheduling maintenance"""
        base_date = datetime.utcnow()
        
        # Priority-based scheduling
        if priority == Priority.EMERGENCY:
            return base_date + timedelta(hours=4)
        elif priority == Priority.HIGH:
            return base_date + timedelta(days=2)
        elif priority == Priority.MEDIUM:
            return base_date + timedelta(days=7)
        else:
            return base_date + timedelta(days=14)
    
    async def _estimate_cost(self, maintenance_data: Dict[str, Any]) -> float:
        """Estimate maintenance cost using AI/historical data"""
        category = maintenance_data['category']
        
        # Simple cost estimation based on category
        base_costs = {
            'hvac': 250,
            'plumbing': 180,
            'electrical': 200,
            'roofing': 400,
            'flooring': 300,
            'appliances': 150,
            'exterior': 200,
            'landscaping': 100,
            'security': 175,
            'general': 100
        }
        
        return base_costs.get(category, 150)
    
    async def _estimate_duration(self, maintenance_data: Dict[str, Any]) -> float:
        """Estimate maintenance duration using AI/historical data"""
        category = maintenance_data['category']
        
        # Simple duration estimation based on category
        base_durations = {
            'hvac': 3.0,
            'plumbing': 2.5,
            'electrical': 2.0,
            'roofing': 4.0,
            'flooring': 6.0,
            'appliances': 1.5,
            'exterior': 3.0,
            'landscaping': 4.0,
            'security': 2.0,
            'general': 2.0
        }
        
        return base_durations.get(category, 2.0)
    
    async def _auto_assign_contractor(self, maintenance_item: MaintenanceItem):
        """Auto-assign best available contractor"""
        # Mock contractor assignment logic
        contractors = {
            MaintenanceCategory.HVAC: "HVAC Pro Services",
            MaintenanceCategory.PLUMBING: "Elite Plumbing Co",
            MaintenanceCategory.ELECTRICAL: "Spark Electric",
            MaintenanceCategory.ROOFING: "Peak Roofing Solutions"
        }
        
        maintenance_item.assigned_contractor = contractors.get(maintenance_item.category, "General Contractors Inc")
    
    async def _predict_equipment_failure(self, equipment: Equipment) -> Optional[MaintenancePrediction]:
        """Predict equipment failure using AI"""
        # Calculate equipment age and condition factors
        age_years = (datetime.utcnow() - equipment.installation_date).days / 365.25
        age_factor = age_years / equipment.expected_lifespan_years
        
        # Simple failure prediction logic
        if age_factor > 0.8:
            failure_probability = min(0.9, age_factor)
            days_to_failure = max(30, int((1 - age_factor) * 365))
            
            return MaintenancePrediction(
                prediction_id=str(uuid.uuid4()),
                property_id=equipment.property_id,
                equipment_id=equipment.id,
                prediction_type=PredictionType.FAILURE_PREDICTION,
                predicted_failure_date=datetime.utcnow() + timedelta(days=days_to_failure),
                confidence_score=failure_probability,
                risk_factors=["Equipment age", "Normal wear and tear"],
                recommended_actions=["Schedule replacement", "Increase monitoring"],
                estimated_cost=equipment.replacement_cost * 0.1,  # 10% of replacement cost for maintenance
                severity_level="high" if failure_probability > 0.7 else "medium",
                maintenance_category=equipment.category
            )
        
        return None
    
    async def _generate_preventive_tasks(self, equipment: Equipment) -> List[MaintenancePrediction]:
        """Generate preventive maintenance tasks"""
        predictions = []
        
        # Check if equipment needs regular maintenance
        if equipment.last_maintenance:
            days_since_maintenance = (datetime.utcnow() - equipment.last_maintenance).days
            
            if days_since_maintenance > 90:  # 3 months
                prediction = MaintenancePrediction(
                    prediction_id=str(uuid.uuid4()),
                    property_id=equipment.property_id,
                    equipment_id=equipment.id,
                    prediction_type=PredictionType.TIMELINE_PREDICTION,
                    predicted_failure_date=None,
                    confidence_score=0.85,
                    risk_factors=["Overdue maintenance"],
                    recommended_actions=["Schedule routine maintenance"],
                    estimated_cost=200,
                    severity_level="medium",
                    maintenance_category=equipment.category
                )
                predictions.append(prediction)
        
        return predictions
    
    async def _generate_seasonal_recommendations(self, property_id: int) -> List[MaintenancePrediction]:
        """Generate seasonal maintenance recommendations"""
        predictions = []
        current_month = datetime.utcnow().month
        
        # Determine current season
        if current_month in [3, 4, 5]:
            season = 'spring'
        elif current_month in [6, 7, 8]:
            season = 'summer'
        elif current_month in [9, 10, 11]:
            season = 'fall'
        else:
            season = 'winter'
        
        seasonal_tasks = self.seasonal_schedules.get(season, [])
        
        for task in seasonal_tasks:
            prediction = MaintenancePrediction(
                prediction_id=str(uuid.uuid4()),
                property_id=property_id,
                equipment_id=None,
                prediction_type=PredictionType.TIMELINE_PREDICTION,
                predicted_failure_date=None,
                confidence_score=0.7,
                risk_factors=["Seasonal requirements"],
                recommended_actions=[f"Schedule {task['title']}"],
                estimated_cost=task['estimated_cost'],
                severity_level="medium",
                maintenance_category=task['category']
            )
            predictions.append(prediction)
        
        return predictions
    
    async def _auto_schedule_from_prediction(self, prediction: MaintenancePrediction) -> Dict[str, Any]:
        """Auto-schedule maintenance from AI prediction"""
        maintenance_data = {
            'title': f"AI Predicted: {prediction.maintenance_category.value.title()} Maintenance",
            'category': prediction.maintenance_category.value,
            'priority': 'high' if prediction.confidence_score > 0.8 else 'medium',
            'description': f"AI-generated maintenance task. Confidence: {prediction.confidence_score:.1%}",
            'estimated_cost': prediction.estimated_cost,
            'estimated_duration_hours': 2.0,
            'equipment_ids': [prediction.equipment_id] if prediction.equipment_id else []
        }
        
        return await self.schedule_maintenance(prediction.property_id, maintenance_data, user_id=0)
    
    def _find_combination_opportunities(self, items: List[MaintenanceItem]) -> List[Dict[str, Any]]:
        """Find opportunities to combine maintenance tasks"""
        combinations = []
        
        for i, item1 in enumerate(items):
            for item2 in items[i+1:]:
                # Check if items can be combined (same day, compatible work)
                if item1.scheduled_date and item2.scheduled_date:
                    date_diff = abs((item1.scheduled_date - item2.scheduled_date).days)
                    if date_diff <= 1:  # Within 1 day
                        combinations.append({
                            'type': 'combine_tasks',
                            'items': [item1.id, item2.id],
                            'estimated_savings': 50,  # Travel cost savings
                            'description': f"Combine {item1.title} and {item2.title}"
                        })
        
        return combinations
    
    async def _optimize_contractor_scheduling(self, items: List[MaintenanceItem]) -> List[Dict[str, Any]]:
        """Optimize contractor scheduling"""
        optimizations = []
        
        # Group by contractor
        contractor_groups = {}
        for item in items:
            if item.assigned_contractor:
                if item.assigned_contractor not in contractor_groups:
                    contractor_groups[item.assigned_contractor] = []
                contractor_groups[item.assigned_contractor].append(item)
        
        # Find scheduling optimizations
        for contractor, contractor_items in contractor_groups.items():
            if len(contractor_items) > 1:
                optimizations.append({
                    'type': 'contractor_optimization',
                    'contractor': contractor,
                    'items': [item.id for item in contractor_items],
                    'estimated_savings': len(contractor_items) * 25,
                    'description': f"Batch {len(contractor_items)} tasks for {contractor}"
                })
        
        return optimizations
    
    def _calculate_average_completion_time(self, items: List[MaintenanceItem]) -> float:
        """Calculate average completion time"""
        completed_items = [item for item in items if item.completed_at and item.actual_duration_hours]
        if not completed_items:
            return 0.0
        
        return sum(item.actual_duration_hours for item in completed_items) / len(completed_items)
    
    def _analyze_by_category(self, items: List[MaintenanceItem]) -> Dict[str, Any]:
        """Analyze maintenance by category"""
        category_stats = {}
        
        for item in items:
            category = item.category.value
            if category not in category_stats:
                category_stats[category] = {
                    'count': 0,
                    'total_cost': 0,
                    'completed': 0
                }
            
            category_stats[category]['count'] += 1
            category_stats[category]['total_cost'] += item.actual_cost or item.estimated_cost
            if item.status == MaintenanceStatus.COMPLETED:
                category_stats[category]['completed'] += 1
        
        return category_stats
    
    def _analyze_costs(self, items: List[MaintenanceItem]) -> Dict[str, Any]:
        """Analyze maintenance costs"""
        total_estimated = sum(item.estimated_cost for item in items)
        total_actual = sum(item.actual_cost or 0 for item in items if item.actual_cost)
        
        return {
            'total_estimated': total_estimated,
            'total_actual': total_actual,
            'variance': total_actual - total_estimated if total_actual > 0 else 0,
            'average_cost': total_estimated / len(items) if items else 0
        }
    
    def _analyze_timeline(self, items: List[MaintenanceItem]) -> Dict[str, Any]:
        """Analyze maintenance timeline performance"""
        on_time = len([item for item in items if item.status == MaintenanceStatus.COMPLETED])
        overdue = len([item for item in items if item.status == MaintenanceStatus.OVERDUE])
        
        return {
            'on_time_completion_rate': on_time / len(items) if items else 0,
            'overdue_items': overdue,
            'total_items': len(items)
        }
    
    def _analyze_contractor_performance(self, items: List[MaintenanceItem]) -> Dict[str, Any]:
        """Analyze contractor performance"""
        contractor_stats = {}
        
        for item in items:
            if item.assigned_contractor:
                contractor = item.assigned_contractor
                if contractor not in contractor_stats:
                    contractor_stats[contractor] = {
                        'tasks_completed': 0,
                        'total_tasks': 0,
                        'avg_cost': 0,
                        'on_time_rate': 0
                    }
                
                contractor_stats[contractor]['total_tasks'] += 1
                if item.status == MaintenanceStatus.COMPLETED:
                    contractor_stats[contractor]['tasks_completed'] += 1
        
        return contractor_stats
    
    async def _generate_analytics_insights(self, items: List[MaintenanceItem]) -> List[str]:
        """Generate AI-powered insights from analytics"""
        insights = []
        
        if items:
            # Cost insights
            total_cost = sum(item.actual_cost or item.estimated_cost for item in items)
            avg_cost = total_cost / len(items)
            
            if avg_cost > 300:
                insights.append("Average maintenance cost is above benchmark - consider preventive maintenance")
            
            # Category insights
            category_counts = {}
            for item in items:
                category = item.category.value
                category_counts[category] = category_counts.get(category, 0) + 1
            
            if category_counts:
                most_common = max(category_counts, key=category_counts.get)
                insights.append(f"Most frequent maintenance category: {most_common}")
            
            # Timing insights
            overdue_items = [item for item in items if item.status == MaintenanceStatus.OVERDUE]
            if overdue_items:
                insights.append(f"{len(overdue_items)} overdue items - review scheduling processes")
        
        return insights

# Global smart maintenance service instance
smart_maintenance_service = SmartMaintenanceService()