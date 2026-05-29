'use client';

import { useState } from 'react';
import { DashboardShell } from '@/components/DashboardShell';
import Link from 'next/link';

const CHART_DATA_30 = [42,38,55,61,47,52,68,72,59,64,77,71,83,69,75,88,79,92,84,97,89,103,95,110,101,118,107,124,116,131];

function BarChart({ data }: { data: number[] }) {
  const max = Math.max(...data) * 1.12;
  const step = Math.ceil(data.length / 10);
  return (
    <div style={{ display: 'flex', alignItems: 'flex-end', gap: 7, height: 200, paddingTop: 8 }}>
      {data.map((v, i) => {
        const rep = Math.round(v * (0.22 + (i % 5) * 0.03));
        const capH = (v / max) * 100;
        const repH = (rep / max) * 100;
        return (
          <div key={i} style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 7, height: '100%', justifyContent: 'flex-end' }}
            title={`Day ${i + 1} · ${v} captured · ${rep} replayed`}>
            <div style={{ width: '100%', maxWidth: 26, display: 'flex', flexDirection: 'column', justifyContent: 'flex-end', gap: 2, height: '100%' }}>
              <div style={{ width: '100%', height: `${repH}%`, background: 'var(--border-strong)', borderRadius: '3px 3px 0 0' }} />
              <div style={{ width: '100%', height: `${capH - repH}%`, background: 'var(--accent)', borderRadius: '3px 3px 0 0' }} />
            </div>
            <div style={{ fontFamily: 'var(--font-mono)', fontSize: 9.5, color: 'var(--text-tertiary)' }}>
              {i % step === 0 ? i + 1 : ''}
            </div>
          </div>
        );
      })}
    </div>
  );
}

const RECENT_SESSIONS = [
  { id: 'sess_8f2a91c4', status: 'err', label: 'failed', note: 'db.query failed', model: 'gpt-4o', steps: 8, dur: '3.4s', cost: '$0.0171', when: '2m ago' },
  { id: 'sess_5e19af20', status: 'ok',  label: 'completed', note: '', model: 'gpt-4o', steps: 11, dur: '5.1s', cost: '$0.0243', when: '6m ago' },
  { id: 'sess_b73c0d84', status: 'replay', label: 'replayed', note: 'replayed', model: 'claude-3.7', steps: 9, dur: '4.0s', cost: '$0.0192', when: '11m ago' },
  { id: 'sess_3b71de09', status: 'err', label: 'failed', note: 'LLM timeout', model: 'gpt-4o', steps: 6, dur: '30.2s', cost: '$0.0088', when: '14m ago' },
  { id: 'sess_a201ffe5', status: 'ok',  label: 'completed', note: '', model: 'gpt-4o-mini', steps: 7, dur: '1.9s', cost: '$0.0021', when: '19m ago' },
  { id: 'sess_c9d4e7b1', status: 'ok',  label: 'completed', note: '', model: 'claude-3.7', steps: 13, dur: '6.7s', cost: '$0.0311', when: '24m ago' },
];

const ATTENTION = [
  { id: 'sess_8f2a91c4', msg: 'db.query — column "refund_window" not found', when: '2m ago' },
  { id: 'sess_3b71de09', msg: 'LLM timeout after 30s on synthesize step', when: '14m ago' },
  { id: 'sess_d40ac1f7', msg: 'tool · stripe.charge returned 402', when: '38m ago' },
  { id: 'sess_9c02bb31', msg: 'memory · context window exceeded', when: '1h ago' },
];

export default function DashboardPage() {
  const [range, setRange] = useState(30);

  const getData = (r: number) => {
    if (r === 7) return CHART_DATA_30.slice(-7);
    if (r === 90) return Array.from({ length: 90 }, (_, i) => 38 + Math.round(i * 1.05) + (i % 7) * 6);
    return CHART_DATA_30;
  };

  return (
    <DashboardShell active="overview" title="Overview" crumb="workspace / overview" action={{ label: 'New capture', href: '/dashboard/settings/api-keys' }}>
      {/* Header row */}
      <div className="page-head">
        <div>
          <h2>Good morning, Dana.</h2>
          <p>Here&apos;s what your agents have been doing in <span className="mono" style={{ color: 'var(--text-secondary)' }}>production · checkout-agent</span>.</p>
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
          <div className="sv">12,847</div>
          <div className="sd up">
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none"><path d="M5 19V9m0 0l-3 3m3-3l3 3M14 5h6v6" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"/></svg>
            +18.2% vs prev 30d
          </div>
        </div>
        <div className="stat">
          <div className="sl">
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none"><path d="M11 5 4 12l7 7M4 12h16" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round"/></svg>
            Replays run
          </div>
          <div className="sv">3,204</div>
          <div className="sd up">
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none"><path d="M5 19V9m0 0l-3 3m3-3l3 3M14 5h6v6" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"/></svg>
            +9.4%
          </div>
        </div>
        <div className="stat">
          <div className="sl">
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none"><path d="M12 3l7 3v5c0 4.5-3 8-7 10-4-2-7-5.5-7-10V6z" stroke="currentColor" strokeWidth="1.6" strokeLinejoin="round"/></svg>
            Failure rate
          </div>
          <div className="sv">1.65<small>%</small></div>
          <div className="sd down">
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none"><path d="M5 5v10m0 0l-3-3m3 3l3-3M14 19h6v-6" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"/></svg>
            -0.4 pts (good)
          </div>
        </div>
        <div className="stat">
          <div className="sl">
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none"><circle cx="12" cy="12" r="8" stroke="currentColor" strokeWidth="1.7"/><path d="M12 7v5l3 2" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round"/></svg>
            Token spend
          </div>
          <div className="sv">$1,284</div>
          <div className="sd flat">
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none"><path d="M5 12h14" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round"/></svg>
            on track · 64% of budget
          </div>
        </div>
      </div>

      {/* Chart + Attention */}
      <div style={{ display: 'grid', gridTemplateColumns: '1.65fr 1fr', gap: 16, marginTop: 16 }}>
        <div className="card">
          <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', marginBottom: 22 }}>
            <div>
              <h3 style={{ fontFamily: 'var(--font-body)', fontWeight: 700, fontSize: 16 }}>Sessions over time</h3>
              <p style={{ fontSize: 12.5, color: 'var(--text-tertiary)', marginTop: 3 }}>Captured vs replayed, daily</p>
            </div>
            <div style={{ display: 'flex', gap: 16, fontSize: 12, color: 'var(--text-secondary)' }}>
              <span style={{ display: 'inline-flex', alignItems: 'center', gap: 7 }}>
                <i style={{ width: 9, height: 9, borderRadius: 3, background: 'var(--accent)', display: 'inline-block' }} /> Captured
              </span>
              <span style={{ display: 'inline-flex', alignItems: 'center', gap: 7 }}>
                <i style={{ width: 9, height: 9, borderRadius: 3, background: 'var(--border-strong)', display: 'inline-block' }} /> Replayed
              </span>
            </div>
          </div>
          <BarChart data={getData(range)} />
        </div>

        <div className="card">
          <div className="between" style={{ marginBottom: 6 }}>
            <h3 style={{ fontFamily: 'var(--font-body)', fontWeight: 700, fontSize: 16 }}>Needs attention</h3>
            <span className="badge err"><span className="d" />4 failing</span>
          </div>
          {ATTENTION.map((a) => (
            <Link href={`/dashboard/sessions/${a.id}`} key={a.id} style={{ display: 'flex', gap: 12, padding: '14px 0', borderBottom: '1px solid var(--border-subtle)', cursor: 'pointer', textDecoration: 'none' }}>
              <div style={{ width: 30, height: 30, borderRadius: 8, display: 'grid', placeItems: 'center', background: 'color-mix(in oklab, var(--error) 14%, transparent)', color: 'var(--error)', flex: 'none' }}>
                <svg width="15" height="15" viewBox="0 0 24 24" fill="none"><path d="M12 8v5M12 16.5v.5" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/><circle cx="12" cy="12" r="9" stroke="currentColor" strokeWidth="1.6"/></svg>
              </div>
              <div style={{ flex: 1 }}>
                <div style={{ fontFamily: 'var(--font-mono)', fontSize: 13, color: 'var(--text-secondary)' }}>{a.id}</div>
                <div style={{ fontSize: 12.5, color: 'var(--text-tertiary)', marginTop: 3 }}>{a.msg}</div>
              </div>
              <span style={{ fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--text-tertiary)', whiteSpace: 'nowrap' }}>{a.when}</span>
            </Link>
          ))}
          <a className="btn btn-subtle btn-sm" href="/dashboard/sessions" style={{ width: '100%', marginTop: 14 }}>View all failures</a>
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
            <th>Session</th><th>Status</th><th>Model</th><th>Steps</th><th>Duration</th><th>Cost</th><th style={{ textAlign: 'right' }}>Captured</th>
          </tr></thead>
          <tbody>
            {RECENT_SESSIONS.map((s) => (
              <tr key={s.id} className="clickable" onClick={() => window.location.href = `/dashboard/sessions/${s.id}`}>
                <td className="cell-mono">{s.id}</td>
                <td><span className={`badge ${s.status}`}><span className="d" />{s.label}</span></td>
                <td className="cell-mono" style={{ color: 'var(--text-secondary)' }}>{s.model}</td>
                <td className="cell-mono">{s.steps}</td>
                <td className="cell-mono">{s.dur}</td>
                <td className="cell-mono">{s.cost}</td>
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
              <code style={{ fontFamily: 'var(--font-cli)', fontSize: 13 }}>capsule init --project billing-agent</code>
            </div>
          </div>
        </div>
        <a className="btn btn-ghost btn-sm" href="/dashboard/settings/api-keys">Get API key →</a>
      </div>
    </DashboardShell>
  );
}
