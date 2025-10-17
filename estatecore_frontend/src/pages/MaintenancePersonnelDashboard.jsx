import React, { useState, useEffect } from 'react';
import api from '../api';

const MaintenancePersonnelDashboard = () => {
  const [workOrders, setWorkOrders] = useState([]);
  const [myStats, setMyStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [selectedOrder, setSelectedOrder] = useState(null);
  const [activeFilter, setActiveFilter] = useState('assigned');

  useEffect(() => {
    fetchWorkOrders();
    fetchMyStats();
  }, []);

  const fetchWorkOrders = async () => {
    try {
      const response = await api.get('/api/portal/maintenance/dashboard');
      if (response.success) {
        setWorkOrders(response.data.work_orders || []);
        setMyStats(response.data.stats);
      } else {
        console.error('Error fetching maintenance dashboard:', response.error);
        // Fallback to mock data
        setWorkOrders([
        {
          id: 1,
          title: 'HVAC System Repair',
          description: 'Air conditioning unit not cooling properly in Unit 5B',
          property: 'Sunset Apartments',
          unit: '5B',
          tenant: 'Jane Doe',
          priority: 'high',
          status: 'assigned',
          assigned_date: '2025-01-01',
          due_date: '2025-01-03',
          estimated_hours: 3,
          category: 'hvac'
        },
        {
          id: 2,
          title: 'Kitchen Faucet Replacement',
          description: 'Replace leaking kitchen faucet',
          property: 'Oak Ridge Complex',
          unit: '2A',
          tenant: 'John Smith',
          priority: 'medium',
          status: 'in_progress',
          assigned_date: '2024-12-30',
          due_date: '2025-01-02',
          estimated_hours: 2,
          category: 'plumbing'
        },
        {
          id: 3,
          title: 'Window Lock Repair',
          description: 'Bedroom window lock is broken',
          property: 'Green Valley Homes',
          unit: '12C',
          tenant: 'Mike Johnson',
          priority: 'low',
          status: 'completed',
          assigned_date: '2024-12-28',
          completed_date: '2024-12-29',
          estimated_hours: 1,
          actual_hours: 1.5,
          category: 'general'
        },
        {
          id: 4,
          title: 'Electrical Outlet Installation',
          description: 'Install additional outlet in living room',
          property: 'Sunset Apartments',
          unit: '7D',
          tenant: 'Sarah Wilson',
          priority: 'medium',
          status: 'scheduled',
          assigned_date: '2025-01-02',
          due_date: '2025-01-04',
          estimated_hours: 4,
          category: 'electrical'
        }
      ]);
      }
    } catch (error) {
      console.error('Error fetching work orders:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchMyStats = async () => {
    try {
      // Stats are now fetched with work orders in fetchWorkOrders
      if (!myStats) {
        // Fallback mock stats if not already set
        setMyStats({
          total_assigned: 15,
          completed_this_week: 8,
          pending_orders: 4,
          avg_completion_time: 2.3,
          rating: 4.8,
          specialties: ['HVAC', 'Plumbing', 'Electrical']
        });
      }
    } catch (error) {
      console.error('Error fetching stats:', error);
    }
  };

  const updateWorkOrderStatus = async (orderId, newStatus, notes = '') => {
    try {
      const response = await api.put(`/api/workorders/${orderId}`, {
        status: newStatus,
        notes: notes,
        completed_date: newStatus === 'completed' ? new Date().toISOString() : null
      });
      
      if (response.success) {
        fetchWorkOrders();
        setSelectedOrder(null);
      }
    } catch (error) {
      console.error('Error updating work order:', error);
    }
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: 'numeric',
      minute: '2-digit'
    });
  };

  const getPriorityColor = (priority) => {
    switch (priority) {
      case 'high': return 'bg-red-100 text-red-800 border-red-200';
      case 'medium': return 'bg-yellow-100 text-yellow-800 border-yellow-200';
      case 'low': return 'bg-green-100 text-green-800 border-green-200';
      default: return 'bg-gray-100 text-gray-800 border-gray-200';
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'assigned': return 'bg-blue-100 text-blue-800';
      case 'in_progress': return 'bg-orange-100 text-orange-800';
      case 'completed': return 'bg-green-100 text-green-800';
      case 'scheduled': return 'bg-purple-100 text-purple-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const getCategoryIcon = (category) => {
    switch (category) {
      case 'hvac': return '❄️';
      case 'plumbing': return '🔧';
      case 'electrical': return '⚡';
      case 'general': return '🔨';
      default: return '🛠️';
    }
  };

  const filteredWorkOrders = workOrders.filter(order => {
    switch (activeFilter) {
      case 'assigned': return order.status === 'assigned';
      case 'in_progress': return order.status === 'in_progress';
      case 'completed': return order.status === 'completed';
      case 'all': return true;
      default: return order.status === 'assigned';
    }
  });

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        <span className="ml-2">Loading maintenance dashboard...</span>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="py-6">
            <h1 className="text-3xl font-bold text-gray-900">Maintenance Dashboard</h1>
            <p className="text-gray-600">Your assigned work orders and maintenance tasks</p>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Stats Cards */}
        {myStats && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
            <div className="bg-white rounded-lg shadow p-6 border-l-4 border-blue-500">
              <h3 className="text-sm font-medium text-gray-500">Assigned Orders</h3>
              <p className="text-3xl font-bold text-blue-600">{myStats.total_assigned}</p>
              <p className="text-sm text-gray-600">Total active assignments</p>
            </div>
            
            <div className="bg-white rounded-lg shadow p-6 border-l-4 border-green-500">
              <h3 className="text-sm font-medium text-gray-500">Completed This Week</h3>
              <p className="text-3xl font-bold text-green-600">{myStats.completed_this_week}</p>
              <p className="text-sm text-gray-600">Work orders finished</p>
            </div>
            
            <div className="bg-white rounded-lg shadow p-6 border-l-4 border-orange-500">
              <h3 className="text-sm font-medium text-gray-500">Avg. Completion Time</h3>
              <p className="text-3xl font-bold text-orange-600">{myStats.avg_completion_time}h</p>
              <p className="text-sm text-gray-600">Hours per task</p>
            </div>
            
            <div className="bg-white rounded-lg shadow p-6 border-l-4 border-purple-500">
              <h3 className="text-sm font-medium text-gray-500">Performance Rating</h3>
              <p className="text-3xl font-bold text-purple-600">{myStats.rating}/5</p>
              <p className="text-sm text-gray-600">⭐ Tenant satisfaction</p>
            </div>
          </div>
        )}

        {/* Filter Tabs */}
        <div className="bg-white rounded-lg shadow mb-6">
          <div className="border-b border-gray-200">
            <nav className="flex space-x-8 px-6">
              {[
                { id: 'assigned', label: 'Assigned', count: workOrders.filter(o => o.status === 'assigned').length },
                { id: 'in_progress', label: 'In Progress', count: workOrders.filter(o => o.status === 'in_progress').length },
                { id: 'completed', label: 'Completed', count: workOrders.filter(o => o.status === 'completed').length },
                { id: 'all', label: 'All Orders', count: workOrders.length }
              ].map(tab => (
                <button
                  key={tab.id}
                  onClick={() => setActiveFilter(tab.id)}
                  className={`flex items-center py-4 px-1 border-b-2 font-medium text-sm ${
                    activeFilter === tab.id
                      ? 'border-blue-500 text-blue-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                  }`}
                >
                  {tab.label}
                  <span className="ml-2 bg-gray-100 text-gray-600 py-0.5 px-2 rounded-full text-xs">
                    {tab.count}
                  </span>
                </button>
              ))}
            </nav>
          </div>
        </div>

        {/* Work Orders Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredWorkOrders.map((order) => (
            <div key={order.id} className="bg-white rounded-lg shadow hover:shadow-md transition-shadow">
              <div className="p-6">
                <div className="flex items-start justify-between mb-4">
                  <div className="flex items-center space-x-2">
                    <span className="text-2xl">{getCategoryIcon(order.category)}</span>
                    <div>
                      <h3 className="font-semibold text-gray-900">{order.title}</h3>
                      <p className="text-sm text-gray-600">{order.property} - Unit {order.unit}</p>
                    </div>
                  </div>
                  <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full border ${getPriorityColor(order.priority)}`}>
                    {order.priority}
                  </span>
                </div>
                
                <p className="text-sm text-gray-700 mb-4">{order.description}</p>
                
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span className="text-gray-500">Tenant:</span>
                    <span className="font-medium">{order.tenant}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-500">Assigned:</span>
                    <span className="font-medium">{formatDate(order.assigned_date)}</span>
                  </div>
                  {order.due_date && (
                    <div className="flex justify-between">
                      <span className="text-gray-500">Due:</span>
                      <span className="font-medium">{formatDate(order.due_date)}</span>
                    </div>
                  )}
                  <div className="flex justify-between">
                    <span className="text-gray-500">Est. Time:</span>
                    <span className="font-medium">{order.estimated_hours}h</span>
                  </div>
                </div>
                
                <div className="mt-4 flex items-center justify-between">
                  <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getStatusColor(order.status)}`}>
                    {order.status.replace('_', ' ')}
                  </span>
                  
                  <div className="flex space-x-2">
                    {order.status === 'assigned' && (
                      <button
                        onClick={() => updateWorkOrderStatus(order.id, 'in_progress')}
                        className="bg-blue-600 text-white px-3 py-1 rounded text-sm hover:bg-blue-700"
                      >
                        Start
                      </button>
                    )}
                    {order.status === 'in_progress' && (
                      <button
                        onClick={() => updateWorkOrderStatus(order.id, 'completed')}
                        className="bg-green-600 text-white px-3 py-1 rounded text-sm hover:bg-green-700"
                      >
                        Complete
                      </button>
                    )}
                    <button
                      onClick={() => setSelectedOrder(order)}
                      className="bg-gray-100 text-gray-700 px-3 py-1 rounded text-sm hover:bg-gray-200"
                    >
                      Details
                    </button>
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>

        {filteredWorkOrders.length === 0 && (
          <div className="text-center py-12">
            <div className="text-6xl mb-4">🔧</div>
            <h3 className="text-lg font-medium text-gray-900 mb-2">No work orders found</h3>
            <p className="text-gray-600">
              {activeFilter === 'assigned' && "You don't have any assigned work orders at the moment."}
              {activeFilter === 'in_progress' && "No work orders are currently in progress."}
              {activeFilter === 'completed' && "No completed work orders to show."}
            </p>
          </div>
        )}

        {/* Specialties */}
        {myStats && (
          <div className="mt-8 bg-white rounded-lg shadow p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Your Specialties</h3>
            <div className="flex flex-wrap gap-2">
              {myStats.specialties.map((specialty, index) => (
                <span key={index} className="inline-flex px-3 py-1 text-sm font-medium rounded-full bg-blue-100 text-blue-800">
                  {specialty}
                </span>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Work Order Details Modal */}
      {selectedOrder && (
        <div className="fixed inset-0 z-50 overflow-y-auto">
          <div className="flex items-center justify-center min-h-screen px-4">
            <div className="fixed inset-0 bg-black opacity-50" onClick={() => setSelectedOrder(null)}></div>
            <div className="relative bg-white rounded-lg shadow-xl max-w-2xl w-full">
              <div className="px-6 py-4 border-b border-gray-200">
                <div className="flex items-center justify-between">
                  <h3 className="text-lg font-semibold text-gray-900">Work Order Details</h3>
                  <button
                    onClick={() => setSelectedOrder(null)}
                    className="text-gray-400 hover:text-gray-600"
                  >
                    ✕
                  </button>
                </div>
              </div>
              
              <div className="px-6 py-4 space-y-4">
                <div>
                  <h4 className="font-medium text-gray-900">{selectedOrder.title}</h4>
                  <p className="text-sm text-gray-600 mt-1">{selectedOrder.description}</p>
                </div>
                
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="text-sm text-gray-500">Property</label>
                    <p className="font-medium text-gray-900">{selectedOrder.property}</p>
                  </div>
                  <div>
                    <label className="text-sm text-gray-500">Unit</label>
                    <p className="font-medium text-gray-900">{selectedOrder.unit}</p>
                  </div>
                  <div>
                    <label className="text-sm text-gray-500">Tenant</label>
                    <p className="font-medium text-gray-900">{selectedOrder.tenant}</p>
                  </div>
                  <div>
                    <label className="text-sm text-gray-500">Priority</label>
                    <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getPriorityColor(selectedOrder.priority)}`}>
                      {selectedOrder.priority}
                    </span>
                  </div>
                </div>
                
                <div className="border-t pt-4">
                  <h5 className="font-medium text-gray-900 mb-2">Contact Information</h5>
                  <p className="text-sm text-gray-600">
                    For emergencies or questions about this work order, contact the property manager at (555) 123-4567.
                  </p>
                </div>
              </div>
              
              <div className="px-6 py-4 border-t border-gray-200 flex justify-end space-x-3">
                <button
                  onClick={() => setSelectedOrder(null)}
                  className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200"
                >
                  Close
                </button>
                {selectedOrder.status === 'assigned' && (
                  <button
                    onClick={() => updateWorkOrderStatus(selectedOrder.id, 'in_progress')}
                    className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
                  >
                    Start Work
                  </button>
                )}
                {selectedOrder.status === 'in_progress' && (
                  <button
                    onClick={() => updateWorkOrderStatus(selectedOrder.id, 'completed')}
                    className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700"
                  >
                    Mark Complete
                  </button>
                )}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default MaintenancePersonnelDashboard;