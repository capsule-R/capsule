'use client';

import { useEffect } from 'react';

export default function DashboardError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    // In production: send to Sentry / error tracking
    console.error('[dashboard error]', error);
  }, [error]);

  return (
    <div style={{
      minHeight: '100vh', background: 'var(--bg-base)', display: 'flex',
      flexDirection: 'column', alignItems: 'center', justifyContent: 'center',
      padding: '40px 24px', textAlign: 'center',
    }}>
      <div style={{ maxWidth: 480 }}>
        {/* Icon */}
        <div style={{
          width: 56, height: 56, borderRadius: 14, margin: '0 auto 24px',
          background: 'color-mix(in oklab, var(--error) 12%, transparent)',
          border: '1px solid color-mix(in oklab, var(--error) 30%, transparent)',
          display: 'grid', placeItems: 'center', color: 'var(--error)',
        }}>
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
            <path d="M12 8v5M12 16.5v.5" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
            <circle cx="12" cy="12" r="9" stroke="currentColor" strokeWidth="1.6"/>
          </svg>
        </div>

        <h2 style={{ fontFamily: 'var(--font-display)', fontSize: 24, fontWeight: 700, marginBottom: 10 }}>
          Something went wrong
        </h2>
        <p style={{ fontSize: 14.5, color: 'var(--text-secondary)', lineHeight: 1.65, marginBottom: 28 }}>
          An unexpected error occurred while loading this page. The error has been logged.
        </p>

        {/* Error detail (dev only style) */}
        {error.message && (
          <div style={{
            padding: '10px 14px', borderRadius: 8, background: 'var(--bg-elevated)',
            border: '1px solid var(--border-default)', fontFamily: 'var(--font-mono)',
            fontSize: 12.5, color: 'var(--error)', textAlign: 'left', marginBottom: 24,
            wordBreak: 'break-all',
          }}>
            {error.message}
            {error.digest && (
              <div style={{ color: 'var(--text-tertiary)', marginTop: 6 }}>digest: {error.digest}</div>
            )}
          </div>
        )}

        <div style={{ display: 'flex', gap: 12, justifyContent: 'center', flexWrap: 'wrap' }}>
          <button className="btn btn-primary" onClick={reset} style={{ minWidth: 140 }}>
            Try again
          </button>
          <a href="/dashboard" className="btn btn-ghost" style={{ minWidth: 140 }}>
            Back to dashboard
          </a>
        </div>
      </div>
    </div>
  );
}
