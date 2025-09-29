import React, { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'

const TenantPortal = () => {
  const navigate = useNavigate()
  const [user, setUser] = useState(() => {
    try {
      return JSON.parse(localStorage.getItem('user') || '{}')
    } catch {
      return {}
    }
  })

  const [tenantData, setTenantData] = useState({
    personalInfo: {
      name: user.username || 'Loading...',
      email: user.email || 'Loading...',
      phone: 'Loading...',
      emergencyContact: 'Loading...'
    },
    leaseInfo: {
      propertyAddress: 'Loading...',
      leaseStart: '',
      leaseEnd: '',
      monthlyRent: 0,
      depositAmount: 0,
      leaseStatus: 'Loading...'
    },
    accountInfo: {
      balance: 0,
      nextPaymentDue: '',
      paymentMethod: 'Loading...',
      autoPayEnabled: false
    }
  })
  
  const [dashboardData, setDashboardData] = useState({
    recentPayments: 0,
    pendingMaintenance: 0,
    unreadNotifications: 0,
    unreadMessages: 0
  })
  
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  const [notifications, setNotifications] = useState([])

  const [maintenanceRequests, setMaintenanceRequests] = useState([])

  const [paymentHistory, setPaymentHistory] = useState([])

  const [activeTab, setActiveTab] = useState('dashboard')

  // Check if user is tenant and load data
  useEffect(() => {
    if (user.role && user.role !== 'tenant') {
      navigate('/')
      return
    }
    
    if (user.id) {
      loadTenantData()
    }
  }, [user.role, user.id, navigate])

  const loadTenantData = async () => {
    setLoading(true)
    setError(null)
    
    try {
      const token = localStorage.getItem('token')
      const headers = {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      }

      // Load all tenant data in parallel
      const [profileRes, dashboardRes, notificationsRes, maintenanceRes, paymentsRes] = await Promise.all([
        fetch(`/api/tenant-portal/profile/${user.id}`, { headers }),
        fetch(`/api/tenant-portal/dashboard/${user.id}`, { headers }),
        fetch(`/api/tenant-portal/notifications/${user.id}?limit=10`, { headers }),
        fetch(`/api/tenant-portal/maintenance/${user.id}?limit=10`, { headers }),
        fetch(`/api/tenant-portal/payments/${user.id}?limit=10`, { headers })
      ])

      if (profileRes.ok) {
        const profileData = await profileRes.json()
        setTenantData({
          personalInfo: {
            name: profileData.user.username,
            email: profileData.user.email,
            phone: profileData.tenant?.phone || 'Not provided',
            emergencyContact: profileData.tenant?.emergency_contact || 'Not provided'
          },
          leaseInfo: {
            propertyAddress: profileData.property?.address || 'No property assigned',
            leaseStart: profileData.lease?.start_date || '',
            leaseEnd: profileData.lease?.end_date || '',
            monthlyRent: profileData.lease?.monthly_rent || 0,
            depositAmount: profileData.lease?.security_deposit || 0,
            leaseStatus: profileData.lease?.status || 'Unknown'
          },
          accountInfo: {
            balance: profileData.balance || 0,
            nextPaymentDue: profileData.next_payment_due || '',
            paymentMethod: profileData.payment_method || 'Not configured',
            autoPayEnabled: profileData.auto_pay_enabled || false
          }
        })
      }

      if (dashboardRes.ok) {
        const dashboardData = await dashboardRes.json()
        setDashboardData(dashboardData)
      }

      if (notificationsRes.ok) {
        const notificationsData = await notificationsRes.json()
        setNotifications(notificationsData.notifications || [])
      }

      if (maintenanceRes.ok) {
        const maintenanceData = await maintenanceRes.json()
        setMaintenanceRequests(maintenanceData.maintenance_requests || [])
      }

      if (paymentsRes.ok) {
        const paymentsData = await paymentsRes.json()
        setPaymentHistory(paymentsData.payments || [])
      }

    } catch (error) {
      console.error('Error loading tenant data:', error)
      setError('Failed to load tenant data. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD'
    }).format(amount)
  }

  const getNotificationIcon = (type) => {
    switch (type) {
      case 'payment': return '💳'
      case 'maintenance': return '🔧'
      case 'announcement': return '📢'
      default: return '📨'
    }
  }

  const getStatusColor = (status) => {
    switch (status) {
      case 'Paid': return 'bg-green-100 text-green-800'
      case 'In Progress': return 'bg-yellow-100 text-yellow-800'
      case 'Scheduled': return 'bg-blue-100 text-blue-800'
      case 'Pending': return 'bg-orange-100 text-orange-800'
      case 'Active': return 'bg-green-100 text-green-800'
      default: return 'bg-gray-100 text-gray-800'
    }
  }

  const getPriorityColor = (priority) => {
    switch (priority) {
      case 'High': return 'bg-red-100 text-red-800'
      case 'Medium': return 'bg-yellow-100 text-yellow-800'
      case 'Low': return 'bg-green-100 text-green-800'
      default: return 'bg-gray-100 text-gray-800'
    }
  }

  const markNotificationAsRead = async (notificationId) => {
    try {
      const token = localStorage.getItem('token')
      const response = await fetch(`/api/tenant-portal/notifications/${notificationId}/read`, {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      })

      if (response.ok) {
        setNotifications(prev => 
          prev.map(notif => 
            notif.id === notificationId ? { ...notif, read: true } : notif
          )
        )
      }
    } catch (error) {
      console.error('Error marking notification as read:', error)
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600 dark:text-gray-400">Loading tenant portal...</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900 flex items-center justify-center">
        <div className="text-center max-w-md mx-auto p-6">
          <div className="text-red-600 text-6xl mb-4">⚠️</div>
          <h2 className="text-2xl font-bold text-gray-900 dark:text-gray-100 mb-2">Error Loading Portal</h2>
          <p className="text-gray-600 dark:text-gray-400 mb-4">{error}</p>
          <button
            onClick={loadTenantData}
            className="bg-blue-600 text-white px-6 py-2 rounded-md hover:bg-blue-700 transition-colors"
          >
            Try Again
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      {/* Header */}
      <header className="bg-white dark:bg-gray-800 shadow-sm border-b dark:border-gray-700">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-4">
            <div>
              <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">
                Welcome back, {tenantData.personalInfo.name.split(' ')[0]}! 👋
              </h1>
              <p className="text-sm text-gray-600 dark:text-gray-400">
                {tenantData.leaseInfo.propertyAddress}
              </p>
            </div>
            <div className="flex items-center space-x-4">
              <div className="relative">
                <button className="p-2 text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-full">
                  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 17h5l-5 5v-5z" />
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 7H4a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2V9a2 2 0 00-2-2z" />
                  </svg>
                  {notifications.filter(n => !n.read).length > 0 && (
                    <span className="absolute -top-1 -right-1 bg-red-500 text-white text-xs rounded-full h-5 w-5 flex items-center justify-center">
                      {notifications.filter(n => !n.read).length}
                    </span>
                  )}
                </button>
              </div>
              <button
                onClick={() => {
                  localStorage.removeItem('token')
                  localStorage.removeItem('user')
                  navigate('/login')
                }}
                className="flex items-center px-3 py-2 text-sm text-red-600 hover:bg-red-50 dark:hover:bg-red-900 rounded-md border border-red-200 dark:border-red-700"
              >
                🚪 Logout
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Navigation Tabs */}
      <div className="bg-white dark:bg-gray-800 shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <nav className="flex space-x-8">
            {[
              { id: 'dashboard', name: 'Dashboard', icon: '🏠' },
              { id: 'payments', name: 'Payments', icon: '💳' },
              { id: 'maintenance', name: 'Maintenance', icon: '🔧' },
              { id: 'documents', name: 'Documents', icon: '📄' },
              { id: 'profile', name: 'Profile', icon: '👤' }
            ].map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`py-4 px-1 border-b-2 font-medium text-sm flex items-center space-x-2 ${
                  activeTab === tab.id
                    ? 'border-blue-500 text-blue-600 dark:text-blue-400'
                    : 'border-transparent text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300 hover:border-gray-300'
                }`}
              >
                <span>{tab.icon}</span>
                <span>{tab.name}</span>
              </button>
            ))}
          </nav>
        </div>
      </div>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Dashboard Tab */}
        {activeTab === 'dashboard' && (
          <div className="space-y-6">
            {/* Quick Stats */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
                <div className="flex items-center">
                  <div className="flex-shrink-0">
                    <div className="w-8 h-8 bg-green-100 rounded-full flex items-center justify-center">
                      <span className="text-green-600 font-semibold">💰</span>
                    </div>
                  </div>
                  <div className="ml-4">
                    <p className="text-sm font-medium text-gray-500 dark:text-gray-400">Account Balance</p>
                    <p className="text-2xl font-semibold text-gray-900 dark:text-gray-100">
                      {formatCurrency(tenantData.accountInfo.balance)}
                    </p>
                  </div>
                </div>
              </div>

              <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
                <div className="flex items-center">
                  <div className="flex-shrink-0">
                    <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center">
                      <span className="text-blue-600 font-semibold">📅</span>
                    </div>
                  </div>
                  <div className="ml-4">
                    <p className="text-sm font-medium text-gray-500 dark:text-gray-400">Next Payment Due</p>
                    <p className="text-2xl font-semibold text-gray-900 dark:text-gray-100">
                      {tenantData.accountInfo.nextPaymentDue ? new Date(tenantData.accountInfo.nextPaymentDue).toLocaleDateString() : 'N/A'}
                    </p>
                  </div>
                </div>
              </div>

              <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
                <div className="flex items-center">
                  <div className="flex-shrink-0">
                    <div className="w-8 h-8 bg-purple-100 rounded-full flex items-center justify-center">
                      <span className="text-purple-600 font-semibold">🏠</span>
                    </div>
                  </div>
                  <div className="ml-4">
                    <p className="text-sm font-medium text-gray-500 dark:text-gray-400">Lease Status</p>
                    <p className="text-lg font-semibold text-gray-900 dark:text-gray-100">
                      <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getStatusColor(tenantData.leaseInfo.leaseStatus)}`}>
                        {tenantData.leaseInfo.leaseStatus}
                      </span>
                    </p>
                  </div>
                </div>
              </div>
            </div>

            {/* Recent Notifications */}
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow">
              <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700">
                <h3 className="text-lg font-medium text-gray-900 dark:text-gray-100">Recent Notifications</h3>
              </div>
              <div className="p-6">
                <div className="space-y-4">
                  {notifications.slice(0, 3).map((notification) => (
                    <div
                      key={notification.id}
                      className={`p-4 rounded-lg border-l-4 cursor-pointer ${
                        notification.read ? 'bg-gray-50 dark:bg-gray-700 border-gray-300' : 'bg-blue-50 dark:bg-blue-900 border-blue-400'
                      }`}
                      onClick={() => markNotificationAsRead(notification.id)}
                    >
                      <div className="flex items-start">
                        <span className="text-2xl mr-3">{getNotificationIcon(notification.type)}</span>
                        <div className="flex-1">
                          <p className="font-medium text-gray-900 dark:text-gray-100">{notification.title}</p>
                          <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">{notification.message}</p>
                          <p className="text-xs text-gray-500 dark:text-gray-500 mt-2">{notification.date}</p>
                        </div>
                        {!notification.read && (
                          <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            {/* Quick Actions */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              <button
                onClick={() => setActiveTab('payments')}
                className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow hover:shadow-md transition-shadow text-center"
              >
                <div className="text-3xl mb-2">💳</div>
                <h3 className="font-medium text-gray-900 dark:text-gray-100">Pay Rent</h3>
                <p className="text-sm text-gray-600 dark:text-gray-400">Make payment online</p>
              </button>

              <button
                onClick={() => setActiveTab('maintenance')}
                className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow hover:shadow-md transition-shadow text-center"
              >
                <div className="text-3xl mb-2">🔧</div>
                <h3 className="font-medium text-gray-900 dark:text-gray-100">Report Issue</h3>
                <p className="text-sm text-gray-600 dark:text-gray-400">Submit maintenance request</p>
              </button>

              <button
                onClick={() => setActiveTab('documents')}
                className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow hover:shadow-md transition-shadow text-center"
              >
                <div className="text-3xl mb-2">📄</div>
                <h3 className="font-medium text-gray-900 dark:text-gray-100">View Lease</h3>
                <p className="text-sm text-gray-600 dark:text-gray-400">Access documents</p>
              </button>

              <button
                onClick={() => setActiveTab('profile')}
                className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow hover:shadow-md transition-shadow text-center"
              >
                <div className="text-3xl mb-2">👤</div>
                <h3 className="font-medium text-gray-900 dark:text-gray-100">Update Profile</h3>
                <p className="text-sm text-gray-600 dark:text-gray-400">Manage your info</p>
              </button>
            </div>
          </div>
        )}

        {/* Payments Tab */}
        {activeTab === 'payments' && (
          <div className="space-y-6">
            {/* Payment Summary */}
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
              <h3 className="text-lg font-medium text-gray-900 dark:text-gray-100 mb-4">Payment Summary</h3>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div>
                  <p className="text-sm text-gray-600 dark:text-gray-400">Monthly Rent</p>
                  <p className="text-2xl font-bold text-gray-900 dark:text-gray-100">
                    {formatCurrency(tenantData.leaseInfo.monthlyRent)}
                  </p>
                </div>
                <div>
                  <p className="text-sm text-gray-600 dark:text-gray-400">Next Due Date</p>
                  <p className="text-2xl font-bold text-gray-900 dark:text-gray-100">
                    {tenantData.accountInfo.nextPaymentDue ? new Date(tenantData.accountInfo.nextPaymentDue).toLocaleDateString() : 'N/A'}
                  </p>
                </div>
                <div>
                  <p className="text-sm text-gray-600 dark:text-gray-400">Current Balance</p>
                  <p className="text-2xl font-bold text-green-600">
                    {formatCurrency(tenantData.accountInfo.balance)}
                  </p>
                </div>
              </div>
              <div className="mt-6">
                <button className="bg-blue-600 text-white px-6 py-3 rounded-md hover:bg-blue-700 transition-colors">
                  💳 Pay Rent Now
                </button>
              </div>
            </div>

            {/* Payment History */}
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow">
              <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700">
                <h3 className="text-lg font-medium text-gray-900 dark:text-gray-100">Payment History</h3>
              </div>
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
                  <thead className="bg-gray-50 dark:bg-gray-700">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                        Date
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                        Type
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                        Amount
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                        Status
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                        Receipt
                      </th>
                    </tr>
                  </thead>
                  <tbody className="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-700">
                    {paymentHistory.map((payment) => (
                      <tr key={payment.id}>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-gray-100">
                          {new Date(payment.date).toLocaleDateString()}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-gray-100">
                          {payment.type}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-gray-100">
                          {formatCurrency(payment.amount)}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getStatusColor(payment.status)}`}>
                            {payment.status}
                          </span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm">
                          <a href={payment.receiptUrl} className="text-blue-600 hover:text-blue-900">
                            📄 Download
                          </a>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}

        {/* Maintenance Tab */}
        {activeTab === 'maintenance' && (
          <div className="space-y-6">
            {/* Create New Request */}
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
              <h3 className="text-lg font-medium text-gray-900 dark:text-gray-100 mb-4">Submit New Maintenance Request</h3>
              <button className="bg-blue-600 text-white px-6 py-3 rounded-md hover:bg-blue-700 transition-colors">
                🔧 Create New Request
              </button>
            </div>

            {/* Existing Requests */}
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow">
              <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700">
                <h3 className="text-lg font-medium text-gray-900 dark:text-gray-100">Your Maintenance Requests</h3>
              </div>
              <div className="p-6">
                <div className="space-y-4">
                  {maintenanceRequests.map((request) => (
                    <div key={request.id} className="border border-gray-200 dark:border-gray-700 rounded-lg p-4">
                      <div className="flex justify-between items-start mb-2">
                        <h4 className="font-medium text-gray-900 dark:text-gray-100">{request.title}</h4>
                        <div className="flex space-x-2">
                          <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getPriorityColor(request.priority)}`}>
                            {request.priority} Priority
                          </span>
                          <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getStatusColor(request.status)}`}>
                            {request.status}
                          </span>
                        </div>
                      </div>
                      <p className="text-sm text-gray-600 dark:text-gray-400 mb-2">{request.description}</p>
                      <div className="text-xs text-gray-500 dark:text-gray-500">
                        <p>Submitted: {request.date_submitted ? new Date(request.date_submitted).toLocaleDateString() : request.dateSubmitted}</p>
                        {(request.scheduled_date || request.scheduledDate) && <p>Scheduled: {request.scheduled_date ? new Date(request.scheduled_date).toLocaleDateString() : request.scheduledDate}</p>}
                        <p>Category: {request.category}</p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Documents Tab */}
        {activeTab === 'documents' && (
          <div className="space-y-6">
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
              <h3 className="text-lg font-medium text-gray-900 dark:text-gray-100 mb-4">Your Documents</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="border border-gray-200 dark:border-gray-700 rounded-lg p-4 hover:bg-gray-50 dark:hover:bg-gray-700 cursor-pointer">
                  <div className="flex items-center">
                    <span className="text-2xl mr-3">📄</span>
                    <div>
                      <h4 className="font-medium text-gray-900 dark:text-gray-100">Lease Agreement</h4>
                      <p className="text-sm text-gray-600 dark:text-gray-400">Active lease document</p>
                    </div>
                  </div>
                </div>
                <div className="border border-gray-200 dark:border-gray-700 rounded-lg p-4 hover:bg-gray-50 dark:hover:bg-gray-700 cursor-pointer">
                  <div className="flex items-center">
                    <span className="text-2xl mr-3">🧾</span>
                    <div>
                      <h4 className="font-medium text-gray-900 dark:text-gray-100">Payment Receipts</h4>
                      <p className="text-sm text-gray-600 dark:text-gray-400">Download payment history</p>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Profile Tab */}
        {activeTab === 'profile' && (
          <div className="space-y-6">
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
              <h3 className="text-lg font-medium text-gray-900 dark:text-gray-100 mb-4">Personal Information</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">Full Name</label>
                  <input
                    type="text"
                    value={tenantData.personalInfo.name}
                    className="mt-1 block w-full border border-gray-300 dark:border-gray-600 rounded-md px-3 py-2 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
                    readOnly
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">Email</label>
                  <input
                    type="email"
                    value={tenantData.personalInfo.email}
                    className="mt-1 block w-full border border-gray-300 dark:border-gray-600 rounded-md px-3 py-2 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
                    readOnly
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">Phone</label>
                  <input
                    type="tel"
                    value={tenantData.personalInfo.phone}
                    className="mt-1 block w-full border border-gray-300 dark:border-gray-600 rounded-md px-3 py-2 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">Emergency Contact</label>
                  <input
                    type="text"
                    value={tenantData.personalInfo.emergencyContact}
                    className="mt-1 block w-full border border-gray-300 dark:border-gray-600 rounded-md px-3 py-2 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
                  />
                </div>
              </div>
              <div className="mt-6">
                <button className="bg-blue-600 text-white px-6 py-2 rounded-md hover:bg-blue-700 transition-colors">
                  Save Changes
                </button>
              </div>
            </div>

            {/* Lease Information */}
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
              <h3 className="text-lg font-medium text-gray-900 dark:text-gray-100 mb-4">Lease Information</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">Property Address</label>
                  <p className="mt-1 text-gray-900 dark:text-gray-100">{tenantData.leaseInfo.propertyAddress}</p>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">Monthly Rent</label>
                  <p className="mt-1 text-gray-900 dark:text-gray-100">{formatCurrency(tenantData.leaseInfo.monthlyRent)}</p>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">Lease Start</label>
                  <p className="mt-1 text-gray-900 dark:text-gray-100">{tenantData.leaseInfo.leaseStart ? new Date(tenantData.leaseInfo.leaseStart).toLocaleDateString() : 'N/A'}</p>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">Lease End</label>
                  <p className="mt-1 text-gray-900 dark:text-gray-100">{tenantData.leaseInfo.leaseEnd ? new Date(tenantData.leaseInfo.leaseEnd).toLocaleDateString() : 'N/A'}</p>
                </div>
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  )
}

export default TenantPortal
