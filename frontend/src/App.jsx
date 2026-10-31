import { useState, useEffect } from 'react'
import axios from 'axios'

/**
 * AIrys Main Application
 * Desktop frontend for the personal AI assistant
 */
function App() {
  const [serverStatus, setServerStatus] = useState('checking...')
  const [showSettings, setShowSettings] = useState(false)

  // Check if backend server is running
  useEffect(() => {
    checkServerConnection()
  }, [])

  const checkServerConnection = async () => {
    try {
      await axios.get('/api/v1/chat/health')
      setServerStatus('connected')
    } catch (error) {
      setServerStatus('disconnected')
      console.error('Backend server is not responding')
      // Show error notification using localStorage toast
      const toasts = JSON.parse(localStorage.getItem('airys-toasts') || '[]')
      toasts.push({ id: Date.now(), message: 'Backend server is not responding', type: 'error' })
      localStorage.setItem('airys-toasts', JSON.stringify(toasts))
    }
  }

  const handleSaveSettings = () => {
    console.log('Saving settings:', arguments[0])
    // Save to localStorage if needed
    setShowSettings(false)
    alert('Settings saved!')
  }

  return (
    <div className="app-container">
      {/* Toast Notifications */}
      <div className="fixed top-4 right-4 z-50 space-y-2">
        {JSON.parse(localStorage.getItem('airys-toasts') || '[]').map((toast, i) => (
          <div key={toast.id} className={`px-4 py-3 rounded-lg shadow-lg text-sm font-medium ${
            toast.type === 'error' ? 'bg-red-500 text-white' : 'bg-emerald-500 text-slate-900'
          }`} onClick={() => {
            const toasts = JSON.parse(localStorage.getItem('airys-toasts') || '[]')
            localStorage.setItem('airys-toasts', JSON.stringify(toasts.slice(1)))
          }}>
            {toast.message}
          </div>
        ))}
      </div>

      <header className="app-header">
        <h1 className="text-3xl font-bold gradient-text">AIrys</h1>
        <div className="header-controls">
          <span className={`server-status ${serverStatus} text-xs px-3 py-1 rounded-full`}>
            {serverStatus}
          </span>
          <button onClick={() => setShowSettings(true)} className="px-4 py-2">⚙️ Settings</button>
        </div>
      </header>

      <main className="app-main p-4 max-w-6xl mx-auto flex-1">
        {!showSettings ? (
          <>
            {serverStatus === 'connected' && <MemoryPanel />}
            <ChatInterface onServerReconnect={checkServerConnection} />
          </>
        ) : (
          <SettingsModal onClose={() => setShowSettings(false)} />
        )}
      </main>
    </div>
  )
}

export default App
