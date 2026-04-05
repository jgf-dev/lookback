'use client';

import { useMemo, useState } from 'react';
import { TimelineCanvas } from '../components/TimelineCanvas';
import { useLiveIngestion } from '../lib/useLiveIngestion';

export default function HomePage() {
  const { entries, screenshotsById, connectionState, finishDay } = useLiveIngestion();
  const [flowState, setFlowState] = useState<'live' | 'finishing' | 'review'>('live');

  const statsText = useMemo(() => {
    const screenshotCount = Object.keys(screenshotsById).length;
    return `${entries.length} timeline entries • ${screenshotCount} screenshots`;
  }, [entries.length, screenshotsById]);

  const onFinishDay = () => {
    setFlowState('finishing');
    finishDay();

    // Placeholder for navigation into summary/review flow.
    setTimeout(() => setFlowState('review'), 600);
  };

  return (
    <main style={{ maxWidth: 1100, margin: '0 auto', padding: 20, display: 'grid', gap: 18 }}>
      <header style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 12 }}>
        <div>
          <h1 style={{ margin: 0, fontSize: 28 }}>Live Timeline</h1>
          <p style={{ margin: '6px 0 0', color: '#94a3b8' }}>
            Connection: {connectionState} · {statsText}
          </p>
        </div>

        <button
          type="button"
          onClick={onFinishDay}
          disabled={flowState !== 'live'}
          style={{
            border: '1px solid #475569',
            borderRadius: 10,
            padding: '10px 14px',
            background: flowState === 'live' ? '#16a34a' : '#334155',
            color: 'white',
            cursor: flowState === 'live' ? 'pointer' : 'not-allowed'
          }}
        >
          Finish Day
        </button>
      </header>

      {flowState === 'review' ? (
        <section
          style={{
            border: '1px solid #0ea5e9',
            borderRadius: 10,
            background: '#082f49',
            padding: 14,
            color: '#bae6fd'
          }}
        >
          Day closed. Handing off to summary/review flow…
        </section>
      ) : null}

      <TimelineCanvas entries={entries} screenshotsById={screenshotsById} />
    </main>
  );
}
