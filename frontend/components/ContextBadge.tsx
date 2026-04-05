import type { PropsWithChildren } from 'react';

type ContextBadgeProps = PropsWithChildren<{
  tone?: 'project' | 'task';
}>;

export function ContextBadge({ children, tone = 'project' }: ContextBadgeProps) {
  return (
    <span
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        borderRadius: 999,
        padding: '2px 10px',
        fontSize: 12,
        border: '1px solid',
        borderColor: tone === 'project' ? '#334155' : '#7c3aed',
        background: tone === 'project' ? '#1e293b' : '#2e1065',
        color: tone === 'project' ? '#cbd5e1' : '#ddd6fe'
      }}
    >
      {children}
    </span>
  );
}
