import React, { useState, useEffect, useRef } from 'react';
import api from '../api';

const ConversationalAI = () => {
  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [sessionId, setSessionId] = useState(null);
  const [quickActions, setQuickActions] = useState([]);
  const [activeTab, setActiveTab] = useState('chat');
  const [conversationHistory, setConversationHistory] = useState([]);
  const [userSessions, setUserSessions] = useState([]);
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);

  // Auto-scroll to bottom
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Initialize component
  useEffect(() => {
    loadQuickActions();
    loadUserSessions();
    
    // Welcome message
    const welcomeMessage = {
      id: Date.now(),
      type: 'bot',
      content: "Hello! I'm your EstateCore AI assistant. I can help you with property management, maintenance, financial reports, and market intelligence. How can I assist you today?",
      timestamp: new Date().toISOString(),
      intent: 'greeting',
      confidence: 1.0
    };
    
    setMessages([welcomeMessage]);
  }, []);

  // Load quick actions
  const loadQuickActions = async () => {
    try {
      const result = await api.get('/api/chatbot/quick-actions');
      if (result.success) {
        setQuickActions(result.data);
      }
    } catch (error) {
      console.error('Failed to load quick actions:', error);
    }
  };

  // Load user sessions
  const loadUserSessions = async () => {
    try {
      const user = JSON.parse(localStorage.getItem('user') || '{}');
      const userId = user.id || 1;
      
      const result = await api.get(`/api/chatbot/sessions?user_id=${userId}`);
      if (result.success) {
        setUserSessions(result.data);
      }
    } catch (error) {
      console.error('Failed to load user sessions:', error);
    }
  };

  // Send message to chatbot
  const sendMessage = async (messageText = inputMessage) => {
    if (!messageText.trim() || isLoading) return;

    const user = JSON.parse(localStorage.getItem('user') || '{}');
    const userId = user.id || 'anonymous';

    // Add user message to UI
    const userMessage = {
      id: Date.now(),
      type: 'user',
      content: messageText,
      timestamp: new Date().toISOString()
    };

    setMessages(prev => [...prev, userMessage]);
    setInputMessage('');
    setIsLoading(true);

    try {
      const result = await api.post('/api/chatbot/message', {
        message: messageText,
        user_id: userId,
        session_id: sessionId
      });

      if (result.success) {
        const botData = result.data;
        
        // Update session ID if new
        if (!sessionId && botData.session_id) {
          setSessionId(botData.session_id);
        }

        // Add bot response to UI
        const botMessage = {
          id: Date.now() + 1,
          type: 'bot',
          content: botData.response,
          timestamp: botData.timestamp,
          intent: botData.intent,
          confidence: botData.confidence,
          entities: botData.entities,
          suggestedActions: botData.suggested_actions,
          requiresFollowup: botData.requires_followup,
          responseType: botData.response_type
        };

        setMessages(prev => [...prev, botMessage]);
      } else {
        // Add error message
        const errorMessage = {
          id: Date.now() + 1,
          type: 'bot',
          content: `Sorry, I encountered an error: ${result.error}`,
          timestamp: new Date().toISOString(),
          responseType: 'error'
        };

        setMessages(prev => [...prev, errorMessage]);
      }
    } catch (error) {
      console.error('Failed to send message:', error);
      
      const errorMessage = {
        id: Date.now() + 1,
        type: 'bot',
        content: 'Sorry, I\'m having trouble connecting right now. Please try again.',
        timestamp: new Date().toISOString(),
        responseType: 'error'
      };

      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  // Handle quick action click
  const handleQuickAction = (action) => {
    sendMessage(action.text);
  };

  // Handle suggested action click
  const handleSuggestedAction = (action) => {
    sendMessage(action.text);
  };

  // Load conversation history
  const loadConversationHistory = async (sessionId) => {
    try {
      const result = await api.get(`/api/chatbot/conversation/${sessionId}`);
      if (result.success) {
        setConversationHistory(result.data);
      }
    } catch (error) {
      console.error('Failed to load conversation history:', error);
    }
  };

  // Start new conversation
  const startNewConversation = () => {
    setMessages([{
      id: Date.now(),
      type: 'bot',
      content: "Hello! I'm your EstateCore AI assistant. How can I help you today?",
      timestamp: new Date().toISOString(),
      intent: 'greeting',
      confidence: 1.0
    }]);
    setSessionId(null);
    setInputMessage('');
  };

  // Format timestamp
  const formatTimestamp = (timestamp) => {
    return new Date(timestamp).toLocaleTimeString('en-US', {
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  // Group quick actions by category
  const groupedQuickActions = quickActions.reduce((acc, action) => {
    if (!acc[action.category]) {
      acc[action.category] = [];
    }
    acc[action.category].push(action);
    return acc;
  }, {});

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      <div className="container mx-auto px-4 py-8">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100 mb-2">
            🤖 AI-Powered Conversational Assistant
          </h1>
          <p className="text-gray-600 dark:text-gray-400">
            Chat with your AI assistant for property management, maintenance, and market insights
          </p>
        </div>

        {/* Navigation Tabs */}
        <div className="mb-6">
          <div className="flex space-x-1 bg-white dark:bg-gray-800 rounded-lg p-1 shadow">
            <button
              onClick={() => setActiveTab('chat')}
              className={`flex-1 px-4 py-2 rounded-md font-medium text-sm transition-colors ${
                activeTab === 'chat'
                  ? 'bg-blue-100 text-blue-700 dark:bg-blue-900 dark:text-blue-200'
                  : 'text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200'
              }`}
            >
              💬 Chat
            </button>
            <button
              onClick={() => setActiveTab('actions')}
              className={`flex-1 px-4 py-2 rounded-md font-medium text-sm transition-colors ${
                activeTab === 'actions'
                  ? 'bg-blue-100 text-blue-700 dark:bg-blue-900 dark:text-blue-200'
                  : 'text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200'
              }`}
            >
              ⚡ Quick Actions
            </button>
            <button
              onClick={() => setActiveTab('history')}
              className={`flex-1 px-4 py-2 rounded-md font-medium text-sm transition-colors ${
                activeTab === 'history'
                  ? 'bg-blue-100 text-blue-700 dark:bg-blue-900 dark:text-blue-200'
                  : 'text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200'
              }`}
            >
              📜 History
            </button>
          </div>
        </div>

        {/* Tab Content */}
        {activeTab === 'chat' && (
          <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
            {/* Chat Interface */}
            <div className="lg:col-span-3">
              <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg flex flex-col" style={{ height: '600px' }}>
                {/* Chat Header */}
                <div className="p-4 border-b border-gray-200 dark:border-gray-700 flex justify-between items-center">
                  <div className="flex items-center">
                    <div className="w-3 h-3 bg-green-500 rounded-full mr-2"></div>
                    <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
                      EstateCore AI Assistant
                    </h3>
                  </div>
                  <button
                    onClick={startNewConversation}
                    className="text-sm text-blue-600 hover:text-blue-700 dark:text-blue-400 dark:hover:text-blue-300"
                  >
                    🔄 New Chat
                  </button>
                </div>

                {/* Messages Area */}
                <div className="flex-1 overflow-y-auto p-4 space-y-4">
                  {messages.map((message) => (
                    <div
                      key={message.id}
                      className={`flex ${message.type === 'user' ? 'justify-end' : 'justify-start'}`}
                    >
                      <div className={`max-w-xs lg:max-w-md ${
                        message.type === 'user'
                          ? 'bg-blue-600 text-white'
                          : message.responseType === 'error'
                          ? 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200'
                          : 'bg-gray-100 text-gray-900 dark:bg-gray-700 dark:text-gray-100'
                      } rounded-lg p-3`}>
                        <div className="text-sm whitespace-pre-wrap">{message.content}</div>
                        
                        {/* Message metadata */}
                        <div className="mt-2 text-xs opacity-75">
                          {formatTimestamp(message.timestamp)}
                          {message.intent && message.intent !== 'unclear' && (
                            <span className="ml-2">
                              • {message.intent.replace('_', ' ')}
                              {message.confidence && (
                                <span className="ml-1">({Math.round(message.confidence * 100)}%)</span>
                              )}
                            </span>
                          )}
                        </div>

                        {/* Suggested Actions */}
                        {message.suggestedActions && message.suggestedActions.length > 0 && (
                          <div className="mt-3 flex flex-wrap gap-2">
                            {message.suggestedActions.map((action, index) => (
                              <button
                                key={index}
                                onClick={() => handleSuggestedAction(action)}
                                className="px-2 py-1 bg-blue-100 text-blue-700 dark:bg-blue-900 dark:text-blue-200 rounded text-xs hover:bg-blue-200 dark:hover:bg-blue-800"
                              >
                                {action.text}
                              </button>
                            ))}
                          </div>
                        )}

                        {/* Entities */}
                        {message.entities && message.entities.length > 0 && (
                          <div className="mt-2 text-xs opacity-60">
                            Detected: {message.entities.map(e => `${e.type}: ${e.value}`).join(', ')}
                          </div>
                        )}
                      </div>
                    </div>
                  ))}
                  
                  {isLoading && (
                    <div className="flex justify-start">
                      <div className="bg-gray-100 text-gray-900 dark:bg-gray-700 dark:text-gray-100 rounded-lg p-3">
                        <div className="flex items-center">
                          <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600 mr-2"></div>
                          <span className="text-sm">AI is thinking...</span>
                        </div>
                      </div>
                    </div>
                  )}
                  
                  <div ref={messagesEndRef} />
                </div>

                {/* Input Area */}
                <div className="p-4 border-t border-gray-200 dark:border-gray-700">
                  <form
                    onSubmit={(e) => {
                      e.preventDefault();
                      sendMessage();
                    }}
                    className="flex space-x-2"
                  >
                    <input
                      ref={inputRef}
                      type="text"
                      value={inputMessage}
                      onChange={(e) => setInputMessage(e.target.value)}
                      placeholder="Ask me about properties, maintenance, financials, or market data..."
                      className="flex-1 px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
                      disabled={isLoading}
                    />
                    <button
                      type="submit"
                      disabled={isLoading || !inputMessage.trim()}
                      className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      {isLoading ? '⏳' : '📤'}
                    </button>
                  </form>
                </div>
              </div>
            </div>

            {/* Quick Actions Sidebar */}
            <div className="lg:col-span-1">
              <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-4">
                <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4">
                  Quick Actions
                </h3>
                <div className="space-y-4">
                  {Object.entries(groupedQuickActions).map(([category, actions]) => (
                    <div key={category}>
                      <h4 className="text-sm font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wide mb-2">
                        {category}
                      </h4>
                      <div className="space-y-2">
                        {actions.map((action) => (
                          <button
                            key={action.id}
                            onClick={() => handleQuickAction(action)}
                            className="w-full text-left px-3 py-2 text-sm bg-gray-50 dark:bg-gray-700 hover:bg-gray-100 dark:hover:bg-gray-600 rounded-lg transition-colors flex items-center"
                          >
                            <span className="mr-2">{action.icon}</span>
                            <span className="text-gray-900 dark:text-gray-100">{action.text}</span>
                          </button>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Quick Actions Tab */}
        {activeTab === 'actions' && (
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6">
            <h2 className="text-xl font-semibold text-gray-900 dark:text-gray-100 mb-6">
              Available Actions
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {Object.entries(groupedQuickActions).map(([category, actions]) => (
                <div key={category} className="space-y-4">
                  <h3 className="text-lg font-medium text-gray-900 dark:text-gray-100 capitalize">
                    {category} Actions
                  </h3>
                  <div className="space-y-3">
                    {actions.map((action) => (
                      <div
                        key={action.id}
                        className="p-4 bg-gray-50 dark:bg-gray-700 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-600 cursor-pointer transition-colors"
                        onClick={() => {
                          setActiveTab('chat');
                          handleQuickAction(action);
                        }}
                      >
                        <div className="flex items-center mb-2">
                          <span className="text-2xl mr-3">{action.icon}</span>
                          <h4 className="font-medium text-gray-900 dark:text-gray-100">
                            {action.text}
                          </h4>
                        </div>
                        <p className="text-sm text-gray-500 dark:text-gray-400 capitalize">
                          {category} • Click to ask
                        </p>
                      </div>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* History Tab */}
        {activeTab === 'history' && (
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6">
            <div className="flex justify-between items-center mb-6">
              <h2 className="text-xl font-semibold text-gray-900 dark:text-gray-100">
                Conversation History
              </h2>
              <button
                onClick={loadUserSessions}
                className="text-sm text-blue-600 hover:text-blue-700 dark:text-blue-400 dark:hover:text-blue-300"
              >
                🔄 Refresh
              </button>
            </div>

            {userSessions.length === 0 ? (
              <div className="text-center py-8 text-gray-500 dark:text-gray-400">
                <p className="text-lg mb-2">📝 No conversation history yet</p>
                <p>Start chatting to see your conversation history here.</p>
              </div>
            ) : (
              <div className="space-y-4">
                {userSessions.map((session, index) => (
                  <div
                    key={session.session_id}
                    className="p-4 bg-gray-50 dark:bg-gray-700 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-600 cursor-pointer transition-colors"
                    onClick={() => loadConversationHistory(session.session_id)}
                  >
                    <div className="flex justify-between items-start">
                      <div>
                        <h4 className="font-medium text-gray-900 dark:text-gray-100">
                          Session #{index + 1}
                        </h4>
                        <p className="text-sm text-gray-500 dark:text-gray-400">
                          Started: {new Date(session.created_at).toLocaleString()}
                        </p>
                        <p className="text-sm text-gray-500 dark:text-gray-400">
                          Last activity: {new Date(session.last_activity).toLocaleString()}
                        </p>
                      </div>
                      <span className="text-sm text-blue-600 dark:text-blue-400">
                        View →
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default ConversationalAI;