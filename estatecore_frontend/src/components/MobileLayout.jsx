import React, { useState, useEffect } from 'react'
import { Link, useLocation } from 'react-router-dom'

const MobileLayout = ({ children, user, onLogout }) => {
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const [isMobile, setIsMobile] = useState(false)
  const location = useLocation()

  useEffect(() => {
    const checkScreenSize = () => {
      setIsMobile(window.innerWidth < 768)
      if (window.innerWidth >= 768) {
        setSidebarOpen(false)
      }
    }

    checkScreenSize()
    window.addEventListener('resize', checkScreenSize)
    return () => window.removeEventListener('resize', checkScreenSize)
  }, [])

  // Close sidebar when route changes on mobile
  useEffect(() => {
    if (isMobile) {
      setSidebarOpen(false)
    }
  }, [location.pathname, isMobile])

  const navigationSections = [
    {
      title: 'Property Management',
      items: [
        { name: 'Dashboard', path: '/', icon: '📊' },
        { name: 'Properties', path: '/properties', icon: '🏢' },
        { name: 'Tenants', path: '/tenants', icon: '👤' },
        { name: 'Maintenance', path: '/maintenance', icon: '🔧' },
        { name: 'Access Control', path: '/access-control', icon: '🔐' }
      ]
    },
    {
      title: 'Financial',
      items: [
        { name: 'Rent Dashboard', path: '/rent-dashboard', icon: '💰' },
        { name: 'Payments', path: '/payments', icon: '💳' },
        { name: 'Financial Reports', path: '/financial-reports', icon: '📈' }
      ]
    },
    {
      title: 'AI & Automation',
      items: [
        { name: 'Analytics', path: '/analytics', icon: '📊' },
        { name: 'Smart Dispatch', path: '/smart-dispatch', icon: '🤖' },
        { name: 'LPR Management', path: '/lpr', icon: '🚗' }
      ]
    },
    {
      title: 'Communication',
      items: [
        { name: 'Messages', path: '/messages', icon: '📧' },
        { name: 'Documents', path: '/documents', icon: '📄' }
      ]
    }
  ]

  const NavLink = ({ item, mobile = false }) => {
    const isActive = location.pathname === item.path
    const baseClasses = mobile
      ? "flex items-center px-4 py-3 text-base font-medium border-l-4"
      : "flex items-center px-3 py-2 text-sm font-medium rounded-md"
    
    const activeClasses = isActive
      ? mobile
        ? "border-blue-500 text-blue-700 bg-blue-50"
        : "bg-blue-100 text-blue-700"
      : mobile
        ? "border-transparent text-gray-600 hover:text-gray-900 hover:bg-gray-50"
        : "text-gray-600 hover:text-gray-900 hover:bg-gray-50"

    return (
      <Link
        to={item.path}
        className={`${baseClasses} ${activeClasses}`}
      >
        <span className={mobile ? "text-xl mr-4" : "text-base mr-3"}>
          {item.icon}
        </span>
        {item.name}
      </Link>
    )
  }

  return (
    <div className="h-screen flex overflow-hidden bg-gray-100">
      {/* Mobile sidebar overlay */}
      {isMobile && sidebarOpen && (
        <div
          className="fixed inset-0 flex z-40 md:hidden"
          role="dialog"
          aria-modal="true"
        >
          <div
            className="fixed inset-0 bg-gray-600 bg-opacity-75"
            onClick={() => setSidebarOpen(false)}
          ></div>
          
          {/* Mobile sidebar */}
          <div className="relative flex-1 flex flex-col max-w-xs w-full bg-white">
            <div className="absolute top-0 right-0 -mr-12 pt-2">
              <button
                type="button"
                className="ml-1 flex items-center justify-center h-10 w-10 rounded-full focus:outline-none focus:ring-2 focus:ring-inset focus:ring-white"
                onClick={() => setSidebarOpen(false)}
              >
                <span className="sr-only">Close sidebar</span>
                <svg className="h-6 w-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
            
            <div className="flex-1 h-0 pt-5 pb-4 overflow-y-auto">
              <div className="flex-shrink-0 flex items-center px-4">
                <span className="text-2xl font-bold text-blue-600">🏠 EstateCore</span>
              </div>
              <nav className="mt-5 space-y-1">
                {navigationSections.map((section) => (
                  <div key={section.title} className="px-4 py-2">
                    <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wider">
                      {section.title}
                    </h3>
                    <div className="mt-2 space-y-1">
                      {section.items.map((item) => (
                        <NavLink key={item.name} item={item} mobile={true} />
                      ))}
                    </div>
                  </div>
                ))}
              </nav>
            </div>
          </div>
        </div>
      )}

      {/* Desktop sidebar */}
      <div className={`${isMobile ? 'hidden' : 'flex'} flex-col w-64 bg-white border-r border-gray-200`}>
        <div className="flex items-center h-16 flex-shrink-0 px-4 bg-white border-b border-gray-200">
          <span className="text-xl font-bold text-blue-600">🏠 EstateCore</span>
        </div>
        <div className="flex-1 flex flex-col overflow-y-auto">
          <nav className="flex-1 px-4 py-4 space-y-6">
            {navigationSections.map((section) => (
              <div key={section.title}>
                <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2">
                  {section.title}
                </h3>
                <div className="space-y-1">
                  {section.items.map((item) => (
                    <NavLink key={item.name} item={item} />
                  ))}
                </div>
              </div>
            ))}
          </nav>
        </div>
      </div>

      {/* Main content */}
      <div className="flex flex-col w-0 flex-1 overflow-hidden">
        {/* Mobile header */}
        <div className="md:hidden flex items-center justify-between h-16 bg-white border-b border-gray-200 px-4">
          <button
            type="button"
            className="text-gray-500 hover:text-gray-900 focus:outline-none focus:ring-2 focus:ring-inset focus:ring-blue-500"
            onClick={() => setSidebarOpen(true)}
          >
            <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
            </svg>
          </button>
          <span className="text-lg font-semibold text-gray-900">EstateCore</span>
          <div className="flex items-center space-x-2">
            <span className="text-sm text-gray-700">{user?.username}</span>
            <button
              onClick={onLogout}
              className="text-red-600 hover:text-red-800 text-sm"
            >
              Logout
            </button>
          </div>
        </div>

        {/* Desktop header */}
        <div className="hidden md:flex items-center justify-between h-16 bg-white border-b border-gray-200 px-6">
          <h1 className="text-2xl font-semibold text-gray-900">
            Property Management System
          </h1>
          <div className="flex items-center space-x-4">
            <span className="text-gray-700">Welcome, {user?.username}</span>
            <button
              onClick={onLogout}
              className="bg-red-600 text-white px-4 py-2 rounded-md hover:bg-red-700 text-sm"
            >
              Logout
            </button>
          </div>
        </div>

        {/* Page content */}
        <main className="flex-1 relative overflow-y-auto focus:outline-none">
          <div className="py-6">
            <div className="max-w-7xl mx-auto px-4 sm:px-6 md:px-8">
              {children}
            </div>
          </div>
        </main>
      </div>
    </div>
  )
}

export default MobileLayout