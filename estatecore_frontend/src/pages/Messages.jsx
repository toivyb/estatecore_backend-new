import React, { useState, useEffect } from 'react'

const Messages = () => {
  const [messages, setMessages] = useState([])
  const [loading, setLoading] = useState(true)
  const [showCompose, setShowCompose] = useState(false)
  const [selectedMessage, setSelectedMessage] = useState(null)
  const [newMessage, setNewMessage] = useState({
    to: '',
    subject: '',
    message: ''
  })

  useEffect(() => {
    fetchMessages()
  }, [])

  const fetchMessages = async () => {
    try {
      const user = JSON.parse(localStorage.getItem('user') || '{}')
      if (!user.id) return
      
      const response = await fetch(`/api/messages?user_id=${user.id}`)
      const data = await response.json()
      
      if (Array.isArray(data)) {
        setMessages(data)
      } else {
        setMessages([])
      }
    } catch (error) {
      console.error('Error fetching messages:', error)
      setMessages([])
    } finally {
      setLoading(false)
    }
  }

  const handleSendMessage = async (e) => {
    e.preventDefault()
    try {
      const response = await fetch('/api/messages', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(newMessage)
      })
      
      if (response.ok) {
        setNewMessage({ to: '', subject: '', message: '' })
        setShowCompose(false)
        fetchMessages()
        alert('Message sent successfully!')
      }
    } catch (error) {
      console.error('Error sending message:', error)
    }
  }

  const getMessageStatusColor = (status) => {
    return status === 'read' ? 'text-gray-600' : 'text-gray-900 font-semibold'
  }

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold text-gray-900">Communications</h1>
        <button
          onClick={() => setShowCompose(!showCompose)}
          className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700"
        >
          📝 Compose Message
        </button>
      </div>

      {/* Communication Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <div className="bg-white p-6 rounded-lg shadow">
          <h3 className="text-sm font-medium text-gray-500">Total Messages</h3>
          <p className="text-2xl font-bold text-gray-900">{messages.length}</p>
        </div>
        <div className="bg-white p-6 rounded-lg shadow">
          <h3 className="text-sm font-medium text-gray-500">Unread</h3>
          <p className="text-2xl font-bold text-red-600">
            {messages.filter(m => m.status === 'unread').length}
          </p>
        </div>
        <div className="bg-white p-6 rounded-lg shadow">
          <h3 className="text-sm font-medium text-gray-500">Today</h3>
          <p className="text-2xl font-bold text-blue-600">
            {messages.filter(m => 
              new Date(m.timestamp).toDateString() === new Date().toDateString()
            ).length}
          </p>
        </div>
        <div className="bg-white p-6 rounded-lg shadow">
          <h3 className="text-sm font-medium text-gray-500">Response Rate</h3>
          <p className="text-2xl font-bold text-green-600">94%</p>
        </div>
      </div>

      {/* Smart Communication Features */}
      <div className="bg-gradient-to-r from-purple-50 to-blue-50 rounded-lg p-6 border border-purple-200">
        <div className="flex items-center mb-4">
          <span className="text-2xl mr-2">💬</span>
          <h3 className="text-lg font-medium text-gray-900">Smart Communication Hub</h3>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="bg-white p-4 rounded-lg">
            <h4 className="font-medium text-purple-800">AI Auto-Responses</h4>
            <p className="text-sm text-gray-600">
              Automatically respond to common tenant inquiries with smart templates.
            </p>
          </div>
          <div className="bg-white p-4 rounded-lg">
            <h4 className="font-medium text-purple-800">Sentiment Analysis</h4>
            <p className="text-sm text-gray-600">
              AI analyzes message tone to prioritize urgent or negative communications.
            </p>
          </div>
          <div className="bg-white p-4 rounded-lg">
            <h4 className="font-medium text-purple-800">Multi-Channel</h4>
            <p className="text-sm text-gray-600">
              Unified inbox for email, SMS, and in-app messages.
            </p>
          </div>
        </div>
      </div>

      {/* Compose Message Form */}
      {showCompose && (
        <div className="bg-white p-6 rounded-lg shadow">
          <h3 className="text-lg font-medium mb-4">Compose Message</h3>
          <form onSubmit={handleSendMessage} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                To
              </label>
              <input
                type="email"
                value={newMessage.to}
                onChange={(e) => setNewMessage({...newMessage, to: e.target.value})}
                className="w-full p-2 border border-gray-300 rounded-md"
                placeholder="recipient@email.com"
                required
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Subject
              </label>
              <input
                type="text"
                value={newMessage.subject}
                onChange={(e) => setNewMessage({...newMessage, subject: e.target.value})}
                className="w-full p-2 border border-gray-300 rounded-md"
                placeholder="Message subject"
                required
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Message
              </label>
              <textarea
                value={newMessage.message}
                onChange={(e) => setNewMessage({...newMessage, message: e.target.value})}
                className="w-full p-2 border border-gray-300 rounded-md"
                rows="6"
                placeholder="Type your message here..."
                required
              />
            </div>
            
            <div className="flex gap-2">
              <button
                type="submit"
                className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700"
              >
                📤 Send Message
              </button>
              <button
                type="button"
                className="bg-gray-600 text-white px-4 py-2 rounded-md hover:bg-gray-700"
              >
                📋 Save Draft
              </button>
              <button
                type="button"
                onClick={() => setShowCompose(false)}
                className="bg-gray-300 text-gray-700 px-4 py-2 rounded-md hover:bg-gray-400"
              >
                Cancel
              </button>
            </div>
          </form>
        </div>
      )}

      {/* Messages List */}
      <div className="bg-white rounded-lg shadow overflow-hidden">
        <div className="px-6 py-4 border-b border-gray-200">
          <h3 className="text-lg font-medium text-gray-900">Message History</h3>
        </div>
        
        <div className="divide-y divide-gray-200">
          {messages.map((message) => (
            <div
              key={message.id}
              className={`p-6 hover:bg-gray-50 cursor-pointer transition-colors ${
                message.status === 'unread' ? 'bg-blue-50' : ''
              }`}
              onClick={() => setSelectedMessage(message)}
            >
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center mb-2">
                    <span className={`text-sm ${getMessageStatusColor(message.status)}`}>
                      {message.from}
                    </span>
                    {message.status === 'unread' && (
                      <span className="ml-2 inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                        New
                      </span>
                    )}
                  </div>
                  
                  <h4 className={`text-base mb-2 ${getMessageStatusColor(message.status)}`}>
                    {message.subject}
                  </h4>
                  
                  <p className="text-sm text-gray-600 mb-2">
                    {message.message.substring(0, 150)}...
                  </p>
                  
                  <div className="flex items-center text-xs text-gray-500">
                    <span>{new Date(message.timestamp).toLocaleDateString()}</span>
                    <span className="mx-2">•</span>
                    <span>{new Date(message.timestamp).toLocaleTimeString()}</span>
                  </div>
                </div>
                
                <div className="ml-4 flex-shrink-0">
                  <button className="text-gray-400 hover:text-gray-600">
                    <span className="text-lg">📧</span>
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Message Detail Modal */}
      {selectedMessage && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-lg max-w-2xl w-full mx-4 max-h-screen overflow-y-auto">
            <div className="p-6 border-b border-gray-200">
              <div className="flex justify-between items-start">
                <div>
                  <h3 className="text-lg font-medium text-gray-900">
                    {selectedMessage.subject}
                  </h3>
                  <p className="text-sm text-gray-600">
                    From: {selectedMessage.from}
                  </p>
                  <p className="text-sm text-gray-600">
                    {new Date(selectedMessage.timestamp).toLocaleString()}
                  </p>
                </div>
                <button
                  onClick={() => setSelectedMessage(null)}
                  className="text-gray-400 hover:text-gray-600"
                >
                  ✕
                </button>
              </div>
            </div>
            
            <div className="p-6">
              <p className="text-gray-900 whitespace-pre-wrap">
                {selectedMessage.message}
              </p>
            </div>
            
            <div className="p-6 border-t border-gray-200 flex gap-2">
              <button className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700">
                📤 Reply
              </button>
              <button className="bg-gray-600 text-white px-4 py-2 rounded-md hover:bg-gray-700">
                ↗️ Forward
              </button>
              <button className="bg-red-600 text-white px-4 py-2 rounded-md hover:bg-red-700">
                🗑️ Delete
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Quick Message Templates */}
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-medium mb-4">Quick Templates</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <button className="text-left p-4 border border-gray-200 rounded-lg hover:bg-gray-50">
            <h4 className="font-medium text-gray-900">Rent Reminder</h4>
            <p className="text-sm text-gray-600">Automated rent payment reminder</p>
          </button>
          <button className="text-left p-4 border border-gray-200 rounded-lg hover:bg-gray-50">
            <h4 className="font-medium text-gray-900">Maintenance Update</h4>
            <p className="text-sm text-gray-600">Status update on maintenance requests</p>
          </button>
          <button className="text-left p-4 border border-gray-200 rounded-lg hover:bg-gray-50">
            <h4 className="font-medium text-gray-900">Lease Renewal</h4>
            <p className="text-sm text-gray-600">Lease renewal discussion template</p>
          </button>
        </div>
      </div>
    </div>
  )
}

export default Messages
