export type Entry = {
  id: number
  created_at: string
  source: string
  content: string
  project?: string | null
  task?: string | null
  context?: string | null
}

export type Insight = {
  id: number
  created_at: string
  title: string
  description: string
  action?: string | null
  confidence: number
}
