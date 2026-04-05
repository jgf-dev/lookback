import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Lookback",
  description: "Timeline capture and daily review",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
