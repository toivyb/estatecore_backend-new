import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';

export default function WorkOrderDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [workOrder, setWorkOrder] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchWorkOrderDetail();
  }, [id]);

  const fetchWorkOrderDetail = async () => {
    try {
      setLoading(true);
      // Mock work order data
      const mockWorkOrder = {
        id: id,
        title: 'HVAC System Maintenance',
        description: 'Annual maintenance check for HVAC system in Building A',
        status: 'in_progress',
        priority: 'medium',
        property: 'Sunset Apartments - Building A',
        unit: 'Unit 205',
        category: 'HVAC',
        assignedTo: 'John Smith',
        requester: 'Jane Doe (Tenant)',
        createdAt: '2024-09-25T10:30:00Z',
        updatedAt: '2024-09-27T14:22:00Z',
        dueDate: '2024-09-30T17:00:00Z',
        estimatedCost: 250,
        actualCost: null,
        notes: [
          {
            id: 1,
            author: 'John Smith',
            timestamp: '2024-09-26T09:15:00Z',
            content: 'Initial inspection completed. Filter needs replacement.'
          },
          {
            id: 2,
            author: 'System',
            timestamp: '2024-09-27T14:22:00Z',
            content: 'Status updated to In Progress'
          }
        ]
      };
      
      setWorkOrder(mockWorkOrder);
    } catch (error) {
      console.error('Error fetching work order:', error);
    } finally {
      setLoading(false);
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'open': return 'bg-blue-100 text-blue-800';
      case 'in_progress': return 'bg-yellow-100 text-yellow-800';
      case 'completed': return 'bg-green-100 text-green-800';
      case 'cancelled': return 'bg-red-100 text-red-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const getPriorityColor = (priority) => {
    switch (priority) {
      case 'low': return 'bg-green-100 text-green-800';
      case 'medium': return 'bg-yellow-100 text-yellow-800';
      case 'high': return 'bg-orange-100 text-orange-800';
      case 'urgent': return 'bg-red-100 text-red-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (!workOrder) {
    return (
      <div className="text-center py-12">
        <div className="text-gray-500">Work order not found</div>
        <button 
          onClick={() => navigate('/maintenance')}
          className="mt-4 bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700"
        >
          Back to Maintenance
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-white p-6 rounded-lg shadow">
        <div className="flex justify-between items-start mb-4">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Work Order #{workOrder.id}</h1>
            <p className="text-gray-600">{workOrder.title}</p>
          </div>
          <button 
            onClick={() => navigate('/maintenance')}
            className="bg-gray-600 text-white px-4 py-2 rounded hover:bg-gray-700"
          >
            🔙 Back
          </button>
        </div>

        <div className="flex space-x-4">
          <span className={`px-3 py-1 rounded-full text-sm font-medium ${getStatusColor(workOrder.status)}`}>
            {workOrder.status.replace('_', ' ')}
          </span>
          <span className={`px-3 py-1 rounded-full text-sm font-medium ${getPriorityColor(workOrder.priority)}`}>
            {workOrder.priority} priority
          </span>
        </div>
      </div>

      {/* Details Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Work Order Information */}
        <div className="bg-white p-6 rounded-lg shadow">
          <h3 className="text-lg font-semibold mb-4">📋 Work Order Details</h3>
          
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700">Description</label>
              <p className="mt-1 text-gray-900">{workOrder.description}</p>
            </div>
            
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700">Property</label>
                <p className="mt-1 text-gray-900">{workOrder.property}</p>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">Unit</label>
                <p className="mt-1 text-gray-900">{workOrder.unit}</p>
              </div>
            </div>
            
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700">Category</label>
                <p className="mt-1 text-gray-900">{workOrder.category}</p>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">Assigned To</label>
                <p className="mt-1 text-gray-900">{workOrder.assignedTo}</p>
              </div>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700">Requested By</label>
              <p className="mt-1 text-gray-900">{workOrder.requester}</p>
            </div>
          </div>
        </div>

        {/* Timeline & Costs */}
        <div className="bg-white p-6 rounded-lg shadow">
          <h3 className="text-lg font-semibold mb-4">⏰ Timeline & Costs</h3>
          
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700">Created</label>
              <p className="mt-1 text-gray-900">{formatDate(workOrder.createdAt)}</p>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700">Last Updated</label>
              <p className="mt-1 text-gray-900">{formatDate(workOrder.updatedAt)}</p>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700">Due Date</label>
              <p className="mt-1 text-gray-900">{formatDate(workOrder.dueDate)}</p>
            </div>
            
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700">Estimated Cost</label>
                <p className="mt-1 text-gray-900">${workOrder.estimatedCost}</p>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">Actual Cost</label>
                <p className="mt-1 text-gray-900">{workOrder.actualCost ? `$${workOrder.actualCost}` : 'TBD'}</p>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Notes & Updates */}
      <div className="bg-white p-6 rounded-lg shadow">
        <h3 className="text-lg font-semibold mb-4">📝 Notes & Updates</h3>
        
        <div className="space-y-4">
          {workOrder.notes.map(note => (
            <div key={note.id} className="border-l-4 border-blue-500 pl-4 py-2">
              <div className="flex justify-between items-start">
                <div className="font-medium text-gray-900">{note.author}</div>
                <div className="text-sm text-gray-500">{formatDate(note.timestamp)}</div>
              </div>
              <p className="mt-1 text-gray-700">{note.content}</p>
            </div>
          ))}
        </div>
        
        <div className="mt-6 pt-4 border-t">
          <textarea
            placeholder="Add a note..."
            className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            rows="3"
          />
          <button className="mt-2 bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700">
            ➕ Add Note
          </button>
        </div>
      </div>

      {/* Actions */}
      <div className="bg-white p-6 rounded-lg shadow">
        <h3 className="text-lg font-semibold mb-4">⚡ Actions</h3>
        
        <div className="flex flex-wrap gap-4">
          <button className="bg-green-600 text-white px-4 py-2 rounded hover:bg-green-700">
            ✅ Mark Complete
          </button>
          <button className="bg-yellow-600 text-white px-4 py-2 rounded hover:bg-yellow-700">
            ⏸️ Put on Hold
          </button>
          <button className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700">
            ✏️ Edit Details
          </button>
          <button className="bg-purple-600 text-white px-4 py-2 rounded hover:bg-purple-700">
            👤 Reassign
          </button>
          <button className="bg-red-600 text-white px-4 py-2 rounded hover:bg-red-700">
            ❌ Cancel
          </button>
        </div>
      </div>
    </div>
  );
}