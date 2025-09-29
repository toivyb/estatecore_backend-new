import React, { useState, useEffect } from 'react';

const CollaborationDashboard = () => {
  const [activeTab, setActiveTab] = useState('overview');
  const [notifications, setNotifications] = useState([]);
  const [teamMembers, setTeamMembers] = useState([]);
  const [recentMessages, setRecentMessages] = useState([]);
  const [upcomingMeetings, setUpcomingMeetings] = useState([]);
  const [sharedDocuments, setSharedDocuments] = useState([]);
  const [projects, setProjects] = useState([]);

  useEffect(() => {
    fetchCollaborationData();
  }, []);

  const fetchCollaborationData = async () => {
    try {
      // Mock data - replace with actual API calls
      setTeamMembers([
        { id: 1, name: 'John Smith', role: 'Property Manager', avatar: '/api/placeholder/40/40', status: 'online', lastSeen: new Date() },
        { id: 2, name: 'Sarah Johnson', role: 'Maintenance Lead', avatar: '/api/placeholder/40/40', status: 'busy', lastSeen: new Date(Date.now() - 30000) },
        { id: 3, name: 'Mike Wilson', role: 'Accountant', avatar: '/api/placeholder/40/40', status: 'offline', lastSeen: new Date(Date.now() - 3600000) },
        { id: 4, name: 'Emily Davis', role: 'Leasing Agent', avatar: '/api/placeholder/40/40', status: 'online', lastSeen: new Date() }
      ]);

      setRecentMessages([
        { id: 1, sender: 'John Smith', message: 'Unit 205 inspection completed', timestamp: new Date(Date.now() - 600000), read: false },
        { id: 2, sender: 'Sarah Johnson', message: 'HVAC maintenance scheduled for Building A', timestamp: new Date(Date.now() - 1800000), read: true },
        { id: 3, sender: 'Mike Wilson', message: 'Monthly financial report ready for review', timestamp: new Date(Date.now() - 3600000), read: false }
      ]);

      setUpcomingMeetings([
        { id: 1, title: 'Weekly Team Standup', time: '10:00 AM', attendees: 4, type: 'video', link: '/meeting/123' },
        { id: 2, title: 'Property Inspection Review', time: '2:00 PM', attendees: 3, type: 'video', link: '/meeting/456' },
        { id: 3, title: 'Budget Planning Session', time: '4:00 PM', attendees: 5, type: 'video', link: '/meeting/789' }
      ]);

      setSharedDocuments([
        { id: 1, name: 'Q3 Property Report.pdf', sharedBy: 'John Smith', sharedAt: new Date(Date.now() - 86400000), size: '2.4 MB' },
        { id: 2, name: 'Maintenance Protocol.docx', sharedBy: 'Sarah Johnson', sharedAt: new Date(Date.now() - 172800000), size: '1.1 MB' },
        { id: 3, name: 'Budget Proposal 2024.xlsx', sharedBy: 'Mike Wilson', sharedAt: new Date(Date.now() - 259200000), size: '890 KB' }
      ]);

      setProjects([
        { id: 1, name: 'Building A Renovation', progress: 75, members: 6, dueDate: '2024-10-15', status: 'active' },
        { id: 2, name: 'Tenant Onboarding System', progress: 45, members: 4, dueDate: '2024-11-01', status: 'active' },
        { id: 3, name: 'Energy Efficiency Upgrade', progress: 90, members: 3, dueDate: '2024-09-30', status: 'review' }
      ]);

      setNotifications([
        { id: 1, type: 'message', text: 'New message from John Smith', time: '5 min ago', read: false },
        { id: 2, type: 'meeting', text: 'Meeting starting in 15 minutes', time: '10 min ago', read: false },
        { id: 3, type: 'document', text: 'Document shared: Budget Report', time: '1 hour ago', read: true }
      ]);

    } catch (error) {
      console.error('Error fetching collaboration data:', error);
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'online': return 'bg-green-500';
      case 'busy': return 'bg-yellow-500';
      case 'offline': return 'bg-gray-500';
      default: return 'bg-gray-500';
    }
  };

  const formatTime = (date) => {
    return new Intl.DateTimeFormat('en-US', {
      hour: 'numeric',
      minute: '2-digit',
      hour12: true
    }).format(date);
  };

  const formatDate = (date) => {
    return new Intl.DateTimeFormat('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric'
    }).format(date);
  };

  const TabButton = ({ id, label, icon: Icon, active, onClick }) => (
    <button
      onClick={() => onClick(id)}
      className={`flex items-center px-4 py-2 rounded-lg transition-colors ${
        active 
          ? 'bg-blue-600 text-white' 
          : 'text-gray-600 hover:bg-gray-100 dark:text-gray-300 dark:hover:bg-gray-700'
      }`}
    >
      <Icon className="w-4 h-4 mr-2" />
      {label}
    </button>
  );

  const StatCard = ({ title, value, icon: Icon, color = 'blue' }) => (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm font-medium text-gray-600 dark:text-gray-400">{title}</p>
          <p className="text-2xl font-bold text-gray-900 dark:text-white">{value}</p>
        </div>
        <div className={`p-3 rounded-full bg-${color}-100 dark:bg-${color}-900`}>
          <Icon className={`w-6 h-6 text-${color}-600 dark:text-${color}-400`} />
        </div>
      </div>
    </div>
  );

  const OverviewTab = () => (
    <div className="space-y-6">
      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatCard title="Team Members" value={teamMembers.length} icon={Users} color="blue" />
        <StatCard title="Active Projects" value={projects.filter(p => p.status === 'active').length} icon={FileText} color="green" />
        <StatCard title="Unread Messages" value={recentMessages.filter(m => !m.read).length} icon={MessageSquare} color="yellow" />
        <StatCard title="Today's Meetings" value={upcomingMeetings.length} icon={Video} color="purple" />
      </div>

      {/* Quick Actions */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Quick Actions</h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <button className="flex flex-col items-center p-4 border border-gray-200 dark:border-gray-700 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors">
            <Video className="w-8 h-8 text-blue-600 mb-2" />
            <span className="text-sm font-medium">Start Meeting</span>
          </button>
          <button className="flex flex-col items-center p-4 border border-gray-200 dark:border-gray-700 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors">
            <MessageSquare className="w-8 h-8 text-green-600 mb-2" />
            <span className="text-sm font-medium">Send Message</span>
          </button>
          <button className="flex flex-col items-center p-4 border border-gray-200 dark:border-gray-700 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors">
            <FileText className="w-8 h-8 text-purple-600 mb-2" />
            <span className="text-sm font-medium">Share Document</span>
          </button>
          <button className="flex flex-col items-center p-4 border border-gray-200 dark:border-gray-700 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors">
            <UserPlus className="w-8 h-8 text-orange-600 mb-2" />
            <span className="text-sm font-medium">Invite Member</span>
          </button>
        </div>
      </div>

      {/* Recent Activity */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Recent Messages</h3>
          <div className="space-y-3">
            {recentMessages.slice(0, 5).map(message => (
              <div key={message.id} className="flex items-start space-x-3 p-3 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700">
                <div className="flex-shrink-0">
                  <div className="w-8 h-8 bg-blue-100 dark:bg-blue-900 rounded-full flex items-center justify-center">
                    <MessageCircle className="w-4 h-4 text-blue-600 dark:text-blue-400" />
                  </div>
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-gray-900 dark:text-white">{message.sender}</p>
                  <p className="text-sm text-gray-600 dark:text-gray-400 truncate">{message.message}</p>
                  <p className="text-xs text-gray-500 dark:text-gray-500">{formatTime(message.timestamp)}</p>
                </div>
                {!message.read && (
                  <div className="w-2 h-2 bg-blue-600 rounded-full"></div>
                )}
              </div>
            ))}
          </div>
        </div>

        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Upcoming Meetings</h3>
          <div className="space-y-3">
            {upcomingMeetings.map(meeting => (
              <div key={meeting.id} className="flex items-center justify-between p-3 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700">
                <div className="flex items-center space-x-3">
                  <div className="w-8 h-8 bg-purple-100 dark:bg-purple-900 rounded-full flex items-center justify-center">
                    <VideoIcon className="w-4 h-4 text-purple-600 dark:text-purple-400" />
                  </div>
                  <div>
                    <p className="text-sm font-medium text-gray-900 dark:text-white">{meeting.title}</p>
                    <p className="text-xs text-gray-600 dark:text-gray-400">{meeting.time} • {meeting.attendees} attendees</p>
                  </div>
                </div>
                <button className="px-3 py-1 bg-blue-600 text-white text-xs rounded-lg hover:bg-blue-700">
                  Join
                </button>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );

  const TeamTab = () => (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-bold text-gray-900 dark:text-white">Team Members</h2>
        <button className="flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700">
          <UserPlus className="w-4 h-4 mr-2" />
          Invite Member
        </button>
      </div>

      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md">
        <div className="p-6 border-b border-gray-200 dark:border-gray-700">
          <div className="flex items-center space-x-4">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
              <input
                type="text"
                placeholder="Search team members..."
                className="w-full pl-10 pr-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent dark:bg-gray-700 dark:text-white"
              />
            </div>
            <button className="flex items-center px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700">
              <Filter className="w-4 h-4 mr-2" />
              Filter
            </button>
          </div>
        </div>

        <div className="p-6">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {teamMembers.map(member => (
              <div key={member.id} className="flex items-center space-x-4 p-4 border border-gray-200 dark:border-gray-700 rounded-lg">
                <div className="relative">
                  <img
                    src={member.avatar}
                    alt={member.name}
                    className="w-12 h-12 rounded-full"
                  />
                  <div className={`absolute bottom-0 right-0 w-3 h-3 ${getStatusColor(member.status)} rounded-full border-2 border-white dark:border-gray-800`}></div>
                </div>
                <div className="flex-1">
                  <h3 className="font-medium text-gray-900 dark:text-white">{member.name}</h3>
                  <p className="text-sm text-gray-600 dark:text-gray-400">{member.role}</p>
                  <p className="text-xs text-gray-500 dark:text-gray-500">
                    {member.status === 'online' ? 'Online' : `Last seen ${formatTime(member.lastSeen)}`}
                  </p>
                </div>
                <div className="flex space-x-2">
                  <button className="p-2 text-gray-400 hover:text-blue-600 hover:bg-blue-50 dark:hover:bg-blue-900 rounded-lg">
                    <MessageSquare className="w-4 h-4" />
                  </button>
                  <button className="p-2 text-gray-400 hover:text-green-600 hover:bg-green-50 dark:hover:bg-green-900 rounded-lg">
                    <Video className="w-4 h-4" />
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );

  const ProjectsTab = () => (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-bold text-gray-900 dark:text-white">Projects</h2>
        <button className="flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700">
          <Plus className="w-4 h-4 mr-2" />
          New Project
        </button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6">
        {projects.map(project => (
          <div key={project.id} className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="font-semibold text-gray-900 dark:text-white">{project.name}</h3>
              <span className={`px-2 py-1 text-xs rounded-full ${
                project.status === 'active' 
                  ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200'
                  : 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200'
              }`}>
                {project.status}
              </span>
            </div>
            
            <div className="mb-4">
              <div className="flex justify-between text-sm text-gray-600 dark:text-gray-400 mb-1">
                <span>Progress</span>
                <span>{project.progress}%</span>
              </div>
              <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                <div 
                  className="bg-blue-600 h-2 rounded-full" 
                  style={{ width: `${project.progress}%` }}
                ></div>
              </div>
            </div>

            <div className="flex items-center justify-between text-sm text-gray-600 dark:text-gray-400">
              <div className="flex items-center">
                <Users className="w-4 h-4 mr-1" />
                <span>{project.members} members</span>
              </div>
              <div className="flex items-center">
                <Calendar className="w-4 h-4 mr-1" />
                <span>{formatDate(new Date(project.dueDate))}</span>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );

  const DocumentsTab = () => (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-bold text-gray-900 dark:text-white">Shared Documents</h2>
        <button className="flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700">
          <Share2 className="w-4 h-4 mr-2" />
          Share Document
        </button>
      </div>

      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md">
        <div className="p-6">
          <div className="space-y-4">
            {sharedDocuments.map(doc => (
              <div key={doc.id} className="flex items-center justify-between p-4 border border-gray-200 dark:border-gray-700 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700">
                <div className="flex items-center space-x-4">
                  <div className="w-10 h-10 bg-blue-100 dark:bg-blue-900 rounded-lg flex items-center justify-center">
                    <FileText className="w-5 h-5 text-blue-600 dark:text-blue-400" />
                  </div>
                  <div>
                    <h3 className="font-medium text-gray-900 dark:text-white">{doc.name}</h3>
                    <p className="text-sm text-gray-600 dark:text-gray-400">
                      Shared by {doc.sharedBy} • {formatDate(doc.sharedAt)} • {doc.size}
                    </p>
                  </div>
                </div>
                <div className="flex items-center space-x-2">
                  <button className="p-2 text-gray-400 hover:text-blue-600 hover:bg-blue-50 dark:hover:bg-blue-900 rounded-lg">
                    <Share2 className="w-4 h-4" />
                  </button>
                  <button className="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-50 dark:hover:bg-gray-700 rounded-lg">
                    <Archive className="w-4 h-4" />
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      {/* Header */}
      <div className="bg-white dark:bg-gray-800 shadow-sm border-b border-gray-200 dark:border-gray-700">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-6">
            <div>
              <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Collaboration Dashboard</h1>
              <p className="text-gray-600 dark:text-gray-400">Manage team collaboration and communication</p>
            </div>
            
            {/* Notifications */}
            <div className="flex items-center space-x-4">
              <div className="relative">
                <button className="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg">
                  <Bell className="w-6 h-6" />
                  {notifications.filter(n => !n.read).length > 0 && (
                    <span className="absolute top-0 right-0 w-2 h-2 bg-red-500 rounded-full"></span>
                  )}
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Navigation Tabs */}
      <div className="bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex space-x-8 py-4">
            <TabButton id="overview" label="Overview" icon={Users} active={activeTab === 'overview'} onClick={setActiveTab} />
            <TabButton id="team" label="Team" icon={Users} active={activeTab === 'team'} onClick={setActiveTab} />
            <TabButton id="projects" label="Projects" icon={FileText} active={activeTab === 'projects'} onClick={setActiveTab} />
            <TabButton id="documents" label="Documents" icon={Archive} active={activeTab === 'documents'} onClick={setActiveTab} />
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {activeTab === 'overview' && <OverviewTab />}
        {activeTab === 'team' && <TeamTab />}
        {activeTab === 'projects' && <ProjectsTab />}
        {activeTab === 'documents' && <DocumentsTab />}
      </div>
    </div>
  );
};

export default CollaborationDashboard;