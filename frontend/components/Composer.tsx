'use client'

import { useState } from 'react'
import { addEntry } from '@/lib/api'

/**
 * UI component for creating a manual timeline entry with optional project and task labels.
 *
 * The component renders inputs for project and task, a textarea for the entry content, and a button
 * that saves the entry. Saving is ignored when the content is empty or only whitespace; on save it
 * calls `addEntry({ source: 'manual', content, project, task })`, clears the content field, and
 * invokes the provided `onSaved` callback.
 *
 * @param onSaved - Callback invoked after a successful save to notify parent components
 * @returns The JSX element containing the composer UI (project/task inputs, content textarea, and save button)
 */
export function Composer({ onSaved }: { onSaved: () => void }) {
  const [content, setContent] = useState('')
  const [project, setProject] = useState('')
  const [task, setTask] = useState('')

  const save = async () => {
    if (!content.trim()) return
    await addEntry({ source: 'manual', content, project, task })
    setContent('')
    onSaved()
  }

  return (
    <div className="card">
      <h3>Capture thought/comment</h3>
      <div className="row">
        <input placeholder="Project" value={project} onChange={(e) => setProject(e.target.value)} />
        <input placeholder="Task" value={task} onChange={(e) => setTask(e.target.value)} />
      </div>
      <textarea rows={4} placeholder="What are you thinking/doing?" value={content} onChange={(e) => setContent(e.target.value)} />
      <div style={{ marginTop: 10 }}>
        <button onClick={save}>Add to Timeline</button>
      </div>
    </div>
  )
}
