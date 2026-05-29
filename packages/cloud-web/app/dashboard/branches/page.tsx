'use client';

import { useState, useMemo } from 'react';
import Link from 'next/link';
import { DashboardShell } from '@/components/DashboardShell';

/* ─── Mock data ─────────────────────────────────────────────── */
interface Branch {
  id: string;
  name: string;
  originSession: string;
  originStep: number;
  project: [string, string];
  status: 'open' | 'merged' | 'abandoned';
  replays: number;
  author: string;
  age: string;
  note: string;
}

const PROJECTS: [string, string][] = [
  ['checkout-agent', 'var(--accent)'],
  ['support-triage', 'var(--replay)'],
  ['billing-agent', 'var(--warn)'],
  ['contract-review', 'var(--success)'],
];

function rng(seed: number) {
  let s = seed;
  return () => { s = (s * 1103515245 + 12345) & 0x7fffffff; return s / 0x7fffffff; };
}

const r = rng(99);
const HEX = '0123456789abcdef';
const NAMES = ['fix-schema', 'retry-timeout', 'swap-model', 'alt-prompt', 'fix-query', 'remove-context', 'increase-temp', 'add-fallback', 'cache-bust', 'patch-tool'];
const AUTHORS = ['dana@helix.ai', 'marcus@helix.ai', 'priya@helix.ai'];
const NOTES = [
  'Remove refund_window column from query',
  'Switch to gpt-4o-mini for cost reduction',
  'Fix LLM timeout by bumping to 60s',
  'Alternative prompt without chain-of-thought',
  'Add retry logic for flaky tool calls',
  'Strip context window to stay under 8k',
  'Raise temperature to 0.4 for diversity',
  'Add fallback to web.search on DB miss',
  'Invalidate stale memory before synthesis',
  'Patch stripe.charge to handle 402 gracefully',
];
const STATUSES = (['open', 'open', 'open', 'merged', 'merged', 'abandoned'] as const);

const ALL_BRANCHES: Branch[] = Array.from({ length: 37 }, (_, i) => {
  const id = 'br_' + Array.from({ length: 6 }, () => HEX[Math.floor(r() * 16)]).join('');
  const sessionId = 'sess_' + Array.from({ length: 8 }, () => HEX[Math.floor(r() * 16)]).join('');
  const proj = PROJECTS[Math.floor(r() * PROJECTS.length)];
  const status = STATUSES[Math.floor(r() * STATUSES.length)];
  const mins = i * 11 + Math.floor(r() * 8);
  const age = mins < 60 ? `${mins}m ago` : mins < 1440 ? `${Math.floor(mins / 60)}h ago` : `${Math.floor(mins / 1440)}d ago`;
  return {
    id,
    name: `${NAMES[i % NAMES.length]}-${(i + 1).toString().padStart(2, '0')}`,
    originSession: sessionId,
    originStep: 2 + Math.floor(r() * 6),
    project: proj,
    status,
    replays: Math.floor(r() * 5) + 1,
    author: AUTHORS[Math.floor(r() * AUTHORS.length)],
    age,
    note: NOTES[i % NOTES.length],
  };
});

const STATUS_COLOR: Record<string, string> = {
  open: 'var(--replay)',
  merged: 'var(--success)',
  abandoned: 'var(--text-tertiary)',
};

export default function BranchesPage() {
  const [filter, setFilter] = useState<'all' | 'open' | 'merged' | 'abandoned'>('all');
  const [q, setQ] = useState('');

  const filtered = useMemo(() => ALL_BRANCHES.filter((b) => {
    if (filter !== 'all' && b.status !== filter) return false;
    if (q && !b.name.includes(q) && !b.id.includes(q) && !b.originSession.includes(q)) return false;
    return true;
  }), [filter, q]);

  const counts = {
    open: ALL_BRANCHES.filter((b) => b.status === 'open').length,
    merged: ALL_BRANCHES.filter((b) => b.status === 'merged').length,
    abandoned: ALL_BRANCHES.filter((b) => b.status === 'abandoned').length,
  };

  return (
    <DashboardShell active="branches" title="Branches" crumb="workspace / branches">
      <div className="page-head">
        <div>
          <h2>Branches</h2>
          <p>Forked sessions where you diverged from an original execution to test a fix or hypothesis.</p>
        </div>
        <Link href="/dashboard/sessions" className="btn btn-ghost btn-sm">
          View sessions →
        </Link>
      </div>

      {/* Stats row */}
      <div className="branches-stat-grid" style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 14, marginBottom: 20 }}>
        {([
          { label: 'Open', key: 'open', color: 'var(--replay)' },
          { label: 'Merged', key: 'merged', color: 'var(--success)' },
          { label: 'Abandoned', key: 'abandoned', color: 'var(--text-tertiary)' },
        ] as const).map(({ label, key, color }) => (
          <div
            key={key}
            onClick={() => setFilter(filter === key ? 'all' : key)}
            className="card"
            style={{ cursor: 'pointer', borderColor: filter === key ? color : 'var(--border-default)', transition: 'border-color 0.15s' }}
          >
            <div style={{ fontSize: 12.5, color: 'var(--text-tertiary)', marginBottom: 8 }}>{label}</div>
            <div style={{ fontFamily: 'var(--font-display)', fontSize: 32, fontWeight: 700, color }}>{counts[key]}</div>
          </div>
        ))}
      </div>

      {/* Filters */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 14, flexWrap: 'wrap' }}>
        <div className="segmented">
          {(['all', 'open', 'merged', 'abandoned'] as const).map((s) => (
            <button key={s} className={filter === s ? 'active' : ''} onClick={() => setFilter(s)}>
              {s.charAt(0).toUpperCase() + s.slice(1)}
            </button>
          ))}
        </div>
        <div style={{ flex: 1 }} />
        <div style={{ display: 'flex', alignItems: 'center', gap: 9, background: 'var(--bg-card)', border: '1px solid var(--border-default)', borderRadius: 'var(--radius-sm)', padding: '9px 13px', width: 260, color: 'var(--text-tertiary)' }}>
          <svg width="15" height="15" viewBox="0 0 24 24" fill="none"><circle cx="10.5" cy="10.5" r="6.5" stroke="currentColor" strokeWidth="1.7"/><path d="M16 16l4 4" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round"/></svg>
          <input
            value={q}
            onChange={(e) => setQ(e.target.value)}
            placeholder="Search branches…"
            style={{ background: 'none', border: 'none', outline: 'none', color: 'var(--text-primary)', fontFamily: 'var(--font-body)', fontSize: 14, width: '100%' }}
          />
        </div>
      </div>

      {/* Table */}
      <div className="table-wrap">
        <table className="tbl">
          <thead>
            <tr>
              <th>Branch</th>
              <th>Origin session</th>
              <th>Project</th>
              <th>Status</th>
              <th>Replays</th>
              <th>Author</th>
              <th>Created</th>
              <th style={{ textAlign: 'right' }}>Actions</th>
            </tr>
          </thead>
          <tbody>
            {filtered.length === 0 ? (
              <tr><td colSpan={8}><div className="empty">No branches match these filters.</div></td></tr>
            ) : filtered.map((b) => (
              <tr
                key={b.id}
                className="clickable"
                onClick={() => window.location.href = `/dashboard/sessions/${b.originSession}`}
              >
                <td>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                    <svg width="13" height="13" viewBox="0 0 24 24" fill="none" style={{ color: STATUS_COLOR[b.status], flexShrink: 0 }}><circle cx="6" cy="6" r="2.4" stroke="currentColor" strokeWidth="1.8"/><circle cx="18" cy="18" r="2.4" stroke="currentColor" strokeWidth="1.8"/><circle cx="6" cy="18" r="2.4" stroke="currentColor" strokeWidth="1.8"/><path d="M6 8.4v3.6a3 3 0 0 0 3 3h6.6" stroke="currentColor" strokeWidth="1.8"/></svg>
                    <div>
                      <div style={{ fontFamily: 'var(--font-mono)', fontSize: 13, fontWeight: 600 }}>{b.name}</div>
                      <div style={{ fontSize: 11.5, color: 'var(--text-tertiary)', marginTop: 2 }}>{b.note}</div>
                    </div>
                  </div>
                </td>
                <td>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                    <span style={{ fontFamily: 'var(--font-mono)', fontSize: 12.5, color: 'var(--text-secondary)' }}>{b.originSession}</span>
                    <span style={{ fontSize: 11, color: 'var(--text-tertiary)', fontFamily: 'var(--font-mono)' }}>from step {b.originStep}</span>
                  </div>
                </td>
                <td>
                  <span style={{ display: 'flex', alignItems: 'center', gap: 7 }}>
                    <span style={{ width: 8, height: 8, borderRadius: 2, background: b.project[1], display: 'inline-block', flexShrink: 0 }} />
                    {b.project[0]}
                  </span>
                </td>
                <td>
                  <span style={{
                    display: 'inline-flex', alignItems: 'center', gap: 6,
                    fontFamily: 'var(--font-mono)', fontSize: 11.5,
                    color: STATUS_COLOR[b.status],
                    background: `color-mix(in oklab, ${STATUS_COLOR[b.status]} 12%, transparent)`,
                    border: `1px solid color-mix(in oklab, ${STATUS_COLOR[b.status]} 30%, transparent)`,
                    borderRadius: 6, padding: '3px 9px',
                  }}>
                    <span style={{ width: 6, height: 6, borderRadius: '50%', background: 'currentColor' }} />
                    {b.status}
                  </span>
                </td>
                <td className="cell-mono">{b.replays}</td>
                <td style={{ fontSize: 13, color: 'var(--text-secondary)' }}>{b.author}</td>
                <td className="cell-sub">{b.age}</td>
                <td>
                  <div className="row-actions" onClick={(e) => e.stopPropagation()}>
                    <span
                      title="Open origin session"
                      style={{ width: 28, height: 28, borderRadius: 6, border: '1px solid var(--border-default)', background: 'var(--bg-base)', display: 'grid', placeItems: 'center', cursor: 'pointer', color: 'var(--text-secondary)' }}
                    >
                      <svg width="13" height="13" viewBox="0 0 24 24" fill="none"><path d="M11 5 4 12l7 7M4 12h16" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"/></svg>
                    </span>
                    <span
                      title="Compare"
                      style={{ width: 28, height: 28, borderRadius: 6, border: '1px solid var(--border-default)', background: 'var(--bg-base)', display: 'grid', placeItems: 'center', cursor: 'pointer', color: 'var(--text-secondary)' }}
                    >
                      <svg width="13" height="13" viewBox="0 0 24 24" fill="none"><path d="M9 3H5a2 2 0 0 0-2 2v4m6-6h10a2 2 0 0 1 2 2v4M9 3v18m0 0h10a2 2 0 0 0 2-2V9M9 21H5a2 2 0 0 1-2-2V9m0 0h18" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"/></svg>
                    </span>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Count */}
      <div style={{ marginTop: 14, fontSize: 13, color: 'var(--text-tertiary)' }}>
        Showing {filtered.length} of {ALL_BRANCHES.length} branches
      </div>
    </DashboardShell>
  );
}
