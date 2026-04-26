'use client';

import React, { useState } from 'react';
import type { CapturedItem } from '../lib/api';
import { updateItem } from '../lib/api';

const SOURCE_ICONS: Record<string, string> = {
  manual_note: '📝',
  speech: '🎙️',
  audio: '🎵',
  screenshot: '🖼️',
};

interface Props {
  item: CapturedItem;
  onUpdated: (updated: CapturedItem) => void;
}

export default function TimelineItemCard({ item, onUpdated }: Props) {
  const [editing, setEditing] = useState(false);
  const [draft, setDraft] = useState(item.raw_content);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const icon = SOURCE_ICONS[item.source_type] ?? '📌';
  const time = new Date(item.timestamp).toLocaleTimeString([], {
    hour: '2-digit',
    minute: '2-digit',
  });
  const date = new Date(item.timestamp).toLocaleDateString([], {
    month: 'short',
    day: 'numeric',
  });

  async function handleSave() {
    if (draft.trim() === item.raw_content) {
      setEditing(false);
      return;
    }
    setSaving(true);
    setError(null);
    try {
      const updated = await updateItem(item.id, {
        raw_content: draft.trim(),
        user_edits: { edited_at: new Date().toISOString() },
      });
      onUpdated(updated);
      setEditing(false);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Save failed');
    } finally {
      setSaving(false);
    }
  }

  function handleKeyDown(e: React.KeyboardEvent) {
    if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) void handleSave();
    if (e.key === 'Escape') {
      setDraft(item.raw_content);
      setEditing(false);
    }
  }

  const cardStyle: React.CSSProperties = {
    background: '#fff',
    border: '1px solid #e5e7eb',
    borderRadius: 8,
    padding: '12px 16px',
    marginBottom: 10,
    boxShadow: '0 1px 3px rgba(0,0,0,.06)',
  };

  const headerStyle: React.CSSProperties = {
    display: 'flex',
    alignItems: 'center',
    gap: 8,
    marginBottom: 6,
  };

  const metaStyle: React.CSSProperties = {
    fontSize: 12,
    color: '#9ca3af',
    marginLeft: 'auto',
  };

  const contentStyle: React.CSSProperties = {
    fontSize: 15,
    color: '#111827',
    lineHeight: 1.5,
    cursor: 'pointer',
    wordBreak: 'break-word',
  };

  const enrichedStyle: React.CSSProperties = {
    fontSize: 13,
    color: '#6b7280',
    marginTop: 4,
    fontStyle: 'italic',
  };

  const tagStyle: React.CSSProperties = {
    display: 'inline-block',
    background: '#eff6ff',
    color: '#3b82f6',
    borderRadius: 99,
    padding: '1px 8px',
    fontSize: 11,
    marginRight: 4,
    marginTop: 6,
  };

  const taskStyle: React.CSSProperties = {
    fontSize: 12,
    color: '#7c3aed',
    marginTop: 4,
  };

  return (
    <div style={cardStyle}>
      <div style={headerStyle}>
        <span style={{ fontSize: 18 }}>{icon}</span>
        <span
          style={{
            fontSize: 11,
            textTransform: 'uppercase',
            letterSpacing: '0.05em',
            color: '#6b7280',
            fontWeight: 600,
          }}
        >
          {item.source_type.replace('_', ' ')}
        </span>
        <span style={metaStyle}>
          {date} · {time}
          {item.user_edits && (
            <span style={{ marginLeft: 6, color: '#f59e0b' }} title="Edited">
              ✏️
            </span>
          )}
        </span>
      </div>

      {editing ? (
        <div>
          <textarea
            value={draft}
            onChange={(e) => setDraft(e.target.value)}
            onKeyDown={handleKeyDown}
            autoFocus
            rows={3}
            style={{
              width: '100%',
              resize: 'vertical',
              fontSize: 14,
              border: '1px solid #93c5fd',
              borderRadius: 4,
              padding: 6,
              outline: 'none',
              boxSizing: 'border-box',
            }}
          />
          <div style={{ display: 'flex', gap: 6, marginTop: 4 }}>
            <button
              onClick={() => void handleSave()}
              disabled={saving}
              style={{
                fontSize: 12,
                padding: '3px 10px',
                background: '#3b82f6',
                color: '#fff',
                border: 'none',
                borderRadius: 4,
                cursor: 'pointer',
              }}
            >
              {saving ? 'Saving…' : 'Save'}
            </button>
            <button
              onClick={() => {
                setDraft(item.raw_content);
                setEditing(false);
              }}
              style={{
                fontSize: 12,
                padding: '3px 10px',
                background: '#f3f4f6',
                border: 'none',
                borderRadius: 4,
                cursor: 'pointer',
              }}
            >
              Cancel
            </button>
            {error && <span style={{ fontSize: 12, color: '#ef4444' }}>{error}</span>}
          </div>
        </div>
      ) : (
        <div
          style={contentStyle}
          onClick={() => setEditing(true)}
          title="Click to edit"
          role="button"
          tabIndex={0}
          onKeyDown={(e) => e.key === 'Enter' && setEditing(true)}
        >
          {item.raw_content}
        </div>
      )}

      {item.enriched_content && item.enriched_content !== item.raw_content && (
        <div style={enrichedStyle}>{item.enriched_content}</div>
      )}

      {item.inferred_project_task && (
        <div style={taskStyle}>🏷 {item.inferred_project_task}</div>
      )}

      {item.tags.length > 0 && (
        <div>
          {item.tags.map((t) => (
            <span key={t} style={tagStyle}>
              {t}
            </span>
          ))}
        </div>
      )}
    </div>
  );
}
