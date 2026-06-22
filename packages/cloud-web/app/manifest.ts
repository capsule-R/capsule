import type { MetadataRoute } from 'next';

// PWA manifest — Next serves this at /manifest.webmanifest and auto-links it.
export default function manifest(): MetadataRoute.Manifest {
  return {
    name: 'Capsule — Deterministic Replay for AI Agents',
    short_name: 'Capsule',
    description:
      'Capture, replay, and debug every AI agent execution. Time-travel through any session.',
    start_url: '/',
    display: 'standalone',
    background_color: '#0A0A0A',
    theme_color: '#0A0A0A',
    icons: [
      { src: '/icon-192.png', sizes: '192x192', type: 'image/png' },
      { src: '/icon-512.png', sizes: '512x512', type: 'image/png' },
      { src: '/icon-512.png', sizes: '512x512', type: 'image/png', purpose: 'maskable' },
    ],
  };
}
