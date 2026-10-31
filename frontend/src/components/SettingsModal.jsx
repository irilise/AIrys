import { useState } from 'react'

/**
 * Settings Modal Component
 * Application configuration and preferences
 */
function SettingsModal({ onClose }) {
  const [settings, setSettings] = useState({
    // Ollama settings
    ollamaHost: 'http://localhost:11434',
    ollamaModel: 'llama3.2',
    
    // Server settings
    serverUrl: 'http://127.0.0.1:7860',
    
    // Model inference settings (future)
    temperature: 0.7,
    maxTokens: 2048,
    
    // UI preferences
    theme: 'dark',
    showContext: true,
    streamingSpeed: 'normal'
  })

  const handleSaveSettings = () => {
    console.log('Saving settings:', settings)
    localStorage.setItem('airys-settings', JSON.stringify(settings))
    toast.success('Settings saved!')
    onClose()
  }

  return (
    <div className="modal-overlay">
      <div className="settings-modal w-[90vw] max-w-lg rounded-xl p-6 bg-slate-900 shadow-2xl overflow-y-auto max-h-[80vh]">
        <h2 className="text-2xl font-bold mb-6 gradient-text">⚙️ Settings</h2>
        
        <div className="settings-section space-y-3 mb-6 pb-5 border-b border-white/10">
          <h3 className="text-sm text-primary-200 uppercase tracking-wider font-semibold mb-2">Ollama Configuration</h3>
          
          <label>
            Host:
            <input
              type="text"
              value={settings.ollamaHost}
              onChange={(e) => setSettings({...settings, ollamaHost: e.target.value})}
              placeholder="http://localhost:11434"
              className="w-full px-3 py-2 mt-1 bg-white/5 border border-white/20 rounded-lg text-gray-100 focus:outline-none focus:border-primary-500"
            />
          </label>
          
          <label>
            Model:
            <input
              type="text"
              value={settings.ollamaModel}
              onChange={(e) => setSettings({...settings, ollamaModel: e.target.value})}
              placeholder="llama3.2"
              className="w-full px-3 py-2 mt-1 bg-white/5 border border-white/20 rounded-lg text-gray-100 focus:outline-none focus:border-primary-500"
            />
          </label>
          
          <p className="text-xs text-purple-200 mb-0">
            Make sure this model is loaded in Ollama first!
            Run: <code className="bg-black/30 px-1.5 py-0.5 rounded text-sm font-mono text-gray-200">ollama run {settings.ollamaModel}</code>
          </p>
        </div>

        <div className="settings-section space-y-3 mb-6 pb-5 border-b border-white/10">
          <h3 className="text-sm text-primary-200 uppercase tracking-wider font-semibold mb-2">Inference Settings</h3>
          
          <label>
            Temperature:
            <input
              type="range"
              min="0"
              max="1"
              step="0.1"
              value={settings.temperature}
              onChange={(e) => setSettings({...settings, temperature: parseFloat(e.target.value)})}
              className="w-full mb-1"
            />
            <span className="text-xs text-gray-300">{settings.temperature}</span>
          </label>
          
          <label>
            Max Tokens:
            <input
              type="number"
              value={settings.maxTokens}
              onChange={(e) => setSettings({...settings, maxTokens: parseInt(e.target.value)})}
              className="w-full px-3 py-2 mt-1 bg-white/5 border border-white/20 rounded-lg text-gray-100 focus:outline-none focus:border-primary-500"
            />
          </label>
        </div>

        <div className="settings-section space-y-3 mb-6 pb-5 border-b border-white/10">
          <h3 className="text-sm text-primary-200 uppercase tracking-wider font-semibold mb-2">UI Preferences</h3>
          
          <label>
            Theme:
            <select
              value={settings.theme}
              onChange={(e) => setSettings({...settings, theme: e.target.value})}
              className="w-full px-3 py-2 mt-1 bg-white/5 border border-white/20 rounded-lg text-gray-100 focus:outline-none focus:border-primary-500"
            >
              <option value="dark">Dark</option>
              <option value="light">Light</option>
              <option value="auto">Auto</option>
            </select>
          </label>
          
          <label>
            Show Context:
            <input
              type="checkbox"
              checked={settings.showContext}
              onChange={(e) => setSettings({...settings, showContext: e.target.checked})}
              className="mt-1 accent-primary-500"
            />
          </label>
        </div>

        <div className="flex justify-end gap-3 mb-6">
          <button onClick={onClose} className="px-4 py-2 bg-white/5 rounded-lg hover:bg-white/10 transition-colors text-gray-200">Cancel</button>
          <button onClick={handleSaveSettings} className="px-4 py-2 bg-gradient-to-r from-primary-500 to-primary-600 text-white font-bold rounded-lg hover:-translate-y-0.5 shadow-lg">Save Settings</button>
        </div>
      </div>
    </div>
  )
}

export default SettingsModal
