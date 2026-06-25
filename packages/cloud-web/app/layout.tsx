import type { Metadata, Viewport } from 'next';
import { Analytics } from '@vercel/analytics/next';
import './globals.css';

export const metadata: Metadata = {
  title: 'Capsule — Deterministic Replay for AI Agents',
  description: 'Capture, replay, and debug every AI agent execution. Time-travel through any session.',
  // Favicon (app/favicon.ico, app/icon.svg), apple-touch icon (app/apple-icon.png),
  // and the PWA manifest (app/manifest.ts) are auto-linked by Next from the
  // file-based metadata conventions — no manual <link> tags needed.
};

export const viewport: Viewport = {
  themeColor: '#0A0A0A',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" suppressHydrationWarning>
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        <link
          href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&family=Fragment+Mono:ital,wght@0,400;0,500;1,400&display=swap"
          rel="stylesheet"
        />
      </head>
      <body suppressHydrationWarning>
        {children}
        <Analytics />
      </body>
    </html>
  );
}
