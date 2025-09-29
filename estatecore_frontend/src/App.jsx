import React, { useState, useEffect } from 'react'
import { Routes, Route, Link, Navigate, useNavigate } from 'react-router-dom'
import ProtectedRoute from './components/ProtectedRoute.jsx'
import Sidebar from './components/Sidebar.jsx'
import { ThemeProvider } from './contexts/ThemeContext.jsx'
import { PermissionProvider } from './components/PermissionGuard.jsx'
import ThemeToggle from './components/ThemeToggle.jsx'
import Login from './pages/Login.jsx'
import Dashboard from './pages/Dashboard.jsx'
import Properties from './pages/Properties.jsx'
import Tenants from './pages/Tenants.jsx'
import Maintenance from './pages/Maintenance.jsx'
import AccessControl from './pages/AccessControl.jsx'
import RentDashboard from './pages/RentDashboard.jsx'
import RentCollection from './pages/RentCollection.jsx'
import LeaseManagement from './pages/LeaseManagement.jsx'
import FinancialReports from './pages/FinancialReports.jsx'
import FinancialDashboard from './pages/FinancialDashboard.jsx'
import AIDashboard from './pages/AIDashboard.jsx'
import Payments from './pages/Payments.jsx'
import SetupWizard from './pages/SetupWizard.jsx'
import MaintenanceDispatch from './pages/MaintenanceDispatch.jsx'
import AIAnalyticsDashboard from './pages/AIAnalyticsDashboard.jsx'
import Messages from './pages/Messages.jsx'
import Documents from './pages/Documents.jsx'
import InviteRegister from './pages/InviteRegister.jsx'
import LPRDashboard from './pages/LPRDashboard.jsx'
import InviteUser from './pages/InviteUser.jsx'
import LPRCompanies from './pages/LPRCompanies.jsx'
import IoTDashboard from './pages/IoTDashboard.jsx'
import PredictiveMaintenance from './pages/PredictiveMaintenance.jsx'
import OccupancyAnalytics from './pages/OccupancyAnalytics.jsx'
import BillingDashboard from './pages/BillingDashboard.jsx'
import EnvironmentalDashboard from './pages/EnvironmentalDashboard.jsx'
import MaintenanceSchedulingDashboard from './components/MaintenanceSchedulingDashboard.jsx'
import TenantScreening from './pages/TenantScreening.jsx'
import EnergyManagement from './pages/EnergyManagement.jsx'
import AIManagementDashboard from './pages/AIManagementDashboard.jsx'
import BetaTestingDashboard from './pages/BetaTestingDashboard.jsx'
import BulkOperationsDashboard from './components/BulkOperationsDashboard.jsx'
import FormsWizardDashboard from './components/FormsWizardDashboard.jsx'
import PerformanceDashboard from './components/PerformanceDashboard.jsx'
import TestingDashboard from './components/TestingDashboard.jsx'
import TenantPortal from './pages/TenantPortal.jsx'
import LiveCameraAnalysis from './pages/LiveCameraAnalysis.jsx'
import AIHub from './pages/AIHub.jsx'
import ComputerVisionDashboard from './pages/ComputerVisionDashboard.jsx'
import DocumentProcessingDashboard from './pages/DocumentProcessingDashboard.jsx'
import PredictiveMaintenanceDashboard from './pages/PredictiveMaintenanceDashboard.jsx'
import MarketIntelligenceDashboard from './pages/MarketIntelligenceDashboard.jsx'
import ConversationalAI from './pages/ConversationalAI.jsx'
import AdvancedAnalyticsDashboard from './pages/AdvancedAnalyticsDashboard.jsx'
import VoiceAssistant from './pages/VoiceAssistant.jsx'
import AIValuationDashboard from './pages/AIValuationDashboard.jsx'
import FinancialAnalyticsDashboard from './pages/FinancialAnalyticsDashboard.jsx'
import WorkOrderList from './pages/WorkOrderList.jsx'
import WorkOrderDetail from './pages/WorkOrderDetail.jsx'
import NewWorkOrder from './pages/NewWorkOrder.jsx'
import MaintenanceBoard from './pages/MaintenanceBoard.jsx'
import MaintenanceWorkflow from './pages/MaintenanceWorkflow.jsx'
import Reports from './pages/Reports.jsx'
import Forecasts from './pages/Forecasts.jsx'
import AssetHealth from './pages/AssetHealth.jsx'
import RevenueLeakage from './pages/RevenueLeakage.jsx'
import RiskFlags from './pages/RiskFlags.jsx'
import SecurityDashboard from './pages/SecurityDashboard.jsx'
import AutomationDashboard from './pages/AutomationDashboard.jsx'
import SmartMaintenanceDashboard from './pages/SmartMaintenanceDashboard.jsx'
import CollaborationDashboard from './pages/CollaborationDashboard.jsx'
import BlockchainDashboard from './pages/BlockchainDashboard.jsx'
import Companies from './pages/Companies.jsx'
import Users from './pages/Users.jsx'

// Using the enhanced Users component from pages/Users.jsx

const SystemSettings = () => (
  <div className="bg-white rounded-lg shadow p-6">
    <h2 className="text-2xl font-bold mb-4">System Settings</h2>
    <p className="text-gray-600">System configuration and settings...</p>
  </div>
)

const AdminTools = () => (
  <div className="bg-white rounded-lg shadow p-6">
    <h2 className="text-2xl font-bold mb-4">Admin Tools</h2>
    <p className="text-gray-600">Administrative tools and utilities...</p>
  </div>
)

const AuditLogs = () => (
  <div className="bg-white rounded-lg shadow p-6">
    <h2 className="text-2xl font-bold mb-4">Audit Logs</h2>
    <p className="text-gray-600">System audit logs and activity tracking...</p>
  </div>
)

export default function App(){
  const navigate = useNavigate()
  const [token, setToken] = useState(localStorage.getItem('token'))
  const [user, setUser] = useState(() => {
    try {
      return JSON.parse(localStorage.getItem('user') || '{}')
    } catch {
      return {}
    }
  })

  // Listen for localStorage changes
  useEffect(() => {
    const handleStorageChange = () => {
      setToken(localStorage.getItem('token'))
      try {
        setUser(JSON.parse(localStorage.getItem('user') || '{}'))
      } catch {
        setUser({})
      }
    }

    window.addEventListener('storage', handleStorageChange)
    
    // Also listen for custom events for same-window updates
    window.addEventListener('loginStateChange', handleStorageChange)
    
    return () => {
      window.removeEventListener('storage', handleStorageChange)
      window.removeEventListener('loginStateChange', handleStorageChange)
    }
  }, [])
  
  // If no token, show login page
  if (!token) {
    return (
      <ThemeProvider>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/invite-register" element={<InviteRegister />} />
          <Route path="*" element={<Navigate to="/login" replace />} />
        </Routes>
      </ThemeProvider>
    )
  }
  
  return (
    <PermissionProvider>
      <ThemeProvider>
        <div className="flex h-screen bg-gray-100 dark:bg-gray-900">
        {token && <Sidebar user={user} />}
        
        <div className="flex-1 flex flex-col">
        {token && (
          <header className="bg-white dark:bg-gray-800 shadow-sm border-b dark:border-gray-700 px-6 py-4 flex-shrink-0">
            <div className="flex items-center justify-between">
              <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">Property Management</h1>
              <div className="flex items-center gap-4">
                <div className="text-right">
                  <div className="text-sm font-medium text-gray-900 dark:text-gray-100">
                    {user.username || user.email}
                  </div>
                  <div className="text-xs text-gray-500 dark:text-gray-400 capitalize">
                    {user.role?.replace('_', ' ')}
                  </div>
                </div>
                <ThemeToggle />
                <button 
                  onClick={()=>{
                    localStorage.removeItem('token'); 
                    localStorage.removeItem('user'); 
                    window.dispatchEvent(new Event('loginStateChange'));
                    navigate('/login');
                  }}
                  className="flex items-center px-3 py-2 text-sm text-red-600 hover:bg-red-50 dark:hover:bg-red-900 rounded-md border border-red-200 dark:border-red-700 hover:border-red-300 dark:hover:border-red-600 transition-colors"
                  title="Logout"
                >
                  <span className="mr-1">🚪</span>
                  Logout
                </button>
              </div>
            </div>
          </header>
        )}
        
        <main className="flex-1 overflow-y-auto p-6 pt-16 md:pt-6 min-h-0 bg-gray-50 dark:bg-gray-900">
          <Routes>
            <Route path="/login" element={<Login />} />
            <Route path="/invite-register" element={<InviteRegister />} />
            <Route path="/" element={
              <ProtectedRoute>
                <Dashboard />
              </ProtectedRoute>
            } />
            <Route path="/properties" element={
              <ProtectedRoute>
                <Properties />
              </ProtectedRoute>
            } />
            <Route path="/users" element={
              <ProtectedRoute>
                <Users />
              </ProtectedRoute>
            } />
            <Route path="/tenants" element={
              <ProtectedRoute>
                <Tenants />
              </ProtectedRoute>
            } />
            <Route path="/tenant-screening" element={
              <ProtectedRoute>
                <TenantScreening />
              </ProtectedRoute>
            } />
            <Route path="/energy-management" element={
              <ProtectedRoute>
                <EnergyManagement />
              </ProtectedRoute>
            } />
            <Route path="/rent" element={
              <ProtectedRoute>
                <RentCollection />
              </ProtectedRoute>
            } />
            <Route path="/lease-management" element={
              <ProtectedRoute>
                <LeaseManagement />
              </ProtectedRoute>
            } />
            <Route path="/maintenance" element={
              <ProtectedRoute>
                <Maintenance />
              </ProtectedRoute>
            } />
            <Route path="/maintenance-scheduling" element={
              <ProtectedRoute>
                <MaintenanceSchedulingDashboard />
              </ProtectedRoute>
            } />
            <Route path="/access" element={
              <ProtectedRoute>
                <AccessControl />
              </ProtectedRoute>
            } />
            <Route path="/financial-reports" element={
              <ProtectedRoute>
                <FinancialReports />
              </ProtectedRoute>
            } />
            <Route path="/financial" element={
              <ProtectedRoute>
                <FinancialDashboard />
              </ProtectedRoute>
            } />
            <Route path="/ai-dashboard" element={
              <ProtectedRoute>
                <AIDashboard />
              </ProtectedRoute>
            } />
            <Route path="/ai-management-dashboard" element={
              <ProtectedRoute>
                <AIManagementDashboard />
              </ProtectedRoute>
            } />
            <Route path="/system-settings" element={
              <ProtectedRoute>
                <SystemSettings />
              </ProtectedRoute>
            } />
            <Route path="/admin-tools" element={
              <ProtectedRoute>
                <AdminTools />
              </ProtectedRoute>
            } />
            <Route path="/audit-logs" element={
              <ProtectedRoute>
                <AuditLogs />
              </ProtectedRoute>
            } />
            <Route path="/payments" element={
              <ProtectedRoute>
                <Payments />
              </ProtectedRoute>
            } />
            <Route path="/setup-wizard" element={
              <ProtectedRoute>
                <SetupWizard />
              </ProtectedRoute>
            } />
            <Route path="/maintenance-dispatch" element={
              <ProtectedRoute>
                <MaintenanceDispatch />
              </ProtectedRoute>
            } />
            <Route path="/ai-analytics" element={
              <ProtectedRoute>
                <AIAnalyticsDashboard />
              </ProtectedRoute>
            } />
            <Route path="/messages" element={
              <ProtectedRoute>
                <Messages />
              </ProtectedRoute>
            } />
            <Route path="/documents" element={
              <ProtectedRoute>
                <Documents />
              </ProtectedRoute>
            } />
            <Route path="/lpr-dashboard" element={
              <ProtectedRoute>
                <LPRDashboard />
              </ProtectedRoute>
            } />
            <Route path="/invite-user" element={
              <ProtectedRoute>
                <InviteUser />
              </ProtectedRoute>
            } />
            <Route path="/lpr-companies" element={
              <ProtectedRoute>
                <LPRCompanies />
              </ProtectedRoute>
            } />
            <Route path="/bulk-operations" element={
              <ProtectedRoute>
                <BulkOperationsDashboard />
              </ProtectedRoute>
            } />
            <Route path="/forms-wizards" element={
              <ProtectedRoute>
                <FormsWizardDashboard />
              </ProtectedRoute>
            } />
            <Route path="/performance" element={
              <ProtectedRoute>
                <PerformanceDashboard />
              </ProtectedRoute>
            } />
            <Route path="/testing" element={
              <ProtectedRoute>
                <TestingDashboard />
              </ProtectedRoute>
            } />
            <Route path="/beta-testing" element={
              <ProtectedRoute>
                <BetaTestingDashboard />
              </ProtectedRoute>
            } />
            <Route path="/iot-dashboard" element={
              <ProtectedRoute>
                <IoTDashboard />
              </ProtectedRoute>
            } />
            <Route path="/predictive-maintenance" element={
              <ProtectedRoute>
                <PredictiveMaintenance />
              </ProtectedRoute>
            } />
            <Route path="/occupancy-analytics" element={
              <ProtectedRoute>
                <OccupancyAnalytics />
              </ProtectedRoute>
            } />
            <Route path="/billing-dashboard" element={
              <ProtectedRoute>
                <BillingDashboard />
              </ProtectedRoute>
            } />
            <Route path="/environmental-dashboard" element={
              <ProtectedRoute>
                <EnvironmentalDashboard />
              </ProtectedRoute>
            } />
            <Route path="/tenant-portal" element={
              <ProtectedRoute>
                <TenantPortal />
              </ProtectedRoute>
            } />
            <Route path="/live-camera-analysis" element={
              <ProtectedRoute>
                <LiveCameraAnalysis />
              </ProtectedRoute>
            } />
            <Route path="/ai-hub" element={
              <ProtectedRoute>
                <AIHub />
              </ProtectedRoute>
            } />
            <Route path="/ai/computer-vision" element={
              <ProtectedRoute>
                <ComputerVisionDashboard />
              </ProtectedRoute>
            } />
            <Route path="/ai/document-processing" element={
              <ProtectedRoute>
                <DocumentProcessingDashboard />
              </ProtectedRoute>
            } />
            <Route path="/ai/predictive-maintenance" element={
              <ProtectedRoute>
                <PredictiveMaintenanceDashboard />
              </ProtectedRoute>
            } />
            <Route path="/ai/market-intelligence" element={
              <ProtectedRoute>
                <MarketIntelligenceDashboard />
              </ProtectedRoute>
            } />
            <Route path="/ai/conversational-ai" element={
              <ProtectedRoute>
                <ConversationalAI />
              </ProtectedRoute>
            } />
            <Route path="/ai/advanced-analytics" element={
              <ProtectedRoute>
                <AdvancedAnalyticsDashboard />
              </ProtectedRoute>
            } />
            <Route path="/ai/voice-assistant" element={
              <ProtectedRoute>
                <VoiceAssistant />
              </ProtectedRoute>
            } />
            <Route path="/ai/property-valuation" element={
              <ProtectedRoute>
                <AIValuationDashboard />
              </ProtectedRoute>
            } />
            <Route path="/financial-analytics" element={
              <ProtectedRoute>
                <FinancialAnalyticsDashboard />
              </ProtectedRoute>
            } />
            <Route path="/work-orders" element={
              <ProtectedRoute>
                <WorkOrderList />
              </ProtectedRoute>
            } />
            <Route path="/work-orders/:id" element={
              <ProtectedRoute>
                <WorkOrderDetail />
              </ProtectedRoute>
            } />
            <Route path="/work-orders/new" element={
              <ProtectedRoute>
                <NewWorkOrder />
              </ProtectedRoute>
            } />
            <Route path="/maintenance-board" element={
              <ProtectedRoute>
                <MaintenanceBoard />
              </ProtectedRoute>
            } />
            <Route path="/maintenance-workflow" element={
              <ProtectedRoute>
                <MaintenanceWorkflow />
              </ProtectedRoute>
            } />
            <Route path="/reports" element={
              <ProtectedRoute>
                <Reports />
              </ProtectedRoute>
            } />
            <Route path="/forecasts" element={
              <ProtectedRoute>
                <Forecasts />
              </ProtectedRoute>
            } />
            <Route path="/asset-health" element={
              <ProtectedRoute>
                <AssetHealth />
              </ProtectedRoute>
            } />
            <Route path="/revenue-leakage" element={
              <ProtectedRoute>
                <RevenueLeakage />
              </ProtectedRoute>
            } />
            <Route path="/risk-flags" element={
              <ProtectedRoute>
                <RiskFlags />
              </ProtectedRoute>
            } />
            <Route path="/security-dashboard" element={
              <ProtectedRoute>
                <SecurityDashboard />
              </ProtectedRoute>
            } />
            <Route path="/automation" element={
              <ProtectedRoute>
                <AutomationDashboard />
              </ProtectedRoute>
            } />
            <Route path="/smart-maintenance" element={
              <ProtectedRoute>
                <SmartMaintenanceDashboard />
              </ProtectedRoute>
            } />
            <Route path="/collaboration" element={
              <ProtectedRoute>
                <CollaborationDashboard />
              </ProtectedRoute>
            } />
            <Route path="/blockchain" element={
              <ProtectedRoute>
                <BlockchainDashboard />
              </ProtectedRoute>
            } />
            <Route path="/companies" element={
              <ProtectedRoute>
                <Companies />
              </ProtectedRoute>
            } />
            <Route path="/users" element={
              <ProtectedRoute>
                <Users />
              </ProtectedRoute>
            } />
          </Routes>
        </main>
        </div>
        </div>
      </ThemeProvider>
    </PermissionProvider>
  )
}
