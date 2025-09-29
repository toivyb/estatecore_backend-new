import React, { useState, useEffect } from 'react';
import { 
  Bell, 
  X, 
  Check, 
  CheckCheck, 
  AlertCircle, 
  Info, 
  AlertTriangle, 
  Mail,
  MessageSquare,
  CreditCard,
  Wrench,
  Calendar,
  User,
  Home,
  Shield,
  Trash2,
  Filter,
  Search,
  Settings,
  Volume2,
  VolumeX,
  Clock
} from 'lucide-react';

const UnifiedNotificationCenter = ({ isOpen, onClose }) => {
  const [notifications, setNotifications] = useState([]);
  const [filteredNotifications, setFilteredNotifications] = useState([]);
  const [activeFilter, setActiveFilter] = useState('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [soundEnabled, setSoundEnabled] = useState(true);
  const [unreadCount, setUnreadCount] = useState(0);

  // Mock notification data
  useEffect(() => {
    const mockNotifications = [
      {
        id: 1,
        type: 'payment',
        title: 'Payment Received',
        message: 'Rent payment of $1,200 received from John Doe (Unit 205)',
        timestamp: new Date(Date.now() - 300000),
        priority: 'normal',
        isRead: false,
        actions: [
          { label: 'View Receipt', action: 'view_receipt' },
          { label: 'Send Confirmation', action: 'send_confirmation' }
        ],
        metadata: { tenant: 'John Doe', amount: '$1,200', unit: '205' }
      },
      {
        id: 2,
        type: 'maintenance',
        title: 'Urgent Maintenance Request',
        message: 'Water leak reported in Unit 105 - requires immediate attention',
        timestamp: new Date(Date.now() - 600000),
        priority: 'urgent',
        isRead: false,
        actions: [
          { label: 'Assign Technician', action: 'assign_tech' },
          { label: 'Contact Tenant', action: 'contact_tenant' }
        ],
        metadata: { unit: '105', category: 'plumbing', severity: 'urgent' }
      },
      {
        id: 3,
        type: 'security',
        title: 'Security Alert',
        message: 'Unauthorized access attempt detected at Building A entrance',
        timestamp: new Date(Date.now() - 900000),
        priority: 'high',
        isRead: true,
        actions: [
          { label: 'View Camera Feed', action: 'view_camera' },
          { label: 'Alert Security', action: 'alert_security' }
        ],
        metadata: { location: 'Building A', camera: 'CAM-001' }
      },
      {
        id: 4,
        type: 'lease',
        title: 'Lease Expiring Soon',
        message: 'Lease for Unit 307 expires in 30 days - renewal required',
        timestamp: new Date(Date.now() - 1800000),
        priority: 'normal',
        isRead: false,
        actions: [
          { label: 'Send Renewal Notice', action: 'send_renewal' },
          { label: 'Schedule Meeting', action: 'schedule_meeting' }
        ],
        metadata: { unit: '307', tenant: 'Sarah Smith', expiryDate: '2024-10-27' }
      },
      {
        id: 5,
        type: 'message',
        title: 'New Message',
        message: 'Message from tenant regarding parking space allocation',
        timestamp: new Date(Date.now() - 3600000),
        priority: 'normal',
        isRead: true,
        actions: [
          { label: 'Reply', action: 'reply' },
          { label: 'Forward', action: 'forward' }
        ],
        metadata: { sender: 'Mike Johnson', subject: 'Parking Space' }
      },
      {
        id: 6,
        type: 'system',
        title: 'System Update',
        message: 'EstateCore system will be updated tonight at 2:00 AM',
        timestamp: new Date(Date.now() - 7200000),
        priority: 'low',
        isRead: true,
        actions: [
          { label: 'View Details', action: 'view_details' }
        ],
        metadata: { version: '4.1.2', downtime: '30 minutes' }
      }
    ];

    setNotifications(mockNotifications);
    setFilteredNotifications(mockNotifications);
    setUnreadCount(mockNotifications.filter(n => !n.isRead).length);
  }, []);

  // Filter notifications based on active filter and search query
  useEffect(() => {
    let filtered = notifications;

    if (activeFilter !== 'all') {
      filtered = filtered.filter(notification => {
        if (activeFilter === 'unread') return !notification.isRead;
        if (activeFilter === 'urgent') return notification.priority === 'urgent';
        if (activeFilter === 'high') return notification.priority === 'high';
        return notification.type === activeFilter;
      });
    }

    if (searchQuery) {
      filtered = filtered.filter(notification =>
        notification.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
        notification.message.toLowerCase().includes(searchQuery.toLowerCase())
      );
    }

    setFilteredNotifications(filtered);
  }, [notifications, activeFilter, searchQuery]);

  const getNotificationIcon = (type, priority) => {
    const iconProps = {
      className: `w-5 h-5 ${priority === 'urgent' ? 'text-red-500' : 
                             priority === 'high' ? 'text-orange-500' : 
                             'text-blue-500'}`
    };

    switch (type) {
      case 'payment': return <CreditCard {...iconProps} />;
      case 'maintenance': return <Wrench {...iconProps} />;
      case 'security': return <Shield {...iconProps} />;
      case 'lease': return <Home {...iconProps} />;
      case 'message': return <MessageSquare {...iconProps} />;
      case 'system': return <Settings {...iconProps} />;
      default: return <Bell {...iconProps} />;
    }
  };

  const getPriorityColor = (priority) => {
    switch (priority) {
      case 'urgent': return 'border-l-red-500 bg-red-50 dark:bg-red-900/20';
      case 'high': return 'border-l-orange-500 bg-orange-50 dark:bg-orange-900/20';
      case 'normal': return 'border-l-blue-500 bg-blue-50 dark:bg-blue-900/20';
      case 'low': return 'border-l-gray-500 bg-gray-50 dark:bg-gray-900/20';
      default: return 'border-l-gray-500 bg-gray-50 dark:bg-gray-900/20';
    }
  };

  const formatTimestamp = (timestamp) => {
    const now = new Date();
    const diff = now - timestamp;
    const minutes = Math.floor(diff / 60000);
    const hours = Math.floor(diff / 3600000);
    const days = Math.floor(diff / 86400000);

    if (minutes < 1) return 'Just now';
    if (minutes < 60) return `${minutes}m ago`;
    if (hours < 24) return `${hours}h ago`;
    return `${days}d ago`;
  };

  const markAsRead = (notificationId) => {
    setNotifications(prev => 
      prev.map(notification => 
        notification.id === notificationId 
          ? { ...notification, isRead: true }
          : notification
      )
    );
    setUnreadCount(prev => Math.max(0, prev - 1));
  };

  const markAllAsRead = () => {
    setNotifications(prev => 
      prev.map(notification => ({ ...notification, isRead: true }))
    );
    setUnreadCount(0);
  };

  const deleteNotification = (notificationId) => {
    setNotifications(prev => 
      prev.filter(notification => notification.id !== notificationId)
    );
  };

  const handleNotificationAction = (notificationId, action) => {
    console.log(`Executing action ${action} for notification ${notificationId}`);
    // Implement specific action handlers here
    markAsRead(notificationId);
  };

  const filterOptions = [
    { id: 'all', label: 'All', icon: Bell },
    { id: 'unread', label: 'Unread', icon: Mail },
    { id: 'urgent', label: 'Urgent', icon: AlertTriangle },
    { id: 'high', label: 'High Priority', icon: AlertCircle },
    { id: 'payment', label: 'Payments', icon: CreditCard },
    { id: 'maintenance', label: 'Maintenance', icon: Wrench },
    { id: 'security', label: 'Security', icon: Shield },
    { id: 'lease', label: 'Leases', icon: Home },
    { id: 'message', label: 'Messages', icon: MessageSquare },
    { id: 'system', label: 'System', icon: Settings }
  ];

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 overflow-hidden">
      <div className="absolute inset-0 bg-black bg-opacity-50" onClick={onClose}></div>
      
      <div className="absolute right-0 top-0 h-full w-full max-w-2xl bg-white dark:bg-gray-800 shadow-xl">
        <div className="flex flex-col h-full">
          {/* Header */}
          <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-3">
                <Bell className="w-6 h-6 text-gray-700 dark:text-gray-300" />
                <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
                  Notifications
                </h2>
                {unreadCount > 0 && (
                  <span className="bg-red-500 text-white text-xs font-medium px-2 py-1 rounded-full">
                    {unreadCount}
                  </span>
                )}
              </div>
              
              <div className="flex items-center space-x-2">
                <button
                  onClick={() => setSoundEnabled(!soundEnabled)}
                  className="p-2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700"
                >
                  {soundEnabled ? <Volume2 className="w-5 h-5" /> : <VolumeX className="w-5 h-5" />}
                </button>
                
                <button
                  onClick={markAllAsRead}
                  className="p-2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700"
                  title="Mark all as read"
                >
                  <CheckCheck className="w-5 h-5" />
                </button>
                
                <button
                  onClick={onClose}
                  className="p-2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>
            </div>
            
            {/* Search and Filters */}
            <div className="mt-4 space-y-3">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
                <input
                  type="text"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  placeholder="Search notifications..."
                  className="w-full pl-10 pr-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent dark:bg-gray-700 dark:text-white"
                />
              </div>
              
              <div className="flex flex-wrap gap-2">
                {filterOptions.map(option => {
                  const Icon = option.icon;
                  return (
                    <button
                      key={option.id}
                      onClick={() => setActiveFilter(option.id)}
                      className={`flex items-center px-3 py-1 rounded-full text-sm transition-colors ${
                        activeFilter === option.id
                          ? 'bg-blue-600 text-white'
                          : 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600'
                      }`}
                    >
                      <Icon className="w-3 h-3 mr-1" />
                      {option.label}
                    </button>
                  );
                })}
              </div>
            </div>
          </div>

          {/* Notifications List */}
          <div className="flex-1 overflow-y-auto">
            {filteredNotifications.length === 0 ? (
              <div className="flex flex-col items-center justify-center h-64 text-gray-500 dark:text-gray-400">
                <Bell className="w-12 h-12 mb-4" />
                <p className="text-lg font-medium">No notifications</p>
                <p className="text-sm">You're all caught up!</p>
              </div>
            ) : (
              <div className="divide-y divide-gray-200 dark:divide-gray-700">
                {filteredNotifications.map(notification => (
                  <div
                    key={notification.id}
                    className={`px-6 py-4 border-l-4 ${getPriorityColor(notification.priority)} ${
                      !notification.isRead ? 'bg-opacity-100' : 'bg-opacity-50'
                    }`}
                  >
                    <div className="flex items-start space-x-3">
                      <div className="flex-shrink-0 pt-1">
                        {getNotificationIcon(notification.type, notification.priority)}
                      </div>
                      
                      <div className="flex-1 min-w-0">
                        <div className="flex items-start justify-between">
                          <div className="flex-1">
                            <h3 className={`text-sm font-medium ${
                              !notification.isRead 
                                ? 'text-gray-900 dark:text-white' 
                                : 'text-gray-700 dark:text-gray-300'
                            }`}>
                              {notification.title}
                            </h3>
                            <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                              {notification.message}
                            </p>
                            
                            {/* Metadata */}
                            {notification.metadata && (
                              <div className="flex flex-wrap gap-2 mt-2">
                                {Object.entries(notification.metadata).map(([key, value]) => (
                                  <span
                                    key={key}
                                    className="inline-flex items-center px-2 py-1 rounded-full text-xs bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300"
                                  >
                                    {key}: {value}
                                  </span>
                                ))}
                              </div>
                            )}
                            
                            {/* Actions */}
                            {notification.actions && (
                              <div className="flex flex-wrap gap-2 mt-3">
                                {notification.actions.map((action, index) => (
                                  <button
                                    key={index}
                                    onClick={() => handleNotificationAction(notification.id, action.action)}
                                    className="px-3 py-1 text-xs bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
                                  >
                                    {action.label}
                                  </button>
                                ))}
                              </div>
                            )}
                          </div>
                          
                          <div className="flex items-center space-x-2 ml-4">
                            <div className="text-xs text-gray-500 dark:text-gray-400 flex items-center">
                              <Clock className="w-3 h-3 mr-1" />
                              {formatTimestamp(notification.timestamp)}
                            </div>
                            
                            {!notification.isRead && (
                              <button
                                onClick={() => markAsRead(notification.id)}
                                className="p-1 text-gray-400 hover:text-blue-600 dark:hover:text-blue-400 rounded"
                                title="Mark as read"
                              >
                                <Check className="w-4 h-4" />
                              </button>
                            )}
                            
                            <button
                              onClick={() => deleteNotification(notification.id)}
                              className="p-1 text-gray-400 hover:text-red-600 dark:hover:text-red-400 rounded"
                              title="Delete notification"
                            >
                              <Trash2 className="w-4 h-4" />
                            </button>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Footer */}
          <div className="px-6 py-4 border-t border-gray-200 dark:border-gray-700">
            <div className="flex items-center justify-between text-sm text-gray-600 dark:text-gray-400">
              <span>{filteredNotifications.length} notifications</span>
              <button className="text-blue-600 dark:text-blue-400 hover:underline">
                Notification Settings
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default UnifiedNotificationCenter;