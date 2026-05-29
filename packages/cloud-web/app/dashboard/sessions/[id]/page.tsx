'use client';

import { useState, useRef, useCallback, useEffect } from 'react';
import { DashboardShell } from '@/components/DashboardShell';

/* ─── Types ─────────────────────────────────────────────────── */
interface Step {
  idx: number;
  kind: 'llm' | 'tool' | 'memory' | 'branch' | 'session';
  label: string;
  sub: string;
  status: 'ok' | 'err' | 'warn' | 'info';
  dur: string;
  tokens?: string;
  detail: Detail;
}

interface Detail {
  title: string;
  meta: { k: string; v: string }[];
  input?: string;
  output?: string;
  error?: string;
}

/* ─── Mock data ─────────────────────────────────────────────── */
const KIND_COLOR: Record<string, string> = {
  llm: 'var(--accent)',
  tool: 'var(--warn)',
  memory: 'var(--replay)',
  branch: '#A78BFA',
  session: 'var(--success)',
};

const STATUS_DOT: Record<string, string> = {
  ok: 'var(--success)',
  err: 'var(--error)',
  warn: 'var(--warn)',
  info: 'var(--replay)',
};

/* ─── Mini timeline ─────────────────────────────────────────── */
function Timeline({ steps, active, onSeek }: {
  steps: Step[]; active: number; onSeek: (i: number) => void;
}) {
  const trackRef = useRef<HTMLDivElement>(null);
  const dragging = useRef(false);

  const seekFromEvent = useCallback((e: MouseEvent | React.MouseEvent) => {
    if (!trackRef.current) return;
    const rect = trackRef.current.getBoundingClientRect();
    const pct = Math.max(0, Math.min(1, (e.clientX - rect.left) / rect.width));
    const idx = Math.round(pct * (steps.length - 1));
    onSeek(idx);
  }, [steps.length, onSeek]);

  const handleMouseMove = useCallback((e: MouseEvent) => {
    if (dragging.current) seekFromEvent(e);
  }, [seekFromEvent]);

  const handleMouseUp = useCallback(() => { dragging.current = false; }, []);

  useEffect(() => {
    window.addEventListener('mousemove', handleMouseMove);
    window.addEventListener('mouseup', handleMouseUp);
    return () => {
      window.removeEventListener('mousemove', handleMouseMove);
      window.removeEventListener('mouseup', handleMouseUp);
    };
  }, [handleMouseMove, handleMouseUp]);

  const pct = steps.length > 1 ? (active / (steps.length - 1)) * 100 : 0;

  return (
    <div style={{ padding: '20px 24px 16px', borderBottom: '1px solid var(--border-subtle)' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 14, marginBottom: 14 }}>
        {/* Step dots */}
        <div
          ref={trackRef}
          onMouseDown={(e) => { dragging.current = true; seekFromEvent(e); }}
          onClick={(e) => seekFromEvent(e)}
          style={{ flex: 1, height: 40, position: 'relative', cursor: 'pointer', display: 'flex', alignItems: 'center' }}
        >
          {/* Track */}
          <div style={{ position: 'absolute', left: 0, right: 0, height: 3, background: 'var(--bg-elevated)', borderRadius: 3 }}>
            <div style={{ width: `${pct}%`, height: '100%', background: 'var(--accent)', borderRadius: 3, transition: 'width 0.12s' }} />
          </div>

          {/* Step markers */}
          {steps.map((s, i) => {
            const left = steps.length > 1 ? (i / (steps.length - 1)) * 100 : 0;
            return (
              <div
                key={i}
                style={{
                  position: 'absolute',
                  left: `${left}%`,
                  transform: 'translate(-50%, 0)',
                  width: i === active ? 14 : 10,
                  height: i === active ? 14 : 10,
                  borderRadius: '50%',
                  background: i <= active ? KIND_COLOR[s.kind] : 'var(--bg-elevated)',
                  border: `2px solid ${i === active ? KIND_COLOR[s.kind] : i < active ? KIND_COLOR[s.kind] : 'var(--border-default)'}`,
                  transition: 'all 0.12s',
                  zIndex: 2,
                  boxShadow: i === active ? `0 0 0 3px color-mix(in oklab, ${KIND_COLOR[s.kind]} 20%, transparent)` : 'none',
                }}
              />
            );
          })}

          {/* Thumb */}
          <div style={{
            position: 'absolute',
            left: `${pct}%`,
            transform: 'translateX(-50%)',
            width: 18,
            height: 18,
            borderRadius: '50%',
            background: 'var(--bg-base)',
            border: '3px solid var(--accent)',
            zIndex: 3,
            pointerEvents: 'none',
            transition: 'left 0.12s',
          }} />
        </div>
      </div>

      {/* Step labels */}
      <div style={{ display: 'flex', justifyContent: 'space-between' }}>
        {steps.map((s, i) => (
          <div
            key={i}
            onClick={() => onSeek(i)}
            style={{
              fontSize: 9.5,
              fontFamily: 'var(--font-mono)',
              color: i === active ? 'var(--text-primary)' : 'var(--text-tertiary)',
              cursor: 'pointer',
              maxWidth: 70,
              textAlign: 'center',
              whiteSpace: 'nowrap',
              overflow: 'hidden',
              textOverflow: 'ellipsis',
              transition: 'color 0.1s',
            }}
            title={s.label}
          >
            {s.label.split(' · ')[1] ?? s.label}
          </div>
        ))}
      </div>
    </div>
  );
}

/* ─── Code block ─────────────────────────────────────────────── */
function CodeBlock({ code, label }: { code: string; label: string }) {
  const [copied, setCopied] = useState(false);
  const copy = () => {
    navigator.clipboard.writeText(code).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 1500);
    });
  };
  return (
    <div style={{ marginTop: 12 }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 6 }}>
        <span style={{ fontSize: 11, fontFamily: 'var(--font-mono)', color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '0.06em' }}>{label}</span>
        <button onClick={copy} style={{ fontSize: 11, fontFamily: 'var(--font-mono)', color: 'var(--text-tertiary)', background: 'none', border: 'none', cursor: 'pointer', padding: '2px 6px' }}>
          {copied ? '✓ copied' : 'copy'}
        </button>
      </div>
      <pre style={{ margin: 0, padding: '12px 14px', background: 'var(--bg-elevated)', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-subtle)', fontFamily: 'var(--font-mono)', fontSize: 12.5, color: 'var(--text-secondary)', overflowX: 'auto', whiteSpace: 'pre-wrap', wordBreak: 'break-all', lineHeight: 1.6 }}>
        {code}
      </pre>
    </div>
  );
}

/* ─── Page ───────────────────────────────────────────────────── */
import { createClient } from '@/lib/supabase/client';

export default function SessionDetailPage({ params }: { params: { id: string } }) {
  const sessionId = params.id ?? 'sess_8f2a91c4';
  const [STEPS, setSteps] = useState<Step[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  const [active, setActive] = useState(0);
  const [playing, setPlaying] = useState(false);
  const [speed, setSpeed] = useState(1);
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  useEffect(() => {
    async function loadData() {
      try {
        const supabase = createClient();
        const { data: { session: authSession } } = await supabase.auth.getSession();
        const token = authSession?.access_token;
        if (!token) return;

        const headers = { Authorization: `Bearer ${token}` };
        const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

        // Fetch workspace
        const wsRes = await fetch(`${apiUrl}/workspaces`, { headers });
        if (!wsRes.ok) throw new Error('Failed to fetch workspaces');
        const workspaces = await wsRes.json();
        if (workspaces.length === 0) throw new Error('No workspace found');
        const wsId = workspaces[0].id;

        // Fetch events
        const eventsRes = await fetch(`${apiUrl}/workspaces/${wsId}/sessions/${sessionId}/events`, { headers });
        if (!eventsRes.ok) throw new Error('Failed to fetch session events or no capsule binary found');
        
        const eventsData = await eventsRes.json();
        
        // Map backend event format to frontend Step format
        const mappedSteps: Step[] = eventsData.map((e: any, idx: number) => {
          // The backend returns the raw JSON of the capsule event model
          const kind = e.event_type || 'llm';
          const title = e.name || `${kind} call`;
          return {
            idx,
            kind: kind === 'llm_call' ? 'llm' : kind === 'tool_call' ? 'tool' : 'session',
            label: `${kind} · ${e.name || 'step'}`,
            sub: e.model || e.tool_name || '',
            status: e.status === 'error' ? 'err' : 'ok',
            dur: e.duration_ms ? `${(e.duration_ms / 1000).toFixed(1)}s` : '—',
            detail: {
              title,
              meta: [],
              input: e.input_str || JSON.stringify(e.input_data, null, 2),
              output: e.output_str || JSON.stringify(e.output_data, null, 2),
              error: e.error_message,
            }
          };
        });
        
        setSteps(mappedSteps);
        // Default to the first error step, or the last step if no errors
        const errIndex = mappedSteps.findIndex(s => s.status === 'err');
        setActive(errIndex >= 0 ? errIndex : Math.max(0, mappedSteps.length - 1));
      } catch (err: any) {
        console.error(err);
        setError(err.message);
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, [sessionId]);

  const step = STEPS[active];

  const play = useCallback(() => {
    if (STEPS.length === 0) return;
    if (active >= STEPS.length - 1) { setActive(0); }
    setPlaying(true);
  }, [active, STEPS.length]);

  const pause = useCallback(() => {
    setPlaying(false);
    if (intervalRef.current) clearInterval(intervalRef.current);
  }, []);

  useEffect(() => {
    if (playing) {
      intervalRef.current = setInterval(() => {
        setActive((prev) => {
          if (prev >= STEPS.length - 1) {
            setPlaying(false);
            return prev;
          }
          return prev + 1;
        });
      }, 900 / speed);
    } else {
      if (intervalRef.current) clearInterval(intervalRef.current);
    }
    return () => { if (intervalRef.current) clearInterval(intervalRef.current); };
  }, [playing, speed]);

  if (loading || STEPS.length === 0) {
    return (
      <DashboardShell active="sessions" title="Session" crumb={`workspace / sessions / ${sessionId}`}>
        <div style={{ padding: 40, textAlign: 'center', color: 'var(--text-tertiary)' }}>
          {error ? `Error: ${error}` : 'Loading session events...'}
        </div>
      </DashboardShell>
    );
  }

  return (
    <DashboardShell active="sessions" title="Session" crumb={`workspace / sessions / ${sessionId}`}>
      {/* Header */}
      <div className="page-head" style={{ marginBottom: 20 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12, flexWrap: 'wrap' }}>
          <span style={{ fontFamily: 'var(--font-mono)', fontSize: 15, fontWeight: 600, color: 'var(--text-primary)' }}>{sessionId}</span>
          <span className="badge err"><span className="d" />failed</span>
          {[
            { icon: '🗂', label: 'checkout-agent' },
            { icon: '🤖', label: 'gpt-4o' },
            { icon: '⏱', label: '3.4s' },
            { icon: '💸', label: '$0.0171' },
            { icon: '🕐', label: '2m ago' },
          ].map(({ icon, label }) => (
            <span key={label} style={{ display: 'inline-flex', alignItems: 'center', gap: 5, fontSize: 12.5, color: 'var(--text-secondary)', background: 'var(--bg-card)', border: '1px solid var(--border-subtle)', borderRadius: 'var(--radius-sm)', padding: '4px 10px' }}>
              {icon} {label}
            </span>
          ))}
        </div>
        <div className="flex gap-8">
          <button className="btn btn-ghost btn-sm" onClick={() => { setActive(0); setPlaying(true); }}>
            <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor"><path d="M6 4l14 8-14 8V4z"/></svg>
            Replay
          </button>
          <button className="btn btn-ghost btn-sm" onClick={() => window.location.href = '/dashboard/branches'}>
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none"><circle cx="6" cy="6" r="2.4" stroke="currentColor" strokeWidth="1.8"/><circle cx="18" cy="18" r="2.4" stroke="currentColor" strokeWidth="1.8"/><circle cx="6" cy="18" r="2.4" stroke="currentColor" strokeWidth="1.8"/><path d="M6 8.4v3.6a3 3 0 0 0 3 3h6.6" stroke="currentColor" strokeWidth="1.8"/></svg>
            Branches
          </button>
          <a className="btn btn-ghost btn-sm" href={`/api/sessions/${sessionId}/export`} download>
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none"><path d="M4 12v7a1 1 0 0 0 1 1h14a1 1 0 0 0 1-1v-7M12 3v12m0 0l-4-4m4 4l4-4" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"/></svg>
            Export .capsule
          </a>
        </div>
      </div>

      {/* Replay scrubber card */}
      <div className="card" style={{ padding: 0, marginBottom: 16, overflow: 'hidden' }}>
        {/* Controls bar */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 12, padding: '14px 20px', borderBottom: '1px solid var(--border-subtle)' }}>
          <button
            onClick={playing ? pause : play}
            style={{ width: 36, height: 36, borderRadius: 8, border: '1px solid var(--border-default)', background: 'var(--bg-elevated)', display: 'grid', placeItems: 'center', cursor: 'pointer', color: 'var(--text-primary)', flexShrink: 0 }}
          >
            {playing ? (
              <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor"><rect x="6" y="5" width="4" height="14" rx="1"/><rect x="14" y="5" width="4" height="14" rx="1"/></svg>
            ) : (
              <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor"><path d="M6 4l14 8-14 8V4z"/></svg>
            )}
          </button>

          <div style={{ display: 'flex', alignItems: 'center', gap: 4, fontSize: 12.5, fontFamily: 'var(--font-mono)', color: 'var(--text-secondary)' }}>
            <span style={{ color: 'var(--text-primary)', fontWeight: 600 }}>Step {active + 1}</span>
            <span style={{ color: 'var(--text-tertiary)' }}>/ {STEPS.length}</span>
          </div>

          <button onClick={() => setActive(Math.max(0, active - 1))} style={{ width: 28, height: 28, borderRadius: 6, border: '1px solid var(--border-default)', background: 'var(--bg-base)', display: 'grid', placeItems: 'center', cursor: 'pointer', color: 'var(--text-secondary)' }}>
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none"><path d="M15 18l-6-6 6-6" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/></svg>
          </button>
          <button onClick={() => setActive(Math.min(STEPS.length - 1, active + 1))} style={{ width: 28, height: 28, borderRadius: 6, border: '1px solid var(--border-default)', background: 'var(--bg-base)', display: 'grid', placeItems: 'center', cursor: 'pointer', color: 'var(--text-secondary)' }}>
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none"><path d="M9 18l6-6-6-6" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/></svg>
          </button>

          <div style={{ flex: 1 }} />

          {/* Speed */}
          <div className="segmented" style={{ '--seg-h': '28px' } as React.CSSProperties}>
            {[0.5, 1, 2].map((s) => (
              <button key={s} className={speed === s ? 'active' : ''} onClick={() => setSpeed(s)} style={{ fontSize: 11.5, padding: '0 10px' }}>
                {s}×
              </button>
            ))}
          </div>
        </div>

        {/* Timeline track */}
        <Timeline steps={STEPS} active={active} onSeek={setActive} />
      </div>

      {/* Three-column layout */}
      <div className="session-detail-grid" style={{ display: 'grid', gridTemplateColumns: '220px 1fr 260px', gap: 12, alignItems: 'start' }}>

        {/* Step list */}
        <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
          <div style={{ padding: '12px 16px', borderBottom: '1px solid var(--border-subtle)', fontSize: 12, fontWeight: 600, color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.06em' }}>
            Steps
          </div>
          {STEPS.map((s, i) => (
            <div
              key={i}
              onClick={() => setActive(i)}
              style={{
                padding: '10px 16px',
                cursor: 'pointer',
                borderBottom: '1px solid var(--border-subtle)',
                background: i === active ? 'color-mix(in oklab, var(--accent) 6%, transparent)' : 'transparent',
                borderLeft: `3px solid ${i === active ? KIND_COLOR[s.kind] : 'transparent'}`,
                transition: 'background 0.1s',
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: 7 }}>
                <span style={{ width: 7, height: 7, borderRadius: '50%', background: STATUS_DOT[s.status], flexShrink: 0 }} />
                <span style={{ fontFamily: 'var(--font-mono)', fontSize: 11.5, color: i === active ? 'var(--text-primary)' : 'var(--text-secondary)', fontWeight: i === active ? 600 : 400, flex: 1, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                  {s.label}
                </span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: 3, paddingLeft: 14 }}>
                <span style={{ fontSize: 10.5, color: 'var(--text-tertiary)', fontFamily: 'var(--font-mono)' }}>{s.sub}</span>
                <span style={{ fontSize: 10.5, color: 'var(--text-tertiary)', fontFamily: 'var(--font-mono)' }}>{s.dur}</span>
              </div>
            </div>
          ))}
        </div>

        {/* Detail panel */}
        <div className="card">
          <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 18 }}>
            <span style={{ padding: '3px 10px', borderRadius: 'var(--radius-sm)', background: `color-mix(in oklab, ${KIND_COLOR[step.kind]} 15%, transparent)`, color: KIND_COLOR[step.kind], fontFamily: 'var(--font-mono)', fontSize: 12, fontWeight: 600 }}>
              {step.kind}
            </span>
            <h3 style={{ fontFamily: 'var(--font-body)', fontWeight: 600, fontSize: 15, color: 'var(--text-primary)' }}>{step.detail.title}</h3>
          </div>

          {/* Meta chips */}
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8, marginBottom: 18 }}>
            {step.detail.meta.map(({ k, v }) => (
              <div key={k} style={{ display: 'flex', alignItems: 'center', gap: 5, fontSize: 12, background: 'var(--bg-elevated)', border: '1px solid var(--border-subtle)', borderRadius: 'var(--radius-sm)', padding: '4px 10px' }}>
                <span style={{ color: 'var(--text-tertiary)', fontFamily: 'var(--font-mono)' }}>{k}</span>
                <span style={{ color: 'var(--text-primary)', fontFamily: 'var(--font-mono)', fontWeight: 600 }}>{v}</span>
              </div>
            ))}
          </div>

          {step.detail.error && (
            <div style={{ marginBottom: 16, padding: '12px 14px', background: 'color-mix(in oklab, var(--error) 10%, transparent)', border: '1px solid color-mix(in oklab, var(--error) 30%, transparent)', borderRadius: 'var(--radius-sm)' }}>
              <div style={{ fontSize: 11.5, fontFamily: 'var(--font-mono)', color: 'var(--error)', fontWeight: 600, marginBottom: 6 }}>ERROR</div>
              <pre style={{ margin: 0, fontFamily: 'var(--font-mono)', fontSize: 12, color: 'var(--error)', whiteSpace: 'pre-wrap', wordBreak: 'break-all', lineHeight: 1.6 }}>{step.detail.error}</pre>
            </div>
          )}

          {step.detail.input && <CodeBlock code={step.detail.input} label="Input" />}
          {step.detail.output && <CodeBlock code={step.detail.output} label="Output" />}
        </div>

        {/* Right sidebar */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
          {/* Session info */}
          <div className="card">
            <div style={{ fontSize: 12, fontWeight: 600, color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 14 }}>Session info</div>
            {[
              { k: 'ID', v: sessionId },
              { k: 'Project', v: 'checkout-agent' },
              { k: 'Status', v: 'failed' },
              { k: 'Steps', v: '8' },
              { k: 'Duration', v: '3.4s' },
              { k: 'Cost', v: '$0.0171' },
              { k: 'Captured', v: '2m ago' },
              { k: 'SDK version', v: '0.3.1' },
            ].map(({ k, v }) => (
              <div key={k} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', padding: '7px 0', borderBottom: '1px solid var(--border-subtle)', gap: 8 }}>
                <span style={{ fontSize: 12, color: 'var(--text-tertiary)', fontFamily: 'var(--font-mono)', flexShrink: 0 }}>{k}</span>
                <span style={{ fontSize: 12, color: 'var(--text-primary)', fontFamily: 'var(--font-mono)', textAlign: 'right', wordBreak: 'break-all' }}>{v}</span>
              </div>
            ))}
          </div>

          {/* Branches */}
          <div className="card">
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 12 }}>
              <div style={{ fontSize: 12, fontWeight: 600, color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.06em' }}>Branches</div>
            </div>
            {[
              { id: 'br_9a2f1c', label: 'fix-schema', age: '3d ago', replays: 2 },
              { id: 'br_2b8d44', label: 'retry-with-timeout', age: '1d ago', replays: 1 },
            ].map((b) => (
              <div key={b.id} style={{ padding: '9px 0', borderBottom: '1px solid var(--border-subtle)' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                  <svg width="12" height="12" viewBox="0 0 24 24" fill="none"><circle cx="6" cy="6" r="2.4" stroke="currentColor" strokeWidth="1.8"/><circle cx="18" cy="18" r="2.4" stroke="currentColor" strokeWidth="1.8"/><circle cx="6" cy="18" r="2.4" stroke="currentColor" strokeWidth="1.8"/><path d="M6 8.4v3.6a3 3 0 0 0 3 3h6.6" stroke="currentColor" strokeWidth="1.8"/></svg>
                  <span style={{ fontSize: 12.5, fontFamily: 'var(--font-mono)', color: 'var(--text-primary)' }}>{b.label}</span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: 4 }}>
                  <span style={{ fontSize: 11, color: 'var(--text-tertiary)', fontFamily: 'var(--font-mono)' }}>{b.id}</span>
                  <span style={{ fontSize: 11, color: 'var(--text-tertiary)', fontFamily: 'var(--font-mono)' }}>{b.replays} replay{b.replays !== 1 ? 's' : ''} · {b.age}</span>
                </div>
              </div>
            ))}
            <a href="/dashboard/branches" style={{ display: 'block', marginTop: 10, fontSize: 12, color: 'var(--text-secondary)', textAlign: 'center', textDecoration: 'none' }}>View all branches →</a>
          </div>
        </div>
      </div>
    </DashboardShell>
  );
}
