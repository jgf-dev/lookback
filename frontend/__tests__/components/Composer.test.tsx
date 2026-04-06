/**
 * Tests for frontend/components/Composer.tsx
 */

import React from 'react'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { Composer } from '@/components/Composer'
import * as api from '@/lib/api'
import type { Entry } from '@/types'

jest.mock('@/lib/api')

const MOCK_ENTRY: Entry = {
  id: 1,
  created_at: '2024-01-01T12:00:00',
  source: 'manual',
  content: 'hello',
  project: null,
  task: null,
  context: null,
}

describe('Composer', () => {
  const mockAddEntry = api.addEntry as jest.MockedFunction<typeof api.addEntry>
  const mockOnSaved = jest.fn()

  beforeEach(() => {
    mockAddEntry.mockResolvedValue(MOCK_ENTRY)
    mockOnSaved.mockClear()
  })

  // ---------------------------------------------------------------------------
  // Rendering
  // ---------------------------------------------------------------------------

  it('renders the heading', () => {
    render(<Composer onSaved={mockOnSaved} />)
    expect(screen.getByText('Capture thought/comment')).toBeInTheDocument()
  })

  it('renders Project input', () => {
    render(<Composer onSaved={mockOnSaved} />)
    expect(screen.getByPlaceholderText('Project')).toBeInTheDocument()
  })

  it('renders Task input', () => {
    render(<Composer onSaved={mockOnSaved} />)
    expect(screen.getByPlaceholderText('Task')).toBeInTheDocument()
  })

  it('renders the content textarea', () => {
    render(<Composer onSaved={mockOnSaved} />)
    expect(screen.getByPlaceholderText("What are you thinking/doing?")).toBeInTheDocument()
  })

  it('renders Add to Timeline button', () => {
    render(<Composer onSaved={mockOnSaved} />)
    expect(screen.getByRole('button', { name: 'Add to Timeline' })).toBeInTheDocument()
  })

  it('inputs start empty', () => {
    render(<Composer onSaved={mockOnSaved} />)
    expect(screen.getByPlaceholderText('Project')).toHaveValue('')
    expect(screen.getByPlaceholderText('Task')).toHaveValue('')
    expect(screen.getByPlaceholderText("What are you thinking/doing?")).toHaveValue('')
  })

  // ---------------------------------------------------------------------------
  // Interactions
  // ---------------------------------------------------------------------------

  it('updates content textarea on user input', async () => {
    render(<Composer onSaved={mockOnSaved} />)
    const textarea = screen.getByPlaceholderText("What are you thinking/doing?")
    await userEvent.type(textarea, 'my thought')
    expect(textarea).toHaveValue('my thought')
  })

  it('updates project input on user input', async () => {
    render(<Composer onSaved={mockOnSaved} />)
    const input = screen.getByPlaceholderText('Project')
    await userEvent.type(input, 'Alpha')
    expect(input).toHaveValue('Alpha')
  })

  it('updates task input on user input', async () => {
    render(<Composer onSaved={mockOnSaved} />)
    const input = screen.getByPlaceholderText('Task')
    await userEvent.type(input, 'TaskOne')
    expect(input).toHaveValue('TaskOne')
  })

  // ---------------------------------------------------------------------------
  // Save logic
  // ---------------------------------------------------------------------------

  it('does not call addEntry when content is empty', async () => {
    render(<Composer onSaved={mockOnSaved} />)
    await userEvent.click(screen.getByRole('button', { name: 'Add to Timeline' }))
    expect(mockAddEntry).not.toHaveBeenCalled()
  })

  it('does not call onSaved when content is empty', async () => {
    render(<Composer onSaved={mockOnSaved} />)
    await userEvent.click(screen.getByRole('button', { name: 'Add to Timeline' }))
    expect(mockOnSaved).not.toHaveBeenCalled()
  })

  it('does not call addEntry when content is only whitespace', async () => {
    render(<Composer onSaved={mockOnSaved} />)
    await userEvent.type(screen.getByPlaceholderText("What are you thinking/doing?"), '   ')
    await userEvent.click(screen.getByRole('button', { name: 'Add to Timeline' }))
    expect(mockAddEntry).not.toHaveBeenCalled()
  })

  it('calls addEntry with source=manual when content is provided', async () => {
    render(<Composer onSaved={mockOnSaved} />)
    await userEvent.type(screen.getByPlaceholderText("What are you thinking/doing?"), 'my note')
    await userEvent.click(screen.getByRole('button', { name: 'Add to Timeline' }))
    await waitFor(() => expect(mockAddEntry).toHaveBeenCalled())
    expect(mockAddEntry).toHaveBeenCalledWith(
      expect.objectContaining({ source: 'manual', content: 'my note' }),
    )
  })

  it('passes project and task to addEntry', async () => {
    render(<Composer onSaved={mockOnSaved} />)
    await userEvent.type(screen.getByPlaceholderText('Project'), 'Proj1')
    await userEvent.type(screen.getByPlaceholderText('Task'), 'Task1')
    await userEvent.type(screen.getByPlaceholderText("What are you thinking/doing?"), 'note')
    await userEvent.click(screen.getByRole('button', { name: 'Add to Timeline' }))
    await waitFor(() => expect(mockAddEntry).toHaveBeenCalled())
    expect(mockAddEntry).toHaveBeenCalledWith(
      expect.objectContaining({ project: 'Proj1', task: 'Task1' }),
    )
  })

  it('clears content field after successful save', async () => {
    render(<Composer onSaved={mockOnSaved} />)
    const textarea = screen.getByPlaceholderText("What are you thinking/doing?")
    await userEvent.type(textarea, 'note to clear')
    await userEvent.click(screen.getByRole('button', { name: 'Add to Timeline' }))
    await waitFor(() => expect(textarea).toHaveValue(''))
  })

  it('calls onSaved after successful save', async () => {
    render(<Composer onSaved={mockOnSaved} />)
    await userEvent.type(screen.getByPlaceholderText("What are you thinking/doing?"), 'trigger callback')
    await userEvent.click(screen.getByRole('button', { name: 'Add to Timeline' }))
    await waitFor(() => expect(mockOnSaved).toHaveBeenCalledTimes(1))
  })
})