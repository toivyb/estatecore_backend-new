import React from 'react'

const ResponsiveDashboard = ({ children, title, subtitle, actions }) => {
  return (
    <div className="min-h-full">
      {/* Page header */}
      {(title || subtitle || actions) && (
        <div className="bg-white shadow-sm border-b border-gray-200">
          <div className="px-4 sm:px-6 lg:px-8">
            <div className="py-6">
              <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between space-y-4 sm:space-y-0">
                <div>
                  {title && (
                    <h1 className="text-2xl font-bold text-gray-900 sm:text-3xl">
                      {title}
                    </h1>
                  )}
                  {subtitle && (
                    <p className="mt-2 text-sm text-gray-600 sm:text-base">
                      {subtitle}
                    </p>
                  )}
                </div>
                {actions && (
                  <div className="flex flex-col sm:flex-row space-y-2 sm:space-y-0 sm:space-x-3">
                    {actions}
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Page content */}
      <div className="px-4 sm:px-6 lg:px-8 py-6">
        {children}
      </div>
    </div>
  )
}

// Responsive grid container
export const GridContainer = ({ children, className = '' }) => (
  <div className={`grid grid-cols-1 gap-4 sm:gap-6 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 ${className}`}>
    {children}
  </div>
)

// Responsive metric card
export const MetricCard = ({ 
  title, 
  value, 
  change, 
  changeType = 'positive', 
  icon, 
  color = 'blue',
  onClick 
}) => {
  const colorClasses = {
    blue: 'from-blue-500 to-blue-600',
    green: 'from-green-500 to-green-600',
    purple: 'from-purple-500 to-purple-600',
    orange: 'from-orange-500 to-orange-600',
    red: 'from-red-500 to-red-600',
    gray: 'from-gray-500 to-gray-600'
  }

  const changeClasses = {
    positive: 'text-green-600',
    negative: 'text-red-600',
    neutral: 'text-gray-600'
  }

  return (
    <div 
      className={`bg-gradient-to-r ${colorClasses[color]} rounded-lg shadow-sm overflow-hidden ${
        onClick ? 'cursor-pointer hover:shadow-md transition-shadow' : ''
      }`}
      onClick={onClick}
    >
      <div className="p-4 sm:p-6">
        <div className="flex items-center">
          <div className="flex-shrink-0">
            {icon && (
              <div className="text-2xl sm:text-3xl text-white opacity-90">
                {icon}
              </div>
            )}
          </div>
          <div className="ml-4 w-0 flex-1">
            <dl>
              <dt className="text-sm font-medium text-white opacity-90 truncate">
                {title}
              </dt>
              <dd className="flex items-baseline">
                <div className="text-xl sm:text-2xl font-semibold text-white">
                  {value}
                </div>
                {change && (
                  <div className={`ml-2 flex items-baseline text-sm font-semibold ${changeClasses[changeType]}`}>
                    <span className="sr-only">{changeType === 'positive' ? 'Increased' : 'Decreased'} by</span>
                    {change}
                  </div>
                )}
              </dd>
            </dl>
          </div>
        </div>
      </div>
    </div>
  )
}

// Responsive chart container
export const ChartContainer = ({ 
  title, 
  subtitle, 
  children, 
  actions,
  fullWidth = false,
  height = 'h-64 sm:h-80'
}) => (
  <div className={`bg-white rounded-lg shadow-sm border border-gray-200 ${
    fullWidth ? 'col-span-1 sm:col-span-2 lg:col-span-3 xl:col-span-4' : ''
  }`}>
    {(title || subtitle || actions) && (
      <div className="px-4 py-4 sm:px-6 sm:py-5 border-b border-gray-200">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between space-y-2 sm:space-y-0">
          <div>
            {title && (
              <h3 className="text-base sm:text-lg font-medium text-gray-900">
                {title}
              </h3>
            )}
            {subtitle && (
              <p className="mt-1 text-sm text-gray-500">
                {subtitle}
              </p>
            )}
          </div>
          {actions && (
            <div className="flex space-x-2">
              {actions}
            </div>
          )}
        </div>
      </div>
    )}
    <div className={`p-4 sm:p-6 ${height}`}>
      {children}
    </div>
  </div>
)

// Responsive table container
export const TableContainer = ({ children, className = '' }) => (
  <div className={`bg-white shadow-sm rounded-lg border border-gray-200 ${className}`}>
    {children}
  </div>
)

// Responsive form container
export const FormContainer = ({ 
  title, 
  subtitle, 
  children, 
  onSubmit,
  submitText = 'Submit',
  cancelText = 'Cancel',
  onCancel,
  maxWidth = 'max-w-2xl'
}) => (
  <div className={`mx-auto ${maxWidth}`}>
    <div className="bg-white shadow-sm rounded-lg border border-gray-200">
      {(title || subtitle) && (
        <div className="px-4 py-5 sm:px-6 border-b border-gray-200">
          {title && (
            <h3 className="text-lg font-medium text-gray-900">
              {title}
            </h3>
          )}
          {subtitle && (
            <p className="mt-1 text-sm text-gray-500">
              {subtitle}
            </p>
          )}
        </div>
      )}
      <form onSubmit={onSubmit} className="px-4 py-5 sm:p-6 space-y-4 sm:space-y-6">
        {children}
        {(onSubmit || onCancel) && (
          <div className="flex flex-col sm:flex-row sm:justify-end space-y-3 sm:space-y-0 sm:space-x-3 pt-4 border-t border-gray-200">
            {onCancel && (
              <button
                type="button"
                onClick={onCancel}
                className="w-full sm:w-auto px-4 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
              >
                {cancelText}
              </button>
            )}
            {onSubmit && (
              <button
                type="submit"
                className="w-full sm:w-auto px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
              >
                {submitText}
              </button>
            )}
          </div>
        )}
      </form>
    </div>
  </div>
)

// Responsive modal
export const ResponsiveModal = ({ 
  isOpen, 
  onClose, 
  title, 
  children, 
  size = 'default' 
}) => {
  if (!isOpen) return null

  const sizeClasses = {
    small: 'max-w-md',
    default: 'max-w-lg',
    large: 'max-w-2xl',
    xlarge: 'max-w-4xl'
  }

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      <div className="flex items-center justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0">
        <div 
          className="fixed inset-0 bg-gray-500 bg-opacity-75 transition-opacity"
          onClick={onClose}
        ></div>

        <div className={`inline-block align-bottom bg-white rounded-lg px-4 pt-5 pb-4 text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:p-6 w-full ${sizeClasses[size]}`}>
          <div className="flex items-center justify-between mb-4">
            {title && (
              <h3 className="text-lg font-medium text-gray-900">
                {title}
              </h3>
            )}
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-gray-600 focus:outline-none"
            >
              <svg className="h-6 w-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
          {children}
        </div>
      </div>
    </div>
  )
}

export default ResponsiveDashboard