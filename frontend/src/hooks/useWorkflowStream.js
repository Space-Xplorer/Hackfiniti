import { useEffect, useRef, useState } from 'react'

const BASE_URL = import.meta.env.VITE_API_URL ?? 'http://localhost:8000/api'

export function useWorkflowStream(applicationId) {
  const [events, setEvents] = useState([])
  const [connected, setConnected] = useState(false)
  const esRef = useRef(null)

  useEffect(() => {
    if (!applicationId) return
    const token = localStorage.getItem('token')
    const url = `${BASE_URL}/workflow/stream/${applicationId}?token=${token}`
    const es = new EventSource(url)
    esRef.current = es

    es.onopen = () => setConnected(true)
    es.onmessage = (e) => setEvents((prev) => [...prev, JSON.parse(e.data)])
    es.onerror = () => {
      setConnected(false)
      es.close()
    }

    return () => {
      es.close()
      setConnected(false)
    }
  }, [applicationId])

  return { connected, events }
}
