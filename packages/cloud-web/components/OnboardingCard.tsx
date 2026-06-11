'use client';

/** First-run onboarding card shown on the Overview page until the
 *  workspace has its first captured session. */

const STEPS = [
  {
    n: '01',
    label: 'Install',
    code: 'pip install capsule-trace',
  },
  {
    n: '02',
    label: 'Instrument',
    code: 'import capsule_trace as capsule\n\n@capsule.trace(agent_name="my-agent")\ndef run_agent():\n    ...',
  },
  {
    n: '03',
    label: 'Upload',
    code: 'capsule-trace login --api-key YOUR_KEY\ncapsule-trace upload SESSION_ID',
  },
];

export function OnboardingCard() {
  return (
    <div
      className="card"
      style={{ marginBottom: 24, padding: '26px 28px' }}
    >
      <h3 style={{ fontFamily: 'var(--font-body)', fontWeight: 600, fontSize: 17, color: 'var(--text-primary)', marginBottom: 18 }}>
        Capture your first session
      </h3>

      <div style={{ display: 'flex', gap: 16, flexWrap: 'wrap' }}>
        {STEPS.map((s) => (
          <div key={s.n} style={{ flex: 1, minWidth: 220 }}>
            <div style={{ fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--text-tertiary)', marginBottom: 6 }}>
              {s.n}
            </div>
            <div style={{ fontSize: 13.5, fontWeight: 600, color: 'var(--text-secondary)', marginBottom: 10 }}>
              {s.label}
            </div>
            <pre
              style={{
                margin: 0,
                padding: '13px 14px',
                background: 'var(--mono-bg)',
                border: '1px solid var(--border-subtle)',
                borderRadius: 8,
                fontFamily: 'var(--font-mono)',
                fontSize: 12.5,
                lineHeight: 1.6,
                color: 'var(--mono-text)',
                whiteSpace: 'pre',
                overflowX: 'auto',
              }}
            >
              {s.code}
            </pre>
          </div>
        ))}
      </div>

      <div style={{ marginTop: 20 }}>
        <a className="btn btn-primary btn-sm" href="/dashboard/settings/api-keys">
          Get your API key →
        </a>
      </div>
    </div>
  );
}
