import React from 'react';
import { useTheme } from '../contexts/ThemeContext';

const DarkModeDemo = () => {
  const { isDarkMode, toggleTheme, theme } = useTheme();

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6 max-w-2xl mx-auto">
      <h2 className="text-2xl font-bold text-gray-900 dark:text-gray-100 mb-4">
        Dark Mode Demo
      </h2>
      
      <div className="space-y-4">
        <div className="bg-gray-100 dark:bg-gray-700 p-4 rounded-lg">
          <h3 className="text-lg font-semibold text-gray-800 dark:text-gray-200 mb-2">
            Current Theme Status
          </h3>
          <p className="text-gray-600 dark:text-gray-400">
            Active Theme: <span className="font-mono bg-blue-100 dark:bg-blue-900 px-2 py-1 rounded">{theme}</span>
          </p>
          <p className="text-gray-600 dark:text-gray-400">
            Dark Mode: <span className={`font-semibold ${isDarkMode ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'}`}>
              {isDarkMode ? 'Enabled' : 'Disabled'}
            </span>
          </p>
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="border border-gray-300 dark:border-gray-600 p-4 rounded-lg">
            <h4 className="font-semibold text-gray-700 dark:text-gray-300 mb-2">Theme Features</h4>
            <ul className="text-sm text-gray-600 dark:text-gray-400 space-y-1">
              <li>✅ Automatic system preference detection</li>
              <li>✅ Persistent theme storage</li>
              <li>✅ Smooth transition animations</li>
              <li>✅ Context-based theme management</li>
            </ul>
          </div>
          
          <div className="border border-gray-300 dark:border-gray-600 p-4 rounded-lg">
            <h4 className="font-semibold text-gray-700 dark:text-gray-300 mb-2">Styled Components</h4>
            <div className="space-y-2">
              <button className="w-full bg-blue-600 text-white px-3 py-2 rounded hover:bg-blue-700 transition-colors">
                Primary Button
              </button>
              <button className="w-full border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 px-3 py-2 rounded hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors">
                Secondary Button
              </button>
            </div>
          </div>
        </div>
        
        <div className="bg-gradient-to-r from-blue-500 to-purple-600 p-4 rounded-lg text-white">
          <h4 className="font-semibold mb-2">Theme Toggle Instructions</h4>
          <p className="text-sm opacity-90">
            Click the theme toggle button in the top-right corner of the navigation bar to switch between light and dark modes.
            Your preference will be saved automatically!
          </p>
        </div>
        
        <div className="text-center">
          <button
            onClick={toggleTheme}
            className="inline-flex items-center px-6 py-3 bg-indigo-600 text-white font-semibold rounded-lg hover:bg-indigo-700 transition-colors"
          >
            {isDarkMode ? (
              <>
                <svg className="w-5 h-5 mr-2" fill="currentColor" viewBox="0 0 20 20">
                  <path
                    fillRule="evenodd"
                    d="M10 2a1 1 0 011 1v1a1 1 0 11-2 0V3a1 1 0 011-1zm4 8a4 4 0 11-8 0 4 4 0 018 0zm-.464 4.95l.707.707a1 1 0 001.414-1.414l-.707-.707a1 1 0 00-1.414 1.414zm2.12-10.607a1 1 0 010 1.414l-.706.707a1 1 0 11-1.414-1.414l.707-.707a1 1 0 011.414 0zM17 11a1 1 0 100-2h-1a1 1 0 100 2h1zm-7 4a1 1 0 011 1v1a1 1 0 11-2 0v-1a1 1 0 011-1zM5.05 6.464A1 1 0 106.465 5.05l-.708-.707a1 1 0 00-1.414 1.414l.707.707zm1.414 8.486l-.707.707a1 1 0 01-1.414-1.414l.707-.707a1 1 0 011.414 1.414zM4 11a1 1 0 100-2H3a1 1 0 000 2h1z"
                    clipRule="evenodd"
                  />
                </svg>
                Switch to Light Mode
              </>
            ) : (
              <>
                <svg className="w-5 h-5 mr-2" fill="currentColor" viewBox="0 0 20 20">
                  <path
                    fillRule="evenodd"
                    d="M17.293 13.293A8 8 0 016.707 2.707a8.001 8.001 0 1010.586 10.586z"
                    clipRule="evenodd"
                  />
                </svg>
                Switch to Dark Mode
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
};

export default DarkModeDemo;