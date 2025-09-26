#!/usr/bin/env python3
"""Test the Market Intelligence System"""

import asyncio
from ai_services.market_intelligence.market_data_engine import RealTimeMarketEngine, PropertyType
from ai_services.market_intelligence.market_analytics_service import AdvancedMarketAnalytics

async def test_market_intelligence():
    print("Testing Market Intelligence System")
    print("=" * 50)
    
    # Test Market Data Engine
    engine = RealTimeMarketEngine()
    
    print("1. Testing Market Data Retrieval...")
    market_data = await engine.get_market_data("New York, NY", PropertyType.SINGLE_FAMILY)
    print(f"   Retrieved {len(market_data)} market data points")
    for data in market_data[:3]:
        print(f"   - {data.metric.value}: ${data.value:,.2f} (confidence: {data.confidence_score:.2f})")
    
    print("\n2. Testing Market Trends Analysis...")
    trends = await engine.analyze_market_trends("New York, NY", PropertyType.SINGLE_FAMILY)
    print(f"   Analyzed {len(trends)} market trends")
    for trend in trends[:3]:
        print(f"   - {trend.metric.value}: {trend.change_percent:+.2f}% ({trend.trend_direction})")
    
    print("\n3. Testing Investment Opportunities...")
    opportunities = await engine.identify_market_opportunities(5)
    print(f"   Found {len(opportunities)} investment opportunities")
    for opp in opportunities[:3]:
        print(f"   - {opp.location} ({opp.property_type.value}): {opp.potential_return:.2f}% return, ${opp.estimated_value:,.0f}")
    
    # Test Advanced Analytics
    print("\n4. Testing Advanced Market Analytics...")
    analytics = AdvancedMarketAnalytics(engine)
    
    print("   Testing Market Forecast...")
    from ai_services.market_intelligence.market_data_engine import MarketMetric
    forecast = await analytics.generate_market_forecast("New York, NY", PropertyType.SINGLE_FAMILY, MarketMetric.MEDIAN_PRICE)
    print(f"   Current: ${forecast.current_value:,.0f}")
    print(f"   1-year forecast: ${forecast.forecast_1_year:,.0f} ({forecast.methodology})")
    
    print("   Testing Competitive Analysis...")
    competition = await analytics.analyze_competition("New York, NY", PropertyType.SINGLE_FAMILY)
    print(f"   Market position: {competition.market_position}")
    print(f"   Market share: {competition.market_share_estimate:.1f}%")
    print(f"   Key competitors: {len(competition.key_competitors)}")
    
    print("   Testing Market Segmentation...")
    segments = await analytics.segment_market("New York, NY")
    print(f"   Identified {len(segments)} market segments")
    for segment in segments[:2]:
        print(f"   - {segment.segment_name}: {segment.growth_rate:.1%} growth, {segment.profit_potential} profit potential")

if __name__ == "__main__":
    asyncio.run(test_market_intelligence())