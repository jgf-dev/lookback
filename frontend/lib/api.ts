import { Entry, Insight } from '@/types'

const API = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

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
  const res = await fetch(`${API}/entries`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
  return (await res.json()) as Entry
}

/**
 * Fetches timeline entries from the configured API.
 *
 * @returns An array of `Entry` objects representing the timeline
 */
export async function timeline() {
  const res = await fetch(`${API}/timeline`, { cache: 'no-store' })
  return (await res.json()) as Entry[]
}

/**
 * Triggers the server to generate insights and retrieves the resulting insights.
 *
 * @returns The array of generated `Insight` objects
 */
export async function generateInsights() {
  const res = await fetch(`${API}/insights/generate`, { method: 'POST' })
  return (await res.json()) as Insight[]
}
