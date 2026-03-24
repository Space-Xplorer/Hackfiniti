import { useEffect, useRef, useState } from 'react';

const RAW_API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';
const API_BASE_URL = RAW_API_BASE_URL.replace(/\/+$/, '');

export default function useWorkflowStream(token, applicationId) {
  const [events, setEvents] = useState([]);
  const [connected, setConnected] = useState(false);
  const sourceRef = useRef(null);

  useEffect(() => {
    if (!token || !applicationId) {
      return undefined;
    }

    const url = `${API_BASE_URL}/workflow/stream/${applicationId}`;
    const source = new EventSource(url);
    sourceRef.current = source;
    setConnected(true);

    source.onmessage = (evt) => {
      try {
        const data = JSON.parse(evt.data);
        setEvents((prev) => [...prev, data]);
      } catch {
        setEvents((prev) => [...prev, { raw: evt.data }]);
      }
    };

    source.onerror = () => {
      setConnected(false);
      source.close();
    };

    return () => {
      source.close();
      setConnected(false);
    };
  }, [token, applicationId]);

  return { events, connected };
}
