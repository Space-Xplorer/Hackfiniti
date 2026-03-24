const BASE_URL = import.meta.env.VITE_API_URL ?? 'http://localhost:8000/api'

function getToken() {
  return localStorage.getItem('token')
}

async function request(path, options = {}) {
  const token = getToken()
  const headers = {
    'Content-Type': 'application/json',
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
    ...options.headers,
  }
  const res = await fetch(`${BASE_URL}${path}`, { ...options, headers })
  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: res.statusText }))
    throw new Error(error.detail ?? 'Request failed')
  }
  return res.json()
}

export const apiClient = {
  // Auth
  register: (data) => request('/auth/register', { method: 'POST', body: JSON.stringify(data) }),
  login: (email, password) => {
    const form = new URLSearchParams({ username: email, password })
    return fetch(`${BASE_URL}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: form,
    }).then((r) => r.json())
  },

  // Applications
  listApplications: () => request('/applications'),
  createApplication: (data) => request('/applications', { method: 'POST', body: JSON.stringify(data) }),
  getApplication: (id) => request(`/applications/${id}`),

  // Workflow
  submitWorkflow: (applicationId) =>
    request('/workflow/submit', { method: 'POST', body: JSON.stringify({ application_id: applicationId }) }),
  getWorkflowStatus: (id) => request(`/workflow/status/${id}`),
  getWorkflowResults: (id) => request(`/workflow/results/${id}`),

  // Health
  getHealth: () => fetch(`${BASE_URL.replace('/api', '')}/health`).then((r) => r.json()),
}
