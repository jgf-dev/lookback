/**
 * Tests for frontend/lib/api.ts
 *
 * Uses the global `fetch` mock provided by jest-fetch-mock (configured in
 * jest.setup.ts).  The module-level API constant defaults to
 * http://localhost:8000 when NEXT_PUBLIC_API_URL is not set.
 */

import { addEntry, generateInsights, timeline } from '@/lib/api'
import type { Entry, Insight } from '@/types'

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

const MOCK_ENTRY: Entry = {
  id: 1,
  created_at: '2024-01-01T12:00:00',
  source: 'manual',
  content: 'hello world',
  project: 'TestProject',
  task: 'TestTask',
  context: null,
}

const MOCK_INSIGHT: Insight = {
  id: 1,
  created_at: '2024-01-01T12:00:00',
  title: 'Primary focus area',
  description: 'You worked on TestProject.',
  action: 'Block time.',
  confidence: 0.8,
}

// ---------------------------------------------------------------------------
// addEntry
// ---------------------------------------------------------------------------

describe('addEntry', () => {
  beforeEach(() => {
    ;(global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => MOCK_ENTRY,
    })
  })

  it('calls the correct URL', async () => {
    await addEntry({ source: 'manual', content: 'hello' })
    expect(fetch).toHaveBeenCalledWith(
      expect.stringContaining('/entries'),
      expect.any(Object),
    )
  })

  it('uses POST method', async () => {
    await addEntry({ source: 'manual', content: 'hello' })
    const [, options] = (fetch as jest.Mock).mock.calls[0]
    expect(options.method).toBe('POST')
  })

  it('sets Content-Type to application/json', async () => {
    await addEntry({ source: 'manual', content: 'hello' })
    const [, options] = (fetch as jest.Mock).mock.calls[0]
    expect(options.headers['Content-Type']).toBe('application/json')
  })

  it('serialises the payload to JSON body', async () => {
    const payload = { source: 'manual', content: 'note', project: 'P', task: 'T' }
    await addEntry(payload)
    const [, options] = (fetch as jest.Mock).mock.calls[0]
    expect(JSON.parse(options.body)).toMatchObject(payload)
  })

  it('returns parsed Entry object', async () => {
    const result = await addEntry({ source: 'manual', content: 'hello' })
    expect(result).toEqual(MOCK_ENTRY)
  })

  it('includes optional context in body when provided', async () => {
    await addEntry({ source: 'manual', content: 'x', context: 'myCtx' })
    const [, options] = (fetch as jest.Mock).mock.calls[0]
    const body = JSON.parse(options.body)
    expect(body.context).toBe('myCtx')
  })

  it('omits undefined optional fields from serialisation gracefully', async () => {
    await addEntry({ source: 'manual', content: 'minimal' })
    const [, options] = (fetch as jest.Mock).mock.calls[0]
    const body = JSON.parse(options.body)
    expect(body.source).toBe('manual')
    expect(body.content).toBe('minimal')
  })
})

// ---------------------------------------------------------------------------
// timeline
// ---------------------------------------------------------------------------

describe('timeline', () => {
  beforeEach(() => {
    ;(global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => [MOCK_ENTRY],
    })
  })

  it('calls the correct URL', async () => {
    await timeline()
    expect(fetch).toHaveBeenCalledWith(
      expect.stringContaining('/timeline'),
      expect.any(Object),
    )
  })

  it('uses cache: no-store option', async () => {
    await timeline()
    const [, options] = (fetch as jest.Mock).mock.calls[0]
    expect(options.cache).toBe('no-store')
  })

  it('returns array of Entry objects', async () => {
    const result = await timeline()
    expect(Array.isArray(result)).toBe(true)
    expect(result[0]).toEqual(MOCK_ENTRY)
  })

  it('returns empty array when server returns []', async () => {
    ;(global.fetch as jest.Mock).mockReset()
    ;(global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => [],
    })
    const result = await timeline()
    expect(result).toEqual([])
  })

  it('does not use POST method', async () => {
    await timeline()
    const [, options] = (fetch as jest.Mock).mock.calls[0]
    expect(options.method).toBeUndefined()
  })
})

// ---------------------------------------------------------------------------
// generateInsights
// ---------------------------------------------------------------------------

describe('generateInsights', () => {
  beforeEach(() => {
    ;(global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => [MOCK_INSIGHT],
    })
  })

  it('calls the correct URL', async () => {
    await generateInsights()
    expect(fetch).toHaveBeenCalledWith(
      expect.stringContaining('/insights/generate'),
      expect.any(Object),
    )
  })

  it('uses POST method', async () => {
    await generateInsights()
    const [, options] = (fetch as jest.Mock).mock.calls[0]
    expect(options.method).toBe('POST')
  })

  it('returns array of Insight objects', async () => {
    const result = await generateInsights()
    expect(Array.isArray(result)).toBe(true)
    expect(result[0]).toEqual(MOCK_INSIGHT)
  })

  it('returns empty array when no insights available', async () => {
    ;(global.fetch as jest.Mock).mockReset()
    ;(global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => [],
    })
    const result = await generateInsights()
    expect(result).toEqual([])
  })

  it('hits the /insights/generate path not /insights', async () => {
    await generateInsights()
    const [url] = (fetch as jest.Mock).mock.calls[0]
    expect(url).toMatch(/\/insights\/generate$/)
  })
})

// ---------------------------------------------------------------------------
// API base URL resolution
// ---------------------------------------------------------------------------

describe('API base URL', () => {
  it('defaults to http://localhost:8000 when env var is absent', async () => {
    ;(global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => [],
    })
    await timeline()
    const [url] = (fetch as jest.Mock).mock.calls[0]
    expect(url).toMatch(/^http:\/\/localhost:8000/)
  })
})