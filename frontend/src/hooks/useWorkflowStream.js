import { useEffect, useRef, useState } from 'react'

const API_BASE_URL = (import.meta.env.VITE_API_URL || 'http://localhost:8000/api').replace(/\/+$/, '')

export default function useWorkflowStream(token, applicationId) {
  const [events, setEvents] = useState([])
  const [connected, setConnected] = useState(false)
  const sourceRef = useRef(null)

  useEffect(() => {
    if (!token || !applicationId) return

    const source = new EventSource(`${API_BASE_URL}/workflow/stream/${applicationId}`)
    sourceRef.current = source
    setConnected(true)

    source.onmessage = (evt) => {
      try {
        setEvents((prev) => [...prev, JSON.parse(evt.data)])
      } catch {
        setEvents((prev) => [...prev, { raw: evt.data }])
      }
    }

    source.onerror = () => {
      setConnected(false)
      source.close()
    }

    return () => {
      source.close()
      setConnected(false)
    }
  }, [token, applicationId])

  return { events, connected }
}
