import React, { useState, useEffect } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '../components/ui/card';

const MarketIntelligenceDashboard = () => {
  const [activeTab, setActiveTab] = useState('overview');
  const [loading, setLoading] = useState(false);
  const [selectedLocation, setSelectedLocation] = useState('New York, NY');
  const [selectedPropertyType, setSelectedPropertyType] = useState('single_family');
  const [dashboardData, setDashboardData] = useState(null);
  const [marketData, setMarketData] = useState([]);
  const [opportunities, setOpportunities] = useState([]);
  const [forecast, setForecast] = useState(null);
  const [competitiveAnalysis, setCompetitiveAnalysis] = useState(null);

  const tabs = [
    { id: 'overview', label: 'Market Overview', icon: '📊' },
    { id: 'trends', label: 'Market Trends', icon: '📈' },
    { id: 'forecast', label: 'Price Forecast', icon: '🔮' },
    { id: 'opportunities', label: 'Investment Opportunities', icon: '💎' },
    { id: 'competition', label: 'Competitive Analysis', icon: '🏆' }
  ];

  const locations = [
    'New York, NY', 'Los Angeles, CA', 'Chicago, IL', 'Houston, TX',
    'Phoenix, AZ', 'Philadelphia, PA', 'San Antonio, TX', 'San Diego, CA'
  ];

  const propertyTypes = [
    { value: 'single_family', label: 'Single Family' },
    { value: 'multifamily', label: 'Multifamily' },
    { value: 'apartment', label: 'Apartment' },
    { value: 'condo', label: 'Condo' },
    { value: 'townhouse', label: 'Townhouse' }
  ];

  useEffect(() => {
    loadDashboardData();
  }, [selectedLocation, selectedPropertyType]);

  const loadDashboardData = async () => {
    setLoading(true);
    try {
      const response = await fetch(`/api/market/dashboard-data?location=${encodeURIComponent(selectedLocation)}&property_type=${selectedPropertyType}`);
      const result = await response.json();

      if (result.success) {
        setDashboardData(result.dashboard);
        setMarketData(result.dashboard.current_market_data.data || []);
        setOpportunities(result.dashboard.investment_opportunities.opportunities || []);
        setForecast(result.dashboard.price_forecast.forecast || null);
        setCompetitiveAnalysis(result.dashboard.competitive_analysis.competitive_analysis || null);
      }
    } catch (error) {
      console.error('Failed to load dashboard data:', error);
    }
    setLoading(false);
  };

  const formatCurrency = (value) => {
    if (value >= 1000000) {
      return `$${(value / 1000000).toFixed(1)}M`;
    } else if (value >= 1000) {
      return `$${(value / 1000).toFixed(0)}K`;
    } else {
      return `$${value.toFixed(0)}`;
    }
  };

  const formatPercent = (value) => {
    return `${value >= 0 ? '+' : ''}${value.toFixed(1)}%`;
  };

  const getMetricIcon = (metric) => {
    const icons = {
      'median_price': '🏠',
      'average_rent': '💰',
      'price_per_sqft': '📏',
      'days_on_market': '📅',
      'occupancy_rate': '📊'
    };
    return icons[metric] || '📊';
  };

  const renderOverviewTab = () => (
    <div className="space-y-6">
      {/* Market Metrics Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
        {marketData.map((data, index) => (
          <Card key={index} className="hover:shadow-lg transition-shadow">
            <CardContent className="p-4">
              <div className="flex items-center justify-between mb-2">
                <span className="text-2xl">{getMetricIcon(data.metric)}</span>
                <span className={`text-xs px-2 py-1 rounded ${
                  data.confidence_score > 0.8 ? 'bg-green-100 text-green-800' : 
                  data.confidence_score > 0.6 ? 'bg-yellow-100 text-yellow-800' : 
                  'bg-red-100 text-red-800'
                }`}>
                  {Math.round(data.confidence_score * 100)}% confidence
                </span>
              </div>
              <div className="text-2xl font-bold text-gray-900 mb-1">
                {data.metric.includes('price') || data.metric.includes('rent') 
                  ? formatCurrency(data.value)
                  : data.metric === 'occupancy_rate' 
                  ? `${data.value.toFixed(1)}%`
                  : data.value.toFixed(0)
                }
              </div>
              <div className="text-sm text-gray-600 capitalize">
                {data.metric.replace('_', ' ')}
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Top Opportunities */}
      <Card>
        <CardHeader>
          <CardTitle>🚀 Top Investment Opportunities</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {opportunities.slice(0, 3).map((opp, index) => (
              <div key={index} className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                <div className="flex-1">
                  <div className="font-semibold text-gray-900">{opp.location}</div>
                  <div className="text-sm text-gray-600 capitalize">
                    {opp.property_type.replace('_', ' ')} • {opp.opportunity_type.replace('_', ' ')}
                  </div>
                </div>
                <div className="text-right">
                  <div className="text-lg font-bold text-green-600">
                    {formatPercent(opp.potential_return)}
                  </div>
                  <div className="text-sm text-gray-500">
                    {formatCurrency(opp.estimated_value)}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Market Status */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle>📈 Market Health</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="flex justify-between items-center">
                <span>Market Liquidity</span>
                <span className="text-green-600 font-semibold">Good</span>
              </div>
              <div className="flex justify-between items-center">
                <span>Price Stability</span>
                <span className="text-yellow-600 font-semibold">Moderate</span>
              </div>
              <div className="flex justify-between items-center">
                <span>Investment Climate</span>
                <span className="text-green-600 font-semibold">Favorable</span>
              </div>
              <div className="flex justify-between items-center">
                <span>Data Quality</span>
                <span className="text-green-600 font-semibold">High</span>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>ℹ️ Market Insights</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3 text-sm">
              <div className="p-3 bg-blue-50 rounded border-l-4 border-blue-400">
                <strong>Market Trend:</strong> {selectedLocation} showing steady growth in {propertyTypes.find(pt => pt.value === selectedPropertyType)?.label.toLowerCase()} segment.
              </div>
              <div className="p-3 bg-green-50 rounded border-l-4 border-green-400">
                <strong>Opportunity:</strong> Current market conditions favor long-term investment strategies.
              </div>
              <div className="p-3 bg-yellow-50 rounded border-l-4 border-yellow-400">
                <strong>Risk Factor:</strong> Monitor interest rate changes and local economic indicators.
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );

  const renderForecastTab = () => (
    <div className="space-y-6">
      {forecast && (
        <>
          <Card>
            <CardHeader>
              <CardTitle>🔮 Price Forecast - {selectedLocation}</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
                <div className="text-center p-4 bg-blue-50 rounded-lg">
                  <div className="text-sm text-gray-600 mb-1">Current Value</div>
                  <div className="text-2xl font-bold text-blue-600">
                    {formatCurrency(forecast.current_value)}
                  </div>
                </div>
                <div className="text-center p-4 bg-green-50 rounded-lg">
                  <div className="text-sm text-gray-600 mb-1">1 Month</div>
                  <div className="text-2xl font-bold text-green-600">
                    {formatCurrency(forecast.forecast_1_month)}
                  </div>
                  <div className="text-sm text-green-600">
                    {formatPercent((forecast.forecast_1_month - forecast.current_value) / forecast.current_value * 100)}
                  </div>
                </div>
                <div className="text-center p-4 bg-yellow-50 rounded-lg">
                  <div className="text-sm text-gray-600 mb-1">6 Months</div>
                  <div className="text-2xl font-bold text-yellow-600">
                    {formatCurrency(forecast.forecast_6_month)}
                  </div>
                  <div className="text-sm text-yellow-600">
                    {formatPercent((forecast.forecast_6_month - forecast.current_value) / forecast.current_value * 100)}
                  </div>
                </div>
                <div className="text-center p-4 bg-purple-50 rounded-lg">
                  <div className="text-sm text-gray-600 mb-1">1 Year</div>
                  <div className="text-2xl font-bold text-purple-600">
                    {formatCurrency(forecast.forecast_1_year)}
                  </div>
                  <div className="text-sm text-purple-600">
                    {formatPercent((forecast.forecast_1_year - forecast.current_value) / forecast.current_value * 100)}
                  </div>
                </div>
              </div>

              <div className="bg-gray-50 p-4 rounded-lg">
                <h4 className="font-semibold mb-2">Forecast Methodology</h4>
                <p className="text-sm text-gray-600 mb-2">{forecast.methodology}</p>
                <p className="text-sm text-gray-600">
                  Model Accuracy: {Math.round(forecast.model_accuracy * 100)}%
                </p>
              </div>
            </CardContent>
          </Card>
        </>
      )}
    </div>
  );

  const renderOpportunitiesTab = () => (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>💎 Investment Opportunities</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-gray-50">
                <tr>
                  <th className="text-left p-3">Location</th>
                  <th className="text-left p-3">Type</th>
                  <th className="text-left p-3">Opportunity</th>
                  <th className="text-right p-3">Potential Return</th>
                  <th className="text-right p-3">Risk Score</th>
                  <th className="text-left p-3">Recommendation</th>
                </tr>
              </thead>
              <tbody>
                {opportunities.map((opp, index) => (
                  <tr key={index} className="border-b hover:bg-gray-50">
                    <td className="p-3 font-medium">{opp.location}</td>
                    <td className="p-3 capitalize">{opp.property_type.replace('_', ' ')}</td>
                    <td className="p-3 capitalize">{opp.opportunity_type.replace('_', ' ')}</td>
                    <td className="p-3 text-right font-semibold text-green-600">
                      {formatPercent(opp.potential_return)}
                    </td>
                    <td className="p-3 text-right">
                      <span className={`px-2 py-1 rounded text-xs ${
                        opp.risk_score < 0.3 ? 'bg-green-100 text-green-800' :
                        opp.risk_score < 0.6 ? 'bg-yellow-100 text-yellow-800' :
                        'bg-red-100 text-red-800'
                      }`}>
                        {Math.round(opp.risk_score * 100)}%
                      </span>
                    </td>
                    <td className="p-3">
                      <span className={`px-2 py-1 rounded text-xs ${
                        opp.recommendation === 'Analyze' ? 'bg-blue-100 text-blue-800' :
                        'bg-gray-100 text-gray-800'
                      }`}>
                        {opp.recommendation}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>
    </div>
  );

  const renderCompetitionTab = () => (
    <div className="space-y-6">
      {competitiveAnalysis && (
        <>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <Card>
              <CardHeader>
                <CardTitle>🏆 Market Position</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-center">
                  <div className="text-3xl font-bold text-blue-600 capitalize mb-2">
                    {competitiveAnalysis.market_position}
                  </div>
                  <div className="text-sm text-gray-600">
                    {Math.round(competitiveAnalysis.market_share_estimate)}% market share
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>💰 Price Position</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-center">
                  <div className="text-3xl font-bold text-green-600 capitalize mb-2">
                    {competitiveAnalysis.average_price_position}
                  </div>
                  <div className="text-sm text-gray-600">
                    Relative to competition
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>📊 Analysis Date</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-center">
                  <div className="text-lg font-semibold text-gray-900 mb-2">
                    {new Date(competitiveAnalysis.analysis_date).toLocaleDateString()}
                  </div>
                  <div className="text-sm text-gray-600">
                    Last updated
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <CardTitle>✅ Competitive Advantages</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  {competitiveAnalysis.competitive_advantages.filter(Boolean).map((advantage, index) => (
                    <div key={index} className="flex items-center space-x-2">
                      <span className="text-green-500">✓</span>
                      <span className="text-sm">{advantage}</span>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>🎯 Market Gaps</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  {competitiveAnalysis.market_gaps.filter(Boolean).map((gap, index) => (
                    <div key={index} className="flex items-center space-x-2">
                      <span className="text-yellow-500">⚠</span>
                      <span className="text-sm">{gap}</span>
                    </div>
                  ))}
                  {competitiveAnalysis.market_gaps.filter(Boolean).length === 0 && (
                    <div className="text-sm text-gray-500 italic">No significant gaps identified</div>
                  )}
                </div>
              </CardContent>
            </Card>
          </div>

          <Card>
            <CardHeader>
              <CardTitle>🏢 Key Competitors</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="text-left p-3">Company</th>
                      <th className="text-right p-3">Portfolio Size</th>
                      <th className="text-right p-3">Avg Rent</th>
                      <th className="text-right p-3">Occupancy</th>
                      <th className="text-left p-3">Reputation</th>
                      <th className="text-left p-3">Key Differentiators</th>
                    </tr>
                  </thead>
                  <tbody>
                    {competitiveAnalysis.key_competitors.map((competitor, index) => (
                      <tr key={index} className="border-b hover:bg-gray-50">
                        <td className="p-3 font-medium">{competitor.name}</td>
                        <td className="p-3 text-right">{competitor.estimated_portfolio_size}</td>
                        <td className="p-3 text-right">{formatCurrency(competitor.average_rent)}</td>
                        <td className="p-3 text-right">{competitor.occupancy_rate.toFixed(1)}%</td>
                        <td className="p-3">
                          <span className={`px-2 py-1 rounded text-xs ${
                            competitor.market_reputation === 'Excellent' ? 'bg-green-100 text-green-800' :
                            competitor.market_reputation === 'Good' ? 'bg-blue-100 text-blue-800' :
                            'bg-gray-100 text-gray-800'
                          }`}>
                            {competitor.market_reputation}
                          </span>
                        </td>
                        <td className="p-3 text-xs">
                          {competitor.key_differentiators.join(', ')}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>💡 Strategic Recommendation</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="p-4 bg-blue-50 rounded-lg border-l-4 border-blue-400">
                <p className="font-semibold text-blue-900 mb-2">Recommendation:</p>
                <p className="text-blue-800">{competitiveAnalysis.recommendation}</p>
              </div>
            </CardContent>
          </Card>
        </>
      )}
    </div>
  );

  return (
    <div className="p-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Market Intelligence Dashboard</h1>
        <p className="text-gray-600">Real-time market data, forecasting, and competitive intelligence</p>
      </div>

      {/* Controls */}
      <div className="mb-6 flex flex-wrap gap-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Location</label>
          <select
            value={selectedLocation}
            onChange={(e) => setSelectedLocation(e.target.value)}
            className="border border-gray-300 rounded-md px-3 py-2 text-sm"
          >
            {locations.map(location => (
              <option key={location} value={location}>{location}</option>
            ))}
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Property Type</label>
          <select
            value={selectedPropertyType}
            onChange={(e) => setSelectedPropertyType(e.target.value)}
            className="border border-gray-300 rounded-md px-3 py-2 text-sm"
          >
            {propertyTypes.map(type => (
              <option key={type.value} value={type.value}>{type.label}</option>
            ))}
          </select>
        </div>

        <div className="flex items-end">
          <button
            onClick={loadDashboardData}
            disabled={loading}
            className="bg-blue-600 text-white px-4 py-2 rounded-md text-sm hover:bg-blue-700 disabled:opacity-50"
          >
            {loading ? 'Loading...' : 'Refresh Data'}
          </button>
        </div>
      </div>

      {/* Navigation Tabs */}
      <div className="border-b border-gray-200 mb-6">
        <nav className="flex space-x-8">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`py-2 px-1 border-b-2 font-medium text-sm ${
                activeTab === tab.id
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              <span className="mr-2">{tab.icon}</span>
              {tab.label}
            </button>
          ))}
        </nav>
      </div>

      {/* Tab Content */}
      <div className="min-h-96">
        {loading ? (
          <div className="flex items-center justify-center py-12">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
            <span className="ml-2 text-gray-600">Loading market intelligence data...</span>
          </div>
        ) : (
          <>
            {activeTab === 'overview' && renderOverviewTab()}
            {activeTab === 'trends' && renderOverviewTab()} {/* Could be expanded with trend charts */}
            {activeTab === 'forecast' && renderForecastTab()}
            {activeTab === 'opportunities' && renderOpportunitiesTab()}
            {activeTab === 'competition' && renderCompetitionTab()}
          </>
        )}
      </div>
    </div>
  );
};

export default MarketIntelligenceDashboard;