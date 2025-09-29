import React, { useState, useEffect } from 'react'
import { Bar, Line, Pie, Doughnut } from 'react-chartjs-2'
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  LineElement,
  PointElement,
  ArcElement,
  Title,
  Tooltip,
  Legend,
} from 'chart.js'

ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  LineElement,
  PointElement,
  ArcElement,
  Title,
  Tooltip,
  Legend
)

const Analytics = () => {
  const [analytics, setAnalytics] = useState(null)
  const [dateRange, setDateRange] = useState('30')
  const [loading, setLoading] = useState(true)
  const [activeTab, setActiveTab] = useState('overview')

  useEffect(() => {
    fetchAnalytics()
  }, [dateRange])

  const fetchAnalytics = async () => {
    try {
      const response = await fetch(`/api/analytics?days=${dateRange}`)
      const data = await response.json()
      setAnalytics(data)
    } catch (error) {
      console.error('Error fetching analytics:', error)
    } finally {
      setLoading(false)
    }
  }

  // Chart configurations
  const rentCollectionData = {
    labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
    datasets: [
      {
        label: 'Rent Collected',
        data: [12000, 19000, 15000, 25000, 22000, 30000],
        backgroundColor: 'rgba(59, 130, 246, 0.8)',
        borderColor: 'rgba(59, 130, 246, 1)',
        borderWidth: 2,
      },
      {
        label: 'Rent Due',
        data: [15000, 20000, 18000, 27000, 25000, 32000],
        backgroundColor: 'rgba(239, 68, 68, 0.8)',
        borderColor: 'rgba(239, 68, 68, 1)',
        borderWidth: 2,
      }
    ],
  }

  const occupancyData = {
    labels: ['Occupied', 'Vacant', 'Maintenance'],
    datasets: [
      {
        data: [85, 12, 3],
        backgroundColor: [
          'rgba(34, 197, 94, 0.8)',
          'rgba(245, 158, 11, 0.8)',
          'rgba(239, 68, 68, 0.8)',
        ],
        borderColor: [
          'rgba(34, 197, 94, 1)',
          'rgba(245, 158, 11, 1)',
          'rgba(239, 68, 68, 1)',
        ],
        borderWidth: 2,
      },
    ],
  }

  const maintenanceData = {
    labels: ['Open', 'In Progress', 'Completed', 'Cancelled'],
    datasets: [
      {
        data: [15, 8, 45, 2],
        backgroundColor: [
          'rgba(239, 68, 68, 0.8)',
          'rgba(245, 158, 11, 0.8)',
          'rgba(34, 197, 94, 0.8)',
          'rgba(156, 163, 175, 0.8)',
        ],
      },
    ],
  }

  const revenueData = {
    labels: ['Week 1', 'Week 2', 'Week 3', 'Week 4'],
    datasets: [
      {
        label: 'Revenue',
        data: [8500, 9200, 8800, 10500],
        fill: false,
        borderColor: 'rgba(139, 92, 246, 1)',
        backgroundColor: 'rgba(139, 92, 246, 0.1)',
        tension: 0.4,
      },
    ],
  }

  const chartOptions = {
    responsive: true,
    plugins: {
      legend: {
        position: 'top',
      },
    },
    scales: {
      y: {
        beginAtZero: true,
      },
    },
  }

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold text-gray-900">Advanced Analytics</h1>
        <div className="flex gap-4">
          <select
            value={dateRange}
            onChange={(e) => setDateRange(e.target.value)}
            className="border border-gray-300 rounded-md px-4 py-2"
          >
            <option value="7">Last 7 days</option>
            <option value="30">Last 30 days</option>
            <option value="90">Last 90 days</option>
            <option value="365">Last year</option>
          </select>
          <button className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700">
            📊 Export Report
          </button>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <div className="bg-gradient-to-r from-blue-500 to-blue-600 text-white p-6 rounded-lg shadow">
          <h3 className="text-sm font-medium opacity-90">Total Revenue</h3>
          <p className="text-3xl font-bold">$127,500</p>
          <p className="text-sm opacity-75">↗️ +15.2% from last month</p>
        </div>
        <div className="bg-gradient-to-r from-green-500 to-green-600 text-white p-6 rounded-lg shadow">
          <h3 className="text-sm font-medium opacity-90">Occupancy Rate</h3>
          <p className="text-3xl font-bold">94.2%</p>
          <p className="text-sm opacity-75">↗️ +2.1% from last month</p>
        </div>
        <div className="bg-gradient-to-r from-purple-500 to-purple-600 text-white p-6 rounded-lg shadow">
          <h3 className="text-sm font-medium opacity-90">Avg Rent/Unit</h3>
          <p className="text-3xl font-bold">$1,850</p>
          <p className="text-sm opacity-75">↗️ +5.8% from last month</p>
        </div>
        <div className="bg-gradient-to-r from-orange-500 to-orange-600 text-white p-6 rounded-lg shadow">
          <h3 className="text-sm font-medium opacity-90">Maintenance Cost</h3>
          <p className="text-3xl font-bold">$8,450</p>
          <p className="text-sm opacity-75">↘️ -12.5% from last month</p>
        </div>
      </div>

      {/* Tab Navigation */}
      <div className="border-b border-gray-200">
        <nav className="-mb-px flex space-x-8">
          {[
            { id: 'overview', name: 'Overview' },
            { id: 'financial', name: 'Financial' },
            { id: 'operations', name: 'Operations' },
            { id: 'tenant', name: 'Tenant Analytics' },
            { id: 'predictive', name: 'Predictive' }
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`py-2 px-1 border-b-2 font-medium text-sm ${
                activeTab === tab.id
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700'
              }`}
            >
              {tab.name}
            </button>
          ))}
        </nav>
      </div>

      {/* Tab Content */}
      {activeTab === 'overview' && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="bg-white p-6 rounded-lg shadow">
            <h3 className="text-lg font-medium mb-4">Rent Collection Trends</h3>
            <Bar data={rentCollectionData} options={chartOptions} />
          </div>
          <div className="bg-white p-6 rounded-lg shadow">
            <h3 className="text-lg font-medium mb-4">Occupancy Status</h3>
            <Pie data={occupancyData} />
          </div>
        </div>
      )}

      {activeTab === 'financial' && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="bg-white p-6 rounded-lg shadow">
            <h3 className="text-lg font-medium mb-4">Revenue Trends</h3>
            <Line data={revenueData} options={chartOptions} />
          </div>
          <div className="bg-white p-6 rounded-lg shadow">
            <h3 className="text-lg font-medium mb-4">Expense Breakdown</h3>
            <Doughnut data={maintenanceData} />
          </div>
        </div>
      )}

      {activeTab === 'operations' && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="bg-white p-6 rounded-lg shadow">
            <h3 className="text-lg font-medium mb-4">Maintenance Status</h3>
            <Doughnut data={maintenanceData} />
          </div>
          <div className="bg-white p-6 rounded-lg shadow">
            <h3 className="text-lg font-medium mb-4">Key Metrics</h3>
            <div className="space-y-4">
              <div className="flex justify-between">
                <span>Avg Response Time</span>
                <span className="font-bold">2.3 hours</span>
              </div>
              <div className="flex justify-between">
                <span>Work Orders Completed</span>
                <span className="font-bold">142</span>
              </div>
              <div className="flex justify-between">
                <span>Tenant Satisfaction</span>
                <span className="font-bold">4.7/5</span>
              </div>
            </div>
          </div>
        </div>
      )}

      {activeTab === 'tenant' && (
        <div className="bg-white p-6 rounded-lg shadow">
          <h3 className="text-lg font-medium mb-4">Tenant Analytics</h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="text-center">
              <p className="text-2xl font-bold text-blue-600">18 months</p>
              <p className="text-sm text-gray-600">Average Lease Length</p>
            </div>
            <div className="text-center">
              <p className="text-2xl font-bold text-green-600">12%</p>
              <p className="text-sm text-gray-600">Annual Turnover Rate</p>
            </div>
            <div className="text-center">
              <p className="text-2xl font-bold text-purple-600">$1,200</p>
              <p className="text-sm text-gray-600">Avg Security Deposit</p>
            </div>
          </div>
        </div>
      )}

      {activeTab === 'predictive' && (
        <div className="bg-white p-6 rounded-lg shadow">
          <h3 className="text-lg font-medium mb-4">AI-Powered Insights</h3>
          <div className="space-y-4">
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
              <h4 className="font-medium text-blue-800">Revenue Forecast</h4>
              <p className="text-sm text-blue-600">Based on current trends, expect 8% revenue growth next quarter</p>
            </div>
            <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
              <h4 className="font-medium text-yellow-800">Maintenance Alert</h4>
              <p className="text-sm text-yellow-600">Unit 204 may require HVAC maintenance within 30 days</p>
            </div>
            <div className="bg-green-50 border border-green-200 rounded-lg p-4">
              <h4 className="font-medium text-green-800">Optimization Opportunity</h4>
              <p className="text-sm text-green-600">Consider raising rent by 3% based on market analysis</p>
            </div>
          </div>
        </div>
      )}

      {/* Real-time Activity Feed */}
      <div className="bg-white rounded-lg shadow">
        <div className="px-6 py-4 border-b border-gray-200">
          <h3 className="text-lg font-medium text-gray-900">Real-time Activity</h3>
        </div>
        <div className="p-6">
          <div className="space-y-3">
            <div className="flex items-center space-x-3">
              <div className="w-2 h-2 bg-green-500 rounded-full"></div>
              <span className="text-sm">Rent payment received from Unit 305 - $1,850</span>
              <span className="text-xs text-gray-500">2 min ago</span>
            </div>
            <div className="flex items-center space-x-3">
              <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
              <span className="text-sm">New maintenance request - Unit 102 Plumbing</span>
              <span className="text-xs text-gray-500">15 min ago</span>
            </div>
            <div className="flex items-center space-x-3">
              <div className="w-2 h-2 bg-purple-500 rounded-full"></div>
              <span className="text-sm">Lease renewal signed - Unit 204</span>
              <span className="text-xs text-gray-500">1 hour ago</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default Analytics