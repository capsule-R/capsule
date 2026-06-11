'use client';

import { useState, useRef, useCallback, useEffect } from 'react';
import { DashboardShell } from '@/components/DashboardShell';
import { ToastHost, showToast } from '@/components/Toast';
import {
  apiFetch,
  getPrimaryWorkspace,
  downloadSessionCapsule,
  startReplay,
  getReplayStatus,
  createBranch,
  formatUSD,
  relativeTime,
} from '@/lib/capsule';

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

interface SessionMeta {
  id: string;
  status: string;
  agent_name: string;
  agent_version: string | null;
  step_count: number;
  duration_ms: number | null;
  total_cost_usd: number;
  uploaded_at: string;
}

/* ─── Step kind colours ─────────────────────────────────────── */
const KIND_COLOR: Record<string, string> = {
  llm: 'var(--accent)',
  tool: 'var(--warn)',
  memory: 'var(--replay)',
  branch: 'var(--replay)',
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
        <div
          ref={trackRef}
          onMouseDown={(e) => { dragging.current = true; seekFromEvent(e); }}
          onClick={(e) => seekFromEvent(e)}
          style={{ flex: 1, height: 40, position: 'relative', cursor: 'pointer', display: 'flex', alignItems: 'center' }}
        >
          <div style={{ position: 'absolute', left: 0, right: 0, height: 3, background: 'var(--bg-elevated)', borderRadius: 3 }}>
            <div style={{ width: `${pct}%`, height: '100%', background: 'var(--accent)', borderRadius: 3, transition: 'width 0.12s' }} />
          </div>

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

function fmtDuration(ms: number | null | undefined): string {
  if (!ms || ms <= 0) return '—';
  if (ms < 1000) return `${Math.round(ms)}ms`;
  return `${(ms / 1000).toFixed(1)}s`;
}

/* ─── Page ───────────────────────────────────────────────────── */
export default function SessionDetailPage({ params }: { params: { id: string } }) {
  const sessionId = params.id;
  const [workspaceId, setWorkspaceId] = useState<string | null>(null);
  const [meta, setMeta] = useState<SessionMeta | null>(null);
  const [STEPS, setSteps] = useState<Step[]>([]);
  const [loading, setLoading] = useState(true);
  const [notFound, setNotFound] = useState(false);
  const [eventsError, setEventsError] = useState<string | null>(null);
  const [downloading, setDownloading] = useState(false);
  
  const [mobileTab, setMobileTab] = useState<'steps' | 'inspector'>('steps');
  const [infoExpanded, setInfoExpanded] = useState(false);

  const [active, setActive] = useState(0);
  const [playing, setPlaying] = useState(false);
  const [speed, setSpeed] = useState(1);
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  // Cloud replay job state
  const [replaying, setReplaying] = useState(false);
  const [replayBanner, setReplayBanner] = useState<
    { kind: 'success' | 'warn' | 'error'; text: string } | null
  >(null);
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);

  // Fork-at-step modal state
  const [forkStep, setForkStep] = useState<number | null>(null);
  const [forkNote, setForkNote] = useState('');
  const [forking, setForking] = useState(false);
  const [hoverStep, setHoverStep] = useState<number | null>(null);

  useEffect(() => () => {
    if (pollRef.current) clearInterval(pollRef.current);
  }, []);

  const handleReplay = async () => {
    if (!workspaceId || replaying) return;
    setReplaying(true);
    setReplayBanner(null);
    const { replayId, error } = await startReplay(workspaceId, sessionId);
    if (!replayId) {
      setReplaying(false);
      setReplayBanner({ kind: 'error', text: `Replay failed — ${error ?? 'could not start replay'}` });
      return;
    }
    const startedAt = Date.now();
    pollRef.current = setInterval(async () => {
      if (Date.now() - startedAt > 60_000) {
        if (pollRef.current) clearInterval(pollRef.current);
        setReplaying(false);
        setReplayBanner({ kind: 'error', text: 'Replay failed — timed out' });
        return;
      }
      const st = await getReplayStatus(replayId);
      if (!st || st.status === 'queued' || st.status === 'running') return;
      if (pollRef.current) clearInterval(pollRef.current);
      setReplaying(false);
      if (st.status === 'completed') {
        setReplayBanner(
          st.result?.is_deterministic
            ? { kind: 'success', text: 'Replay complete — deterministic ✓' }
            : { kind: 'warn', text: 'Replay complete — mismatch detected' },
        );
      } else {
        setReplayBanner({ kind: 'error', text: `Replay failed — ${st.error ?? 'unknown error'}` });
      }
    }, 2000);
  };

  const handleFork = async () => {
    if (!workspaceId || forkStep === null || forking) return;
    setForking(true);
    const { branchId, error } = await createBranch(workspaceId, sessionId, forkStep, forkNote.trim());
    setForking(false);
    if (branchId) {
      setForkStep(null);
      setForkNote('');
      showToast('Branch created', 'success', { label: 'View branches', href: '/dashboard/branches' });
    } else {
      showToast(error ?? 'Could not create branch', 'error');
    }
  };

  const copySessionId = () => {
    navigator.clipboard?.writeText(sessionId).then(() => {
      showToast('Session ID copied', 'info');
    });
  };

  useEffect(() => {
    async function loadData() {
      const ws = await getPrimaryWorkspace();
      if (ws.status !== 'ok') { setNotFound(true); setLoading(false); return; }
      const wsId = ws.workspace.id;
      setWorkspaceId(wsId);

      // Session record (DB metadata — always available if the session exists)
      try {
        const metaRes = await apiFetch(`/workspaces/${wsId}/sessions/${sessionId}`);
        if (metaRes.ok) {
          setMeta(await metaRes.json());
        } else if (metaRes.status === 404) {
          setNotFound(true);
          setLoading(false);
          return;
        }
      } catch {
        setNotFound(true);
        setLoading(false);
        return;
      }

      // Detailed events (parsed from the .capsule binary — may be unavailable)
      try {
        const eventsRes = await apiFetch(`/workspaces/${wsId}/sessions/${sessionId}/events`);
        if (!eventsRes.ok) {
          setEventsError('Step-level data is not available for this session.');
        } else {
          const eventsData = await eventsRes.json();
          const asText = (v: any) => (v == null ? undefined : typeof v === 'string' ? v : JSON.stringify(v, null, 2));
          const mappedSteps: Step[] = eventsData.map((e: any, idx: number) => {
            const et: string = e.event_type || 'llm';
            const p = e.payload || {};
            const kind: Step['kind'] =
              et === 'llm_call' ? 'llm'
                : et === 'tool_call' ? 'tool'
                  : (et === 'memory_read' || et === 'memory_write') ? 'memory'
                    : 'session';
            const name = p.tool_name || p.model || et;
            const isErr = et === 'error' || !!p.error || !!p.error_message;

            // Inputs / outputs live in the typed payload (LLM messages / tool args, etc.)
            const input = asText(p.messages?.length ? p.messages : p.arguments ?? p.input);
            const output = asText(p.response ?? p.result ?? p.output ?? p.value);
            const trace = p.stack_trace || p.traceback;
            let error = et === 'error'
              ? (p.error_message || p.error_type || asText(p.error))
              : (typeof p.error === 'string' ? p.error : undefined);
            if (error && p.error_type && !error.startsWith(String(p.error_type))) {
              error = `${p.error_type}: ${error}`;
            }
            if (error && trace) error = `${error}\n\n${trace}`;

            const meta: { k: string; v: string }[] = [];
            if (p.provider) meta.push({ k: 'provider', v: String(p.provider) });
            if (p.model) meta.push({ k: 'model', v: String(p.model) });
            const usage = p.response?.usage;
            if (usage && (usage.prompt_tokens || usage.completion_tokens)) {
              meta.push({ k: 'tokens', v: `${usage.prompt_tokens ?? 0}→${usage.completion_tokens ?? 0}` });
            }
            if (p.tool_name) meta.push({ k: 'tool', v: String(p.tool_name) });

            return {
              idx,
              kind,
              label: `${et} · ${name}`,
              sub: p.model || p.tool_name || '',
              status: isErr ? 'err' : 'ok',
              dur: e.duration_ms ? `${(e.duration_ms / 1000).toFixed(1)}s` : '—',
              detail: { title: String(name), meta, input, output, error },
            };
          });
          setSteps(mappedSteps);
          const errIndex = mappedSteps.findIndex((s) => s.status === 'err');
          setActive(errIndex >= 0 ? errIndex : Math.max(0, mappedSteps.length - 1));
        }
      } catch (err: any) {
        setEventsError('Could not load step data for this session.');
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
  }, [playing, speed, STEPS.length]);

  const handleDownload = async () => {
    if (!workspaceId) return;
    setDownloading(true);
    const { error } = await downloadSessionCapsule(workspaceId, sessionId);
    if (error) alert(error);
    setDownloading(false);
  };

  const isOk = meta ? (meta.status === 'success' || meta.status === 'completed') : true;

  if (loading) {
    return (
      <DashboardShell active="sessions" title="Session" crumb={`workspace / sessions / ${sessionId}`}>
        <div style={{ padding: 40, textAlign: 'center', color: 'var(--text-tertiary)' }}>Loading session…</div>
      </DashboardShell>
    );
  }

  if (notFound) {
    return (
      <DashboardShell active="sessions" title="Session" crumb={`workspace / sessions / ${sessionId}`}>
        <div className="empty">
          <div style={{ fontWeight: 700, fontSize: 16, color: 'var(--text-secondary)', marginBottom: 6 }}>Session not found</div>
          <div style={{ fontSize: 13.5 }}>It may have been deleted or expired past its retention window.</div>
          <a className="btn btn-ghost btn-sm" href="/dashboard/sessions" style={{ marginTop: 18 }}>← Back to sessions</a>
        </div>
      </DashboardShell>
    );
  }

  return (
    <DashboardShell active="sessions" title="Session" crumb={`workspace / sessions / ${sessionId}`}>
      {/* Header */}
      <div className="page-head session-detail-header" style={{ marginBottom: 20 }}>
        <div className="sdh-left" style={{ display: 'flex', alignItems: 'center', gap: 12, flexWrap: 'wrap' }}>
          <span
            onClick={copySessionId}
            title="Click to copy session ID"
            style={{ fontFamily: 'var(--font-mono)', fontSize: 15, fontWeight: 600, color: 'var(--text-primary)', cursor: 'pointer' }}
          >
            {sessionId}
          </span>
          <span className={`badge ${isOk ? 'ok' : 'err'}`}><span className="d" />{meta?.status ?? '—'}</span>
          {[
            { icon: '🤖', label: meta?.agent_name || '—' },
            { icon: '⚙', label: `${meta?.step_count ?? 0} steps` },
            { icon: '⏱', label: fmtDuration(meta?.duration_ms) },
            { icon: '💸', label: formatUSD(meta?.total_cost_usd) },
            { icon: '🕐', label: relativeTime(meta?.uploaded_at) },
          ].map(({ icon, label }) => (
            <span key={label + icon} style={{ display: 'inline-flex', alignItems: 'center', gap: 5, fontSize: 12.5, color: 'var(--text-secondary)', background: 'var(--bg-card)', border: '1px solid var(--border-subtle)', borderRadius: 'var(--radius-sm)', padding: '4px 10px' }}>
              {icon} {label}
            </span>
          ))}
        </div>
        <div className="sdh-actions flex gap-8">
          <button className="btn btn-primary btn-sm" onClick={handleReplay} disabled={replaying}>
            {replaying ? (
              <>
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" style={{ animation: 'spin 0.9s linear infinite' }}>
                  <path d="M12 3a9 9 0 1 1-9 9" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
                </svg>
                Replaying…
              </>
            ) : (
              <>
                <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor"><path d="M6 4l14 8-14 8V4z"/></svg>
                Replay
              </>
            )}
          </button>
          <button className="btn btn-ghost btn-sm" onClick={handleDownload} disabled={downloading}>
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none"><path d="M4 12v7a1 1 0 0 0 1 1h14a1 1 0 0 0 1-1v-7M12 3v12m0 0l-4-4m4 4l4-4" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"/></svg>
            {downloading ? 'Exporting…' : 'Export'}
          </button>
        </div>
      </div>

      {/* Replay result banner */}
      {replayBanner && (
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: 10,
            padding: '11px 16px',
            marginBottom: 16,
            borderRadius: 'var(--radius-sm)',
            fontSize: 13.5,
            background:
              replayBanner.kind === 'success' ? 'rgba(34,197,94,0.1)'
                : replayBanner.kind === 'warn' ? 'rgba(245,158,11,0.1)'
                  : 'rgba(239,68,68,0.1)',
            color:
              replayBanner.kind === 'success' ? 'var(--success)'
                : replayBanner.kind === 'warn' ? 'var(--warn)'
                  : 'var(--error)',
          }}
        >
          <span style={{ flex: 1 }}>{replayBanner.text}</span>
          <button
            aria-label="Dismiss"
            onClick={() => setReplayBanner(null)}
            style={{ border: 'none', background: 'transparent', color: 'inherit', cursor: 'pointer', padding: 2, display: 'grid', placeItems: 'center' }}
          >
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none">
              <path d="M18 6 6 18M6 6l12 12" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
            </svg>
          </button>
        </div>
      )}

      {/* Replay scrubber card */}
      <div className="card" style={{ padding: 0, marginBottom: 16, overflow: 'hidden' }}>
        {STEPS.length === 0 ? (
          <div style={{ padding: '28px 24px', textAlign: 'center', color: 'var(--text-tertiary)', fontSize: 13 }}>
            {eventsError ?? 'No step-level events recorded for this session.'}
          </div>
        ) : (
          <>
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

              <div className="segmented" style={{ '--seg-h': '28px' } as React.CSSProperties}>
                {[0.5, 1, 2].map((s) => (
                  <button key={s} className={speed === s ? 'active' : ''} onClick={() => setSpeed(s)} style={{ fontSize: 11.5, padding: '0 10px' }}>
                    {s}×
                  </button>
                ))}
              </div>
            </div>

            <Timeline steps={STEPS} active={active} onSeek={setActive} />
          </>
        )}
      </div>

      {/* Mobile session info & tabs */}
      <div className="session-mobile-info">
        <div className="card" onClick={() => setInfoExpanded(!infoExpanded)} style={{ marginBottom: 16, cursor: 'pointer', padding: '16px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div style={{ fontSize: 13, fontWeight: 600 }}>Session Info</div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <span className={`badge ${isOk ? 'ok' : 'err'}`}><span className="d" />{meta?.status ?? '—'}</span>
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" style={{ transform: infoExpanded ? 'rotate(180deg)' : 'none', transition: 'transform 0.2s' }}>
                <path d="M6 9l6 6 6-6" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
              </svg>
            </div>
          </div>
          {infoExpanded && (
            <div style={{ marginTop: 16, borderTop: '1px solid var(--border-subtle)', paddingTop: 16, display: 'flex', flexDirection: 'column', gap: 8 }}>
              {[
                { k: 'ID', v: sessionId },
                { k: 'Agent', v: meta?.agent_name || '—' },
                { k: 'Steps', v: String(meta?.step_count ?? 0) },
                { k: 'Duration', v: fmtDuration(meta?.duration_ms) },
                { k: 'Cost', v: formatUSD(meta?.total_cost_usd) },
                { k: 'Captured', v: relativeTime(meta?.uploaded_at) },
                { k: 'Agent version', v: meta?.agent_version || '—' },
              ].map(({ k, v }) => (
                <div key={k} style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span style={{ fontSize: 12, color: 'var(--text-tertiary)' }}>{k}</span>
                  <span style={{ fontSize: 12, color: 'var(--text-primary)', fontFamily: 'var(--font-mono)' }}>{v}</span>
                </div>
              ))}
            </div>
          )}
        </div>

        <div className="segmented" style={{ width: '100%', marginBottom: 16 }}>
          <button className={mobileTab === 'steps' ? 'active' : ''} onClick={() => setMobileTab('steps')} style={{ flex: 1 }}>Steps</button>
          <button className={mobileTab === 'inspector' ? 'active' : ''} onClick={() => setMobileTab('inspector')} style={{ flex: 1 }}>Inspector</button>
        </div>
      </div>

      {/* Three-column layout */}
      <div className={`session-detail-grid ${mobileTab === 'steps' ? 'mobile-show-steps' : 'mobile-show-inspector'}`}>

        {/* Step list */}
        <div className="card sd-step-list" style={{ padding: 0, overflow: 'hidden' }}>
          <div style={{ padding: '12px 16px', borderBottom: '1px solid var(--border-subtle)', fontSize: 12, fontWeight: 600, color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.06em' }}>
            Steps
          </div>
          {STEPS.length === 0 ? (
            <div style={{ padding: '16px', fontSize: 12.5, color: 'var(--text-tertiary)' }}>No steps to show.</div>
          ) : STEPS.map((s, i) => (
            <div
              key={i}
              onClick={() => { setActive(i); setMobileTab('inspector'); }}
              onMouseEnter={() => setHoverStep(i)}
              onMouseLeave={() => setHoverStep((h) => (h === i ? null : h))}
              style={{
                padding: '10px 16px',
                cursor: 'pointer',
                borderBottom: '1px solid var(--border-subtle)',
                background: i === active ? 'color-mix(in oklab, var(--accent) 6%, transparent)' : 'transparent',
                borderLeft: `3px solid ${s.status === 'err' ? 'var(--error)' : i === active ? KIND_COLOR[s.kind] : 'transparent'}`,
                transition: 'background 0.1s',
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: 7 }}>
                <span style={{ width: 7, height: 7, borderRadius: '50%', background: STATUS_DOT[s.status], flexShrink: 0 }} />
                <span style={{ fontFamily: 'var(--font-mono)', fontSize: 11.5, color: s.status === 'err' ? 'var(--error)' : i === active ? 'var(--text-primary)' : 'var(--text-secondary)', fontWeight: i === active ? 600 : 400, flex: 1, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                  {s.label}
                </span>
                <button
                  aria-label={`Fork from step ${i + 1}`}
                  title={`Fork from step ${i + 1}`}
                  onClick={(e) => { e.stopPropagation(); setForkStep(i); setForkNote(''); }}
                  style={{
                    border: 'none',
                    background: 'transparent',
                    color: 'var(--text-tertiary)',
                    cursor: 'pointer',
                    padding: 2,
                    display: 'grid',
                    placeItems: 'center',
                    opacity: hoverStep === i ? 1 : 0,
                    transition: 'opacity 0.12s',
                    flexShrink: 0,
                  }}
                >
                  <svg width="13" height="13" viewBox="0 0 24 24" fill="none">
                    <circle cx="6" cy="6" r="2.4" stroke="currentColor" strokeWidth="1.7" />
                    <circle cx="18" cy="18" r="2.4" stroke="currentColor" strokeWidth="1.7" />
                    <circle cx="6" cy="18" r="2.4" stroke="currentColor" strokeWidth="1.7" />
                    <path d="M6 8.4v3.6a3 3 0 0 0 3 3h6.6" stroke="currentColor" strokeWidth="1.7" />
                  </svg>
                </button>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: 3, paddingLeft: 14 }}>
                <span style={{ fontSize: 10.5, color: 'var(--text-tertiary)', fontFamily: 'var(--font-mono)' }}>{s.sub}</span>
                <span style={{ fontSize: 10.5, color: 'var(--text-tertiary)', fontFamily: 'var(--font-mono)' }}>{s.dur}</span>
              </div>
            </div>
          ))}
        </div>

        {/* Detail panel */}
        <div className="card sd-detail-panel">
          {step ? (
            <>
              <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 18 }}>
                <span style={{ padding: '3px 10px', borderRadius: 'var(--radius-sm)', background: `color-mix(in oklab, ${KIND_COLOR[step.kind]} 15%, transparent)`, color: KIND_COLOR[step.kind], fontFamily: 'var(--font-mono)', fontSize: 12, fontWeight: 600 }}>
                  {step.kind}
                </span>
                <h3 style={{ fontFamily: 'var(--font-body)', fontWeight: 600, fontSize: 15, color: 'var(--text-primary)' }}>{step.detail.title}</h3>
              </div>

              {step.detail.meta.length > 0 && (
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8, marginBottom: 18 }}>
                  {step.detail.meta.map(({ k, v }) => (
                    <div key={k} style={{ display: 'flex', alignItems: 'center', gap: 5, fontSize: 12, background: 'var(--bg-elevated)', border: '1px solid var(--border-subtle)', borderRadius: 'var(--radius-sm)', padding: '4px 10px' }}>
                      <span style={{ color: 'var(--text-tertiary)', fontFamily: 'var(--font-mono)' }}>{k}</span>
                      <span style={{ color: 'var(--text-primary)', fontFamily: 'var(--font-mono)', fontWeight: 600 }}>{v}</span>
                    </div>
                  ))}
                </div>
              )}

              {step.detail.error && (
                <div style={{ marginBottom: 16, padding: '12px 14px', background: 'color-mix(in oklab, var(--error) 10%, transparent)', border: '1px solid color-mix(in oklab, var(--error) 30%, transparent)', borderRadius: 'var(--radius-sm)' }}>
                  <div style={{ fontSize: 11.5, fontFamily: 'var(--font-mono)', color: 'var(--error)', fontWeight: 600, marginBottom: 6 }}>ERROR</div>
                  <pre style={{ margin: 0, fontFamily: 'var(--font-mono)', fontSize: 12, color: 'var(--error)', whiteSpace: 'pre-wrap', wordBreak: 'break-all', lineHeight: 1.6 }}>{step.detail.error}</pre>
                </div>
              )}

              {step.detail.input && <CodeBlock code={step.detail.input} label="Input" />}
              {step.detail.output && <CodeBlock code={step.detail.output} label="Output" />}
            </>
          ) : (
            <div style={{ padding: '20px 4px', color: 'var(--text-tertiary)', fontSize: 13 }}>
              {eventsError ?? 'Select a step to inspect its input, output, and errors.'}
            </div>
          )}
        </div>

        {/* Right sidebar */}
        <div className="sd-right-sidebar" style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
          {/* Session info */}
          <div className="card">
            <div style={{ fontSize: 12, fontWeight: 600, color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 14 }}>Session info</div>
            {[
              { k: 'ID', v: sessionId },
              { k: 'Agent', v: meta?.agent_name || '—' },
              { k: 'Status', v: meta?.status || '—' },
              { k: 'Steps', v: String(meta?.step_count ?? 0) },
              { k: 'Duration', v: fmtDuration(meta?.duration_ms) },
              { k: 'Cost', v: formatUSD(meta?.total_cost_usd) },
              { k: 'Captured', v: relativeTime(meta?.uploaded_at) },
              { k: 'Agent version', v: meta?.agent_version || '—' },
            ].map(({ k, v }) => (
              <div key={k} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', padding: '7px 0', borderBottom: '1px solid var(--border-subtle)', gap: 8 }}>
                <span style={{ fontSize: 12, color: 'var(--text-tertiary)', fontFamily: 'var(--font-mono)', flexShrink: 0 }}>{k}</span>
                <span style={{ fontSize: 12, color: 'var(--text-primary)', fontFamily: 'var(--font-mono)', textAlign: 'right', wordBreak: 'break-all' }}>{v}</span>
              </div>
            ))}
          </div>

          {/* Branches (none yet) */}
          <div className="card">
            <div style={{ fontSize: 12, fontWeight: 600, color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 12 }}>Branches</div>
            <div style={{ fontSize: 12.5, color: 'var(--text-tertiary)', lineHeight: 1.55 }}>
              No branches from this session yet. Fork a step to explore an alternate path.
            </div>
            <a href="/dashboard/branches" style={{ display: 'block', marginTop: 12, fontSize: 12, color: 'var(--text-secondary)', textAlign: 'center', textDecoration: 'none' }}>View all branches →</a>
          </div>
        </div>
      </div>

      {/* Fork-at-step modal */}
      {forkStep !== null && (
        <div className="modal-overlay" onClick={() => !forking && setForkStep(null)}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <div className="modal-head">
              <h2>Fork from step {forkStep + 1}</h2>
              <button className="modal-close" aria-label="Close" onClick={() => !forking && setForkStep(null)}>
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
                  <path d="M18 6 6 18M6 6l12 12" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
                </svg>
              </button>
            </div>
            <div style={{ marginBottom: 20 }}>
              <label style={{ display: 'block', fontSize: 13, fontWeight: 600, marginBottom: 7, color: 'var(--text-secondary)' }}>
                Note <span style={{ fontWeight: 400, color: 'var(--text-tertiary)' }}>(optional)</span>
              </label>
              <textarea
                className="input"
                rows={3}
                placeholder="e.g. retry with temperature=0"
                value={forkNote}
                onChange={(e) => setForkNote(e.target.value)}
                style={{ resize: 'vertical', fontFamily: 'var(--font-body)' }}
              />
            </div>
            <div style={{ display: 'flex', gap: 10 }}>
              <button className="btn btn-ghost" style={{ flex: 1 }} onClick={() => setForkStep(null)} disabled={forking}>
                Cancel
              </button>
              <button className="btn btn-primary" style={{ flex: 1 }} onClick={handleFork} disabled={forking}>
                {forking ? 'Creating…' : 'Create branch'}
              </button>
            </div>
          </div>
        </div>
      )}

      <ToastHost />
    </DashboardShell>
  );
}
