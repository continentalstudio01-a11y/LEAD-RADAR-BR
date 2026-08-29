const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000'

export async function api(path, options = {}) {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: { 'Content-Type': 'application/json', ...(options.headers || {}) },
    ...options,
  })
  if (!response.ok) {
    let message = `Erro ${response.status}`
    try {
      const body = await response.json()
      message = body.detail || body.error || message
    } catch {}
    throw new Error(message)
  }
  const type = response.headers.get('content-type') || ''
  return type.includes('application/json') ? response.json() : response.text()
}

export function exportUrl(minScore = 0) {
  return `${API_BASE}/api/export.csv?min_score=${minScore}`
}
