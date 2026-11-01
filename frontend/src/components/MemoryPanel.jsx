import { useEffect, useState } from 'react'
import axios from 'axios'
import toast from 'react-hot-toast'

function MemoryPanel() {
  const [memories, setMemories] = useState([])
  const [searchQuery, setSearchQuery] = useState('')
  const [content, setContent] = useState('')
  const [category, setCategory] = useState('general')
  const [isLoading, setIsLoading] = useState(false)
  const [isSaving, setIsSaving] = useState(false)

  const loadMemories = async (query = '') => {
    setIsLoading(true)
    try {
      const { data } = query.trim()
        ? await axios.get('/api/v1/memory/search', {
          params: { query: query.trim(), n_results: 10, min_similarity: 0.4 },
        })
        : await axios.get('/api/v1/memory/list', { params: { limit: 50 } })
      setMemories(data.data || [])
    } catch (error) {
      toast.error(error?.response?.data?.detail || 'Could not load memories.')
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    loadMemories()
  }, [])

  const handleSearch = (event) => {
    event.preventDefault()
    loadMemories(searchQuery)
  }

  const handleSave = async (event) => {
    event.preventDefault()
    if (!content.trim() || isSaving) return
    setIsSaving(true)
    try {
      await axios.post('/api/v1/memory/store', {
        content: content.trim(),
        category: category.trim() || 'general',
      })
      setContent('')
      toast.success('Memory saved.')
      await loadMemories(searchQuery)
    } catch (error) {
      toast.error(error?.response?.data?.detail || 'Could not save memory.')
    } finally {
      setIsSaving(false)
    }
  }

  const handleDelete = async (memoryId) => {
    try {
      await axios.delete(`/api/v1/memory/clear/${encodeURIComponent(memoryId)}`)
      setMemories((previous) => previous.filter((memory) => memory.id !== memoryId))
      toast.success('Memory deleted.')
    } catch (error) {
      toast.error(error?.response?.data?.detail || 'Could not delete memory.')
    }
  }

  return (
    <aside className="memory-panel h-[calc(100vh-7rem)] min-h-[30rem] flex flex-col bg-black/20 backdrop-blur-sm rounded-xl p-4 overflow-hidden">
      <h2 className="text-lg font-bold text-primary-400 mb-3">Saved memories</h2>

      <form onSubmit={handleSave} className="space-y-2 mb-4">
        <label htmlFor="memory-content" className="sr-only">New memory</label>
        <textarea
          id="memory-content"
          value={content}
          onChange={(event) => setContent(event.target.value)}
          maxLength={4096}
          rows={3}
          placeholder="Save a preference, fact, or reminder..."
          className="w-full px-3 py-2 bg-white/5 border border-white/20 rounded-lg text-gray-100 focus:outline-none focus:border-primary-500 resize-y"
        />
        <div className="flex gap-2">
          <label htmlFor="memory-category" className="sr-only">Memory category</label>
          <input
            id="memory-category"
            type="text"
            value={category}
            maxLength={64}
            onChange={(event) => setCategory(event.target.value)}
            placeholder="Category"
            className="min-w-0 flex-1 px-3 py-2 bg-white/5 border border-white/20 rounded-lg text-gray-100"
          />
          <button type="submit" disabled={!content.trim() || isSaving} className="primary-button disabled:opacity-50">
            {isSaving ? 'Saving...' : 'Save'}
          </button>
        </div>
      </form>

      <form onSubmit={handleSearch} className="flex gap-2 mb-3">
        <label htmlFor="memory-search" className="sr-only">Search memories</label>
        <input
          id="memory-search"
          type="search"
          value={searchQuery}
          onChange={(event) => setSearchQuery(event.target.value)}
          placeholder="Search memories..."
          className="min-w-0 flex-1 px-3 py-2 bg-white/5 border border-white/20 rounded-lg text-gray-100"
        />
        <button type="submit" className="bg-white/10 hover:bg-white/20">Search</button>
        {searchQuery && (
          <button type="button" onClick={() => { setSearchQuery(''); loadMemories() }} className="bg-white/10 hover:bg-white/20">
            All
          </button>
        )}
      </form>

      <div className="flex-1 overflow-y-auto space-y-2">
        {isLoading ? (
          <p className="text-sm text-gray-400">Loading memories...</p>
        ) : memories.length === 0 ? (
          <p className="text-sm text-gray-400">
            {searchQuery.trim() ? 'No matching memories found.' : 'No saved memories yet.'}
          </p>
        ) : (
          memories.map((memory) => (
            <article key={memory.id} className="bg-white/5 rounded-lg p-3">
              <p className="text-sm text-gray-200 whitespace-pre-wrap break-words">{memory.text}</p>
              <div className="flex items-center justify-between gap-2 mt-2">
                <span className="text-xs text-gray-500">
                  {memory.metadata?.category || 'general'}
                  {typeof memory.score === 'number' && searchQuery.trim()
                    ? ` · ${(memory.score * 100).toFixed(0)}% match`
                    : ''}
                </span>
                <button
                  type="button"
                  onClick={() => handleDelete(memory.id)}
                  className="text-xs text-red-300 hover:text-red-200"
                  aria-label={`Delete memory: ${memory.text}`}
                >
                  Delete
                </button>
              </div>
            </article>
          ))
        )}
      </div>
    </aside>
  )
}

export default MemoryPanel
