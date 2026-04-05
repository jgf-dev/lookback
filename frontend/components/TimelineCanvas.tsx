'use client';

import { useEffect, useMemo, useRef } from 'react';
import { EntryCard } from './EntryCard';
import type { Screenshot, TimelineEntry } from '../lib/types';

type TimelineCanvasProps = {
  entries: TimelineEntry[];
  screenshotsById: Record<string, Screenshot>;
};

type DayGroup = {
  dayKey: string;
  dayLabel: string;
  hourGroups: Array<{
    hourLabel: string;
    minuteGroups: Array<{
      minuteLabel: string;
      entries: TimelineEntry[];
    }>;
  }>;
};

export function TimelineCanvas({ entries, screenshotsById }: TimelineCanvasProps) {
  const endAnchorRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    endAnchorRef.current?.scrollIntoView({ behavior: 'smooth', block: 'end' });
  }, [entries]);

  const grouped = useMemo<DayGroup[]>(() => {
    const dayMap = new Map<string, Map<string, Map<string, TimelineEntry[]>>>();

    for (const entry of entries) {
      const date = new Date(entry.timestamp);
      const dayKey = date.toISOString().slice(0, 10);
      const hourKey = date.toISOString().slice(0, 13);
      const minuteKey = date.toISOString().slice(0, 16);

      if (!dayMap.has(dayKey)) dayMap.set(dayKey, new Map());
      const hourMap = dayMap.get(dayKey)!;
      if (!hourMap.has(hourKey)) hourMap.set(hourKey, new Map());
      const minuteMap = hourMap.get(hourKey)!;
      if (!minuteMap.has(minuteKey)) minuteMap.set(minuteKey, []);

      minuteMap.get(minuteKey)!.push(entry);
    }

    return Array.from(dayMap.entries())
      .sort(([a], [b]) => (a < b ? -1 : 1))
      .map(([dayKey, hourMap]) => ({
        dayKey,
        dayLabel: new Date(`${dayKey}T00:00:00.000Z`).toLocaleDateString(undefined, {
          weekday: 'long',
          year: 'numeric',
          month: 'long',
          day: 'numeric'
        }),
        hourGroups: Array.from(hourMap.entries())
          .sort(([a], [b]) => (a < b ? -1 : 1))
          .map(([hourKey, minuteMap]) => ({
            hourLabel: new Date(`${hourKey}:00:00.000Z`).toLocaleTimeString(undefined, {
              hour: 'numeric'
            }),
            minuteGroups: Array.from(minuteMap.entries())
              .sort(([a], [b]) => (a < b ? -1 : 1))
              .map(([minuteKey, groupedEntries]) => ({
                minuteLabel: new Date(`${minuteKey}:00.000Z`).toLocaleTimeString(undefined, {
                  hour: 'numeric',
                  minute: '2-digit'
                }),
                entries: groupedEntries
              }))
          }))
      }));
  }, [entries]);

  return (
    <section style={{ display: 'flex', flexDirection: 'column', gap: 18 }}>
      {grouped.map((day) => (
        <div key={day.dayKey} style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
          <h2 style={{ margin: 0, color: '#f8fafc' }}>{day.dayLabel}</h2>

          {day.hourGroups.map((hour) => (
            <div key={hour.hourLabel} style={{ borderLeft: '2px solid #334155', paddingLeft: 12 }}>
              <h3 style={{ margin: '0 0 8px', color: '#cbd5e1' }}>{hour.hourLabel}</h3>

              <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                {hour.minuteGroups.map((minute) => (
                  <div key={minute.minuteLabel} style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                    <small style={{ color: '#94a3b8' }}>{minute.minuteLabel}</small>

                    {minute.entries.map((entry) => (
                      <EntryCard
                        key={entry.id}
                        entry={entry}
                        screenshots={entry.screenshotIds
                          .map((id) => screenshotsById[id])
                          .filter((shot): shot is Screenshot => Boolean(shot))}
                      />
                    ))}
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      ))}
      <div ref={endAnchorRef} />
    </section>
  );
}
