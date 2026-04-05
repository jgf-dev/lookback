import Image from 'next/image';
import { ContextBadge } from './ContextBadge';
import type { Screenshot, TimelineEntry } from '../lib/types';

type EntryCardProps = {
  entry: TimelineEntry;
  screenshots: Screenshot[];
};

export function EntryCard({ entry, screenshots }: EntryCardProps) {
  return (
    <article
      style={{
        background: '#111827',
        border: '1px solid #334155',
        borderRadius: 12,
        padding: 14,
        display: 'flex',
        flexDirection: 'column',
        gap: 12
      }}
    >
      <header style={{ display: 'flex', justifyContent: 'space-between', gap: 12 }}>
        <strong style={{ color: '#f8fafc' }}>{entry.source}</strong>
        <time style={{ color: '#94a3b8', fontSize: 13 }}>{new Date(entry.timestamp).toLocaleString()}</time>
      </header>

      <p style={{ margin: 0, lineHeight: 1.45 }}>{entry.transcript}</p>

      <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
        {entry.project ? <ContextBadge tone="project">Project: {entry.project}</ContextBadge> : null}
        {entry.task ? <ContextBadge tone="task">Task: {entry.task}</ContextBadge> : null}
      </div>

      {screenshots.length > 0 ? (
        <div style={{ display: 'grid', gap: 8, gridTemplateColumns: 'repeat(auto-fit, minmax(130px, 1fr))' }}>
          {screenshots.map((shot) => (
            <a key={shot.id} href={shot.url} target="_blank" rel="noreferrer" style={{ display: 'block' }}>
              <Image
                src={shot.url}
                alt={`Screenshot ${shot.id}`}
                width={360}
                height={200}
                style={{ width: '100%', height: 100, objectFit: 'cover', borderRadius: 8 }}
              />
            </a>
          ))}
        </div>
      ) : null}
    </article>
  );
}
