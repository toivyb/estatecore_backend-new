import React, { useState, useEffect } from 'react'

const SetupWizard = () => {
  const [setupProgress, setSetupProgress] = useState(null)
  const [loading, setLoading] = useState(true)
  const [activeStep, setActiveStep] = useState(0)

  useEffect(() => {
    fetchSetupProgress()
  }, [])

  const fetchSetupProgress = async () => {
    try {
      const response = await fetch('https://estatecore-backend-sujs.onrender.com/api/setup/progress')
      const data = await response.json()
      setSetupProgress(data)
      
      // Find the first incomplete step
      const incompleteIndex = data.steps.findIndex(step => !step.completed)
      setActiveStep(incompleteIndex >= 0 ? incompleteIndex : data.steps.length - 1)
    } catch (error) {
      console.error('Error fetching setup progress:', error)
    } finally {
      setLoading(false)
    }
  }

  const getStepIcon = (step, index) => {
    if (step.completed) {
      return '✅'
    } else if (index === activeStep) {
      return '🔄'
    } else {
      return '⏳'
    }
  }

  const getStepStatus = (step, index) => {
    if (step.completed) {
      return 'completed'
    } else if (index === activeStep) {
      return 'active'
    } else {
      return 'pending'
    }
  }

  const renderStepContent = (step, index) => {
    switch (step.id) {
      case 'organization':
        return (
          <div className="p-6">
            <h3 className="text-lg font-medium mb-4">Organization Setup</h3>
            <div className="space-y-4">
              <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                <div className="flex items-center">
                  <span className="text-green-600 mr-2">✅</span>
                  <span className="text-green-800 font-medium">Organization configured</span>
                </div>
                <p className="text-green-700 text-sm mt-1">
                  Your EstateCore organization has been successfully set up.
                </p>
              </div>
            </div>
          </div>
        )
      
      case 'properties':
        return (
          <div className="p-6">
            <h3 className="text-lg font-medium mb-4">Add Properties</h3>
            <div className="space-y-4">
              {step.completed ? (
                <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                  <div className="flex items-center">
                    <span className="text-green-600 mr-2">✅</span>
                    <span className="text-green-800 font-medium">Properties added</span>
                  </div>
                  <p className="text-green-700 text-sm mt-1">
                    You have successfully added properties to your portfolio.
                  </p>
                </div>
              ) : (
                <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                  <div className="flex items-center">
                    <span className="text-blue-600 mr-2">📋</span>
                    <span className="text-blue-800 font-medium">Add your first property</span>
                  </div>
                  <p className="text-blue-700 text-sm mt-1 mb-3">
                    Start by adding properties to your management portfolio.
                  </p>
                  <button className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700">
                    Add Property
                  </button>
                </div>
              )}
            </div>
          </div>
        )
      
      case 'users':
        return (
          <div className="p-6">
            <h3 className="text-lg font-medium mb-4">Create Users</h3>
            <div className="space-y-4">
              {step.completed ? (
                <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                  <div className="flex items-center">
                    <span className="text-green-600 mr-2">✅</span>
                    <span className="text-green-800 font-medium">Users created</span>
                  </div>
                  <p className="text-green-700 text-sm mt-1">
                    You have created user accounts for your team.
                  </p>
                </div>
              ) : (
                <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                  <div className="flex items-center">
                    <span className="text-blue-600 mr-2">👥</span>
                    <span className="text-blue-800 font-medium">Set up user accounts</span>
                  </div>
                  <p className="text-blue-700 text-sm mt-1 mb-3">
                    Create accounts for property managers, staff, and tenants.
                  </p>
                  <button className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700">
                    Manage Users
                  </button>
                </div>
              )}
            </div>
          </div>
        )
      
      case 'payments':
        return (
          <div className="p-6">
            <h3 className="text-lg font-medium mb-4">Payment Setup</h3>
            <div className="space-y-4">
              <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
                <div className="flex items-center">
                  <span className="text-yellow-600 mr-2">⚠️</span>
                  <span className="text-yellow-800 font-medium">Configure payment processing</span>
                </div>
                <p className="text-yellow-700 text-sm mt-1 mb-3">
                  Set up Stripe integration for automated rent collection.
                </p>
                <div className="space-y-2">
                  <button className="bg-purple-600 text-white px-4 py-2 rounded-md hover:bg-purple-700 mr-2">
                    Configure Stripe
                  </button>
                  <button className="bg-gray-600 text-white px-4 py-2 rounded-md hover:bg-gray-700">
                    Test Payments
                  </button>
                </div>
              </div>
            </div>
          </div>
        )
      
      case 'integrations':
        return (
          <div className="p-6">
            <h3 className="text-lg font-medium mb-4">Integrations</h3>
            <div className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="border border-gray-200 rounded-lg p-4">
                  <div className="flex items-center mb-2">
                    <span className="text-2xl mr-2">📧</span>
                    <span className="font-medium">Email Notifications</span>
                  </div>
                  <p className="text-sm text-gray-600 mb-3">
                    Configure automated email notifications for tenants and staff.
                  </p>
                  <button className="bg-blue-600 text-white px-3 py-1 rounded text-sm">
                    Configure
                  </button>
                </div>
                
                <div className="border border-gray-200 rounded-lg p-4">
                  <div className="flex items-center mb-2">
                    <span className="text-2xl mr-2">📱</span>
                    <span className="font-medium">SMS Alerts</span>
                  </div>
                  <p className="text-sm text-gray-600 mb-3">
                    Set up SMS notifications for urgent maintenance and payments.
                  </p>
                  <button className="bg-blue-600 text-white px-3 py-1 rounded text-sm">
                    Configure
                  </button>
                </div>
                
                <div className="border border-gray-200 rounded-lg p-4">
                  <div className="flex items-center mb-2">
                    <span className="text-2xl mr-2">🏦</span>
                    <span className="font-medium">QuickBooks</span>
                  </div>
                  <p className="text-sm text-gray-600 mb-3">
                    Sync financial data with QuickBooks for accounting.
                  </p>
                  <button className="bg-green-600 text-white px-3 py-1 rounded text-sm">
                    Connect
                  </button>
                </div>
                
                <div className="border border-gray-200 rounded-lg p-4">
                  <div className="flex items-center mb-2">
                    <span className="text-2xl mr-2">🔐</span>
                    <span className="font-medium">Smart Locks</span>
                  </div>
                  <p className="text-sm text-gray-600 mb-3">
                    Integrate with smart lock systems for access control.
                  </p>
                  <button className="bg-purple-600 text-white px-3 py-1 rounded text-sm">
                    Setup
                  </button>
                </div>
              </div>
            </div>
          </div>
        )
      
      default:
        return (
          <div className="p-6">
            <h3 className="text-lg font-medium mb-4">{step.name}</h3>
            <p className="text-gray-600">Configuration for this step coming soon...</p>
          </div>
        )
    }
  }

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    )
  }

  if (!setupProgress) {
    return (
      <div className="text-center py-12">
        <p className="text-gray-600">Unable to load setup progress.</p>
      </div>
    )
  }

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <div className="text-center">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Setup Wizard</h1>
        <p className="text-gray-600 mb-6">
          Let's get your EstateCore platform configured and ready to use.
        </p>
        
        {/* Progress Bar */}
        <div className="bg-gray-200 rounded-full h-3 mb-8">
          <div 
            className="bg-blue-600 h-3 rounded-full transition-all duration-300"
            style={{ width: `${setupProgress.progress}%` }}
          ></div>
        </div>
        
        <div className="text-sm text-gray-600 mb-8">
          {setupProgress.completed} of {setupProgress.total} steps completed ({Math.round(setupProgress.progress)}%)
        </div>
      </div>

      {/* Step Navigation */}
      <div className="flex justify-center mb-8">
        <div className="flex space-x-8">
          {setupProgress.steps.map((step, index) => (
            <div
              key={step.id}
              className={`flex flex-col items-center cursor-pointer transition-all duration-200 ${
                getStepStatus(step, index) === 'active' ? 'scale-110' : ''
              }`}
              onClick={() => setActiveStep(index)}
            >
              <div className={`w-12 h-12 rounded-full flex items-center justify-center text-xl mb-2 transition-all duration-200 ${
                step.completed 
                  ? 'bg-green-100 text-green-600 border-2 border-green-300' 
                  : index === activeStep
                    ? 'bg-blue-100 text-blue-600 border-2 border-blue-300'
                    : 'bg-gray-100 text-gray-400 border-2 border-gray-300'
              }`}>
                {getStepIcon(step, index)}
              </div>
              <span className={`text-xs font-medium text-center ${
                step.completed 
                  ? 'text-green-600' 
                  : index === activeStep
                    ? 'text-blue-600'
                    : 'text-gray-400'
              }`}>
                {step.name}
              </span>
            </div>
          ))}
        </div>
      </div>

      {/* Step Content */}
      <div className="bg-white rounded-lg shadow-md">
        {renderStepContent(setupProgress.steps[activeStep], activeStep)}
      </div>

      {/* Navigation Buttons */}
      <div className="flex justify-between">
        <button
          onClick={() => setActiveStep(Math.max(0, activeStep - 1))}
          disabled={activeStep === 0}
          className="bg-gray-300 text-gray-700 px-6 py-2 rounded-md hover:bg-gray-400 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          Previous
        </button>
        
        <button
          onClick={() => setActiveStep(Math.min(setupProgress.steps.length - 1, activeStep + 1))}
          disabled={activeStep === setupProgress.steps.length - 1}
          className="bg-blue-600 text-white px-6 py-2 rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          Next
        </button>
      </div>

      {/* Completion Status */}
      {setupProgress.progress === 100 && (
        <div className="bg-green-50 border border-green-200 rounded-lg p-6 text-center">
          <div className="text-4xl mb-4">🎉</div>
          <h3 className="text-xl font-bold text-green-800 mb-2">Setup Complete!</h3>
          <p className="text-green-700 mb-4">
            Congratulations! Your EstateCore platform is fully configured and ready to use.
          </p>
          <button className="bg-green-600 text-white px-6 py-2 rounded-md hover:bg-green-700">
            Go to Dashboard
          </button>
        </div>
      )}
    </div>
  )
}

export default SetupWizard