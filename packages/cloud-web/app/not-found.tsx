import Link from 'next/link';
import { LogoMark } from '@/components/Logo';

export default function NotFound() {
  return (
    <div style={{
      minHeight: '100vh', background: 'var(--bg-base)', display: 'flex',
      flexDirection: 'column', alignItems: 'center', justifyContent: 'center',
      padding: '40px 24px', textAlign: 'center',
    }}>
      {/* Subtle grid background */}
      <div style={{
        position: 'fixed', inset: 0, zIndex: 0, pointerEvents: 'none',
        backgroundImage: 'linear-gradient(var(--border-subtle) 1px, transparent 1px), linear-gradient(90deg, var(--border-subtle) 1px, transparent 1px)',
        backgroundSize: '52px 52px',
        maskImage: 'radial-gradient(ellipse 60% 50% at 50% 50%, #000, transparent)',
        WebkitMaskImage: 'radial-gradient(ellipse 60% 50% at 50% 50%, #000, transparent)',
      }} />

      <div style={{ position: 'relative', zIndex: 1, maxWidth: 440 }}>
        <a href="/" style={{ display: 'inline-flex', alignItems: 'center', gap: 10, marginBottom: 48, textDecoration: 'none' }}>
          <LogoMark size={36} />
          <span style={{ fontFamily: 'var(--font-display)', fontWeight: 800, fontSize: 18, color: 'var(--text-primary)' }}>Capsule</span>
        </a>

        {/* 404 display */}
        <div style={{
          fontFamily: 'var(--font-display)', fontSize: 'clamp(72px, 16vw, 120px)',
          fontWeight: 800, letterSpacing: '-0.04em', lineHeight: 1,
          color: 'var(--text-primary)', marginBottom: 8,
          textShadow: '0 0 80px rgba(245,245,245,0.06)',
        }}>
          404
        </div>

        <div style={{ fontFamily: 'var(--font-mono)', fontSize: 12.5, color: 'var(--text-tertiary)', marginBottom: 24, letterSpacing: '0.08em', textTransform: 'uppercase' }}>
          Page not found
        </div>

        <p style={{ fontSize: 15, color: 'var(--text-secondary)', lineHeight: 1.65, marginBottom: 36 }}>
          This session, branch, or route doesn&apos;t exist — or was deleted. It may have been moved.
        </p>

        {/* Terminal-style hint */}
        <div style={{
          background: 'var(--bg-card)', border: '1px solid var(--border-default)',
          borderRadius: 'var(--radius-sm)', padding: '10px 16px', marginBottom: 36,
          fontFamily: 'var(--font-mono)', fontSize: 13, color: 'var(--text-secondary)',
          textAlign: 'left',
        }}>
          <span style={{ color: 'var(--replay)' }}>$</span>{' '}
          <span style={{ color: 'var(--text-tertiary)' }}>capsule replay</span>{' '}
          <span style={{ color: 'var(--error)' }}>sess_not_found</span>
          <br />
          <span style={{ color: 'var(--error)' }}>✗ Error:</span>{' '}
          <span style={{ color: 'var(--text-tertiary)' }}>session does not exist in workspace</span>
        </div>

        <div style={{ display: 'flex', gap: 12, justifyContent: 'center', flexWrap: 'wrap' }}>
          <Link href="/dashboard" className="btn btn-primary" style={{ minWidth: 140 }}>
            Go to dashboard
          </Link>
          <Link href="/dashboard/sessions" className="btn btn-ghost" style={{ minWidth: 140 }}>
            Browse sessions
          </Link>
        </div>
      </div>
    </div>
  );
}
