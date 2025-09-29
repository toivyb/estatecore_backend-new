import React, { useState, useEffect } from 'react';

export default function AIValuationDashboard() {
  const [loading, setLoading] = useState(true);
  const [data, setData] = useState(null);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      setLoading(true);
      // Mock data for AI Property Valuation
      const mockData = {
        portfolio: {
          totalValue: 12450000,
          totalProperties: 24,
          averageValue: 518750,
          appreciation: 0.087
        },
        recentValuations: [
          {
            id: 1,
            address: '123 Investment Ave',
            value: 525000,
            confidence: 0.92,
            change: 0.08,
            status: 'Updated'
          },
          {
            id: 2,
            address: '456 Rental St',
            value: 385000,
            confidence: 0.89,
            change: 0.045,
            status: 'Current'
          },
          {
            id: 3,
            address: '789 Commercial Blvd',
            value: 1200000,
            confidence: 0.85,
            change: 0.12,
            status: 'Needs Update'
          }
        ],
        marketTrends: {
          residential: 0.078,
          commercial: 0.065,
          rental: 0.042
        }
      };
      
      setData(mockData);
    } catch (error) {
      console.error('Error fetching data:', error);
    } finally {
      setLoading(false);
    }
  };

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0
    }).format(amount);
  };

  const formatPercent = (value) => {
    return `${(value * 100).toFixed(1)}%`;
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-white p-6 rounded-lg shadow">
        <h1 className="text-2xl font-bold text-gray-900 mb-2">🤖 AI Property Valuation Dashboard</h1>
        <p className="text-gray-600">AI-powered property valuation and market analysis</p>
      </div>

      {/* Portfolio Summary */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <div className="bg-white p-6 rounded-lg shadow">
          <div className="flex items-center">
            <div className="text-3xl mr-4">💰</div>
            <div>
              <h3 className="text-sm font-medium text-gray-500">Portfolio Value</h3>
              <div className="text-2xl font-bold text-green-600">
                {formatCurrency(data?.portfolio?.totalValue || 0)}
              </div>
              <div className="text-sm text-gray-600">
                {data?.portfolio?.totalProperties || 0} properties
              </div>
            </div>
          </div>
        </div>

        <div className="bg-white p-6 rounded-lg shadow">
          <div className="flex items-center">
            <div className="text-3xl mr-4">📈</div>
            <div>
              <h3 className="text-sm font-medium text-gray-500">Average Value</h3>
              <div className="text-2xl font-bold text-blue-600">
                {formatCurrency(data?.portfolio?.averageValue || 0)}
              </div>
              <div className="text-sm text-gray-600">Per property</div>
            </div>
          </div>
        </div>

        <div className="bg-white p-6 rounded-lg shadow">
          <div className="flex items-center">
            <div className="text-3xl mr-4">🔮</div>
            <div>
              <h3 className="text-sm font-medium text-gray-500">Appreciation Rate</h3>
              <div className="text-2xl font-bold text-purple-600">
                {formatPercent(data?.portfolio?.appreciation || 0)}
              </div>
              <div className="text-sm text-gray-600">Annual growth</div>
            </div>
          </div>
        </div>

        <div className="bg-white p-6 rounded-lg shadow">
          <div className="flex items-center">
            <div className="text-3xl mr-4">🎯</div>
            <div>
              <h3 className="text-sm font-medium text-gray-500">AI Confidence</h3>
              <div className="text-2xl font-bold text-orange-600">94.2%</div>
              <div className="text-sm text-gray-600">Average accuracy</div>
            </div>
          </div>
        </div>
      </div>

      {/* Market Trends */}
      <div className="bg-white p-6 rounded-lg shadow">
        <h3 className="text-lg font-semibold mb-4">📊 Market Trends</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="text-center p-4 bg-green-50 rounded">
            <div className="text-2xl mb-2">🏠</div>
            <div className="text-lg font-semibold text-green-600">
              +{formatPercent(data?.marketTrends?.residential || 0)}
            </div>
            <div className="text-sm text-gray-600">Residential</div>
          </div>
          
          <div className="text-center p-4 bg-blue-50 rounded">
            <div className="text-2xl mb-2">🏢</div>
            <div className="text-lg font-semibold text-blue-600">
              +{formatPercent(data?.marketTrends?.commercial || 0)}
            </div>
            <div className="text-sm text-gray-600">Commercial</div>
          </div>
          
          <div className="text-center p-4 bg-purple-50 rounded">
            <div className="text-2xl mb-2">🏠</div>
            <div className="text-lg font-semibold text-purple-600">
              +{formatPercent(data?.marketTrends?.rental || 0)}
            </div>
            <div className="text-sm text-gray-600">Rental Market</div>
          </div>
        </div>
      </div>

      {/* Recent Valuations */}
      <div className="bg-white p-6 rounded-lg shadow">
        <h3 className="text-lg font-semibold mb-4">🏘️ Recent Property Valuations</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {data?.recentValuations?.map(property => (
            <div key={property.id} className="border rounded-lg p-4">
              <div className="flex justify-between items-start mb-3">
                <div>
                  <h4 className="font-medium">{property.address}</h4>
                  <div className="text-sm text-gray-600">Property #{property.id}</div>
                </div>
                <span className={`px-2 py-1 text-xs rounded-full ${
                  property.status === 'Updated' 
                    ? 'bg-green-100 text-green-800'
                    : property.status === 'Current'
                    ? 'bg-blue-100 text-blue-800'
                    : 'bg-yellow-100 text-yellow-800'
                }`}>
                  {property.status}
                </span>
              </div>

              <div className="space-y-2">
                <div className="flex justify-between">
                  <span className="text-sm text-gray-600">Value:</span>
                  <span className="font-semibold">{formatCurrency(property.value)}</span>
                </div>
                
                <div className="flex justify-between">
                  <span className="text-sm text-gray-600">Confidence:</span>
                  <span className="font-medium">{formatPercent(property.confidence)}</span>
                </div>
                
                <div className="flex justify-between">
                  <span className="text-sm text-gray-600">Change:</span>
                  <span className={`font-medium ${
                    property.change > 0 ? 'text-green-600' : 'text-red-600'
                  }`}>
                    {property.change > 0 ? '+' : ''}{formatPercent(property.change)}
                  </span>
                </div>
              </div>

              <div className="mt-4 flex space-x-2">
                <button className="flex-1 bg-blue-600 text-white px-3 py-2 text-sm rounded hover:bg-blue-700">
                  🔄 Re-Value
                </button>
                <button className="bg-gray-600 text-white px-3 py-2 text-sm rounded hover:bg-gray-700">
                  👁️ Details
                </button>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* AI Insights */}
      <div className="bg-white p-6 rounded-lg shadow">
        <h3 className="text-lg font-semibold mb-4">🧠 AI Market Insights</h3>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div>
            <h4 className="font-medium mb-3">🔥 Hot Markets</h4>
            <div className="space-y-3">
              <div className="p-3 bg-red-50 rounded">
                <div className="flex justify-between">
                  <span className="font-medium">Downtown District</span>
                  <span className="text-red-600 font-bold">+15.0%</span>
                </div>
                <div className="text-sm text-gray-600">High confidence: 91%</div>
              </div>
              
              <div className="p-3 bg-orange-50 rounded">
                <div className="flex justify-between">
                  <span className="font-medium">Tech Corridor</span>
                  <span className="text-orange-600 font-bold">+12.0%</span>
                </div>
                <div className="text-sm text-gray-600">High confidence: 88%</div>
              </div>
              
              <div className="p-3 bg-yellow-50 rounded">
                <div className="flex justify-between">
                  <span className="font-medium">Waterfront Area</span>
                  <span className="text-yellow-600 font-bold">+9.0%</span>
                </div>
                <div className="text-sm text-gray-600">Medium confidence: 85%</div>
              </div>
            </div>
          </div>

          <div>
            <h4 className="font-medium mb-3">💡 Investment Opportunities</h4>
            <div className="p-4 border border-green-200 rounded-lg bg-green-50">
              <div className="flex justify-between items-start mb-2">
                <div>
                  <div className="font-medium">567 Opportunity Lane</div>
                  <div className="text-sm text-gray-600">Investment Score: 9.2/10</div>
                </div>
                <div className="text-right">
                  <div className="text-lg font-bold text-green-600">+18%</div>
                  <div className="text-xs text-gray-600">Potential Return</div>
                </div>
              </div>
              <div className="text-sm text-gray-700">
                Strong growth area with new development projects. Moderate risk profile.
              </div>
              <button className="mt-3 w-full bg-green-600 text-white py-2 rounded hover:bg-green-700">
                📋 View Analysis
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Quick Actions */}
      <div className="bg-white p-6 rounded-lg shadow">
        <h3 className="text-lg font-semibold mb-4">⚡ Quick Actions</h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <button className="p-4 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors">
            <div className="text-2xl mb-2">🤖</div>
            <div className="text-sm font-medium">Run AI Valuation</div>
          </button>
          <button className="p-4 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors">
            <div className="text-2xl mb-2">📊</div>
            <div className="text-sm font-medium">Market Analysis</div>
          </button>
          <button className="p-4 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors">
            <div className="text-2xl mb-2">📈</div>
            <div className="text-sm font-medium">Portfolio Report</div>
          </button>
          <button className="p-4 bg-gray-600 text-white rounded-lg hover:bg-gray-700 transition-colors">
            <div className="text-2xl mb-2">⚙️</div>
            <div className="text-sm font-medium">Settings</div>
          </button>
        </div>
      </div>
    </div>
  );
}