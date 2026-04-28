'use client';

import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import type { ReviewResponse } from '../../lib/api';
import { fetchTodayReview } from '../../lib/api';

export default function ReviewPage() {
  const [review, setReview] = useState<ReviewResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [speaking, setSpeaking] = useState(false);

  useEffect(() => {
    fetchTodayReview()
      .then(setReview)
      .catch((e: unknown) =>
        setError(e instanceof Error ? e.message : 'Failed to load review'),
      )
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    return () => {
      if (typeof window !== 'undefined' && 'speechSynthesis' in window) {
        window.speechSynthesis.cancel();
        setSpeaking(false);
      }
    };
  }, []);

  function speakScript() {
    if (!review || typeof window === 'undefined' || !('speechSynthesis' in window)) return;
    const utterance = new SpeechSynthesisUtterance(review.voice_review_script);
    utterance.onstart = () => setSpeaking(true);
    utterance.onend = () => setSpeaking(false);
    utterance.onerror = () => setSpeaking(false);
    window.speechSynthesis.cancel();
    window.speechSynthesis.speak(utterance);
  }

  function stopSpeaking() {
    if (typeof window !== 'undefined' && 'speechSynthesis' in window) {
      window.speechSynthesis.cancel();
      setSpeaking(false);
    }
  }

  const navStyle: React.CSSProperties = {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    padding: '12px 24px',
    borderBottom: '1px solid #e5e7eb',
    background: '#fff',
    position: 'sticky',
    top: 0,
    zIndex: 10,
  };

  const backStyle: React.CSSProperties = {
    fontSize: 13,
    color: '#3b82f6',
    textDecoration: 'none',
    padding: '5px 12px',
    border: '1px solid #bfdbfe',
    borderRadius: 6,
    background: '#eff6ff',
  };

  const contentStyle: React.CSSProperties = {
    maxWidth: 680,
    margin: '0 auto',
    padding: '28px 16px',
    fontFamily: 'sans-serif',
  };

  const cardStyle: React.CSSProperties = {
    background: '#fff',
    border: '1px solid #e5e7eb',
    borderRadius: 10,
    padding: '20px 24px',
    marginBottom: 20,
    boxShadow: '0 1px 4px rgba(0,0,0,.07)',
  };

  const scriptStyle: React.CSSProperties = {
    fontSize: 16,
    lineHeight: 1.7,
    color: '#111827',
    whiteSpace: 'pre-line',
  };

  const actionItemStyle: React.CSSProperties = {
    display: 'flex',
    alignItems: 'flex-start',
    gap: 10,
    padding: '8px 0',
    borderBottom: '1px solid #f3f4f6',
    fontSize: 14,
    color: '#374151',
  };

  const speakBtnStyle: React.CSSProperties = {
    border: 'none',
    borderRadius: 6,
    padding: '8px 16px',
    fontSize: 14,
    cursor: 'pointer',
    marginRight: 8,
    background: speaking ? '#fef3c7' : '#7c3aed',
    color: speaking ? '#92400e' : '#fff',
  };

  return (
    <div style={{ minHeight: '100vh', background: '#f9fafb' }}>
      <nav style={navStyle}>
        <span style={{ fontWeight: 700, fontSize: 17, color: '#111827' }}>
          🌙 End-of-Day Review
        </span>
        <Link href="/" style={backStyle}>
          ← Timeline
        </Link>
      </nav>

      <main style={contentStyle}>
        <h2
          style={{
            fontSize: 15,
            color: '#6b7280',
            fontWeight: 500,
            marginBottom: 20,
            fontFamily: 'sans-serif',
          }}
        >
          {new Date().toLocaleDateString([], {
            weekday: 'long',
            year: 'numeric',
            month: 'long',
            day: 'numeric',
          })}
        </h2>

        {loading && (
          <p style={{ color: '#9ca3af', textAlign: 'center', padding: 48 }}>
            Generating your review…
          </p>
        )}

        {error && (
          <p
            role="alert"
            style={{ color: '#ef4444', textAlign: 'center', padding: 16 }}
          >
            {error}
          </p>
        )}

        {review && (
          <>
            {/* Voice review script */}
            <div style={cardStyle}>
              <h3
                style={{
                  margin: '0 0 12px',
                  fontSize: 15,
                  color: '#374151',
                  fontFamily: 'sans-serif',
                }}
              >
                📋 Daily Summary
              </h3>

              <div style={scriptStyle}>{review.voice_review_script}</div>

              <div style={{ marginTop: 16 }}>
                <button
                  style={speakBtnStyle}
                  onClick={speaking ? stopSpeaking : speakScript}
                  title={speaking ? 'Stop narration' : 'Read aloud'}
                >
                  {speaking ? '⏹ Stop' : '🔊 Read aloud'}
                </button>
                <span style={{ fontSize: 11, color: '#9ca3af' }}>
                  Uses browser text-to-speech
                </span>
              </div>
            </div>

            {/* Next actions */}
            {review.next_actions.length > 0 && (
              <div style={cardStyle}>
                <h3
                  style={{
                    margin: '0 0 12px',
                    fontSize: 15,
                    color: '#374151',
                    fontFamily: 'sans-serif',
                  }}
                >
                  ✅ Suggested next actions
                </h3>
                <div>
                  {review.next_actions.map((action, i) => (
                    <div key={i} style={actionItemStyle}>
                      <span
                        style={{
                          width: 20,
                          height: 20,
                          borderRadius: '50%',
                          border: '2px solid #a78bfa',
                          display: 'inline-block',
                          flexShrink: 0,
                          marginTop: 1,
                        }}
                      />
                      {action}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Empty state */}
            {review.next_actions.length === 0 && review.voice_review_script.includes('0') && (
              <p style={{ color: '#9ca3af', textAlign: 'center', padding: 16 }}>
                No items captured today yet. Head back to the timeline to add some.
              </p>
            )}
          </>
        )}
      </main>
    </div>
  );
}
