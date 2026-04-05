import Link from "next/link";

export default function Home() {
  return (
    <main>
      <h1>Lookback</h1>
      <p>Jump into your workflow:</p>
      <ul>
        <li>
          <Link href="/timeline">Timeline canvas</Link>
        </li>
        <li>
          <Link href="/review">End-of-day review</Link>
        </li>
      </ul>
    </main>
  );
}
