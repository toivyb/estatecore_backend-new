/**
 * Quick Reply Button Component for EstateCore Chatbot
 * 
 * Renders quick reply buttons for common user responses
 */

import React from 'react';\n\nconst QuickReplyButton = ({ text, onClick }) => {\n    return (\n        <button\n            onClick={() => onClick(text)}\n            className=\"inline-flex items-center px-3 py-1.5 text-sm font-medium text-blue-700 bg-blue-50 hover:bg-blue-100 border border-blue-200 rounded-full transition-colors duration-200 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2\"\n        >\n            {text}\n        </button>\n    );\n};\n\nexport default QuickReplyButton;"