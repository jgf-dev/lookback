'use client';

import React from 'react';

const SOURCE_TYPES = ['', 'manual_note', 'speech', 'audio', 'screenshot'] as const;

export interface FilterState {
  search: string;
  sourceType: string;
  tag: string;
}

interface Props {
  filters: FilterState;
  onChange: (f: FilterState) => void;
}

export default function TimelineFilters({ filters, onChange }: Props) {
  const inputStyle: React.CSSProperties = {
    padding: '6px 10px',
    border: '1px solid #d1d5db',
    borderRadius: 6,
    fontSize: 13,
    outline: 'none',
    background: '#fff',
  };

  return (
    <div
      style={{
        display: 'flex',
        gap: 8,
        alignItems: 'center',
        flexWrap: 'wrap',
        marginBottom: 14,
      }}
    >
      <input
        type="search"
        placeholder="Search…"
        value={filters.search}
        onChange={(e) => onChange({ ...filters, search: e.target.value })}
        style={{ ...inputStyle, flexGrow: 1, minWidth: 140 }}
        aria-label="Search timeline"
      />

      <select
        value={filters.sourceType}
        onChange={(e) => onChange({ ...filters, sourceType: e.target.value })}
        style={inputStyle}
        aria-label="Filter by source type"
      >
        {SOURCE_TYPES.map((t) => (
          <option key={t} value={t}>
            {t === '' ? 'All types' : t.replace('_', ' ')}
          </option>
        ))}
      </select>

      <input
        type="text"
        placeholder="Tag filter…"
        value={filters.tag}
        onChange={(e) => onChange({ ...filters, tag: e.target.value })}
        style={{ ...inputStyle, width: 120 }}
        aria-label="Filter by tag"
      />

      {(filters.search || filters.sourceType || filters.tag) && (
        <button
          onClick={() => onChange({ search: '', sourceType: '', tag: '' })}
          style={{
            padding: '5px 10px',
            fontSize: 12,
            border: 'none',
            borderRadius: 6,
            background: '#fee2e2',
            color: '#dc2626',
            cursor: 'pointer',
          }}
        >
          Clear
        </button>
      )}
    </div>
  );
}
