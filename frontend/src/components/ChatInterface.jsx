import { useState, useRef, useEffect } from 'react'
import axios from 'axios'
import toast from 'react-hot-toast'

/**
 * Chat Interface Component
 * Main conversational interface with message history and real-time streaming
 */
function ChatInterface({ onServerReconnect }) {
  const [messages, setMessages] = useState([])
  const [inputText, setInputText] = useState('')
  const [isStreaming, setIsStreaming] = useState(false)
  const messagesEndRef = useRef(null)

  // Auto-scroll to bottom when messages change
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  // Check connection on mount
  useEffect(() => {
    const checkInterval = setInterval(checkServerConnection, 5000)
    return () => clearInterval(checkInterval)
  }, [])

  const checkServerConnection = async () => {
    try {
      await axios.get('/api/v1/chat/health')
      if (onServerReconnect) onServerReconnect()
    } catch (error) {
      console.error('Backend server is not responding')
      toast.error('Backend server is not responding')
    }
  }

  const handleSendMessage = async () => {
    if (!inputText.trim() || isStreaming) return

    // Add user message to UI
    setMessages(prev => [...prev, { role: 'user', content: inputText }])
    setInputText('')
    setIsStreaming(true)

    try {
      const response = await axios.post('/api/v1/chat/complete', {
        message: inputText,
        context: null,
        system_prompt: "You are AIrys, a friendly and helpful personal assistant. Be conversational, practical, and supportive."
      })

      setMessages(prev => [...prev, { role: 'assistant', content: response.data.response }])
    } catch (error) {
      console.error('Error sending message:', error)
      toast.error(error?.response?.data?.detail || 'Failed to connect to backend server.')
    } finally {
      setIsStreaming(false)
    }
  }

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSendMessage()
    }
  }

  return (
    <div className="chat-container h-screen lg:h-[calc(100vh-140px)] flex flex-col">
      <div className="chat-messages flex flex-col flex-1 p-2 gap-2 overflow-y-auto scrollbar-thin scrollbar-thumb-purple-500/50 scrollbar-track-transparent">
        {messages.length === 0 ? (
          <div className="welcome-message text-center items-center justify-center min-h-[30vh]">
            <h2 className="text-3xl font-bold mb-4 gradient-text">Welcome to AIrys</h2>
            <p className="text-lg text-gray-300 mb-6">Your personal AI assistant is ready to help!</p>
            <div className="quick-prompts space-y-2 max-w-md mx-auto">
              <p className="text-sm text-purple-200 font-medium">Try asking:</p>
              <ul className="flex flex-wrap gap-2 justify-center">
                <li className="px-3 py-1.5 rounded-full bg-primary-600/30 text-xs text-primary-200 border border-white/10">"What are some tasks I should remember?"</li>
                <li className="px-3 py-1.5 rounded-full bg-primary-600/30 text-xs text-primary-200 border border-white/10">"Remind me to schedule a dentist appointment"</li>
                <li className="px-3 py-1.5 rounded-full bg-primary-600/30 text-xs text-primary-200 border border-white/10">"What do you know about my preferences?"</li>
              </ul>
            </div>
          </div>
        ) : (
          messages.map((msg, index) => (
            <div key={index} className={`message items-start gap-2 p-3 rounded-xl ${msg.role === 'user' ? 'flex-row-reverse bg-primary-600/40' : 'bg-white/5'}`}>
              {msg.role === 'user' && (
                <>
                  <span className="text-sm font-bold text-primary-400 w-16">You</span>
                  <div className="flex-1 text-base leading-relaxed break-words">{msg.content}</div>
                </>
              )}
              {msg.role === 'assistant' && (
                <>
                  <div className="flex-1 text-base leading-relaxed break-words">
                    {msg.content.split('\n').map((line, i) => (
                      <div key={i} className={line.startsWith('*') ? 'italic' : ''}>
                        {line}
                      </div>
                    ))}
                  </div>
                  <span className="text-xs text-gray-500 mt-2">
                    {new Date().toLocaleTimeString()}
                  </span>
                </>
              )}
              {msg.role === 'error' && (
                <div className="flex-1 text-red-400 text-sm italic">⚠️ {msg.content}</div>
              )}
            </div>
          ))
        )}
        <div ref={messagesEndRef} />
      </div>

      <div className="chat-input-area flex items-center gap-2 px-2 py-2 bg-black/30 border-t border-white/10">
        <textarea
          value={inputText}
          onChange={(e) => setInputText(e.target.value)}
          onKeyPress={handleKeyPress}
          placeholder="Type your message..."
          disabled={isStreaming || serverStatus === 'disconnected'}
          rows={1}
          className="flex-1 min-h-[56px] max-h-[150px] px-4 py-2 rounded-lg bg-white/5 border border-white/20 text-gray-100 focus:outline-none focus:border-primary-500 focus:ring-2 focus:ring-primary-500/30 resize-none"
        />
        <button 
          onClick={handleSendMessage}
          disabled={!inputText.trim() || isStreaming || serverStatus === 'disconnected'}
          className={`px-4 py-2 rounded-lg transition-all duration-200 ${!inputText.trim() || isStreaming ? 'bg-gray-600/50 cursor-not-allowed' : 'primary-button hover:-translate-y-0.5 shadow-lg'}`}
        >
          {isStreaming ? '⏳' : '📤'}
        </button>
      </div>

      <div className="text-center text-xs text-gray-500 px-2 py-1 bg-black/20">
        Status: <span className={`inline-block w-20 text-center px-1.5 rounded-full ${serverStatus === 'connected' ? 'bg-emerald-500 text-slate-900' : 'bg-red-500 text-white'}`}>{serverStatus}</span>
      </div>
    </div>
  )
}

export default ChatInterface
