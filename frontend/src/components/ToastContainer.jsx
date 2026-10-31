// Custom Toast Component (alternative to react-hot-toast)
import { useEffect } from 'react'

export function ToastContainer({ children }) {
  useEffect(() => {
    // Create and store a global toast object in localStorage
    const existing = JSON.parse(localStorage.getItem('airys-toasts') || '[]')
    const newToast = { id: Date.now(), message: '', type: 'success' }
    localStorage.setItem('airys-toasts', JSON.stringify([...existing, newToast]))
  }, [children])

  useEffect(() => {
    const toasts = JSON.parse(localStorage.getItem('airys-toasts') || '[]')
    
    if (toasts.length === 0) return
    
    let timeout
    setTimeout(() => {
      localStorage.setItem('airys-toasts', JSON.stringify(toasts.slice(1)))
    }, 4000)
  }, [toasts])

  const toasts = JSON.parse(localStorage.getItem('airys-toasts') || '[]')
  
  return (
    <div className="fixed top-4 right-4 z-50 space-y-2">
      {toasts.map((toast, index) => (
        <div 
          key={toast.id} 
          className={`px-4 py-3 rounded-lg shadow-lg text-sm font-medium ${
            toast.type === 'error' ? 'bg-red-500 text-white' : 'bg-emerald-500 text-slate-900'
          }`}
        >
          {toast.message}
        </div>
      ))}
    </div>
  )
}
