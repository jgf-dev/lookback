'use client';

import React, { useRef, useState } from 'react';
import type { CapturedItem } from '../lib/api';
import { createNote, transcribeAudio, uploadScreenshot } from '../lib/api';

interface Props {
  onCaptured: (item: CapturedItem) => void;
}

export default function CaptureBar({ onCaptured }: Props) {
  const [note, setNote] = useState('');
  const [busy, setBusy] = useState<'note' | 'audio' | 'image' | null>(null);
  const [error, setError] = useState<string | null>(null);
  const audioRef = useRef<HTMLInputElement>(null);
  const imageRef = useRef<HTMLInputElement>(null);

  async function submitNote(e: React.FormEvent) {
    e.preventDefault();
    const text = note.trim();
    if (!text) return;
    setBusy('note');
    setError(null);
    try {
      const item = await createNote(text);
      onCaptured(item);
      setNote('');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save note');
    } finally {
      setBusy(null);
    }
  }

  async function handleAudio(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;
    setBusy('audio');
    setError(null);
    try {
      const item = await transcribeAudio(file);
      onCaptured(item);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Audio transcription failed');
    } finally {
      setBusy(null);
      if (audioRef.current) audioRef.current.value = '';
    }
  }

  async function handleImage(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;
    setBusy('image');
    setError(null);
    try {
      const item = await uploadScreenshot(file);
      onCaptured(item);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Screenshot analysis failed');
    } finally {
      setBusy(null);
      if (imageRef.current) imageRef.current.value = '';
    }
  }

  const containerStyle: React.CSSProperties = {
    background: '#fff',
    border: '1px solid #e5e7eb',
    borderRadius: 10,
    padding: 14,
    marginBottom: 18,
    boxShadow: '0 1px 4px rgba(0,0,0,.07)',
  };

  const rowStyle: React.CSSProperties = {
    display: 'flex',
    gap: 8,
    alignItems: 'flex-end',
  };

  const textareaStyle: React.CSSProperties = {
    flexGrow: 1,
    resize: 'none',
    fontSize: 14,
    padding: '8px 10px',
    border: '1px solid #d1d5db',
    borderRadius: 6,
    outline: 'none',
    fontFamily: 'inherit',
    lineHeight: 1.5,
  };

  const btnStyle: React.CSSProperties = {
    padding: '8px 14px',
    border: 'none',
    borderRadius: 6,
    fontSize: 13,
    cursor: 'pointer',
    whiteSpace: 'nowrap',
  };

  const iconBtnStyle: React.CSSProperties = {
    ...btnStyle,
    background: '#f3f4f6',
    color: '#374151',
    fontSize: 18,
    padding: '6px 10px',
  };

  return (
    <div style={containerStyle}>
      <form onSubmit={(e) => void submitNote(e)}>
        <div style={rowStyle}>
          <textarea
            value={note}
            onChange={(e) => setNote(e.target.value)}
            placeholder="Capture a thought, note, or observation…"
            rows={2}
            style={textareaStyle}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) {
                void submitNote(e as unknown as React.FormEvent);
              }
            }}
            disabled={busy !== null}
            aria-label="Note text"
          />
          <button
            type="submit"
            disabled={busy !== null || !note.trim()}
            style={{
              ...btnStyle,
              background: busy === 'note' ? '#93c5fd' : '#3b82f6',
              color: '#fff',
            }}
          >
            {busy === 'note' ? '…' : 'Add'}
          </button>
        </div>

        <div style={{ display: 'flex', gap: 8, marginTop: 8 }}>
          {/* Audio upload */}
          <input
            ref={audioRef}
            type="file"
            accept="audio/*"
            style={{ display: 'none' }}
            onChange={(e) => void handleAudio(e)}
            aria-label="Upload audio for transcription"
          />
          <button
            type="button"
            title="Upload audio for transcription (Whisper)"
            onClick={() => audioRef.current?.click()}
            disabled={busy !== null}
            style={iconBtnStyle}
          >
            {busy === 'audio' ? '⏳' : '🎵'}
          </button>

          {/* Screenshot upload */}
          <input
            ref={imageRef}
            type="file"
            accept="image/*"
            style={{ display: 'none' }}
            onChange={(e) => void handleImage(e)}
            aria-label="Upload screenshot for analysis"
          />
          <button
            type="button"
            title="Upload screenshot for analysis (Gemini)"
            onClick={() => imageRef.current?.click()}
            disabled={busy !== null}
            style={iconBtnStyle}
          >
            {busy === 'image' ? '⏳' : '🖼️'}
          </button>

          <span
            style={{ fontSize: 11, color: '#9ca3af', alignSelf: 'center', marginLeft: 4 }}
          >
            ⌘+Enter to submit
          </span>
        </div>
      </form>

      {error && (
        <p
          role="alert"
          style={{ marginTop: 8, fontSize: 12, color: '#ef4444' }}
        >
          {error}
        </p>
      )}
    </div>
  );
}
