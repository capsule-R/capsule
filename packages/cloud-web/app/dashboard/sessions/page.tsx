'use client';

import { useState, useMemo } from 'react';
import Link from 'next/link';
import { DashboardShell } from '@/components/DashboardShell';

const PROJECTS: [string, string][] = [
  ['checkout-agent', 'var(--accent)'],
  ['support-triage', 'var(--replay)'],
  ['billing-agent', 'var(--warn)'],
  ['contract-review', 'var(--success)'],
];
const MODELS = ['gpt-4o', 'gpt-4o-mini', 'claude-3.7'];
const STATUSES: [string, string][] = [['ok','completed'],['ok','completed'],['ok','completed'],['err','failed'],['replay','replayed']];

function rng(seed: number) {
  let s = seed;
  return () => { s = (s * 1103515245 + 12345) & 0x7fffffff; return s / 0x7fffffff; };
}

interface Session {
  id: string; st: [string, string]; proj: [string, string];
  model: string; steps: number; dur: string; cost: string; when: string; costN: number;
}

const r = rng(42);
const HEX = '0123456789abcdef';
const ALL_SESSIONS: Session[] = Array.from({ length: 47 }, (_, i) => {
  const id = 'sess_' + Array.from({ length: 8 }, () => HEX[Math.floor(r() * 16)]).join('');
  const st = STATUSES[Math.floor(r() * STATUSES.length)];
  const proj = PROJECTS[Math.floor(r() * PROJECTS.length)];
  const model = MODELS[Math.floor(r() * MODELS.length)];
  const steps = 4 + Math.floor(r() * 14);
  const dur = st[0] === 'err' && r() > 0.6 ? `${(20 + r() * 12).toFixed(1)}s` : `${(1 + r() * 7).toFixed(1)}s`;
  const cost = `$${(0.002 + r() * 0.04).toFixed(4)}`;
  const mins = i * 7 + Math.floor(r() * 6);
  const when = mins < 60 ? `${mins}m ago` : mins < 1440 ? `${Math.floor(mins / 60)}h ago` : `${Math.floor(mins / 1440)}d ago`;
  return { id, st, proj, model, steps, dur, cost, when, costN: parseFloat(cost.slice(1)) };
});

export default function SessionsPage() {
  const [status, setStatus] = useState('all');
  const [model, setModel] = useState('');
  const [dateRange, setDateRange] = useState('30d');
  const [q, setQ] = useState('');
  const [page, setPage] = useState(1);
  const PER = 10;

  const filtered = useMemo(() => ALL_SESSIONS.filter((s) => {
    if (status !== 'all' && s.st[0] !== status) return false;
    if (model && s.model !== model) return false;
    if (q && !s.id.includes(q)) return false;
    return true;
  }), [status, model, q]);

  const totalPages = Math.max(1, Math.ceil(filtered.length / PER));
  const slice = filtered.slice((page - 1) * PER, page * PER);
  const okCount = filtered.filter((s) => s.st[0] === 'ok').length;
  const errCount = filtered.filter((s) => s.st[0] === 'err').length;
  const totalCost = filtered.reduce((a, s) => a + s.costN, 0);

  const setStatusAndReset = (s: string) => { setStatus(s); setPage(1); };

  return (
    <DashboardShell
      active="sessions"
      title="Sessions"
      crumb="workspace / sessions"
      action={{ label: 'New capture', href: '/dashboard/settings/api-keys' }}
    >
      <div className="page-head">
        <div>
          <h2>Sessions</h2>
          <p>Every captured agent execution. Click a row to open the time-travel inspector.</p>
        </div>
        <div className="flex gap-8">
          <button className="btn btn-ghost btn-sm">
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none"><path d="M4 7h16M7 12h10M10 17h4" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round"/></svg>
            Sort
          </button>
          <button className="btn btn-ghost btn-sm">
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none"><path d="M12 4v12m0 0l-4-4m4 4l4-4M5 20h14" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round"/></svg>
            Export
          </button>
        </div>
      </div>

      {/* Filters */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 16, flexWrap: 'wrap' }}>
        <div className="segmented">
          {(['all','ok','err','replay'] as const).map((s) => (
            <button key={s} className={status === s ? 'active' : ''} onClick={() => setStatusAndReset(s)}>
              {s === 'all' ? 'All' : s === 'ok' ? 'Completed' : s === 'err' ? 'Failed' : 'Replayed'}
            </button>
          ))}
        </div>
        <div className="select-wrap">
          <select className="select" value={model} onChange={(e) => { setModel(e.target.value); setPage(1); }}
            style={{ width: 'auto', padding: '9px 34px 9px 14px' }}>
            <option value="">All models</option>
            {MODELS.map((m) => <option key={m}>{m}</option>)}
          </select>
        </div>
        <div className="select-wrap">
          <select className="select" value={dateRange} onChange={(e) => { setDateRange(e.target.value); setPage(1); }}
            style={{ width: 'auto', padding: '9px 34px 9px 14px' }}>
            <option value="30d">Last 30 days</option>
            <option value="7d">Last 7 days</option>
            <option value="24h">Last 24 hours</option>
          </select>
        </div>
        <div style={{ flex: 1 }} />
        <div style={{ display: 'flex', alignItems: 'center', gap: 9, background: 'var(--bg-card)', border: '1px solid var(--border-default)', borderRadius: 'var(--radius-sm)', padding: '9px 13px', width: 260, color: 'var(--text-tertiary)' }}>
          <svg width="15" height="15" viewBox="0 0 24 24" fill="none"><circle cx="10.5" cy="10.5" r="6.5" stroke="currentColor" strokeWidth="1.7"/><path d="M16 16l4 4" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round"/></svg>
          <input value={q} onChange={(e) => { setQ(e.target.value); setPage(1); }} placeholder="Search by session ID…"
            style={{ background: 'none', border: 'none', outline: 'none', color: 'var(--text-primary)', fontFamily: 'var(--font-body)', fontSize: 14, width: '100%' }} />
        </div>
      </div>

      {/* Summary bar */}
      <div style={{ display: 'flex', gap: 26, padding: '16px 18px', border: '1px solid var(--border-default)', borderBottom: 'none', borderRadius: 'var(--radius) var(--radius) 0 0', background: 'var(--bg-base)' }}>
        {[
          { label: 'Showing', val: `${filtered.length} sessions`, style: {} },
          { label: 'Completed', val: String(okCount), style: { color: 'var(--success)' } },
          { label: 'Failed', val: String(errCount), style: { color: 'var(--error)' } },
          { label: 'Total cost', val: `$${totalCost.toFixed(2)}`, style: {} },
        ].map(({ label, val, style }) => (
          <div key={label} style={{ fontSize: 12.5, color: 'var(--text-tertiary)' }}>
            {label} <b style={{ display: 'block', fontFamily: 'var(--font-display)', fontWeight: 700, fontSize: 20, color: 'var(--text-primary)', marginTop: 3, ...style }}>{val}</b>
          </div>
        ))}
      </div>

      <div className="table-wrap" style={{ borderRadius: '0 0 var(--radius) var(--radius)' }}>
        <table className="tbl">
          <thead><tr>
            <th>Session</th><th>Project</th><th>Model</th><th>Steps</th><th>Status</th><th>Duration</th><th>Cost</th><th>Captured</th><th style={{ textAlign: 'right' }}>Actions</th>
          </tr></thead>
          <tbody>
            {slice.length === 0 ? (
              <tr><td colSpan={9}><div className="empty">No sessions match these filters.</div></td></tr>
            ) : slice.map((s) => (
              <tr key={s.id} className="clickable" onClick={() => window.location.href = `/dashboard/sessions/${s.id}`}>
                <td className="cell-mono">{s.id}</td>
                <td>
                  <span style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                    <span style={{ width: 8, height: 8, borderRadius: 2, background: s.proj[1], display: 'inline-block' }} />
                    {s.proj[0]}
                  </span>
                </td>
                <td className="cell-mono" style={{ color: 'var(--text-secondary)' }}>{s.model}</td>
                <td className="cell-mono">{s.steps}</td>
                <td><span className={`badge ${s.st[0]}`}><span className="d" />{s.st[1]}</span></td>
                <td className="cell-mono">{s.dur}</td>
                <td className="cell-mono">{s.cost}</td>
                <td className="cell-sub">{s.when}</td>
                <td>
                  <div className="row-actions" onClick={(e) => e.stopPropagation()}>
                    <span style={{ width: 28, height: 28, borderRadius: 6, border: '1px solid var(--border-default)', background: 'var(--bg-base)', display: 'grid', placeItems: 'center', cursor: 'pointer', color: 'var(--text-secondary)' }} title="Replay">
                      <svg width="14" height="14" viewBox="0 0 24 24" fill="none"><path d="M11 5 4 12l7 7M4 12h16" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"/></svg>
                    </span>
                    <span style={{ width: 28, height: 28, borderRadius: 6, border: '1px solid var(--border-default)', background: 'var(--bg-base)', display: 'grid', placeItems: 'center', cursor: 'pointer', color: 'var(--text-secondary)' }} title="Branch">
                      <svg width="14" height="14" viewBox="0 0 24 24" fill="none"><circle cx="6" cy="6" r="2.4" stroke="currentColor" strokeWidth="1.8"/><circle cx="18" cy="18" r="2.4" stroke="currentColor" strokeWidth="1.8"/><circle cx="6" cy="18" r="2.4" stroke="currentColor" strokeWidth="1.8"/><path d="M6 8.4v3.6a3 3 0 0 0 3 3h6.6" stroke="currentColor" strokeWidth="1.8"/></svg>
                    </span>
                    <span style={{ width: 28, height: 28, borderRadius: 6, border: '1px solid var(--border-default)', background: 'var(--bg-base)', display: 'grid', placeItems: 'center', cursor: 'pointer', color: 'var(--text-secondary)' }} title="Download .capsule">
                      <svg width="14" height="14" viewBox="0 0 24 24" fill="none"><path d="M12 4v10m0 0l-3.5-3.5M12 14l3.5-3.5M5 19h14" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"/></svg>
                    </span>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Pager */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginTop: 16 }}>
        <div style={{ fontSize: 13, color: 'var(--text-tertiary)' }}>
          {filtered.length ? `Showing ${(page - 1) * PER + 1}–${Math.min(page * PER, filtered.length)} of ${filtered.length}` : 'No results'}
        </div>
        <div style={{ display: 'flex', gap: 6 }}>
          <button className="pg" disabled={page === 1} onClick={() => setPage(p => p - 1)} style={{ minWidth: 32, height: 32, padding: '0 8px', borderRadius: 7, border: '1px solid var(--border-default)', background: 'var(--bg-card)', color: 'var(--text-secondary)', fontFamily: 'var(--font-mono)', fontSize: 12.5, cursor: page === 1 ? 'not-allowed' : 'pointer', opacity: page === 1 ? 0.4 : 1 }}>‹</button>
          {Array.from({ length: totalPages }, (_, i) => i + 1).map((p) => (
            <button key={p} onClick={() => setPage(p)} style={{ minWidth: 32, height: 32, padding: '0 8px', borderRadius: 7, border: `1px solid ${p === page ? 'var(--accent)' : 'var(--border-default)'}`, background: p === page ? 'var(--accent)' : 'var(--bg-card)', color: p === page ? 'var(--text-inverse)' : 'var(--text-secondary)', fontFamily: 'var(--font-mono)', fontSize: 12.5, cursor: 'pointer' }}>{p}</button>
          ))}
          <button disabled={page === totalPages} onClick={() => setPage(p => p + 1)} style={{ minWidth: 32, height: 32, padding: '0 8px', borderRadius: 7, border: '1px solid var(--border-default)', background: 'var(--bg-card)', color: 'var(--text-secondary)', fontFamily: 'var(--font-mono)', fontSize: 12.5, cursor: page === totalPages ? 'not-allowed' : 'pointer', opacity: page === totalPages ? 0.4 : 1 }}>›</button>
        </div>
      </div>
    </DashboardShell>
  );
}
