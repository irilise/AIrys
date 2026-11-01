import { useEffect, useState } from 'react'
import axios from 'axios'
import toast from 'react-hot-toast'

function SettingsModal({ onClose }) {
  const [settings, setSettings] = useState({
    ollama_host: 'http://localhost:11434',
    ollama_model: 'llama3.2',
    temperature: 0.7,
    max_tokens: 2048,
  })
  const [isLoading, setIsLoading] = useState(true)
  const [isSaving, setIsSaving] = useState(false)

  useEffect(() => {
    let active = true
    axios.get('/api/v1/settings')
      .then(({ data }) => {
        if (active) setSettings(data)
      })
      .catch((error) => {
        if (active) toast.error(error?.response?.data?.detail || 'Could not load settings.')
      })
      .finally(() => {
        if (active) setIsLoading(false)
      })
    return () => {
      active = false
    }
  }, [])

  const handleSaveSettings = async (event) => {
    event.preventDefault()
    setIsSaving(true)
    try {
      const { data } = await axios.put('/api/v1/settings', settings)
      setSettings(data)
      toast.success('Settings saved and applied.')
      onClose()
    } catch (error) {
      toast.error(error?.response?.data?.detail || 'Could not save settings.')
    } finally {
      setIsSaving(false)
    }
  }

  return (
    <div className="modal-overlay" role="presentation">
      <form
        onSubmit={handleSaveSettings}
        className="settings-modal w-[90vw] max-w-lg rounded-xl p-6 bg-slate-900 shadow-2xl overflow-y-auto max-h-[80vh]"
        aria-labelledby="settings-title"
      >
        <h2 id="settings-title" className="text-2xl font-bold mb-6 gradient-text">Settings</h2>
        {isLoading ? (
          <p className="text-gray-300">Loading settings...</p>
        ) : (
          <>
            <div className="settings-section space-y-4 mb-6 pb-5 border-b border-white/10">
              <h3 className="text-sm text-primary-200 uppercase tracking-wider font-semibold">
                Ollama configuration
              </h3>
              <label htmlFor="ollama-host">
                Ollama host
                <input
                  id="ollama-host"
                  type="url"
                  required
                  maxLength={2048}
                  value={settings.ollama_host}
                  onChange={(event) => setSettings({ ...settings, ollama_host: event.target.value })}
                  placeholder="http://localhost:11434"
                />
              </label>
              <label htmlFor="ollama-model">
                Chat model
                <input
                  id="ollama-model"
                  type="text"
                  required
                  maxLength={128}
                  value={settings.ollama_model}
                  onChange={(event) => setSettings({ ...settings, ollama_model: event.target.value })}
                  placeholder="llama3.2"
                />
              </label>
              <p className="text-xs text-purple-200">
                Changes are stored in the local data directory and apply to new requests immediately.
              </p>
            </div>

            <div className="settings-section space-y-4 mb-6">
              <h3 className="text-sm text-primary-200 uppercase tracking-wider font-semibold">
                Inference
              </h3>
              <label htmlFor="temperature">
                Temperature: {settings.temperature}
                <input
                  id="temperature"
                  type="range"
                  min="0"
                  max="2"
                  step="0.1"
                  value={settings.temperature}
                  onChange={(event) => setSettings({
                    ...settings,
                    temperature: Number(event.target.value),
                  })}
                  className="w-full"
                />
              </label>
              <label htmlFor="max-tokens">
                Maximum response tokens
                <input
                  id="max-tokens"
                  type="number"
                  min="1"
                  max="8192"
                  required
                  value={settings.max_tokens}
                  onChange={(event) => setSettings({
                    ...settings,
                    max_tokens: Number(event.target.value),
                  })}
                />
              </label>
            </div>
          </>
        )}

        <div className="flex justify-end gap-3">
          <button type="button" onClick={onClose} className="bg-white/5 hover:bg-white/10 text-gray-200">
            Cancel
          </button>
          <button
            type="submit"
            disabled={isLoading || isSaving}
            className="primary-button disabled:opacity-50"
          >
            {isSaving ? 'Saving...' : 'Save settings'}
          </button>
        </div>
      </form>
    </div>
  )
}

export default SettingsModal
