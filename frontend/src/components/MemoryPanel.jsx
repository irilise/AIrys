import { useState, useEffect } from 'react'
import axios from 'axios'

/**
 * Memory Panel Component
 * Shows retrieved memories/context for the current conversation
 */
function MemoryPanel() {
  const [memories, setMemories] = useState([])
  const [searchQuery, setSearchQuery] = useState('')
  const [isSearching, setIsSearching] = useState(false)

  // Search for relevant memories when query changes
  useEffect(() => {
    if (searchQuery.trim()) {
      performMemorySearch()
    } else {
      setMemories([])
    }
  }, [searchQuery])

  const performMemorySearch = async () => {
    setIsSearching(true)
    try {
      const response = await axios.get('/api/v1/memory/search', {
        params: { query: searchQuery, n_results: 5, min_similarity: 0.6 }
      })
      setMemories(response.data.data || [])
    } catch (error) {
      console.error('Error searching memories:', error)
    } finally {
      setIsSearching(false)
    }
  }

  return (
    <div className="memory-panel h-[28rem] bg-black/20 backdrop-blur-sm rounded-xl p-4 mb-4 overflow-hidden">
      <h3 className="text-lg font-bold text-primary-400 mb-3">🧠 Relevant Memories</h3>
      
      <input
        type="text"
        placeholder="Search your memories..."
        value={searchQuery}
        onChange={(e) => setSearchQuery(e.target.value)}
        onKeyPress={(e) => {
          if (e.key === 'Enter') performMemorySearch()
        }}
        className="w-full px-3 py-2 mt-1 bg-white/5 border border-white/20 rounded-lg text-gray-100 focus:outline-none focus:border-primary-500 mb-3"
      />

      {isSearching && <p className="text-emerald-400 italic text-sm mb-3">Searching...</p>}

      {memories.length === 0 ? (
        <p className="text-gray-400">No matching memories found.</p>
      ) : (
        <div className="memory-list flex flex-col gap-2 max-h-[calc(28rem-65px)] overflow-y-auto scrollbar-thin scrollbar-thumb-purple-500/50">
          {memories.map((memory, index) => (
            <div key={index} className="bg-white/5 rounded-lg p-3 transition-all duration-200 hover:bg-primary-600/20 cursor-pointer" onClick={() => console.log(memory)}>
              <p className="text-sm text-gray-200 mb-2">{memory.text}</p>
              <span className="text-xs text-gray-500">Score: {(memory.score * 100).toFixed(0)}%</span>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

export default MemoryPanel
