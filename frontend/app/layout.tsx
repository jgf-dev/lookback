import React, { type ReactNode } from 'react';

export const metadata = {
  title: 'Lookback',
  description: 'Lookback frontend application'
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
