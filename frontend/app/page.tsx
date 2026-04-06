'use client'

import { useEffect, useState } from 'react'
import { Composer } from '@/components/Composer'
import { generateInsights, timeline } from '@/lib/api'
import { Entry, Insight } from '@/types'

/**
 * Render the "Lookback — Rolling Day Canvas" page and manage its timeline and insights state.
 *
 * Initializes `entries` and `insights`, fetches the timeline on mount, and provides UI controls
 * (Composer, Refresh Timeline, Generate Insights) along with Timeline and Insights lists.
 *
 * @returns The rendered HomePage React element
 */
export default function HomePage() {
  const [entries, setEntries] = useState<Entry[]>([])
  const [insights, setInsights] = useState<Insight[]>([])

  const refresh = async () => setEntries(await timeline())

  useEffect(() => {
    refresh()
  }, [])

  return (
    <main>
      <h1>Lookback — Rolling Day Canvas</h1>
      <p>
        Continuously capture voice, text, and screenshots. Enrich with OpenAI/Gemini, then surface trends and
        end-of-day review talking points.
      </p>

      <Composer onSaved={refresh} />

      <div className="card">
        <h3>Actions</h3>
        <div className="row">
          <button onClick={refresh}>Refresh Timeline</button>
          <button onClick={async () => setInsights(await generateInsights())}>Generate Insights</button>
        </div>
      </div>

      <div className="card">
        <h3>Timeline</h3>
        {entries.length === 0 ? (
          <small>No entries yet.</small>
        ) : (
          entries.map((e) => (
            <div key={e.id} style={{ borderBottom: '1px solid #334155', padding: '8px 0' }}>
              <strong>{new Date(e.created_at).toLocaleString()}</strong> · {e.source}
              <div>{e.content}</div>
              <small>
                {e.project || 'General'} / {e.task || '—'}
              </small>
            </div>
          ))
        )}
      </div>

      <div className="card">
        <h3>Insights</h3>
        {insights.length === 0 ? (
          <small>Click “Generate Insights”.</small>
        ) : (
          insights.map((i) => (
            <div key={i.id} style={{ borderBottom: '1px solid #334155', padding: '8px 0' }}>
              <strong>{i.title}</strong> ({Math.round(i.confidence * 100)}%)
              <div>{i.description}</div>
              {i.action && <small>Action: {i.action}</small>}
            </div>
          ))
        )}
      </div>
    </main>
  )
}
