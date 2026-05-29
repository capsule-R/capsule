// Route-level loading state shown while dashboard pages fetch/render
export default function DashboardLoading() {
  return (
    <div style={{
      display: 'grid',
      gridTemplateColumns: '248px 1fr',
      minHeight: '100vh',
      background: 'var(--bg-base)',
    }}>
      {/* Sidebar skeleton */}
      <aside style={{
        background: 'var(--bg-card)',
        borderRight: '1px solid var(--border-default)',
        padding: '18px 16px',
        display: 'flex',
        flexDirection: 'column',
        gap: 8,
      }}>
        {/* Brand */}
        <div style={{ height: 36, width: 120, borderRadius: 8, background: 'var(--bg-elevated)', marginBottom: 16 }} />
        {/* Env switch */}
        <div style={{ height: 40, borderRadius: 8, background: 'var(--bg-elevated)', marginBottom: 8 }} />
        {/* Nav items */}
        {[80, 100, 90, 110, 95].map((w, i) => (
          <div key={i} style={{ height: 36, width: `${w}%`, borderRadius: 8, background: 'var(--bg-elevated)', opacity: 1 - i * 0.1 }} />
        ))}
      </aside>

      {/* Main area skeleton */}
      <div style={{ display: 'flex', flexDirection: 'column' }}>
        {/* Topbar */}
        <div style={{
          height: 64, borderBottom: '1px solid var(--border-default)',
          padding: '0 28px', display: 'flex', alignItems: 'center', gap: 16,
          background: 'var(--bg-base)',
        }}>
          <div style={{ height: 20, width: 160, borderRadius: 6, background: 'var(--bg-elevated)' }} />
          <div style={{ flex: 1 }} />
          <div style={{ height: 36, width: 280, borderRadius: 8, background: 'var(--bg-elevated)' }} />
          <div style={{ height: 34, width: 34, borderRadius: 8, background: 'var(--bg-elevated)' }} />
        </div>

        {/* Content */}
        <div style={{ padding: '32px 28px', display: 'flex', flexDirection: 'column', gap: 20 }}>
          {/* Page heading */}
          <div style={{ height: 32, width: 200, borderRadius: 8, background: 'var(--bg-elevated)' }} />
          {/* Stat grid */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 16 }}>
            {[1, 2, 3, 4].map((i) => (
              <div key={i} style={{ height: 110, borderRadius: 12, background: 'var(--bg-card)', border: '1px solid var(--border-default)', animation: 'pulse 1.6s ease-in-out infinite', animationDelay: `${i * 0.1}s` }} />
            ))}
          </div>
          {/* Main card */}
          <div style={{ height: 280, borderRadius: 12, background: 'var(--bg-card)', border: '1px solid var(--border-default)', animation: 'pulse 1.6s ease-in-out infinite' }} />
          {/* Table skeleton */}
          <div style={{ borderRadius: 12, overflow: 'hidden', border: '1px solid var(--border-default)' }}>
            <div style={{ height: 44, background: 'var(--bg-base)', borderBottom: '1px solid var(--border-default)' }} />
            {[1, 2, 3, 4, 5].map((i) => (
              <div key={i} style={{ height: 52, borderBottom: '1px solid var(--border-subtle)', background: 'var(--bg-card)', animation: 'pulse 1.6s ease-in-out infinite', animationDelay: `${i * 0.08}s` }} />
            ))}
          </div>
        </div>
      </div>

      <style>{`
        @keyframes pulse {
          0%, 100% { opacity: 1; }
          50% { opacity: 0.5; }
        }
      `}</style>
    </div>
  );
}
