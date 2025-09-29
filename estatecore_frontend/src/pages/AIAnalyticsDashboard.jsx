import React, { useState, useEffect } from 'react'
import api from '../api'

const AIAnalyticsDashboard = () => {
  const [analyticsData, setAnalyticsData] = useState(null)
  const [tenantScores, setTenantScores] = useState([])
  const [revenueForecast, setRevenueForecast] = useState(null)
  const [maintenanceForecast, setMaintenanceForecast] = useState(null)
  const [loading, setLoading] = useState(true)
  const [activeTab, setActiveTab] = useState('overview')

  useEffect(() => {
    fetchAnalyticsData()
  }, [])

  const fetchAnalyticsData = async () => {
    try {
      const [analyticsRes, revenueRes, maintenanceRes] = await Promise.all([
        fetch(`${api.BASE}/api/analytics/overview`),
        fetch(`${api.BASE}/api/ai/revenue-forecast`),
        fetch(`${api.BASE}/api/ai/maintenance-forecast`)
      ])

      const [analytics, revenue, maintenance] = await Promise.all([
        analyticsRes.json(),
        revenueRes.json(),
        maintenanceRes.json()
      ])

      setAnalyticsData(analytics)
      setRevenueForecast(revenue)
      setMaintenanceForecast(maintenance)
    } catch (error) {
      console.error('Error fetching analytics data:', error)
    } finally {
      setLoading(false)
    }
  }

  const fetchTenantScore = async (tenantId) => {
    try {
      const response = await fetch(`${api.BASE}/api/ai/tenant-score/${tenantId}`)
      const data = await response.json()
      return data
    } catch (error) {
      console.error('Error fetching tenant score:', error)
      return null
    }
  }

  const renderOverviewTab = () => (
    <div className="space-y-6">
      {/* Key Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-gradient-to-r from-blue-500 to-blue-600 text-white p-6 rounded-lg">
          <h3 className="text-lg font-medium mb-2">Occupancy Rate</h3>
          <p className="text-3xl font-bold">{analyticsData?.key_metrics?.occupancy_rate || 0}%</p>
          <p className="text-blue-100 text-sm">AI optimized targeting</p>
        </div>
        <div className="bg-gradient-to-r from-green-500 to-green-600 text-white p-6 rounded-lg">
          <h3 className="text-lg font-medium mb-2">Revenue Growth</h3>
          <p className="text-3xl font-bold">+{analyticsData?.performance_indicators?.revenue_growth || 0}%</p>
          <p className="text-green-100 text-sm">AI-driven optimization</p>
        </div>
        <div className="bg-gradient-to-r from-purple-500 to-purple-600 text-white p-6 rounded-lg">
          <h3 className="text-lg font-medium mb-2">Tenant Satisfaction</h3>
          <p className="text-3xl font-bold">{analyticsData?.performance_indicators?.tenant_satisfaction || 0}</p>
          <p className="text-purple-100 text-sm">ML sentiment analysis</p>
        </div>
      </div>

      {/* AI Insights */}
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-medium mb-4 flex items-center">
          <span className="text-2xl mr-2">🧠</span>
          AI-Powered Insights
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <h4 className="font-medium text-gray-900 mb-3">Recent Activity</h4>
            <div className="space-y-2">
              {analyticsData?.recent_activity?.map((activity, index) => (
                <div key={index} className="flex items-center text-sm">
                  <span className="w-2 h-2 bg-blue-500 rounded-full mr-3"></span>
                  <span className="text-gray-900">{activity.action}</span>
                  <span className="text-gray-500 ml-auto">{activity.time}</span>
                </div>
              ))}
            </div>
          </div>
          <div>
            <h4 className="font-medium text-gray-900 mb-3">Smart Alerts</h4>
            <div className="space-y-2">
              {analyticsData?.alerts?.map((alert, index) => (
                <div key={index} className={`p-3 rounded-lg text-sm ${
                  alert.type === 'warning' ? 'bg-yellow-50 border border-yellow-200' :
                  alert.type === 'error' ? 'bg-red-50 border border-red-200' :
                  'bg-blue-50 border border-blue-200'
                }`}>
                  <span className="font-medium">{alert.message}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  )

  const renderRevenueTab = () => (
    <div className="space-y-6">
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-medium mb-4 flex items-center">
          <span className="text-2xl mr-2">📈</span>
          Revenue Forecasting
        </h3>
        
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-6">
          <div className="text-center">
            <p className="text-sm text-gray-500">Current Month</p>
            <p className="text-2xl font-bold text-gray-900">
              ${revenueForecast?.current_month?.toLocaleString() || 0}
            </p>
          </div>
          <div className="text-center">
            <p className="text-sm text-gray-500">Next Month</p>
            <p className="text-2xl font-bold text-blue-600">
              ${revenueForecast?.next_month?.toLocaleString() || 0}
            </p>
          </div>
          <div className="text-center">
            <p className="text-sm text-gray-500">Quarterly</p>
            <p className="text-2xl font-bold text-green-600">
              ${revenueForecast?.quarterly?.toLocaleString() || 0}
            </p>
          </div>
          <div className="text-center">
            <p className="text-sm text-gray-500">Annual</p>
            <p className="text-2xl font-bold text-purple-600">
              ${revenueForecast?.annual?.toLocaleString() || 0}
            </p>
          </div>
        </div>

        <div className="bg-gradient-to-r from-blue-50 to-purple-50 rounded-lg p-4 mb-6">
          <h4 className="font-medium text-gray-900 mb-2">AI Trends Analysis</h4>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
            <div>
              <span className="font-medium">Growth Rate:</span>
              <span className="ml-2 text-green-600">+{revenueForecast?.trends?.growth_rate || 0}%</span>
            </div>
            <div>
              <span className="font-medium">Confidence:</span>
              <span className="ml-2 text-blue-600">{revenueForecast?.trends?.confidence || 0}%</span>
            </div>
            <div>
              <span className="font-medium">Trend:</span>
              <span className="ml-2 text-purple-600">📈 Upward</span>
            </div>
          </div>
        </div>

        <div>
          <h4 className="font-medium text-gray-900 mb-3">AI Recommendations</h4>
          <div className="space-y-2">
            {revenueForecast?.recommendations?.map((rec, index) => (
              <div key={index} className="flex items-center text-sm">
                <span className="w-2 h-2 bg-green-500 rounded-full mr-3"></span>
                <span>{rec}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  )

  const renderMaintenanceTab = () => (
    <div className="space-y-6">
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-medium mb-4 flex items-center">
          <span className="text-2xl mr-2">🔧</span>
          Maintenance Forecasting
        </h3>
        
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
          <div className="text-center">
            <p className="text-sm text-gray-500">Upcoming Issues</p>
            <p className="text-2xl font-bold text-orange-600">
              {maintenanceForecast?.upcoming_maintenance || 0}
            </p>
          </div>
          <div className="text-center">
            <p className="text-sm text-gray-500">Monthly Cost</p>
            <p className="text-2xl font-bold text-red-600">
              ${maintenanceForecast?.estimated_monthly_cost?.toLocaleString() || 0}
            </p>
          </div>
          <div className="text-center">
            <p className="text-sm text-gray-500">High Priority</p>
            <p className="text-2xl font-bold text-red-800">
              {maintenanceForecast?.high_priority_items || 0}
            </p>
          </div>
        </div>

        <div>
          <h4 className="font-medium text-gray-900 mb-3">Predictive Alerts</h4>
          <div className="space-y-3">
            {maintenanceForecast?.predictive_alerts?.map((alert, index) => (
              <div key={index} className={`p-4 rounded-lg border ${
                alert.urgency === 'high' ? 'bg-red-50 border-red-200' :
                alert.urgency === 'medium' ? 'bg-yellow-50 border-yellow-200' :
                'bg-blue-50 border-blue-200'
              }`}>
                <div className="flex justify-between items-start">
                  <div>
                    <p className="font-medium text-gray-900">{alert.property}</p>
                    <p className="text-sm text-gray-600">{alert.issue}</p>
                  </div>
                  <span className={`px-2 py-1 text-xs font-semibold rounded-full ${
                    alert.urgency === 'high' ? 'bg-red-100 text-red-800' :
                    alert.urgency === 'medium' ? 'bg-yellow-100 text-yellow-800' :
                    'bg-blue-100 text-blue-800'
                  }`}>
                    {alert.urgency}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="mt-6">
          <h4 className="font-medium text-gray-900 mb-3">Cost Optimization</h4>
          <div className="space-y-2">
            {maintenanceForecast?.cost_optimization?.map((opt, index) => (
              <div key={index} className="flex items-center text-sm">
                <span className="w-2 h-2 bg-green-500 rounded-full mr-3"></span>
                <span>{opt}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  )

  const renderTenantScoringTab = () => (
    <div className="space-y-6">
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-medium mb-4 flex items-center">
          <span className="text-2xl mr-2">👥</span>
          AI Tenant Scoring
        </h3>
        
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
          <p className="text-blue-800 font-medium">Coming Soon</p>
          <p className="text-blue-700 text-sm">
            Advanced tenant scoring based on payment history, communication patterns, and maintenance requests.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="bg-green-50 p-4 rounded-lg">
            <h4 className="font-medium text-green-800">Payment Analytics</h4>
            <p className="text-sm text-green-700">
              ML models analyze payment patterns to predict future behavior
            </p>
          </div>
          <div className="bg-blue-50 p-4 rounded-lg">
            <h4 className="font-medium text-blue-800">Communication Score</h4>
            <p className="text-sm text-blue-700">
              NLP analysis of tenant communications for sentiment scoring
            </p>
          </div>
          <div className="bg-purple-50 p-4 rounded-lg">
            <h4 className="font-medium text-purple-800">Risk Assessment</h4>
            <p className="text-sm text-purple-700">
              Comprehensive risk scoring for lease renewals and decisions
            </p>
          </div>
        </div>
      </div>
    </div>
  )

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold text-gray-900">AI Analytics Dashboard</h1>
        <div className="flex items-center space-x-2">
          <span className="text-sm text-gray-500">Last updated:</span>
          <span className="text-sm font-medium text-gray-900">
            {new Date().toLocaleTimeString()}
          </span>
        </div>
      </div>

      {/* Tab Navigation */}
      <div className="border-b border-gray-200">
        <nav className="-mb-px flex space-x-8">
          {[
            { id: 'overview', name: 'Overview', icon: '📊' },
            { id: 'revenue', name: 'Revenue Forecast', icon: '💰' },
            { id: 'maintenance', name: 'Maintenance AI', icon: '🔧' },
            { id: 'tenants', name: 'Tenant Scoring', icon: '👥' }
          ].map((tab) => (
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
              {tab.name}
            </button>
          ))}
        </nav>
      </div>

      {/* Tab Content */}
      <div>
        {activeTab === 'overview' && renderOverviewTab()}
        {activeTab === 'revenue' && renderRevenueTab()}
        {activeTab === 'maintenance' && renderMaintenanceTab()}
        {activeTab === 'tenants' && renderTenantScoringTab()}
      </div>

      {/* AI Status Indicator */}
      <div className="fixed bottom-4 right-4 bg-green-500 text-white p-3 rounded-full shadow-lg">
        <div className="flex items-center">
          <div className="w-2 h-2 bg-green-200 rounded-full animate-pulse mr-2"></div>
          <span className="text-sm font-medium">AI Online</span>
        </div>
      </div>
    </div>
  )
}

export default AIAnalyticsDashboard