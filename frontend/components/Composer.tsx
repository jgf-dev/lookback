'use client'

import { useState } from 'react'
import { addEntry } from '@/lib/api'

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
