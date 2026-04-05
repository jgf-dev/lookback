import { Entry, Insight } from '@/types'

const API = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

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

export async function timeline() {
  const res = await fetch(`${API}/timeline`, { cache: 'no-store' })
  return (await res.json()) as Entry[]
}

export async function generateInsights() {
  const res = await fetch(`${API}/insights/generate`, { method: 'POST' })
  return (await res.json()) as Insight[]
}
