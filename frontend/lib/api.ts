import { Entry, Insight } from '@/types'

const API = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

/**
 * Shared helper that wraps fetch and verifies response status before parsing JSON.
 *
 * @param url - The URL to fetch
 * @param options - Fetch options (method, headers, body, etc.)
 * @returns Parsed JSON response
 * @throws Error with status and error details if response is not ok
 */
async function fetchJson<T>(url: string, options?: RequestInit): Promise<T> {
  const res = await fetch(url, options)
  if (!res.ok) {
    let errorMessage = `Request failed with status ${res.status}`
    try {
      const errorData = await res.json()
      errorMessage = errorData.message || errorData.detail || JSON.stringify(errorData)
    } catch {
      // If error response is not JSON, use status text
      errorMessage = res.statusText || errorMessage
    }
    throw new Error(errorMessage)
  }
  return (await res.json()) as T
}

/**
 * Creates a new entry on the server using the provided payload.
 *
 * @param payload - Object containing entry data: `source` (origin identifier), `content` (entry text), and optional `project`, `task`, and `context` fields
 * @returns The created `Entry` as returned by the API
 */
export async function addEntry(payload: {
  source: string
  content: string
  project?: string
  task?: string
  context?: string
}) {
  return fetchJson<Entry>(`${API}/entries`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
}

/**
 * Fetches timeline entries from the configured API.
 *
 * @returns An array of `Entry` objects representing the timeline
 */
export async function timeline() {
  return fetchJson<Entry[]>(`${API}/timeline`, { cache: 'no-store' })
}

/**
 * Triggers the server to generate insights and retrieves the resulting insights.
 *
 * @returns The array of generated `Insight` objects
 */
export async function generateInsights() {
  return fetchJson<Insight[]>(`${API}/insights/generate`, { method: 'POST' })
}