import './styles.css'
import type { ReactNode } from 'react'

/**
 * Top-level layout component that wraps application content in a minimal HTML document.
 *
 * @param children - The page content to render inside the `<body>` element.
 * @returns The `<html lang="en">` element whose `<body>` contains `children`.
 */
export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  )
}
