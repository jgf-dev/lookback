'use client';

import React, { useCallback, useEffect, useMemo, useState } from 'react';
import Link from 'next/link';
import type { CapturedItem } from '../lib/api';
import { fetchItems } from '../lib/api';
import { useTimelineStream } from '../lib/useTimelineStream';
import CaptureBar from '../components/CaptureBar';
import TimelineFilters, { type FilterState } from '../components/TimelineFilters';
import TimelineItemCard from '../components/TimelineItem';

export default function TimelinePage() {
  const [items, setItems] = useState<CapturedItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filters, setFilters] = useState<FilterState>({
    search: '',
    sourceType: '',
    tag: '',
  });

  const load = useCallback(async () => {
    try {
      const data = await fetchItems();
      setItems(data);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to load items');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  // Re-fetch when a WebSocket event arrives (created / updated)
  useTimelineStream(
    useCallback(() => {
      void load();
    }, [load]),
  );

  function handleCaptured(item: CapturedItem) {
    setItems((prev) => [item, ...prev]);
  }

  function handleUpdated(updated: CapturedItem) {
    setItems((prev) => prev.map((i) => (i.id === updated.id ? updated : i)));
  }

  const visible = useMemo(() => {
    const q = filters.search.toLowerCase();
    return items.filter((item) => {
      if (filters.sourceType && item.source_type !== filters.sourceType) return false;
      if (filters.tag && !item.tags.includes(filters.tag)) return false;
      if (
        q &&
        !item.raw_content.toLowerCase().includes(q) &&
        !(item.enriched_content ?? '').toLowerCase().includes(q) &&
        !item.tags.some((t) => t.toLowerCase().includes(q))
      ) {
        return false;
      }
      return true;
    });
  }, [items, filters]);

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

  const contentStyle: React.CSSProperties = {
    maxWidth: 680,
    margin: '0 auto',
    padding: '20px 16px',
  };

  const reviewLinkStyle: React.CSSProperties = {
    fontSize: 13,
    color: '#7c3aed',
    textDecoration: 'none',
    padding: '5px 12px',
    border: '1px solid #ddd6fe',
    borderRadius: 6,
    background: '#faf5ff',
  };

  return (
    <div style={{ minHeight: '100vh', background: '#f9fafb', fontFamily: 'sans-serif' }}>
      <nav style={navStyle}>
        <span style={{ fontWeight: 700, fontSize: 17, color: '#111827' }}>
          📍 Lookback
        </span>
        <Link href="/review" style={reviewLinkStyle}>
          End-of-day review →
        </Link>
      </nav>

      <main style={contentStyle}>
        <CaptureBar onCaptured={handleCaptured} />

        <TimelineFilters filters={filters} onChange={setFilters} />

        {loading && (
          <p style={{ color: '#9ca3af', textAlign: 'center', padding: 32 }}>
            Loading…
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

        {!loading && !error && visible.length === 0 && (
          <p style={{ color: '#9ca3af', textAlign: 'center', padding: 32 }}>
            {items.length === 0
              ? 'No items yet — capture something above.'
              : 'No items match your filters.'}
          </p>
        )}

        {visible.map((item) => (
          <TimelineItemCard key={item.id} item={item} onUpdated={handleUpdated} />
        ))}
      </main>
    </div>
  );
}
