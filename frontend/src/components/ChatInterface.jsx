import { useEffect, useRef, useState } from 'react'
import axios from 'axios'
import toast from 'react-hot-toast'

function ChatInterface({ serverStatus }) {
  const [messages, setMessages] = useState([])
  const [inputText, setInputText] = useState('')
  const [isSending, setIsSending] = useState(false)
  const [isLoadingHistory, setIsLoadingHistory] = useState(true)
  const messagesEndRef = useRef(null)

  useEffect(() => {
    let active = true
    axios.get('/api/v1/chat/history')
      .then(({ data }) => {
        if (active) {
          setMessages((data.sessions || []).flatMap((exchange) => [
            { role: 'user', content: exchange.user_message, timestamp: exchange.timestamp },
            { role: 'assistant', content: exchange.response, timestamp: exchange.timestamp },
          ]))
        }
      })
      .catch(() => {
        if (active) toast.error('Could not load saved conversation history.')
      })
      .finally(() => {
        if (active) setIsLoadingHistory(false)
      })

    return () => {
      active = false
    }
  }, [])

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const handleSendMessage = async () => {
    const message = inputText.trim()
    if (!message || isSending || serverStatus !== 'connected') return

    setMessages((previous) => [...previous, {
      role: 'user',
      content: message,
      timestamp: new Date().toISOString(),
    }])
    setInputText('')
    setIsSending(true)

    try {
      const { data } = await axios.post('/api/v1/chat/complete', { message })
      setMessages((previous) => [...previous, {
        role: 'assistant',
        content: data.response,
        timestamp: new Date().toISOString(),
      }])
    } catch (error) {
      const detail = error?.response?.data?.detail || 'Failed to get a response from AIrys.'
      toast.error(detail)
      setMessages((previous) => [...previous, {
        role: 'error',
        content: detail,
        timestamp: new Date().toISOString(),
      }])
    } finally {
      setIsSending(false)
    }
  }

  const handleClearHistory = async () => {
    if (!window.confirm('Clear the saved conversation history?')) return
    try {
      await axios.delete('/api/v1/chat/history')
      setMessages([])
      toast.success('Conversation history cleared.')
    } catch {
      toast.error('Could not clear conversation history.')
    }
  }

  const handleKeyDown = (event) => {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault()
      handleSendMessage()
    }
  }

  return (
    <section className="chat-container h-[calc(100vh-7rem)] min-h-[30rem] flex flex-col">
      <div className="flex items-center justify-between border-b border-white/10 px-4 py-3">
        <h2 className="text-lg font-semibold">Chat</h2>
        <button
          type="button"
          onClick={handleClearHistory}
          disabled={messages.length === 0 || isSending}
          className="text-xs text-gray-300 hover:text-white disabled:opacity-40"
        >
          Clear history
        </button>
      </div>

      <div className="chat-messages flex flex-col flex-1 p-4 gap-3 overflow-y-auto">
        {isLoadingHistory ? (
          <p className="text-center text-gray-400">Loading conversation...</p>
        ) : messages.length === 0 ? (
          <div className="welcome-message text-center items-center justify-center min-h-[30vh]">
            <h2 className="text-3xl font-bold mb-4 gradient-text">Welcome to AIrys</h2>
            <p className="text-lg text-gray-300 mb-6">Your personal AI assistant is ready to help.</p>
            <p className="text-sm text-purple-200">Ask a question, plan your day, or share something you want AIrys to remember.</p>
          </div>
        ) : (
          messages.map((message, index) => (
            <div
              key={`${message.timestamp}-${index}`}
              className={`message items-start gap-3 p-3 rounded-xl ${
                message.role === 'user'
                  ? 'flex-row-reverse bg-primary-600/40'
                  : message.role === 'error'
                    ? 'bg-red-500/10'
                    : 'bg-white/5'
              }`}
            >
              <span className="text-xs font-semibold text-primary-300 shrink-0">
                {message.role === 'user' ? 'You' : message.role === 'error' ? 'Error' : 'AIrys'}
              </span>
              <div className={`flex-1 text-sm leading-relaxed break-words whitespace-pre-wrap ${
                message.role === 'error' ? 'text-red-300' : 'text-gray-100'
              }`}>
                {message.content}
              </div>
              {message.timestamp && (
                <time className="text-xs text-gray-500 shrink-0">
                  {new Date(message.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                </time>
              )}
            </div>
          ))
        )}
        {isSending && <p className="text-sm text-purple-200 px-3">AIrys is thinking...</p>}
        <div ref={messagesEndRef} />
      </div>

      <div className="chat-input-area flex items-center gap-2 px-4 py-3 bg-black/30 border-t border-white/10">
        <textarea
          value={inputText}
          onChange={(event) => setInputText(event.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={serverStatus === 'connected' ? 'Type your message...' : 'Connect to the backend to chat'}
          disabled={isSending || serverStatus !== 'connected'}
          rows={2}
          className="flex-1 min-h-[56px] max-h-[150px] px-4 py-2 rounded-lg bg-white/5 border border-white/20 text-gray-100 focus:outline-none focus:border-primary-500 focus:ring-2 focus:ring-primary-500/30 resize-y"
        />
        <button
          type="button"
          onClick={handleSendMessage}
          disabled={!inputText.trim() || isSending || serverStatus !== 'connected'}
          className="primary-button disabled:bg-gray-600/50 disabled:cursor-not-allowed"
          aria-label="Send message"
        >
          {isSending ? '...' : 'Send'}
        </button>
      </div>
      <div className="text-center text-xs text-gray-500 px-2 py-2 bg-black/20">
        Conversations are stored locally on this device.
      </div>
    </section>
  )
}

export default ChatInterface
