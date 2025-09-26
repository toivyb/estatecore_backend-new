#!/usr/bin/env python3
"""
Real-Time Market Intelligence Engine for EstateCore Phase 7A
Provides live market data, competitive intelligence, and market forecasting
"""

import os
import json
import logging
import requests
import asyncio
import aiohttp
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import sqlite3
import threading
import time
from statistics import mean, median
import random

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PropertyType(Enum):
    SINGLE_FAMILY = "single_family"
    MULTIFAMILY = "multifamily"
    APARTMENT = "apartment"
    CONDO = "condo"
    TOWNHOUSE = "townhouse"
    COMMERCIAL = "commercial"
    MIXED_USE = "mixed_use"

class MarketMetric(Enum):
    MEDIAN_PRICE = "median_price"
    AVERAGE_RENT = "average_rent"
    PRICE_PER_SQFT = "price_per_sqft"
    DAYS_ON_MARKET = "days_on_market"
    INVENTORY_LEVELS = "inventory_levels"
    OCCUPANCY_RATE = "occupancy_rate"
    CAP_RATE = "cap_rate"
    RENT_GROWTH = "rent_growth"

@dataclass
class MarketData:
    """Real-time market data point"""
    location: str
    property_type: PropertyType
    metric: MarketMetric
    value: float
    timestamp: datetime
    source: str
    confidence_score: float
    metadata: Dict[str, Any] = None

@dataclass
class MarketTrend:
    """Market trend analysis"""
    location: str
    property_type: PropertyType
    metric: MarketMetric
    current_value: float
    previous_value: float
    change_percent: float
    trend_direction: str  # "increasing", "decreasing", "stable"
    forecast_30_days: float
    forecast_90_days: float
    confidence: float
    analysis_date: datetime

@dataclass
class CompetitiveIntelligence:
    """Competitive analysis data"""
    competitor_id: str
    property_address: str
    listing_price: float
    rental_rate: Optional[float]
    property_features: Dict[str, Any]
    days_on_market: int
    price_changes: List[Dict[str, Any]]
    competitive_score: float
    analysis_date: datetime

@dataclass
class MarketOpportunity:
    """Investment opportunity identification"""
    opportunity_id: str
    location: str
    property_type: PropertyType
    opportunity_type: str  # "undervalued", "high_growth", "cash_flow"
    estimated_value: float
    current_market_price: float
    potential_return: float
    risk_score: float
    recommendation: str
    confidence_score: float
    analysis_date: datetime
    supporting_data: Dict[str, Any]

class MarketDataProvider:
    """Abstract base for market data providers"""
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key
        self.session = requests.Session()
        self.rate_limit_delay = 1.0  # seconds between requests
        
    async def fetch_market_data(self, location: str, property_type: PropertyType) -> List[MarketData]:
        """Fetch market data for location and property type"""
        raise NotImplementedError
    
    async def fetch_comparable_sales(self, address: str, radius_miles: float = 1.0) -> List[Dict[str, Any]]:
        """Fetch comparable sales data"""
        raise NotImplementedError
    
    async def fetch_rental_comps(self, address: str, radius_miles: float = 1.0) -> List[Dict[str, Any]]:
        """Fetch rental comparable data"""
        raise NotImplementedError

class SimulatedMarketProvider(MarketDataProvider):
    """Simulated market data provider for development and testing"""
    
    def __init__(self):
        super().__init__()
        self.base_prices = {
            "New York, NY": {"single_family": 850000, "multifamily": 1200000, "apartment": 650000},
            "Los Angeles, CA": {"single_family": 750000, "multifamily": 980000, "apartment": 580000},
            "Chicago, IL": {"single_family": 380000, "multifamily": 520000, "apartment": 280000},
            "Houston, TX": {"single_family": 320000, "multifamily": 450000, "apartment": 240000},
            "Phoenix, AZ": {"single_family": 420000, "multifamily": 580000, "apartment": 320000},
            "Philadelphia, PA": {"single_family": 290000, "multifamily": 410000, "apartment": 220000},
            "San Antonio, TX": {"single_family": 260000, "multifamily": 380000, "apartment": 190000},
            "San Diego, CA": {"single_family": 720000, "multifamily": 950000, "apartment": 520000},
            "Dallas, TX": {"single_family": 350000, "multifamily": 480000, "apartment": 260000},
            "San Jose, CA": {"single_family": 1100000, "multifamily": 1450000, "apartment": 780000}
        }
        
        self.rent_multipliers = {
            PropertyType.SINGLE_FAMILY: 0.006,
            PropertyType.MULTIFAMILY: 0.008,
            PropertyType.APARTMENT: 0.009,
            PropertyType.CONDO: 0.007,
            PropertyType.TOWNHOUSE: 0.0065
        }
    
    async def fetch_market_data(self, location: str, property_type: PropertyType) -> List[MarketData]:
        """Generate simulated market data"""
        await asyncio.sleep(0.1)  # Simulate API delay
        
        base_price = self.base_prices.get(location, {}).get(property_type.value, 400000)
        
        # Add some market volatility
        price_variance = random.uniform(-0.05, 0.05)
        current_price = base_price * (1 + price_variance)
        
        rent_multiplier = self.rent_multipliers.get(property_type, 0.007)
        monthly_rent = current_price * rent_multiplier
        
        market_data = [
            MarketData(
                location=location,
                property_type=property_type,
                metric=MarketMetric.MEDIAN_PRICE,
                value=current_price,
                timestamp=datetime.now(),
                source="SimulatedProvider",
                confidence_score=0.85,
                metadata={"variance": price_variance}
            ),
            MarketData(
                location=location,
                property_type=property_type,
                metric=MarketMetric.AVERAGE_RENT,
                value=monthly_rent,
                timestamp=datetime.now(),
                source="SimulatedProvider",
                confidence_score=0.80,
                metadata={"rent_multiplier": rent_multiplier}
            ),
            MarketData(
                location=location,
                property_type=property_type,
                metric=MarketMetric.PRICE_PER_SQFT,
                value=current_price / random.uniform(800, 2500),
                timestamp=datetime.now(),
                source="SimulatedProvider",
                confidence_score=0.75
            ),
            MarketData(
                location=location,
                property_type=property_type,
                metric=MarketMetric.DAYS_ON_MARKET,
                value=random.uniform(15, 120),
                timestamp=datetime.now(),
                source="SimulatedProvider",
                confidence_score=0.70
            ),
            MarketData(
                location=location,
                property_type=property_type,
                metric=MarketMetric.OCCUPANCY_RATE,
                value=random.uniform(85, 98),
                timestamp=datetime.now(),
                source="SimulatedProvider",
                confidence_score=0.85
            )
        ]
        
        return market_data
    
    async def fetch_comparable_sales(self, address: str, radius_miles: float = 1.0) -> List[Dict[str, Any]]:
        """Generate simulated comparable sales"""
        await asyncio.sleep(0.2)
        
        base_price = random.uniform(300000, 800000)
        
        comps = []
        for i in range(random.randint(3, 8)):
            price_variation = random.uniform(-0.15, 0.15)
            comp_price = base_price * (1 + price_variation)
            
            comps.append({
                "address": f"{random.randint(100, 9999)} Main St #{i+1}",
                "sale_price": comp_price,
                "sale_date": (datetime.now() - timedelta(days=random.randint(30, 365))).isoformat(),
                "square_footage": random.randint(800, 2500),
                "bedrooms": random.randint(1, 4),
                "bathrooms": random.randint(1, 3),
                "lot_size": random.uniform(0.1, 0.5),
                "property_type": random.choice(["Single Family", "Condo", "Townhouse"]),
                "days_on_market": random.randint(15, 180),
                "price_per_sqft": comp_price / random.randint(800, 2500),
                "distance_miles": random.uniform(0.1, radius_miles)
            })
        
        return comps

class RealTimeMarketEngine:
    """Main market intelligence engine"""
    
    def __init__(self, database_path: str = "market_intelligence.db"):
        self.database_path = database_path
        self.providers = [SimulatedMarketProvider()]
        self.cache = {}
        self.cache_ttl = 300  # 5 minutes
        self.running = False
        self.update_thread = None
        
        self._initialize_database()
        logger.info("RealTimeMarketEngine initialized")
    
    def _initialize_database(self):
        """Initialize SQLite database for market data storage"""
        conn = sqlite3.connect(self.database_path)
        cursor = conn.cursor()
        
        # Market data table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS market_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                location TEXT NOT NULL,
                property_type TEXT NOT NULL,
                metric TEXT NOT NULL,
                value REAL NOT NULL,
                timestamp TEXT NOT NULL,
                source TEXT NOT NULL,
                confidence_score REAL NOT NULL,
                metadata TEXT
            )
        """)
        
        # Market trends table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS market_trends (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                location TEXT NOT NULL,
                property_type TEXT NOT NULL,
                metric TEXT NOT NULL,
                current_value REAL NOT NULL,
                previous_value REAL NOT NULL,
                change_percent REAL NOT NULL,
                trend_direction TEXT NOT NULL,
                forecast_30_days REAL,
                forecast_90_days REAL,
                confidence REAL,
                analysis_date TEXT NOT NULL
            )
        """)
        
        # Market opportunities table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS market_opportunities (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                opportunity_id TEXT UNIQUE NOT NULL,
                location TEXT NOT NULL,
                property_type TEXT NOT NULL,
                opportunity_type TEXT NOT NULL,
                estimated_value REAL NOT NULL,
                current_market_price REAL NOT NULL,
                potential_return REAL NOT NULL,
                risk_score REAL NOT NULL,
                recommendation TEXT NOT NULL,
                confidence_score REAL NOT NULL,
                analysis_date TEXT NOT NULL,
                supporting_data TEXT
            )
        """)
        
        conn.commit()
        conn.close()
    
    async def get_market_data(self, location: str, property_type: PropertyType, 
                            refresh: bool = False) -> List[MarketData]:
        """Get current market data for location and property type"""
        cache_key = f"{location}_{property_type.value}"
        
        # Check cache first
        if not refresh and cache_key in self.cache:
            cached_data, cached_time = self.cache[cache_key]
            if (datetime.now() - cached_time).seconds < self.cache_ttl:
                return cached_data
        
        # Fetch fresh data
        all_data = []
        for provider in self.providers:
            try:
                provider_data = await provider.fetch_market_data(location, property_type)
                all_data.extend(provider_data)
            except Exception as e:
                logger.error(f"Error fetching data from provider: {e}")
                continue
        
        # Cache the data
        self.cache[cache_key] = (all_data, datetime.now())
        
        # Store in database
        self._store_market_data(all_data)
        
        return all_data
    
    def _store_market_data(self, market_data: List[MarketData]):
        """Store market data in database"""
        conn = sqlite3.connect(self.database_path)
        cursor = conn.cursor()
        
        for data in market_data:
            cursor.execute("""
                INSERT INTO market_data 
                (location, property_type, metric, value, timestamp, source, confidence_score, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                data.location, data.property_type.value, data.metric.value, 
                data.value, data.timestamp.isoformat(), data.source, 
                data.confidence_score, json.dumps(data.metadata or {})
            ))
        
        conn.commit()
        conn.close()
    
    async def analyze_market_trends(self, location: str, property_type: PropertyType,
                                  days_back: int = 30) -> List[MarketTrend]:
        """Analyze market trends over specified period"""
        conn = sqlite3.connect(self.database_path)
        cursor = conn.cursor()
        
        # Get historical data
        cursor.execute("""
            SELECT metric, value, timestamp FROM market_data 
            WHERE location = ? AND property_type = ? AND timestamp >= ?
            ORDER BY timestamp DESC
        """, (
            location, property_type.value, 
            (datetime.now() - timedelta(days=days_back)).isoformat()
        ))
        
        historical_data = cursor.fetchall()
        conn.close()
        
        # Group by metric and analyze trends
        metric_data = {}
        for metric, value, timestamp in historical_data:
            if metric not in metric_data:
                metric_data[metric] = []
            metric_data[metric].append((value, datetime.fromisoformat(timestamp)))
        
        trends = []
        for metric, values in metric_data.items():
            if len(values) < 2:
                continue
                
            # Sort by timestamp
            values.sort(key=lambda x: x[1])
            
            current_value = values[-1][0]
            previous_value = values[0][0] if len(values) > 1 else current_value
            
            change_percent = ((current_value - previous_value) / previous_value * 100) if previous_value != 0 else 0
            
            # Determine trend direction
            if abs(change_percent) < 2:
                trend_direction = "stable"
            elif change_percent > 0:
                trend_direction = "increasing"
            else:
                trend_direction = "decreasing"
            
            # Simple forecasting (in real implementation, use advanced ML models)
            trend_values = [v[0] for v in values[-7:]]  # Last 7 data points
            if len(trend_values) >= 2:
                avg_change = (trend_values[-1] - trend_values[0]) / len(trend_values)
                forecast_30_days = current_value + (avg_change * 30)
                forecast_90_days = current_value + (avg_change * 90)
            else:
                forecast_30_days = current_value
                forecast_90_days = current_value
            
            trend = MarketTrend(
                location=location,
                property_type=property_type,
                metric=MarketMetric(metric),
                current_value=current_value,
                previous_value=previous_value,
                change_percent=change_percent,
                trend_direction=trend_direction,
                forecast_30_days=forecast_30_days,
                forecast_90_days=forecast_90_days,
                confidence=0.75,  # Would be calculated based on data quality and model performance
                analysis_date=datetime.now()
            )
            
            trends.append(trend)
        
        return trends
    
    async def identify_market_opportunities(self, max_opportunities: int = 10) -> List[MarketOpportunity]:
        """Identify potential investment opportunities"""
        opportunities = []
        
        # Major markets to analyze
        major_markets = [
            "New York, NY", "Los Angeles, CA", "Chicago, IL", "Houston, TX", 
            "Phoenix, AZ", "Philadelphia, PA", "San Antonio, TX", "San Diego, CA"
        ]
        
        for location in major_markets[:5]:  # Limit for demo
            for property_type in [PropertyType.SINGLE_FAMILY, PropertyType.MULTIFAMILY]:
                # Get current market data
                market_data = await self.get_market_data(location, property_type)
                
                if not market_data:
                    continue
                
                # Simple opportunity identification logic
                price_data = next((d for d in market_data if d.metric == MarketMetric.MEDIAN_PRICE), None)
                rent_data = next((d for d in market_data if d.metric == MarketMetric.AVERAGE_RENT), None)
                
                if not price_data or not rent_data:
                    continue
                
                # Calculate potential returns
                annual_rent = rent_data.value * 12
                cap_rate = (annual_rent / price_data.value) * 100 if price_data.value > 0 else 0
                
                # Identify opportunity types
                if cap_rate > 8:
                    opportunity_type = "cash_flow"
                    potential_return = cap_rate
                elif cap_rate > 6:
                    opportunity_type = "balanced"
                    potential_return = cap_rate
                else:
                    opportunity_type = "appreciation"
                    potential_return = random.uniform(3, 7)  # Simulated appreciation potential
                
                # Risk scoring (simplified)
                risk_score = max(0.1, min(0.9, (10 - cap_rate) / 10))
                
                opportunity = MarketOpportunity(
                    opportunity_id=f"OPP_{location.replace(', ', '_')}_{property_type.value}_{int(time.time())}",
                    location=location,
                    property_type=property_type,
                    opportunity_type=opportunity_type,
                    estimated_value=price_data.value,
                    current_market_price=price_data.value * random.uniform(0.95, 1.05),
                    potential_return=potential_return,
                    risk_score=risk_score,
                    recommendation="Analyze" if potential_return > 6 else "Monitor",
                    confidence_score=min(price_data.confidence_score, rent_data.confidence_score),
                    analysis_date=datetime.now(),
                    supporting_data={
                        "cap_rate": cap_rate,
                        "annual_rent": annual_rent,
                        "price_per_sqft": next((d.value for d in market_data if d.metric == MarketMetric.PRICE_PER_SQFT), 0)
                    }
                )
                
                opportunities.append(opportunity)
        
        # Sort by potential return and return top opportunities
        opportunities.sort(key=lambda x: x.potential_return, reverse=True)
        return opportunities[:max_opportunities]
    
    def start_real_time_updates(self, update_interval_minutes: int = 15):
        """Start background thread for real-time market data updates"""
        self.running = True
        
        def update_loop():
            while self.running:
                try:
                    # Update market data for key locations
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    
                    # This would be expanded to include all tracked locations
                    key_locations = ["New York, NY", "Los Angeles, CA", "Chicago, IL"]
                    key_types = [PropertyType.SINGLE_FAMILY, PropertyType.MULTIFAMILY]
                    
                    for location in key_locations:
                        for prop_type in key_types:
                            loop.run_until_complete(self.get_market_data(location, prop_type, refresh=True))
                    
                    logger.info("Market data updated successfully")
                    
                except Exception as e:
                    logger.error(f"Error in market data update loop: {e}")
                
                # Sleep until next update
                time.sleep(update_interval_minutes * 60)
        
        self.update_thread = threading.Thread(target=update_loop)
        self.update_thread.daemon = True
        self.update_thread.start()
        
        logger.info(f"Real-time market updates started (interval: {update_interval_minutes} minutes)")
    
    def stop_real_time_updates(self):
        """Stop real-time market data updates"""
        self.running = False
        if self.update_thread:
            self.update_thread.join()
        logger.info("Real-time market updates stopped")

# Global instance
_market_engine = None

def get_market_intelligence_engine() -> RealTimeMarketEngine:
    """Get global market intelligence engine instance"""
    global _market_engine
    if _market_engine is None:
        _market_engine = RealTimeMarketEngine()
    return _market_engine

# Convenience functions
async def get_current_market_data(location: str, property_type: str) -> Dict[str, Any]:
    """Get current market data for a location and property type"""
    engine = get_market_intelligence_engine()
    prop_type = PropertyType(property_type.lower())
    market_data = await engine.get_market_data(location, prop_type)
    
    # Convert to dictionary format
    result = {
        "location": location,
        "property_type": property_type,
        "data": [asdict(data) for data in market_data],
        "last_updated": datetime.now().isoformat()
    }
    
    return result

async def get_market_trends_analysis(location: str, property_type: str, days_back: int = 30) -> Dict[str, Any]:
    """Get market trend analysis"""
    engine = get_market_intelligence_engine()
    prop_type = PropertyType(property_type.lower())
    trends = await engine.analyze_market_trends(location, prop_type, days_back)
    
    return {
        "location": location,
        "property_type": property_type,
        "analysis_period_days": days_back,
        "trends": [asdict(trend) for trend in trends],
        "analysis_date": datetime.now().isoformat()
    }

async def get_investment_opportunities(max_opportunities: int = 10) -> Dict[str, Any]:
    """Get current investment opportunities"""
    engine = get_market_intelligence_engine()
    opportunities = await engine.identify_market_opportunities(max_opportunities)
    
    return {
        "opportunities": [asdict(opp) for opp in opportunities],
        "total_found": len(opportunities),
        "analysis_date": datetime.now().isoformat()
    }

if __name__ == "__main__":
    # Test the market intelligence engine
    async def test_market_engine():
        engine = RealTimeMarketEngine()
        
        # Test market data retrieval
        print("Testing market data retrieval...")
        market_data = await engine.get_market_data("New York, NY", PropertyType.SINGLE_FAMILY)
        for data in market_data:
            print(f"  {data.metric.value}: ${data.value:,.2f} (confidence: {data.confidence_score:.2f})")
        
        print("\nTesting trend analysis...")
        trends = await engine.analyze_market_trends("New York, NY", PropertyType.SINGLE_FAMILY)
        for trend in trends[:3]:
            print(f"  {trend.metric.value}: {trend.change_percent:+.2f}% ({trend.trend_direction})")
        
        print("\nTesting opportunity identification...")
        opportunities = await engine.identify_market_opportunities(5)
        for opp in opportunities:
            print(f"  {opp.location} ({opp.property_type.value}): {opp.potential_return:.2f}% return")
    
    # Run test
    asyncio.run(test_market_engine())