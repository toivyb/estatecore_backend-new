import numpy as np
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from enum import Enum
import random

class OccupancyPattern(Enum):
    HIGH_UTILIZATION = "high_utilization"
    LOW_UTILIZATION = "low_utilization"
    PEAK_HOURS = "peak_hours"
    OFF_HOURS = "off_hours"
    WEEKEND_PATTERN = "weekend_pattern"
    SEASONAL_VARIATION = "seasonal_variation"
    ABNORMAL_PATTERN = "abnormal_pattern"

class SpaceType(Enum):
    RESIDENTIAL_UNIT = "residential_unit"
    COMMON_AREA = "common_area"
    OFFICE_SPACE = "office_space"
    RETAIL_SPACE = "retail_space"
    PARKING_GARAGE = "parking_garage"
    AMENITY_SPACE = "amenity_space"
    LOBBY = "lobby"
    ELEVATOR = "elevator"
    STAIRWELL = "stairwell"

class InsightType(Enum):
    COST_SAVINGS = "cost_savings"
    REVENUE_OPPORTUNITY = "revenue_opportunity"
    OPERATIONAL_EFFICIENCY = "operational_efficiency"
    TENANT_SATISFACTION = "tenant_satisfaction"
    SPACE_OPTIMIZATION = "space_optimization"
    ENERGY_SAVINGS = "energy_savings"

@dataclass
class OccupancyMetrics:
    space_id: str
    space_type: SpaceType
    location: str
    property_id: str
    
    # Current metrics
    current_occupancy_rate: float
    peak_occupancy_rate: float
    average_occupancy_rate: float
    occupancy_variance: float
    
    # Time-based analysis
    peak_hours: List[int]
    low_traffic_hours: List[int]
    busiest_day: str
    quietest_day: str
    
    # Patterns
    detected_patterns: List[OccupancyPattern]
    seasonal_trends: Dict[str, float]
    
    # Utilization efficiency
    utilization_score: float
    capacity_optimization_potential: float
    
    # Financial impact
    revenue_per_sqft: float
    operating_cost_per_sqft: float
    efficiency_rating: str
    
    timestamp: datetime

@dataclass
class OccupancyInsight:
    insight_id: str
    insight_type: InsightType
    title: str
    description: str
    space_id: str
    property_id: str
    
    # Impact metrics
    potential_savings: float
    potential_revenue: float
    implementation_cost: float
    payback_period_months: float
    confidence_score: float
    
    # Actionable recommendations
    recommended_actions: List[str]
    priority_level: str
    expected_outcome: str
    
    # Supporting data
    supporting_metrics: Dict[str, Any]
    affected_spaces: List[str]
    
    created_at: datetime

@dataclass
class SpaceUtilizationReport:
    property_id: str
    report_date: datetime
    
    # Overall metrics
    total_spaces_analyzed: int
    average_utilization_rate: float
    total_potential_revenue: float
    total_cost_savings: float
    
    # Space breakdown
    space_metrics: List[OccupancyMetrics]
    utilization_insights: List[OccupancyInsight]
    
    # Trends and patterns
    trending_patterns: List[str]
    seasonal_insights: Dict[str, Any]
    
    # Recommendations summary
    high_priority_actions: List[str]
    quick_wins: List[str]
    long_term_strategies: List[str]

class OccupancyAnalyticsEngine:
    """
    Advanced occupancy analytics system using IoT sensor data and ML models
    """
    
    def __init__(self):
        self.space_configurations = {}
        self.historical_data = {}
        self.pattern_models = {}
        self.benchmark_data = {}
        self._initialize_space_models()
    
    def _initialize_space_models(self):
        """Initialize space utilization models and benchmarks"""
        # Residential space benchmarks
        self.benchmark_data['residential_unit'] = {
            'optimal_occupancy_rate': 0.65,  # 65% average occupancy is healthy
            'peak_threshold': 0.85,
            'revenue_per_sqft_range': (25, 45),  # $ per sq ft per month
            'cost_per_sqft_range': (8, 15)
        }
        
        # Common area benchmarks
        self.benchmark_data['common_area'] = {
            'optimal_occupancy_rate': 0.35,  # 35% for common areas
            'peak_threshold': 0.70,
            'revenue_per_sqft_range': (0, 5),  # Indirect revenue
            'cost_per_sqft_range': (5, 12)
        }
        
        # Office space benchmarks
        self.benchmark_data['office_space'] = {
            'optimal_occupancy_rate': 0.70,
            'peak_threshold': 0.90,
            'revenue_per_sqft_range': (30, 55),
            'cost_per_sqft_range': (10, 18)
        }
        
        # Amenity space benchmarks
        self.benchmark_data['amenity_space'] = {
            'optimal_occupancy_rate': 0.25,  # Lower utilization expected
            'peak_threshold': 0.60,
            'revenue_per_sqft_range': (0, 8),  # Tenant satisfaction value
            'cost_per_sqft_range': (12, 25)
        }
    
    def analyze_occupancy_patterns(self, iot_data: Dict, property_id: str) -> SpaceUtilizationReport:
        """
        Analyze occupancy patterns from IoT sensor data
        """
        space_metrics = []
        insights = []
        
        # Process each space's occupancy data
        spaces_data = self._group_sensors_by_space(iot_data)
        
        for space_id, sensor_readings in spaces_data.items():
            metrics = self._analyze_space_occupancy(space_id, sensor_readings, property_id)
            if metrics:
                space_metrics.append(metrics)
                
                # Generate insights for this space
                space_insights = self._generate_space_insights(metrics)
                insights.extend(space_insights)
        
        # Generate overall property insights
        property_insights = self._generate_property_insights(space_metrics, property_id)
        insights.extend(property_insights)
        
        # Create comprehensive report
        report = self._create_utilization_report(space_metrics, insights, property_id)
        
        return report
    
    def _group_sensors_by_space(self, iot_data: Dict) -> Dict[str, List[Dict]]:
        """Group sensor readings by space/location"""
        spaces_data = {}
        
        for sensor_data in iot_data.get('sensor_readings', []):
            location = sensor_data.get('location', 'Unknown')
            space_id = self._derive_space_id(location)
            
            if space_id not in spaces_data:
                spaces_data[space_id] = []
            spaces_data[space_id].append(sensor_data)
        
        return spaces_data
    
    def _derive_space_id(self, location: str) -> str:
        """Derive space ID and type from location string"""
        location_lower = location.lower()
        
        if 'unit' in location_lower or 'apartment' in location_lower:
            return f"residential_{location.replace(' ', '_')}"
        elif 'lobby' in location_lower:
            return f"lobby_{location.replace(' ', '_')}"
        elif 'gym' in location_lower or 'fitness' in location_lower:
            return f"amenity_gym_{location.replace(' ', '_')}"
        elif 'pool' in location_lower:
            return f"amenity_pool_{location.replace(' ', '_')}"
        elif 'parking' in location_lower or 'garage' in location_lower:
            return f"parking_{location.replace(' ', '_')}"
        elif 'office' in location_lower:
            return f"office_{location.replace(' ', '_')}"
        else:
            return f"common_{location.replace(' ', '_')}"
    
    def _determine_space_type(self, space_id: str) -> SpaceType:
        """Determine space type from space ID"""
        if 'residential' in space_id:
            return SpaceType.RESIDENTIAL_UNIT
        elif 'lobby' in space_id:
            return SpaceType.LOBBY
        elif 'amenity' in space_id:
            return SpaceType.AMENITY_SPACE
        elif 'parking' in space_id:
            return SpaceType.PARKING_GARAGE
        elif 'office' in space_id:
            return SpaceType.OFFICE_SPACE
        else:
            return SpaceType.COMMON_AREA
    
    def _analyze_space_occupancy(self, space_id: str, sensor_readings: List[Dict], property_id: str) -> Optional[OccupancyMetrics]:
        """Analyze occupancy patterns for a specific space"""
        if not sensor_readings:
            return None
        
        space_type = self._determine_space_type(space_id)
        location = sensor_readings[0].get('location', 'Unknown')
        
        # Extract occupancy data
        occupancy_readings = []
        timestamps = []
        
        for reading in sensor_readings:
            if reading.get('sensor_type') == 'occupancy':
                occupancy_readings.append(float(reading.get('value', 0)))
                timestamps.append(datetime.fromisoformat(reading.get('timestamp', datetime.now().isoformat())))
        
        # If no occupancy sensors, infer from other sensors
        if not occupancy_readings:
            occupancy_readings, timestamps = self._infer_occupancy_from_sensors(sensor_readings)
        
        if not occupancy_readings:
            return None
        
        # Calculate occupancy metrics
        current_occupancy = occupancy_readings[-1] if occupancy_readings else 0
        peak_occupancy = max(occupancy_readings)
        average_occupancy = np.mean(occupancy_readings)
        occupancy_variance = np.var(occupancy_readings)
        
        # Analyze time patterns
        peak_hours, low_traffic_hours = self._analyze_time_patterns(occupancy_readings, timestamps)
        busiest_day, quietest_day = self._analyze_daily_patterns(occupancy_readings, timestamps)
        
        # Detect patterns
        detected_patterns = self._detect_occupancy_patterns(occupancy_readings, timestamps, space_type)
        seasonal_trends = self._analyze_seasonal_trends(occupancy_readings, timestamps)
        
        # Calculate utilization metrics
        utilization_score = self._calculate_utilization_score(average_occupancy, space_type)
        capacity_optimization = self._calculate_optimization_potential(occupancy_readings, space_type)
        
        # Calculate financial metrics
        revenue_per_sqft = self._estimate_revenue_per_sqft(space_type, average_occupancy)
        cost_per_sqft = self._estimate_cost_per_sqft(space_type, average_occupancy)
        efficiency_rating = self._calculate_efficiency_rating(utilization_score, revenue_per_sqft, cost_per_sqft)
        
        return OccupancyMetrics(
            space_id=space_id,
            space_type=space_type,
            location=location,
            property_id=property_id,
            current_occupancy_rate=round(current_occupancy, 3),
            peak_occupancy_rate=round(peak_occupancy, 3),
            average_occupancy_rate=round(average_occupancy, 3),
            occupancy_variance=round(float(occupancy_variance), 3),
            peak_hours=peak_hours,
            low_traffic_hours=low_traffic_hours,
            busiest_day=busiest_day,
            quietest_day=quietest_day,
            detected_patterns=detected_patterns,
            seasonal_trends=seasonal_trends,
            utilization_score=round(utilization_score, 3),
            capacity_optimization_potential=round(capacity_optimization, 3),
            revenue_per_sqft=round(revenue_per_sqft, 2),
            operating_cost_per_sqft=round(cost_per_sqft, 2),
            efficiency_rating=efficiency_rating,
            timestamp=datetime.now()
        )
    
    def _infer_occupancy_from_sensors(self, sensor_readings: List[Dict]) -> Tuple[List[float], List[datetime]]:
        """Infer occupancy from other sensor types"""
        occupancy_data = []
        timestamps = []
        
        for reading in sensor_readings:
            sensor_type = reading.get('sensor_type')
            value = float(reading.get('value', 0))
            timestamp = datetime.fromisoformat(reading.get('timestamp', datetime.now().isoformat()))
            
            # Infer occupancy from different sensors
            inferred_occupancy = 0
            
            if sensor_type == 'motion':
                inferred_occupancy = min(value / 10, 1.0)  # Motion activity scale
            elif sensor_type == 'temperature':
                # Higher temperature might indicate occupancy
                if value > 70:
                    inferred_occupancy = min((value - 70) / 10, 1.0)
            elif sensor_type == 'air_quality':
                # Poor air quality might indicate occupancy
                if value > 50:
                    inferred_occupancy = min((value - 50) / 50, 1.0)
            elif sensor_type == 'sound':
                # Sound levels can indicate activity
                inferred_occupancy = min(value / 70, 1.0)  # Assuming 70dB is high activity
            elif sensor_type == 'energy':
                # Energy usage can indicate occupancy
                if value > 1.0:
                    inferred_occupancy = min(value / 5.0, 1.0)
            
            if inferred_occupancy > 0:
                occupancy_data.append(inferred_occupancy)
                timestamps.append(timestamp)
        
        return occupancy_data, timestamps
    
    def _analyze_time_patterns(self, occupancy_data: List[float], timestamps: List[datetime]) -> Tuple[List[int], List[int]]:
        """Analyze time-based occupancy patterns"""
        if not timestamps:
            return [], []
        
        # Group by hour
        hourly_occupancy = {}
        for i, timestamp in enumerate(timestamps):
            hour = timestamp.hour
            if hour not in hourly_occupancy:
                hourly_occupancy[hour] = []
            hourly_occupancy[hour].append(occupancy_data[i])
        
        # Calculate average occupancy by hour
        hourly_averages = {}
        for hour, readings in hourly_occupancy.items():
            hourly_averages[hour] = np.mean(readings)
        
        # Identify peak and low traffic hours
        if hourly_averages:
            sorted_hours = sorted(hourly_averages.items(), key=lambda x: x[1], reverse=True)
            peak_hours = [hour for hour, avg in sorted_hours[:4] if avg > np.mean(list(hourly_averages.values()))]
            low_traffic_hours = [hour for hour, avg in sorted_hours[-4:] if avg < np.mean(list(hourly_averages.values()))]
        else:
            peak_hours = []
            low_traffic_hours = []
        
        return peak_hours, low_traffic_hours
    
    def _analyze_daily_patterns(self, occupancy_data: List[float], timestamps: List[datetime]) -> Tuple[str, str]:
        """Analyze daily occupancy patterns"""
        if not timestamps:
            return "Unknown", "Unknown"
        
        # Group by day of week
        daily_occupancy = {}
        days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        
        for i, timestamp in enumerate(timestamps):
            day = days[timestamp.weekday()]
            if day not in daily_occupancy:
                daily_occupancy[day] = []
            daily_occupancy[day].append(occupancy_data[i])
        
        # Calculate average occupancy by day
        daily_averages = {}
        for day, readings in daily_occupancy.items():
            daily_averages[day] = np.mean(readings)
        
        if daily_averages:
            busiest_day = max(daily_averages.items(), key=lambda x: x[1])[0]
            quietest_day = min(daily_averages.items(), key=lambda x: x[1])[0]
        else:
            busiest_day = "Unknown"
            quietest_day = "Unknown"
        
        return busiest_day, quietest_day
    
    def _detect_occupancy_patterns(self, occupancy_data: List[float], timestamps: List[datetime], space_type: SpaceType) -> List[OccupancyPattern]:
        """Detect specific occupancy patterns"""
        patterns = []
        
        if not occupancy_data:
            return patterns
        
        avg_occupancy = np.mean(occupancy_data)
        benchmark = self.benchmark_data.get(space_type.value, {})
        optimal_rate = benchmark.get('optimal_occupancy_rate', 0.5)
        
        # High utilization pattern
        if avg_occupancy > optimal_rate * 1.2:
            patterns.append(OccupancyPattern.HIGH_UTILIZATION)
        
        # Low utilization pattern
        elif avg_occupancy < optimal_rate * 0.6:
            patterns.append(OccupancyPattern.LOW_UTILIZATION)
        
        # Check for peak hours pattern
        if timestamps:
            peak_variance = np.var(occupancy_data)
            if peak_variance > 0.1:  # High variance indicates peak/off-peak patterns
                patterns.append(OccupancyPattern.PEAK_HOURS)
        
        # Weekend pattern detection
        weekend_readings = []
        weekday_readings = []
        
        for i, timestamp in enumerate(timestamps):
            if timestamp.weekday() >= 5:  # Saturday, Sunday
                weekend_readings.append(occupancy_data[i])
            else:
                weekday_readings.append(occupancy_data[i])
        
        if weekend_readings and weekday_readings:
            weekend_avg = np.mean(weekend_readings)
            weekday_avg = np.mean(weekday_readings)
            
            if abs(weekend_avg - weekday_avg) > 0.2:
                patterns.append(OccupancyPattern.WEEKEND_PATTERN)
        
        return patterns
    
    def _analyze_seasonal_trends(self, occupancy_data: List[float], timestamps: List[datetime]) -> Dict[str, float]:
        """Analyze seasonal occupancy trends"""
        seasonal_data = {'spring': [], 'summer': [], 'fall': [], 'winter': []}
        
        for i, timestamp in enumerate(timestamps):
            month = timestamp.month
            if month in [3, 4, 5]:
                seasonal_data['spring'].append(occupancy_data[i])
            elif month in [6, 7, 8]:
                seasonal_data['summer'].append(occupancy_data[i])
            elif month in [9, 10, 11]:
                seasonal_data['fall'].append(occupancy_data[i])
            else:
                seasonal_data['winter'].append(occupancy_data[i])
        
        seasonal_trends = {}
        for season, readings in seasonal_data.items():
            if readings:
                seasonal_trends[season] = round(float(np.mean(readings)), 3)
            else:
                seasonal_trends[season] = 0.0
        
        return seasonal_trends
    
    def _calculate_utilization_score(self, average_occupancy: float, space_type: SpaceType) -> float:
        """Calculate utilization efficiency score"""
        benchmark = self.benchmark_data.get(space_type.value, {})
        optimal_rate = benchmark.get('optimal_occupancy_rate', 0.5)
        
        # Score based on how close to optimal rate
        if average_occupancy <= optimal_rate:
            score = average_occupancy / optimal_rate
        else:
            # Penalize over-utilization
            over_utilization = (average_occupancy - optimal_rate) / (1.0 - optimal_rate)
            score = 1.0 - (over_utilization * 0.3)
        
        return max(0.0, min(1.0, score))
    
    def _calculate_optimization_potential(self, occupancy_data: List[float], space_type: SpaceType) -> float:
        """Calculate capacity optimization potential"""
        if not occupancy_data:
            return 0.0
        
        benchmark = self.benchmark_data.get(space_type.value, {})
        optimal_rate = benchmark.get('optimal_occupancy_rate', 0.5)
        current_avg = np.mean(occupancy_data)
        
        # Potential improvement
        if current_avg < optimal_rate:
            return (optimal_rate - current_avg) / optimal_rate
        else:
            # Already at or above optimal, limited optimization potential
            return max(0.0, 0.1 - ((current_avg - optimal_rate) * 0.5))
    
    def _estimate_revenue_per_sqft(self, space_type: SpaceType, occupancy_rate: float) -> float:
        """Estimate revenue per square foot"""
        benchmark = self.benchmark_data.get(space_type.value, {})
        revenue_range = benchmark.get('revenue_per_sqft_range', (0, 30))
        
        # Base revenue scaled by occupancy
        base_revenue = (revenue_range[0] + revenue_range[1]) / 2
        revenue_factor = min(1.0, occupancy_rate * 1.5)  # Higher occupancy can drive higher rates
        
        return base_revenue * revenue_factor
    
    def _estimate_cost_per_sqft(self, space_type: SpaceType, occupancy_rate: float) -> float:
        """Estimate operating cost per square foot"""
        benchmark = self.benchmark_data.get(space_type.value, {})
        cost_range = benchmark.get('cost_per_sqft_range', (5, 15))
        
        # Base cost with occupancy impact
        base_cost = (cost_range[0] + cost_range[1]) / 2
        cost_factor = 0.7 + (occupancy_rate * 0.3)  # Higher occupancy increases maintenance costs
        
        return base_cost * cost_factor
    
    def _calculate_efficiency_rating(self, utilization_score: float, revenue_per_sqft: float, cost_per_sqft: float) -> str:
        """Calculate overall efficiency rating"""
        # Combine utilization and financial efficiency
        financial_efficiency = revenue_per_sqft / max(cost_per_sqft, 1.0)
        
        # Normalize financial efficiency (assume 2:1 ratio is good)
        financial_score = min(1.0, financial_efficiency / 2.0)
        
        overall_score = (utilization_score * 0.6) + (financial_score * 0.4)
        
        if overall_score >= 0.8:
            return "Excellent"
        elif overall_score >= 0.65:
            return "Good"
        elif overall_score >= 0.5:
            return "Fair"
        else:
            return "Poor"
    
    def _generate_space_insights(self, metrics: OccupancyMetrics) -> List[OccupancyInsight]:
        """Generate actionable insights for a specific space"""
        insights = []
        
        # Low utilization insight
        if OccupancyPattern.LOW_UTILIZATION in metrics.detected_patterns:
            insight = OccupancyInsight(
                insight_id=f"low_util_{metrics.space_id}_{int(time.time())}",
                insight_type=InsightType.REVENUE_OPPORTUNITY,
                title="Low Space Utilization Detected",
                description=f"{metrics.location} is underutilized at {metrics.average_occupancy_rate:.1%} occupancy",
                space_id=metrics.space_id,
                property_id=metrics.property_id,
                potential_savings=0.0,
                potential_revenue=metrics.capacity_optimization_potential * metrics.revenue_per_sqft * 1000,  # Assume 1000 sq ft
                implementation_cost=5000.0,
                payback_period_months=6.0,
                confidence_score=0.85,
                recommended_actions=[
                    "Consider marketing campaigns to increase utilization",
                    "Evaluate pricing strategy for competitive positioning",
                    "Explore alternative uses for the space during low-traffic periods"
                ],
                priority_level="Medium",
                expected_outcome=f"Increase occupancy to {metrics.utilization_score + metrics.capacity_optimization_potential:.1%}",
                supporting_metrics={
                    "current_utilization": metrics.average_occupancy_rate,
                    "optimization_potential": metrics.capacity_optimization_potential,
                    "peak_hours": metrics.peak_hours
                },
                affected_spaces=[metrics.space_id],
                created_at=datetime.now()
            )
            insights.append(insight)
        
        # High utilization insight
        elif OccupancyPattern.HIGH_UTILIZATION in metrics.detected_patterns:
            insight = OccupancyInsight(
                insight_id=f"high_util_{metrics.space_id}_{int(time.time())}",
                insight_type=InsightType.OPERATIONAL_EFFICIENCY,
                title="High Space Utilization - Capacity Strain",
                description=f"{metrics.location} is highly utilized at {metrics.average_occupancy_rate:.1%} occupancy",
                space_id=metrics.space_id,
                property_id=metrics.property_id,
                potential_savings=metrics.operating_cost_per_sqft * 500,  # Maintenance savings
                potential_revenue=metrics.revenue_per_sqft * 200,  # Premium pricing potential
                implementation_cost=8000.0,
                payback_period_months=4.0,
                confidence_score=0.90,
                recommended_actions=[
                    "Consider expanding capacity or improving space efficiency",
                    "Implement premium pricing during peak hours",
                    "Schedule preventive maintenance to handle increased wear"
                ],
                priority_level="High",
                expected_outcome="Optimize capacity management and revenue extraction",
                supporting_metrics={
                    "current_utilization": metrics.average_occupancy_rate,
                    "peak_occupancy": metrics.peak_occupancy_rate,
                    "efficiency_rating": metrics.efficiency_rating
                },
                affected_spaces=[metrics.space_id],
                created_at=datetime.now()
            )
            insights.append(insight)
        
        # Peak hours insight
        if OccupancyPattern.PEAK_HOURS in metrics.detected_patterns and metrics.peak_hours:
            peak_hours_str = ", ".join([f"{h}:00" for h in metrics.peak_hours[:3]])
            insight = OccupancyInsight(
                insight_id=f"peak_hours_{metrics.space_id}_{int(time.time())}",
                insight_type=InsightType.REVENUE_OPPORTUNITY,
                title="Peak Hours Pricing Opportunity",
                description=f"{metrics.location} has clear peak usage during {peak_hours_str}",
                space_id=metrics.space_id,
                property_id=metrics.property_id,
                potential_savings=0.0,
                potential_revenue=metrics.revenue_per_sqft * 300,  # Dynamic pricing revenue
                implementation_cost=2000.0,
                payback_period_months=3.0,
                confidence_score=0.80,
                recommended_actions=[
                    "Implement dynamic pricing based on peak/off-peak hours",
                    "Offer incentives for off-peak usage to balance demand",
                    "Optimize staffing and services around peak hours"
                ],
                priority_level="Medium",
                expected_outcome="Increase revenue through optimized pricing strategy",
                supporting_metrics={
                    "peak_hours": metrics.peak_hours,
                    "low_traffic_hours": metrics.low_traffic_hours,
                    "occupancy_variance": metrics.occupancy_variance
                },
                affected_spaces=[metrics.space_id],
                created_at=datetime.now()
            )
            insights.append(insight)
        
        return insights
    
    def _generate_property_insights(self, all_metrics: List[OccupancyMetrics], property_id: str) -> List[OccupancyInsight]:
        """Generate property-level insights"""
        insights = []
        
        if not all_metrics:
            return insights
        
        # Calculate property-wide metrics
        total_revenue = sum(m.revenue_per_sqft for m in all_metrics)
        total_costs = sum(m.operating_cost_per_sqft for m in all_metrics)
        avg_utilization = np.mean([m.average_occupancy_rate for m in all_metrics])
        
        # Property-wide optimization insight
        total_optimization_potential = sum(m.capacity_optimization_potential for m in all_metrics)
        
        if total_optimization_potential > 0.5:  # Significant optimization potential
            insight = OccupancyInsight(
                insight_id=f"property_optimization_{property_id}_{int(time.time())}",
                insight_type=InsightType.SPACE_OPTIMIZATION,
                title="Property-Wide Space Optimization Opportunity",
                description=f"Multiple spaces show optimization potential with {avg_utilization:.1%} average utilization",
                space_id="property_wide",
                property_id=property_id,
                potential_savings=total_costs * 1000 * 0.15,  # 15% cost reduction potential
                potential_revenue=total_revenue * 1000 * total_optimization_potential,
                implementation_cost=25000.0,
                payback_period_months=8.0,
                confidence_score=0.75,
                recommended_actions=[
                    "Conduct comprehensive space utilization audit",
                    "Implement property-wide occupancy monitoring system",
                    "Develop integrated marketing strategy for underutilized spaces",
                    "Consider space reconfiguration for optimal layouts"
                ],
                priority_level="High",
                expected_outcome="Improve overall property ROI through optimized space utilization",
                supporting_metrics={
                    "total_spaces": len(all_metrics),
                    "avg_utilization": avg_utilization,
                    "optimization_potential": total_optimization_potential,
                    "efficiency_distribution": [m.efficiency_rating for m in all_metrics]
                },
                affected_spaces=[m.space_id for m in all_metrics],
                created_at=datetime.now()
            )
            insights.append(insight)
        
        return insights
    
    def _create_utilization_report(self, space_metrics: List[OccupancyMetrics], insights: List[OccupancyInsight], property_id: str) -> SpaceUtilizationReport:
        """Create comprehensive utilization report"""
        
        # Calculate summary metrics
        total_spaces = len(space_metrics)
        avg_utilization = np.mean([m.average_occupancy_rate for m in space_metrics]) if space_metrics else 0
        total_potential_revenue = sum(i.potential_revenue for i in insights)
        total_cost_savings = sum(i.potential_savings for i in insights)
        
        # Identify trending patterns
        all_patterns = []
        for metrics in space_metrics:
            all_patterns.extend([p.value for p in metrics.detected_patterns])
        
        pattern_counts = {}
        for pattern in all_patterns:
            pattern_counts[pattern] = pattern_counts.get(pattern, 0) + 1
        
        trending_patterns = sorted(pattern_counts.items(), key=lambda x: x[1], reverse=True)[:3]
        trending_patterns = [pattern for pattern, count in trending_patterns]
        
        # Generate seasonal insights
        seasonal_insights = {}
        if space_metrics:
            for season in ['spring', 'summer', 'fall', 'winter']:
                seasonal_avg = np.mean([m.seasonal_trends.get(season, 0) for m in space_metrics])
                seasonal_insights[season] = round(float(seasonal_avg), 3)
        
        # Categorize recommendations
        high_priority_actions = []
        quick_wins = []
        long_term_strategies = []
        
        for insight in insights:
            if insight.priority_level == "High":
                high_priority_actions.extend(insight.recommended_actions[:2])
            elif insight.payback_period_months <= 3:
                quick_wins.extend(insight.recommended_actions[:1])
            else:
                long_term_strategies.extend(insight.recommended_actions[:1])
        
        return SpaceUtilizationReport(
            property_id=property_id,
            report_date=datetime.now(),
            total_spaces_analyzed=total_spaces,
            average_utilization_rate=round(float(avg_utilization), 3),
            total_potential_revenue=round(total_potential_revenue, 2),
            total_cost_savings=round(total_cost_savings, 2),
            space_metrics=space_metrics,
            utilization_insights=insights,
            trending_patterns=trending_patterns,
            seasonal_insights=seasonal_insights,
            high_priority_actions=list(set(high_priority_actions)),
            quick_wins=list(set(quick_wins)),
            long_term_strategies=list(set(long_term_strategies))
        )

def serialize_occupancy_metrics(metrics: OccupancyMetrics) -> Dict:
    """Convert OccupancyMetrics to JSON-serializable dict"""
    result = asdict(metrics)
    result['space_type'] = metrics.space_type.value
    result['detected_patterns'] = [p.value for p in metrics.detected_patterns]
    result['timestamp'] = metrics.timestamp.isoformat()
    return result

def serialize_occupancy_insight(insight: OccupancyInsight) -> Dict:
    """Convert OccupancyInsight to JSON-serializable dict"""
    result = asdict(insight)
    result['insight_type'] = insight.insight_type.value
    result['created_at'] = insight.created_at.isoformat()
    return result

def serialize_utilization_report(report: SpaceUtilizationReport) -> Dict:
    """Convert SpaceUtilizationReport to JSON-serializable dict"""
    return {
        'property_id': report.property_id,
        'report_date': report.report_date.isoformat(),
        'total_spaces_analyzed': report.total_spaces_analyzed,
        'average_utilization_rate': report.average_utilization_rate,
        'total_potential_revenue': report.total_potential_revenue,
        'total_cost_savings': report.total_cost_savings,
        'space_metrics': [serialize_occupancy_metrics(m) for m in report.space_metrics],
        'utilization_insights': [serialize_occupancy_insight(i) for i in report.utilization_insights],
        'trending_patterns': report.trending_patterns,
        'seasonal_insights': report.seasonal_insights,
        'high_priority_actions': report.high_priority_actions,
        'quick_wins': report.quick_wins,
        'long_term_strategies': report.long_term_strategies
    }

def generate_occupancy_dashboard_data(report: SpaceUtilizationReport) -> Dict:
    """Generate dashboard data for occupancy analytics"""
    
    # Calculate summary statistics
    metrics = report.space_metrics
    insights = report.utilization_insights
    
    # Space type breakdown
    space_type_breakdown = {}
    for metric in metrics:
        space_type = metric.space_type.value
        if space_type not in space_type_breakdown:
            space_type_breakdown[space_type] = {
                'count': 0,
                'avg_utilization': 0,
                'total_revenue_potential': 0,
                'efficiency_rating': []
            }
        
        space_type_breakdown[space_type]['count'] += 1
        space_type_breakdown[space_type]['avg_utilization'] += metric.average_occupancy_rate
        space_type_breakdown[space_type]['total_revenue_potential'] += metric.revenue_per_sqft
        space_type_breakdown[space_type]['efficiency_rating'].append(metric.efficiency_rating)
    
    # Calculate averages
    for space_type in space_type_breakdown:
        count = space_type_breakdown[space_type]['count']
        space_type_breakdown[space_type]['avg_utilization'] = round(
            space_type_breakdown[space_type]['avg_utilization'] / count, 3
        )
        space_type_breakdown[space_type]['avg_revenue_potential'] = round(
            space_type_breakdown[space_type]['total_revenue_potential'] / count, 2
        )
        
        # Most common efficiency rating
        ratings = space_type_breakdown[space_type]['efficiency_rating']
        space_type_breakdown[space_type]['common_efficiency'] = max(set(ratings), key=ratings.count) if ratings else "Unknown"
    
    # Insight breakdown
    insight_breakdown = {}
    for insight in insights:
        insight_type = insight.insight_type.value
        if insight_type not in insight_breakdown:
            insight_breakdown[insight_type] = {
                'count': 0,
                'total_potential_revenue': 0,
                'total_potential_savings': 0,
                'avg_confidence': 0
            }
        
        insight_breakdown[insight_type]['count'] += 1
        insight_breakdown[insight_type]['total_potential_revenue'] += insight.potential_revenue
        insight_breakdown[insight_type]['total_potential_savings'] += insight.potential_savings
        insight_breakdown[insight_type]['avg_confidence'] += insight.confidence_score
    
    # Calculate averages for insights
    for insight_type in insight_breakdown:
        count = insight_breakdown[insight_type]['count']
        insight_breakdown[insight_type]['avg_confidence'] = round(
            insight_breakdown[insight_type]['avg_confidence'] / count, 3
        )
    
    return {
        'summary': {
            'total_spaces_analyzed': report.total_spaces_analyzed,
            'average_utilization_rate': report.average_utilization_rate,
            'total_potential_revenue': report.total_potential_revenue,
            'total_cost_savings': report.total_cost_savings,
            'total_insights_generated': len(insights),
            'high_priority_insights': len([i for i in insights if i.priority_level == "High"])
        },
        'space_type_breakdown': space_type_breakdown,
        'insight_breakdown': insight_breakdown,
        'trending_patterns': report.trending_patterns,
        'seasonal_insights': report.seasonal_insights,
        'recommendations': {
            'high_priority_actions': report.high_priority_actions,
            'quick_wins': report.quick_wins,
            'long_term_strategies': report.long_term_strategies
        },
        'metrics': [serialize_occupancy_metrics(m) for m in report.space_metrics],
        'insights': [serialize_occupancy_insight(i) for i in report.utilization_insights],
        'dashboard_updated': datetime.now().isoformat()
    }