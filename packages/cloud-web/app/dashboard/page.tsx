'use client';

import { useState, useEffect } from 'react';
import { DashboardShell } from '@/components/DashboardShell';
import { OnboardingCard } from '@/components/OnboardingCard';
import Link from 'next/link';
import {
  apiFetch,
  getPrimaryWorkspace,
  getSessionStats,
  formatUSD,
  relativeTime,
  type SessionStats,
} from '@/lib/capsule';

function BarChart({ data }: { data: { date: string; count: number }[] }) {
  const max = Math.max(1, ...data.map((d) => d.count));
  const step = Math.max(1, Math.ceil(data.length / 10));
  return (
    <div style={{ display: 'flex', alignItems: 'flex-end', gap: data.length > 45 ? 3 : 7, height: 200, paddingTop: 8 }}>
      {data.map((d, i) => {
        const h = (d.count / (max * 1.12)) * 100;
        const label = new Date(`${d.date}T00:00:00Z`);
        return (
          <div key={d.date} style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 7, height: '100%', justifyContent: 'flex-end' }}
            title={`${d.date} · ${d.count} session${d.count !== 1 ? 's' : ''} captured`}>
            <div style={{ width: '100%', maxWidth: 26, height: `${h}%`, minHeight: d.count > 0 ? 3 : 0, background: 'var(--accent)', borderRadius: '3px 3px 0 0', transition: 'height 0.3s' }} />
            <div style={{ fontFamily: 'var(--font-mono)', fontSize: 9.5, color: 'var(--text-tertiary)', whiteSpace: 'nowrap' }}>
              {i % step === 0 ? `${label.getUTCMonth() + 1}/${label.getUTCDate()}` : ''}
            </div>
          </div>
        );
      })}
    </div>
  );
}

interface RecentSession {
  id: string;
  status: string;
  label: string;
  agent: string;
  steps: number;
  dur: string;
  cost: string;
  when: string;
}

export default function DashboardPage() {
  const [range, setRange] = useState(30);
  const [stats, setStats] = useState<SessionStats | null>(null);
  const [statsLoading, setStatsLoading] = useState(true);
  const [recentSessions, setRecentSessions] = useState<RecentSession[]>([]);
  const [failingSessions, setFailingSessions] = useState<RecentSession[]>([]);
  const [sessionsLoading, setSessionsLoading] = useState(true);
  const [workspaceId, setWorkspaceId] = useState<string | null>(null);
  const [noWorkspace, setNoWorkspace] = useState(false);

  // Resolve workspace + load recent sessions once.
  useEffect(() => {
    async function init() {
      const ws = await getPrimaryWorkspace();
      if (ws.status !== 'ok') {
        if (ws.status === 'none') setNoWorkspace(true);
        setStatsLoading(false);
        setSessionsLoading(false);
        return;
      }
      setWorkspaceId(ws.workspace.id);

      try {
        const sessRes = await apiFetch(`/workspaces/${ws.workspace.id}/sessions?limit=10`);
        if (sessRes.ok) {
          const data = await sessRes.json();
          const mapped: RecentSession[] = data.items.map((s: any) => {
            const isOk = s.status === 'success' || s.status === 'completed';
            return {
              id: s.id,
              status: isOk ? 'ok' : 'err',
              label: s.status,
              agent: s.agent_name || '—',
              steps: s.step_count || 0,
              dur: s.duration_ms ? `${(s.duration_ms / 1000).toFixed(1)}s` : '—',
              cost: formatUSD(s.total_cost_usd),
              when: relativeTime(s.uploaded_at),
            };
          });
          setRecentSessions(mapped);
          setFailingSessions(mapped.filter((s) => s.status === 'err').slice(0, 4));
        }
      } catch (err) {
        console.error(err);
      } finally {
        setSessionsLoading(false);
      }
    }
    init();
  }, []);

  // (Re)load stats whenever the range changes and we have a workspace.
  useEffect(() => {
    if (!workspaceId) return;
    let cancelled = false;
    setStatsLoading(true);
    getSessionStats(workspaceId, range).then((s) => {
      if (!cancelled) {
        setStats(s);
        setStatsLoading(false);
      }
    });
    return () => { cancelled = true; };
  }, [workspaceId, range]);

  const hour = new Date().getHours();
  const greeting = hour < 12 ? 'Good morning' : hour < 17 ? 'Good afternoon' : 'Good evening';

  const total = stats?.total ?? 0;
  const failed = stats?.failed ?? 0;
  const failureRate = total > 0 ? ((failed / total) * 100).toFixed(1) : '0';
  const hasSessions = total > 0;

  // First-run onboarding: visible until the first session lands, then
  // permanently dismissed via localStorage.
  const [onboardingDone, setOnboardingDone] = useState(true);
  useEffect(() => {
    if (statsLoading || !stats) return;
    if (stats.total > 0) {
      localStorage.setItem('capsule_onboarding_done', '1');
      setOnboardingDone(true);
    } else {
      setOnboardingDone(localStorage.getItem('capsule_onboarding_done') === '1');
    }
  }, [statsLoading, stats]);
  const showOnboarding = !statsLoading && total === 0 && !onboardingDone;

  return (
    <DashboardShell active="overview" title="Overview" crumb="workspace / overview" action={{ label: 'New capture', href: '/dashboard/sessions?upload=1' }}>
      {/* Header row */}
      <div className="page-head">
        <div>
          <h2>{greeting}.</h2>
          <p>Here&apos;s what your agents have been doing.</p>
        </div>
        <div className="segmented">
          {[7, 30, 90].map((r) => (
            <button key={r} className={range === r ? 'active' : ''} onClick={() => setRange(r)}>{r} days</button>
          ))}
        </div>
      </div>

      {/* Stats */}
      <div className="stat-grid">
        <div className="stat">
          <div className="sl">
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none"><rect x="3" y="4" width="18" height="16" rx="2.5" stroke="currentColor" strokeWidth="1.7"/><path d="M3 8.5h18" stroke="currentColor" strokeWidth="1.7"/></svg>
            Sessions captured
          </div>
          <div className="sv">{statsLoading ? '—' : total.toLocaleString()}</div>
          <div className="sd flat">
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none"><path d="M5 12h14" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round"/></svg>
            all time
          </div>
        </div>
        <div className="stat">
          <div className="sl">
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none"><path d="M11 5 4 12l7 7M4 12h16" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round"/></svg>
            Failed sessions
          </div>
          <div className="sv" style={{ color: failed > 0 ? 'var(--error)' : undefined }}>
            {statsLoading ? '—' : failed.toLocaleString()}
          </div>
          <div className="sd flat">
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none"><path d="M5 12h14" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round"/></svg>
            all time
          </div>
        </div>
        <div className="stat">
          <div className="sl">
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none"><path d="M12 3l7 3v5c0 4.5-3 8-7 10-4-2-7-5.5-7-10V6z" stroke="currentColor" strokeWidth="1.6" strokeLinejoin="round"/></svg>
            Failure rate
          </div>
          <div className="sv">
            {statsLoading ? '—' : failureRate}
            {!statsLoading && <small>%</small>}
          </div>
          <div className="sd flat">
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none"><path d="M5 12h14" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round"/></svg>
            across all sessions
          </div>
        </div>
        <div className="stat">
          <div className="sl">
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none"><circle cx="12" cy="12" r="8" stroke="currentColor" strokeWidth="1.7"/><path d="M12 7v5l3 2" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round"/></svg>
            Token spend
          </div>
          <div className="sv">{statsLoading ? '—' : formatUSD(stats?.total_cost_usd)}</div>
          <div className="sd flat">
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none"><path d="M5 12h14" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round"/></svg>
            all time
          </div>
        </div>
      </div>

      {/* First-run onboarding */}
      {showOnboarding && <OnboardingCard />}

      {/* Chart + Attention */}
      <div className="dash-chart-grid">
        <div className="card">
          <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', marginBottom: 22 }}>
            <div>
              <h3 style={{ fontFamily: 'var(--font-body)', fontWeight: 700, fontSize: 16 }}>Sessions over time</h3>
              <p style={{ fontSize: 12.5, color: 'var(--text-tertiary)', marginTop: 3 }}>Captured per day · last {range} days</p>
            </div>
            <span style={{ display: 'inline-flex', alignItems: 'center', gap: 7, fontSize: 12, color: 'var(--text-secondary)' }}>
              <i style={{ width: 9, height: 9, borderRadius: 3, background: 'var(--accent)', display: 'inline-block' }} /> Captured
            </span>
          </div>
          {statsLoading ? (
            <div style={{ height: 200, display: 'grid', placeItems: 'center', color: 'var(--text-tertiary)', fontSize: 13 }}>Loading…</div>
          ) : !hasSessions ? (
            <div style={{ height: 200, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: 8, color: 'var(--text-tertiary)', textAlign: 'center', padding: '0 24px' }}>
              <svg width="26" height="26" viewBox="0 0 24 24" fill="none" style={{ opacity: 0.5 }}><path d="M4 19V5M4 19h16M8 16l3-4 3 2 4-6" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round"/></svg>
              <div style={{ fontSize: 13.5, color: 'var(--text-secondary)' }}>No sessions captured yet</div>
              <div style={{ fontSize: 12.5 }}>Upload your first <span style={{ fontFamily: 'var(--font-mono)' }}>.capsule</span> and your activity will chart here.</div>
            </div>
          ) : (
            <BarChart data={stats?.daily ?? []} />
          )}
        </div>

        <div className="card">
          <div className="between" style={{ marginBottom: 6 }}>
            <h3 style={{ fontFamily: 'var(--font-body)', fontWeight: 700, fontSize: 16 }}>Needs attention</h3>
            {failingSessions.length > 0 && (
              <span className="badge err"><span className="d" />{failingSessions.length} failing</span>
            )}
          </div>
          {sessionsLoading ? (
            <div style={{ padding: '20px 0', color: 'var(--text-tertiary)', fontSize: 13 }}>Loading…</div>
          ) : failingSessions.length === 0 ? (
            <div style={{ padding: '20px 0', color: 'var(--text-tertiary)', fontSize: 13 }}>
              {recentSessions.length === 0 ? 'Nothing here yet — failed sessions will surface here.' : 'No failing sessions — all clear.'}
            </div>
          ) : failingSessions.map((a) => (
            <Link href={`/dashboard/sessions/${a.id}`} key={a.id} style={{ display: 'flex', gap: 12, padding: '14px 0', borderBottom: '1px solid var(--border-subtle)', cursor: 'pointer', textDecoration: 'none' }}>
              <div style={{ width: 30, height: 30, borderRadius: 8, display: 'grid', placeItems: 'center', background: 'color-mix(in oklab, var(--error) 14%, transparent)', color: 'var(--error)', flex: 'none' }}>
                <svg width="15" height="15" viewBox="0 0 24 24" fill="none"><path d="M12 8v5M12 16.5v.5" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/><circle cx="12" cy="12" r="9" stroke="currentColor" strokeWidth="1.6"/></svg>
              </div>
              <div style={{ flex: 1, minWidth: 0 }}>
                <div style={{ fontFamily: 'var(--font-mono)', fontSize: 13, color: 'var(--text-secondary)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{a.id}</div>
                <div style={{ fontSize: 12.5, color: 'var(--text-tertiary)', marginTop: 3 }}>{a.agent}</div>
              </div>
              <span style={{ fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--text-tertiary)', whiteSpace: 'nowrap' }}>{a.when}</span>
            </Link>
          ))}
          <Link className="btn btn-subtle btn-sm" href="/dashboard/sessions" style={{ width: '100%', marginTop: 14 }}>View all sessions</Link>
        </div>
      </div>

      {/* Recent sessions */}
      <div className="between" style={{ margin: '30px 0 14px' }}>
        <h3 style={{ fontFamily: 'var(--font-body)', fontWeight: 700, fontSize: 16 }}>Recent sessions</h3>
        <Link href="/dashboard/sessions" style={{ fontSize: 13, color: 'var(--text-secondary)' }}>View all →</Link>
      </div>
      <div className="table-wrap">
        <table className="tbl">
          <thead><tr>
            <th>Session</th><th>Status</th><th>Agent</th><th>Steps</th><th className="hide-mobile">Duration</th><th className="hide-mobile">Cost</th><th style={{ textAlign: 'right' }}>Captured</th>
          </tr></thead>
          <tbody>
            {sessionsLoading ? (
              <tr><td colSpan={7}><div className="empty">Loading sessions…</div></td></tr>
            ) : recentSessions.length === 0 ? (
              <tr><td colSpan={7}><div className="empty">{noWorkspace ? 'Create a workspace and capture your first session to get started.' : 'No sessions yet. Upload your first .capsule file to get started.'}</div></td></tr>
            ) : recentSessions.map((s) => (
              <tr key={s.id} className="clickable" onClick={() => window.location.href = `/dashboard/sessions/${s.id}`}>
                <td className="cell-mono">{s.id}</td>
                <td><span className={`badge ${s.status}`}><span className="d" />{s.label}</span></td>
                <td className="cell-mono" style={{ color: 'var(--text-secondary)' }}>{s.agent}</td>
                <td className="cell-mono">{s.steps}</td>
                <td className="cell-mono hide-mobile">{s.dur}</td>
                <td className="cell-mono hide-mobile">{s.cost}</td>
                <td className="cell-sub" style={{ textAlign: 'right' }}>{s.when}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Quick start */}
      <div className="card" style={{ marginTop: 16, display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 20, flexWrap: 'wrap' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
          <div className="avatar" style={{ background: 'var(--bg-elevated)', color: 'var(--text-primary)', border: '1px solid var(--border-default)' }}>
            <svg width="17" height="17" viewBox="0 0 24 24" fill="none"><path d="M8 9l-4 3 4 3M16 9l4 3-4 3M13 6l-2 12" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round"/></svg>
          </div>
          <div>
            <div style={{ fontWeight: 600, fontSize: 14.5 }}>Add capture to another service</div>
            <div style={{ marginTop: 4 }}>
              <span style={{ color: 'var(--replay)', fontFamily: 'var(--font-cli)' }}>$</span>{' '}
              <code style={{ fontFamily: 'var(--font-cli)', fontSize: 13 }}>capsule-trace login --api-key YOUR_KEY</code>
            </div>
          </div>
        </div>
        <a className="btn btn-ghost btn-sm" href="/dashboard/settings/api-keys">Get API key →</a>
      </div>
    </DashboardShell>
  );
}
