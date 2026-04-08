import { healthEndpoint } from '../lib/api';

/**
 * Render the frontend homepage showing the app title, a running-status message, and the backend health endpoint.
 *
 * @returns A JSX element containing a main layout with an <h1> titled "Lookback", a paragraph stating that the frontend is running, and the backend health endpoint rendered inside a <code> element.
 */
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
