import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'Lookback Timeline',
  description: 'Live ingestion timeline for transcripts and screenshots'
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
