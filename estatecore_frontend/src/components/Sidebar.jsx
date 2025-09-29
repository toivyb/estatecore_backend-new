import React, { useState } from 'react'
import { Link, useLocation } from 'react-router-dom'

const Sidebar = ({ user, isCollapsed = false, onToggle }) => {
  const location = useLocation()
  const [openDropdowns, setOpenDropdowns] = useState({})
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false)

  const toggleDropdown = (key) => {
    setOpenDropdowns(prev => ({
      ...prev,
      [key]: !prev[key]
    }))
  }

  const isActive = (path) => location.pathname === path
  const isGroupActive = (paths) => paths.some(path => location.pathname === path)

  const DropdownSection = ({ title, icon, menuKey, children, paths = [] }) => {
    const isOpen = openDropdowns[menuKey]
    const isCurrentGroupActive = isGroupActive(paths)

    return (
      <div className="px-4 py-1">
        <button
          onClick={() => toggleDropdown(menuKey)}
          className={`w-full flex items-center justify-between px-3 py-2 text-left rounded-md transition-colors ${
            isCurrentGroupActive 
              ? 'bg-blue-100 text-blue-700 dark:bg-blue-900 dark:text-blue-200' 
              : 'text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-700'
          }`}
        >
          <div className="flex items-center">
            <span className="mr-3">{icon}</span>
            <span className="font-medium">{title}</span>
          </div>
          <svg
            className={`w-4 h-4 transition-transform ${isOpen ? 'rotate-180' : ''}`}
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
          </svg>
        </button>
        {isOpen && (
          <div className="mt-1 ml-6 space-y-1">
            {children}
          </div>
        )}
      </div>
    )
  }

  const NavLink = ({ to, icon, children, badge = null }) => (
    <Link
      to={to}
      className={`flex items-center px-3 py-2 text-sm rounded-md transition-colors ${
        isActive(to)
          ? 'bg-blue-100 text-blue-700 dark:bg-blue-900 dark:text-blue-200'
          : 'text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-600'
      }`}
    >
      <span className="mr-2 text-sm">{icon}</span>
      <span>{children}</span>
      {badge && (
        <span className="ml-auto bg-red-500 text-white text-xs px-1.5 py-0.5 rounded-full">
          {badge}
        </span>
      )}
    </Link>
  )

  return (
    <>
      {/* Mobile Menu Button */}
      <button
        onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
        className="md:hidden fixed top-4 left-4 z-50 p-2 bg-white dark:bg-gray-800 rounded-md shadow-lg"
      >
        <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
        </svg>
      </button>

      {/* Overlay for mobile */}
      {isMobileMenuOpen && (
        <div 
          className="md:hidden fixed inset-0 bg-black bg-opacity-50 z-40"
          onClick={() => setIsMobileMenuOpen(false)}
        />
      )}

      {/* Sidebar */}
      <div className={`${
        isMobileMenuOpen ? 'translate-x-0' : '-translate-x-full'
      } md:translate-x-0 fixed md:static inset-y-0 left-0 z-50 w-64 bg-white dark:bg-gray-800 shadow-lg flex flex-col transition-transform duration-300 ease-in-out`}>
        {/* Header */}
        <div className="p-4 border-b dark:border-gray-700">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-xl font-bold text-gray-800 dark:text-gray-200">EstateCore</h2>
              <p className="text-xs text-gray-500 dark:text-gray-400">Property Management Platform</p>
            </div>
            <button
              onClick={() => setIsMobileMenuOpen(false)}
              className="md:hidden p-1 text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        </div>

      {/* Navigation */}
      <nav className="flex-1 mt-4 overflow-y-auto">
        {/* Dashboard - Standalone */}
        <div className="px-4 py-2">
          <Link
            to="/"
            className={`flex items-center px-3 py-2 rounded-md transition-colors ${
              isActive('/')
                ? 'bg-blue-100 text-blue-700 dark:bg-blue-900 dark:text-blue-200'
                : 'text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-700'
            }`}
          >
            <span className="mr-3">🏠</span>
            <span className="font-medium">Dashboard</span>
          </Link>
        </div>

        {/* Property Management */}
        <DropdownSection
          title="Property Management"
          icon="🏢"
          menuKey="property"
          paths={['/properties', '/tenants', '/tenant-screening', '/access', '/tenant-portal']}
        >
          <NavLink to="/properties" icon="🏢">Properties</NavLink>
          <NavLink to="/tenants" icon="👤">Tenants</NavLink>
          <NavLink to="/tenant-screening" icon="🔍">Tenant Screening</NavLink>
          <NavLink to="/access" icon="🔐">Access Control</NavLink>
          {user.role === 'tenant' && (
            <NavLink to="/tenant-portal" icon="🏠">Tenant Portal</NavLink>
          )}
        </DropdownSection>

        {/* Maintenance & Operations */}
        <DropdownSection
          title="Maintenance & Operations"
          icon="🔧"
          menuKey="maintenance"
          paths={['/maintenance', '/maintenance-scheduling', '/maintenance-dispatch', '/predictive-maintenance', '/work-orders', '/maintenance-board', '/maintenance-workflow', '/smart-maintenance']}
        >
          <NavLink to="/maintenance" icon="🔧">Maintenance</NavLink>
          <NavLink to="/maintenance-scheduling" icon="🗓️">Scheduling</NavLink>
          <NavLink to="/maintenance-dispatch" icon="🚀">Smart Dispatch</NavLink>
          <NavLink to="/predictive-maintenance" icon="🔮">Predictive Maintenance</NavLink>
          <NavLink to="/work-orders" icon="📋">Work Orders</NavLink>
          <NavLink to="/maintenance-board" icon="📊">Maintenance Board</NavLink>
          <NavLink to="/maintenance-workflow" icon="🔄">Workflow</NavLink>
          <NavLink to="/smart-maintenance" icon="🤖">Smart Maintenance</NavLink>
        </DropdownSection>

        {/* Financial Management */}
        <DropdownSection
          title="Financial Management"
          icon="💰"
          menuKey="financial"
          paths={['/rent', '/lease-management', '/payments', '/financial-reports', '/billing-dashboard', '/financial-analytics']}
        >
          <NavLink to="/rent" icon="💰">Rent Collection</NavLink>
          <NavLink to="/lease-management" icon="📋">Lease Management</NavLink>
          <NavLink to="/payments" icon="💳">Payments</NavLink>
          <NavLink to="/financial-reports" icon="📊">Financial Reports</NavLink>
          <NavLink to="/financial-analytics" icon="📈">Financial Analytics</NavLink>
          <NavLink to="/billing-dashboard" icon="💳">SaaS Billing</NavLink>
        </DropdownSection>

        {/* AI Intelligence Hub */}
        <DropdownSection
          title="AI Intelligence Hub"
          icon="🧠"
          menuKey="ai"
          paths={['/ai-hub', '/ai/computer-vision', '/ai/document-processing', '/ai/predictive-maintenance', '/ai/market-intelligence', '/ai/conversational-ai', '/ai/advanced-analytics', '/ai/voice-assistant', '/ai/property-valuation', '/live-camera-analysis', '/ai-management-dashboard', '/ai-dashboard', '/ai-analytics']}
        >
          <NavLink to="/ai-hub" icon="🧠">AI Hub</NavLink>
          <NavLink to="/ai/property-valuation" icon="💰">Property Valuation</NavLink>
          <NavLink to="/ai/computer-vision" icon="👁️">Computer Vision</NavLink>
          <NavLink to="/ai/document-processing" icon="📄">Document Processing</NavLink>
          <NavLink to="/ai/predictive-maintenance" icon="🔧">Predictive Maintenance</NavLink>
          <NavLink to="/ai/market-intelligence" icon="📊">Market Intelligence</NavLink>
          <NavLink to="/ai/conversational-ai" icon="🤖">Conversational AI</NavLink>
          <NavLink to="/ai/advanced-analytics" icon="📊">Advanced Analytics</NavLink>
          <NavLink to="/ai/voice-assistant" icon="🎤">Voice Assistant</NavLink>
          <NavLink to="/live-camera-analysis" icon="📹">Live Camera Analysis</NavLink>
          <NavLink to="/ai-management-dashboard" icon="🎛️">AI Management</NavLink>
          <NavLink to="/ai-dashboard" icon="📊">AI Analytics</NavLink>
          {user.role === 'super_admin' && (
            <NavLink to="/ai-analytics" icon="🤖">Advanced AI</NavLink>
          )}
        </DropdownSection>

        {/* Reports & Analytics */}
        <DropdownSection
          title="Reports & Analytics"
          icon="📈"
          menuKey="reports"
          paths={['/reports', '/forecasts', '/asset-health', '/revenue-leakage', '/risk-flags']}
        >
          <NavLink to="/reports" icon="📊">Reports</NavLink>
          <NavLink to="/forecasts" icon="🔮">Forecasts</NavLink>
          <NavLink to="/asset-health" icon="🏥">Asset Health</NavLink>
          <NavLink to="/revenue-leakage" icon="💸">Revenue Leakage</NavLink>
          <NavLink to="/risk-flags" icon="⚠️">Risk Flags</NavLink>
        </DropdownSection>

        {/* Analytics & Monitoring */}
        <DropdownSection
          title="Analytics & Monitoring"
          icon="📊"
          menuKey="analytics"
          paths={['/occupancy-analytics', '/environmental-dashboard', '/iot-dashboard', '/energy-management']}
        >
          <NavLink to="/energy-management" icon="⚡">Smart Energy Management</NavLink>
          <NavLink to="/occupancy-analytics" icon="📊">Occupancy Analytics</NavLink>
          <NavLink to="/environmental-dashboard" icon="🌍">Environmental Monitoring</NavLink>
          <NavLink to="/iot-dashboard" icon="📡">IoT Dashboard</NavLink>
        </DropdownSection>

        {/* Security & Access */}
        <DropdownSection
          title="Security & Access"
          icon="🔒"
          menuKey="security"
          paths={['/lpr-dashboard', '/lpr-companies', '/security-dashboard']}
        >
          <NavLink to="/security-dashboard" icon="🔒">Security Dashboard</NavLink>
          <NavLink to="/lpr-dashboard" icon="📷">License Plate Recognition</NavLink>
          <NavLink to="/lpr-companies" icon="🏢">LPR Companies</NavLink>
        </DropdownSection>

        {/* Communication & Documents */}
        <DropdownSection
          title="Communication & Docs"
          icon="💬"
          menuKey="communication"
          paths={['/messages', '/documents', '/collaboration']}
        >
          <NavLink to="/messages" icon="💬">Messages</NavLink>
          <NavLink to="/documents" icon="📁">Documents</NavLink>
          <NavLink to="/collaboration" icon="🤝">Collaboration</NavLink>
        </DropdownSection>

        {/* User Administration */}
        <DropdownSection
          title="User Administration"
          icon="👥"
          menuKey="users"
          paths={['/users', '/companies', '/invite-user', '/bulk-operations', '/forms-wizards']}
        >
          <NavLink to="/users" icon="👥">Users</NavLink>
          <NavLink to="/companies" icon="🏢">Companies</NavLink>
          <NavLink to="/invite-user" icon="✉️">Invite User</NavLink>
          <NavLink to="/bulk-operations" icon="📋">Bulk Operations</NavLink>
          <NavLink to="/forms-wizards" icon="🧙‍♂️">Forms & Wizards</NavLink>
        </DropdownSection>

        {/* System Administration - Super Admin Only */}
        {user.role === 'super_admin' && (
          <>
            <div className="px-4 py-1 mt-6">
              <div className="text-xs font-semibold text-red-600 dark:text-red-400 uppercase tracking-wide border-t pt-4">
                System Administration
              </div>
            </div>
            <DropdownSection
              title="System Administration"
              icon="⚙️"
              menuKey="admin"
              paths={['/setup-wizard', '/system-settings', '/admin-tools', '/audit-logs', '/performance', '/testing', '/beta-testing', '/automation', '/blockchain']}
            >
              <NavLink to="/setup-wizard" icon="🧙‍♂️">Setup Wizard</NavLink>
              <NavLink to="/system-settings" icon="⚙️">System Settings</NavLink>
              <NavLink to="/admin-tools" icon="🛠️">Admin Tools</NavLink>
              <NavLink to="/audit-logs" icon="📋">Audit Logs</NavLink>
              <NavLink to="/performance" icon="⚡">Performance</NavLink>
              <NavLink to="/testing" icon="🧪">Testing</NavLink>
              <NavLink to="/beta-testing" icon="🚀">Beta Testing</NavLink>
              <NavLink to="/automation" icon="🤖">Automation</NavLink>
              <NavLink to="/blockchain" icon="⛓️">Blockchain</NavLink>
            </DropdownSection>
          </>
        )}
      </nav>

        {/* Footer */}
        <div className="p-4 border-t dark:border-gray-700">
          <div className="text-xs text-gray-500 dark:text-gray-400">
            EstateCore v4.0
            <br />
            <span className="text-green-600 dark:text-green-400">● System Operational</span>
          </div>
        </div>
      </div>
    </>
  )
}

export default Sidebar