import { healthEndpoint } from '../lib/api';

export default function Home() {
  return (
    <main style={{ padding: '2rem', fontFamily: 'sans-serif' }}>
      <h1>Lookback</h1>
      <p>Frontend is running.</p>
      <p>
        Backend health endpoint: <code>{healthEndpoint()}</code>
      </p>
    </main>
  );
}
