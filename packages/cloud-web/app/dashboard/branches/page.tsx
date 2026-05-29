'use client';

import { useState, useMemo, useEffect } from 'react';
import Link from 'next/link';
import { DashboardShell } from '@/components/DashboardShell';
import { apiFetch } from '@/lib/capsule';

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

const STATUS_COLOR: Record<string, string> = {
  open: 'var(--replay)',
  merged: 'var(--success)',
  abandoned: 'var(--text-tertiary)',
};

export default function BranchesPage() {
  const [branches, setBranches] = useState<Branch[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<'all' | 'open' | 'merged' | 'abandoned'>('all');
  const [q, setQ] = useState('');

  useEffect(() => {
    async function load() {
      try {
        const wsRes = await apiFetch('/workspaces');
        if (!wsRes.ok) return;
        const workspaces = await wsRes.json();
        if (workspaces.length === 0) return;
        const wsId = workspaces[0].id;

        const res = await apiFetch(`/workspaces/${wsId}/branches`);
        if (!res.ok) return;
        setBranches(await res.json());
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  const filtered = useMemo(() => branches.filter((b) => {
    if (filter !== 'all' && b.status !== filter) return false;
    if (q && !b.name.includes(q) && !b.id.includes(q) && !b.originSession.includes(q)) return false;
    return true;
  }), [filter, q, branches]);

  const counts = {
    open: branches.filter((b) => b.status === 'open').length,
    merged: branches.filter((b) => b.status === 'merged').length,
    abandoned: branches.filter((b) => b.status === 'abandoned').length,
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
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 14, marginBottom: 20 }}>
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
            <div style={{ fontFamily: 'var(--font-display)', fontWeight: 700, fontSize: 28, color }}>
              {loading ? '—' : counts[key]}
            </div>
          </div>
        ))}
      </div>

      {/* Filters */}
      <div style={{ display: 'flex', gap: 10, marginBottom: 16, alignItems: 'center' }}>
        <div className="segmented">
          {(['all', 'open', 'merged', 'abandoned'] as const).map((s) => (
            <button key={s} className={filter === s ? 'active' : ''} onClick={() => setFilter(s)}>
              {s === 'all' ? 'All' : s.charAt(0).toUpperCase() + s.slice(1)}
            </button>
          ))}
        </div>
        <div style={{ flex: 1 }} />
        <div style={{ display: 'flex', alignItems: 'center', gap: 9, background: 'var(--bg-card)', border: '1px solid var(--border-default)', borderRadius: 'var(--radius-sm)', padding: '9px 13px', width: 260, color: 'var(--text-tertiary)' }}>
          <svg width="15" height="15" viewBox="0 0 24 24" fill="none"><circle cx="10.5" cy="10.5" r="6.5" stroke="currentColor" strokeWidth="1.7"/><path d="M16 16l4 4" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round"/></svg>
          <input value={q} onChange={(e) => setQ(e.target.value)} placeholder="Search branches…"
            style={{ background: 'none', border: 'none', outline: 'none', color: 'var(--text-primary)', fontFamily: 'var(--font-body)', fontSize: 14, width: '100%' }} />
        </div>
      </div>

      {/* Table */}
      <div className="table-wrap">
        <table className="tbl">
          <thead>
            <tr>
              <th>Branch</th>
              <th>Origin session</th>
              <th>Step</th>
              <th>Status</th>
              <th>Replays</th>
              <th>Author</th>
              <th>Note</th>
              <th style={{ textAlign: 'right' }}>Age</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr><td colSpan={8}><div className="empty">Loading branches…</div></td></tr>
            ) : filtered.length === 0 ? (
              <tr><td colSpan={8}>
                <div className="empty">
                  {branches.length === 0
                    ? 'No branches yet. Fork a session step in the inspector to create one.'
                    : 'No branches match these filters.'}
                </div>
              </td></tr>
            ) : filtered.map((b) => (
              <tr key={b.id} className="clickable" onClick={() => window.location.href = `/dashboard/sessions/${b.originSession}`}>
                <td>
                  <div style={{ fontFamily: 'var(--font-mono)', fontSize: 13, color: 'var(--text-primary)' }}>{b.id}</div>
                  <div style={{ fontSize: 12, color: 'var(--text-tertiary)', marginTop: 2 }}>{b.name}</div>
                </td>
                <td className="cell-mono" style={{ color: 'var(--text-secondary)' }}>{b.originSession}</td>
                <td className="cell-mono">#{b.originStep}</td>
                <td>
                  <span style={{ fontSize: 12, fontFamily: 'var(--font-mono)', color: STATUS_COLOR[b.status], background: `color-mix(in oklab, ${STATUS_COLOR[b.status]} 12%, transparent)`, border: `1px solid color-mix(in oklab, ${STATUS_COLOR[b.status]} 28%, transparent)`, borderRadius: 4, padding: '2px 8px' }}>
                    {b.status}
                  </span>
                </td>
                <td className="cell-mono">{b.replays}</td>
                <td className="cell-sub">{b.author}</td>
                <td style={{ fontSize: 12.5, color: 'var(--text-tertiary)', maxWidth: 200 }}>{b.note}</td>
                <td className="cell-sub" style={{ textAlign: 'right', whiteSpace: 'nowrap' }}>{b.age}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </DashboardShell>
  );
}
