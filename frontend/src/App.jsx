import { useEffect, useRef, useState } from 'react'
import axios from 'axios'
import toast, { Toaster } from 'react-hot-toast'
import ChatInterface from './components/ChatInterface'
import MemoryPanel from './components/MemoryPanel'
import SettingsModal from './components/SettingsModal'

function App() {
  const [serverStatus, setServerStatus] = useState('checking...')
  const [showSettings, setShowSettings] = useState(false)
  const connectionLost = useRef(false)

  useEffect(() => {
    let active = true

    const checkServerConnection = async () => {
      try {
        await axios.get('/api/v1/chat/health')
        if (active) {
          setServerStatus('connected')
          connectionLost.current = false
        }
      } catch {
        if (active) {
          setServerStatus('disconnected')
          if (!connectionLost.current) toast.error('Backend server is not responding.')
          connectionLost.current = true
        }
      }
    }

    checkServerConnection()
    const intervalId = window.setInterval(checkServerConnection, 10000)
    return () => {
      active = false
      window.clearInterval(intervalId)
    }
  }, [])

  return (
    <div className="app-container">
      <Toaster position="top-right" />
      <header className="app-header">
        <h1 className="text-3xl font-bold gradient-text">AIrys</h1>
        <div className="header-controls">
          <span className={`server-status ${serverStatus} text-xs px-3 py-1 rounded-full`}>
            {serverStatus}
          </span>
          <button onClick={() => setShowSettings(true)} className="px-4 py-2">
            Settings
          </button>
        </div>
      </header>

      <main className="app-main p-4 max-w-6xl mx-auto flex-1 w-full">
        {showSettings ? (
          <SettingsModal onClose={() => setShowSettings(false)} />
        ) : (
          <div className="grid gap-4 lg:grid-cols-[minmax(0,2fr)_minmax(18rem,1fr)]">
            <ChatInterface serverStatus={serverStatus} />
            <MemoryPanel />
          </div>
        )}
      </main>
    </div>
  )
}

export default App
