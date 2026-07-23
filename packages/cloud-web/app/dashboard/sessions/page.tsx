'use client';

import { useState, useMemo, useEffect } from 'react';
import Link from 'next/link';
import { DashboardShell } from '@/components/DashboardShell';
import { UploadModal } from '@/components/UploadModal';
import { ToastHost } from '@/components/Toast';
import {
  apiFetch,
  getPrimaryWorkspace,
  downloadSessionCapsule,
  formatUSD,
  agentColor,
  type UploadedSession,
} from '@/lib/capsule';

interface Session {
  id: string;
  ok: boolean;
  statusLabel: string;
  agent: string;
  steps: number;
  dur: string;
  cost: string;
  costN: number;
  when: string;
  ts: number; // uploaded_at epoch ms, for date filtering
}

const RANGE_MS: Record<string, number> = {
  '24h': 24 * 60 * 60 * 1000,
  '7d': 7 * 24 * 60 * 60 * 1000,
  '30d': 30 * 24 * 60 * 60 * 1000,
  all: Infinity,
};

export default function SessionsPage() {
  const [sessions, setSessions] = useState<Session[]>([]);
  const [workspaceId, setWorkspaceId] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [status, setStatus] = useState<'all' | 'ok' | 'err'>('all');
  const [agent, setAgent] = useState('');
  const [dateRange, setDateRange] = useState('30d');
  const [q, setQ] = useState('');
  const [page, setPage] = useState(1);
  const [downloading, setDownloading] = useState<string | null>(null);
  const [uploadOpen, setUploadOpen] = useState(false);
  const [showFilters, setShowFilters] = useState(false);
  const PER = 10;

  // Auto-open the upload modal when arriving via "+ New capture" (?upload=1)
  useEffect(() => {
    if (typeof window !== 'undefined' && window.location.search.includes('upload=1')) {
      setUploadOpen(true);
    }
  }, []);

  const handleUploaded = (s: UploadedSession) => {
    const ok = s.status === 'success' || s.status === 'completed';
    const row: Session = {
      id: s.id,
      ok,
      statusLabel: s.status,
      agent: s.agent_name || '—',
      steps: s.step_count || 0,
      dur: s.duration_ms ? `${(s.duration_ms / 1000).toFixed(1)}s` : '—',
      cost: formatUSD(s.total_cost_usd),
      costN: Number(s.total_cost_usd ?? 0),
      when: s.uploaded_at ? new Date(s.uploaded_at).toLocaleDateString() : '—',
      ts: s.uploaded_at ? new Date(s.uploaded_at).getTime() : Date.now(),
    };
    setSessions((prev) => [row, ...prev.filter((p) => p.id !== row.id)]);
    setPage(1);
  };

  useEffect(() => {
    async function loadData() {
      const ws = await getPrimaryWorkspace();
      if (ws.status !== 'ok') { setLoading(false); return; }
      setWorkspaceId(ws.workspace.id);
      try {
        const res = await apiFetch(`/workspaces/${ws.workspace.id}/sessions?limit=100`);
        if (!res.ok) throw new Error('Failed to fetch sessions');
        const data = await res.json();
        const mapped: Session[] = data.items.map((s: any) => {
          const ok = s.status === 'success' || s.status === 'completed';
          return {
            id: s.id,
            ok,
            statusLabel: s.status,
            agent: s.agent_name || '—',
            steps: s.step_count || 0,
            dur: s.duration_ms ? `${(s.duration_ms / 1000).toFixed(1)}s` : '—',
            cost: formatUSD(s.total_cost_usd),
            costN: Number(s.total_cost_usd ?? 0),
            when: s.uploaded_at ? new Date(s.uploaded_at).toLocaleDateString() : '—',
            ts: s.uploaded_at ? new Date(s.uploaded_at).getTime() : 0,
          };
        });
        setSessions(mapped);
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, []);

  const agents = useMemo(
    () => Array.from(new Set(sessions.map((s) => s.agent).filter((a) => a && a !== '—'))).sort(),
    [sessions],
  );

  const filtered = useMemo(() => {
    const cutoff = Date.now() - (RANGE_MS[dateRange] ?? Infinity);
    return sessions.filter((s) => {
      if (status === 'ok' && !s.ok) return false;
      // "Failed" means status === 'failed' specifically — not "anything
      // that isn't success", which used to also sweep in 'cancelled'
      // sessions. That mismatched the Overview page's /stats endpoint,
      // which has always counted only true failures (see session_stats in
      // cloud-api's sessions router), so the same account showed two
      // different "failed" numbers depending on which page you were on.
      if (status === 'err' && s.statusLabel !== 'failed') return false;
      if (agent && s.agent !== agent) return false;
      if (q && !s.id.toLowerCase().includes(q.toLowerCase())) return false;
      if (isFinite(cutoff) && s.ts && s.ts < cutoff) return false;
      return true;
    });
  }, [status, agent, q, dateRange, sessions]);

  const totalPages = Math.max(1, Math.ceil(filtered.length / PER));
  const safePage = Math.min(page, totalPages);
  const slice = filtered.slice((safePage - 1) * PER, safePage * PER);
  const okCount = filtered.filter((s) => s.ok).length;
  const errCount = filtered.filter((s) => s.statusLabel === 'failed').length;
  const totalCost = filtered.reduce((a, s) => a + s.costN, 0);

  const handleDownload = async (id: string) => {
    if (!workspaceId) return;
    setDownloading(id);
    const { error } = await downloadSessionCapsule(workspaceId, id);
    if (error) alert(error);
    setDownloading(null);
  };

  return (
    <DashboardShell
      active="sessions"
      title="Sessions"
      crumb="workspace / sessions"
      action={{ label: 'New capture', onClick: () => setUploadOpen(true) }}
    >
      <div className="page-head">
        <div>
          <h2>Sessions</h2>
          <p>Every captured agent execution. Click a row to open the time-travel inspector.</p>
        </div>
        <button className="btn btn-primary btn-sm" onClick={() => setUploadOpen(true)}>
          + Upload .capsule
        </button>
      </div>

      {/* Filters */}
      <div className="sessions-filter-bar" style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 16, flexWrap: 'wrap' }}>
        <div className="segmented">
          {([['all', 'All'], ['ok', 'Completed'], ['err', 'Failed']] as const).map(([s, label]) => (
            <button key={s} className={status === s ? 'active' : ''} onClick={() => { setStatus(s); setPage(1); }}>
              {label}
            </button>
          ))}
        </div>
        
        <button className="btn btn-subtle mobile-filter-btn" onClick={() => setShowFilters(true)}>
          <svg width="15" height="15" viewBox="0 0 24 24" fill="none"><path d="M4 6h16M7 12h10M10 18h4" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round"/></svg>
          Filters
        </button>

        {showFilters && <div className="modal-overlay" onClick={() => setShowFilters(false)} style={{ zIndex: 90 }} />}
        
        <div className={`filters-desktop ${showFilters ? 'mobile-open' : ''}`}>
          {showFilters && (
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
              <h3 style={{ fontSize: 16, fontWeight: 600 }}>Filters</h3>
              <button className="modal-close" onClick={() => setShowFilters(false)}>✕</button>
            </div>
          )}
          <div className="select-wrap">
            <select className="select" value={agent} onChange={(e) => { setAgent(e.target.value); setPage(1); }}
              style={{ width: 'auto', padding: '9px 34px 9px 14px' }}>
              <option value="">All agents</option>
              {agents.map((m) => <option key={m} value={m}>{m}</option>)}
            </select>
          </div>
          <div className="select-wrap">
            <select className="select" value={dateRange} onChange={(e) => { setDateRange(e.target.value); setPage(1); }}
              style={{ width: 'auto', padding: '9px 34px 9px 14px' }}>
              <option value="30d">Last 30 days</option>
              <option value="7d">Last 7 days</option>
              <option value="24h">Last 24 hours</option>
              <option value="all">All time</option>
            </select>
          </div>
        </div>

        <div className="filter-spacer" style={{ flex: 1 }} />
        <div className="search-wrap" style={{ display: 'flex', alignItems: 'center', gap: 9, background: 'var(--bg-card)', border: '1px solid var(--border-default)', borderRadius: 'var(--radius-sm)', padding: '9px 13px', width: 260, color: 'var(--text-tertiary)' }}>
          <svg width="15" height="15" viewBox="0 0 24 24" fill="none"><circle cx="10.5" cy="10.5" r="6.5" stroke="currentColor" strokeWidth="1.7"/><path d="M16 16l4 4" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round"/></svg>
          <input value={q} onChange={(e) => { setQ(e.target.value); setPage(1); }} placeholder="Search by session ID…"
            style={{ background: 'none', border: 'none', outline: 'none', color: 'var(--text-primary)', fontFamily: 'var(--font-body)', fontSize: 14, width: '100%' }} />
        </div>
      </div>

      {/* Summary bar */}
      <div className="sessions-summary" style={{ display: 'flex', gap: 26, padding: '16px 18px', border: '1px solid var(--border-default)', borderBottom: 'none', borderRadius: 'var(--radius) var(--radius) 0 0', background: 'var(--bg-base)' }}>
        {[
          { label: 'Showing', val: `${filtered.length} sessions`, style: {} },
          { label: 'Completed', val: String(okCount), style: { color: 'var(--success)' } },
          { label: 'Failed', val: String(errCount), style: { color: 'var(--error)' } },
          { label: 'Total cost', val: formatUSD(totalCost), style: {} },
        ].map(({ label, val, style }) => (
          <div key={label} style={{ fontSize: 12.5, color: 'var(--text-tertiary)' }}>
            {label} <b style={{ display: 'block', fontFamily: 'var(--font-display)', fontWeight: 700, fontSize: 20, color: 'var(--text-primary)', marginTop: 3, ...style }}>{val}</b>
          </div>
        ))}
      </div>

      <div className="table-wrap" style={{ borderRadius: '0 0 var(--radius) var(--radius)' }}>
        <table className="tbl sessions-tbl">
          <colgroup>
            <col className="col-session" /><col className="col-agent" /><col className="col-steps" />
            <col className="col-status" /><col className="col-duration" /><col className="col-cost" />
            <col className="col-captured" /><col className="col-actions" />
          </colgroup>
          <thead><tr>
            <th>Session</th><th>Agent</th><th>Steps</th><th>Status</th><th className="hide-mobile">Duration</th><th className="hide-mobile">Cost</th><th>Captured</th><th style={{ textAlign: 'right' }}>Actions</th>
          </tr></thead>
          <tbody>
            {loading ? (
              <tr><td colSpan={8}><div className="empty">Loading sessions…</div></td></tr>
            ) : sessions.length === 0 ? (
              <tr><td colSpan={8}><div className="empty">No sessions yet. Upload your first .capsule file to get started.</div></td></tr>
            ) : slice.length === 0 ? (
              <tr><td colSpan={8}><div className="empty">No sessions match these filters.</div></td></tr>
            ) : slice.map((s) => (
              <tr key={s.id} className="clickable" onClick={() => window.location.href = `/dashboard/sessions/${s.id}`}>
                <td className="cell-mono"><div className="truncate-mobile" title={s.id}>{s.id}</div></td>
                <td>
                  <span className="agent-name-cell">
                    <span style={{ width: 8, height: 8, borderRadius: 2, background: agentColor(s.agent), display: 'inline-block', flexShrink: 0 }} />
                    <span className="agent-name" title={s.agent}>{s.agent}</span>
                  </span>
                </td>
                <td className="cell-mono">{s.steps}</td>
                <td><span className={`badge ${s.ok ? 'ok' : 'err'}`}><span className="d" />{s.statusLabel}</span></td>
                <td className="cell-mono hide-mobile">{s.dur}</td>
                <td className="cell-mono hide-mobile">{s.cost}</td>
                <td className="cell-sub">{s.when}</td>
                <td>
                  <div className="row-actions" onClick={(e) => e.stopPropagation()}>
                    <button
                      onClick={() => handleDownload(s.id)}
                      disabled={downloading === s.id}
                      title="Download .capsule"
                      style={{ width: 28, height: 28, borderRadius: 6, border: '1px solid var(--border-default)', background: 'var(--bg-base)', display: 'grid', placeItems: 'center', cursor: downloading === s.id ? 'wait' : 'pointer', color: 'var(--text-secondary)' }}
                    >
                      <svg width="14" height="14" viewBox="0 0 24 24" fill="none"><path d="M12 4v10m0 0l-3.5-3.5M12 14l3.5-3.5M5 19h14" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"/></svg>
                    </button>
                    <Link
                      href={`/dashboard/sessions/${s.id}`}
                      title="Open inspector"
                      style={{ width: 28, height: 28, borderRadius: 6, border: '1px solid var(--border-default)', background: 'var(--bg-base)', display: 'grid', placeItems: 'center', cursor: 'pointer', color: 'var(--text-secondary)' }}
                    >
                      <svg width="14" height="14" viewBox="0 0 24 24" fill="none"><path d="M9 18l6-6-6-6" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/></svg>
                    </Link>
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
          {filtered.length ? `Showing ${(safePage - 1) * PER + 1}–${Math.min(safePage * PER, filtered.length)} of ${filtered.length}` : 'No results'}
        </div>
        <div style={{ display: 'flex', gap: 6 }}>
          <button disabled={safePage === 1} onClick={() => setPage((p) => Math.max(1, p - 1))} style={{ minWidth: 32, height: 32, padding: '0 8px', borderRadius: 7, border: '1px solid var(--border-default)', background: 'var(--bg-card)', color: 'var(--text-secondary)', fontFamily: 'var(--font-mono)', fontSize: 12.5, cursor: safePage === 1 ? 'not-allowed' : 'pointer', opacity: safePage === 1 ? 0.4 : 1 }}>‹</button>
          {Array.from({ length: totalPages }, (_, i) => i + 1).map((p) => (
            <button key={p} onClick={() => setPage(p)} style={{ minWidth: 32, height: 32, padding: '0 8px', borderRadius: 7, border: `1px solid ${p === safePage ? 'var(--accent)' : 'var(--border-default)'}`, background: p === safePage ? 'var(--accent)' : 'var(--bg-card)', color: p === safePage ? 'var(--text-inverse)' : 'var(--text-secondary)', fontFamily: 'var(--font-mono)', fontSize: 12.5, cursor: 'pointer' }}>{p}</button>
          ))}
          <button disabled={safePage === totalPages} onClick={() => setPage((p) => Math.min(totalPages, p + 1))} style={{ minWidth: 32, height: 32, padding: '0 8px', borderRadius: 7, border: '1px solid var(--border-default)', background: 'var(--bg-card)', color: 'var(--text-secondary)', fontFamily: 'var(--font-mono)', fontSize: 12.5, cursor: safePage === totalPages ? 'not-allowed' : 'pointer', opacity: safePage === totalPages ? 0.4 : 1 }}>›</button>
        </div>
      </div>

      {workspaceId && (
        <UploadModal
          workspaceId={workspaceId}
          open={uploadOpen}
          onClose={() => setUploadOpen(false)}
          onUploaded={handleUploaded}
        />
      )}
      <ToastHost />
    </DashboardShell>
  );
}
