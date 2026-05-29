'use client';

import { useState, useEffect } from 'react';
import { DashboardShell } from '@/components/DashboardShell';
import { getCurrentUser } from '@/lib/capsule';

function UsageBar({ label, used, total, unit, color = 'var(--accent)' }: {
  label: string; used: number; total: number; unit: string; color?: string;
}) {
  const pct = Math.min(100, (used / total) * 100);
  const warn = pct >= 80;
  const barColor = warn ? 'var(--warn)' : color;
  return (
    <div style={{ marginBottom: 20 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', marginBottom: 8 }}>
        <span style={{ fontSize: 13.5, fontWeight: 600, color: 'var(--text-primary)' }}>{label}</span>
        <span style={{ fontSize: 12.5, fontFamily: 'var(--font-mono)', color: warn ? 'var(--warn)' : 'var(--text-secondary)' }}>
          {used.toLocaleString()} / {total.toLocaleString()} {unit}
        </span>
      </div>
      <div style={{ height: 7, background: 'var(--bg-elevated)', borderRadius: 4, overflow: 'hidden' }}>
        <div style={{ width: `${pct}%`, height: '100%', background: barColor, borderRadius: 4, transition: 'width 0.4s' }} />
      </div>
      <div style={{ fontSize: 11, color: 'var(--text-tertiary)', marginTop: 5, fontFamily: 'var(--font-mono)' }}>
        {pct.toFixed(0)}% used · resets Jun 1
      </div>
    </div>
  );
}

const PLANS = [
  {
    id: 'starter', label: 'Starter', price: '$0', period: '/mo',
    features: ['1,000 sessions/mo', '7-day retention', '1 project', 'Community support'],
    current: false,
  },
  {
    id: 'growth', label: 'Growth', price: '$49', period: '/mo',
    features: ['25,000 sessions/mo', '90-day retention', '10 projects', 'Branching & replay', 'Email support'],
    current: true,
  },
  {
    id: 'scale', label: 'Scale', price: '$199', period: '/mo',
    features: ['Unlimited sessions', '1-year retention', 'Unlimited projects', 'SSO + audit log', 'Priority support', 'Custom retention'],
    current: false,
  },
];

const INVOICES = [
  { id: 'inv_001', date: 'May 1, 2025', amount: '$49.00', status: 'paid', period: 'May 2025' },
  { id: 'inv_002', date: 'Apr 1, 2025', amount: '$49.00', status: 'paid', period: 'Apr 2025' },
  { id: 'inv_003', date: 'Mar 1, 2025', amount: '$49.00', status: 'paid', period: 'Mar 2025' },
  { id: 'inv_004', date: 'Feb 1, 2025', amount: '$29.00', status: 'paid', period: 'Feb 2025' },
];

export default function BillingPage() {
  const [showUpgrade, setShowUpgrade] = useState(false);
  const [billingEmail, setBillingEmail] = useState('');

  useEffect(() => {
    getCurrentUser().then((u) => {
      if (u?.email) setBillingEmail(u.email);
    });
  }, []);

  return (
    <DashboardShell active="billing" title="Billing & Plan" crumb="workspace / settings / billing">
      <div className="page-head">
        <div>
          <h2>Billing & Plan</h2>
          <p>Manage your plan, usage, and payment details.</p>
        </div>
      </div>

      {/* Current plan banner */}
      <div className="card" style={{ marginBottom: 16, display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 16 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
          <div style={{ width: 44, height: 44, borderRadius: 10, background: 'color-mix(in oklab, var(--accent) 10%, transparent)', border: '1px solid var(--border-default)', display: 'grid', placeItems: 'center', color: 'var(--accent)' }}>
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none"><rect x="3" y="5" width="18" height="14" rx="2.5" stroke="currentColor" strokeWidth="1.7"/><path d="M3 9.5h18" stroke="currentColor" strokeWidth="1.7"/><path d="M7 14.5h4" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round"/></svg>
          </div>
          <div>
            <div style={{ fontWeight: 700, fontSize: 16 }}>Growth Plan</div>
            <div style={{ fontSize: 13, color: 'var(--text-tertiary)', marginTop: 2 }}>$49 / month · renews Jun 1, 2025</div>
          </div>
        </div>
        <div style={{ display: 'flex', gap: 10 }}>
          <button className="btn btn-ghost btn-sm" onClick={() => setShowUpgrade(true)}>Change plan</button>
          <button className="btn btn-ghost btn-sm" style={{ color: 'var(--error)' }}>Cancel plan</button>
        </div>
      </div>

      <div className="billing-grid" style={{ display: 'grid', gridTemplateColumns: '1.3fr 1fr', gap: 16, marginBottom: 16 }}>
        {/* Usage */}
        <div className="card">
          <h3 style={{ fontFamily: 'var(--font-body)', fontWeight: 700, fontSize: 15, marginBottom: 22 }}>Usage this month</h3>
          <UsageBar label="Sessions captured" used={16042} total={25000} unit="sessions" />
          <UsageBar label="Storage" used={3.8} total={10} unit="GB" color="var(--replay)" />
          <UsageBar label="Replays run" used={1204} total={2000} unit="replays" />
        </div>

        {/* Payment method */}
        <div className="card">
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 20 }}>
            <h3 style={{ fontFamily: 'var(--font-body)', fontWeight: 700, fontSize: 15 }}>Payment method</h3>
            <button className="btn btn-ghost btn-sm">Update</button>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 14, padding: '14px 16px', border: '1px solid var(--border-default)', borderRadius: 'var(--radius-sm)', background: 'var(--bg-elevated)' }}>
            {/* Card icon */}
            <div style={{ width: 44, height: 30, borderRadius: 5, background: 'linear-gradient(135deg, #1a1a2e 0%, #16213e 100%)', border: '1px solid var(--border-default)', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
              <svg width="26" height="18" viewBox="0 0 26 18" fill="none"><circle cx="10" cy="9" r="6" fill="#eb001b" fillOpacity="0.8"/><circle cx="16" cy="9" r="6" fill="#f79e1b" fillOpacity="0.8"/></svg>
            </div>
            <div>
              <div style={{ fontWeight: 600, fontSize: 14 }}>•••• •••• •••• 4242</div>
              <div style={{ fontSize: 12, color: 'var(--text-tertiary)', marginTop: 2 }}>Expires 09/27 · Mastercard</div>
            </div>
          </div>

          <div style={{ marginTop: 20 }}>
            <h3 style={{ fontFamily: 'var(--font-body)', fontWeight: 700, fontSize: 15, marginBottom: 12 }}>Billing email</h3>
            <div style={{ display: 'flex', gap: 10 }}>
              <input className="input" value={billingEmail} onChange={(e) => setBillingEmail(e.target.value)} style={{ flex: 1 }} />
              <button className="btn btn-ghost btn-sm">Save</button>
            </div>
          </div>
        </div>
      </div>

      {/* Invoices */}
      <h3 style={{ fontFamily: 'var(--font-body)', fontWeight: 700, fontSize: 15, marginBottom: 12 }}>Invoices</h3>
      <div className="table-wrap">
        <table className="tbl">
          <thead><tr>
            <th>Invoice</th><th>Period</th><th>Date</th><th>Amount</th><th>Status</th><th style={{ textAlign: 'right' }}>Download</th>
          </tr></thead>
          <tbody>
            {INVOICES.map((inv) => (
              <tr key={inv.id}>
                <td className="cell-mono" style={{ color: 'var(--text-secondary)' }}>{inv.id}</td>
                <td>{inv.period}</td>
                <td className="cell-sub">{inv.date}</td>
                <td className="cell-mono" style={{ fontWeight: 600 }}>{inv.amount}</td>
                <td><span className="badge ok"><span className="d" />{inv.status}</span></td>
                <td style={{ textAlign: 'right' }}>
                  <button style={{ padding: '4px 12px', borderRadius: 6, border: '1px solid var(--border-default)', background: 'var(--bg-elevated)', fontSize: 12, fontFamily: 'var(--font-mono)', color: 'var(--text-secondary)', cursor: 'pointer' }}>
                    PDF
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Plan change modal */}
      {showUpgrade && (
        <div className="modal-overlay" onClick={() => setShowUpgrade(false)}>
          <div className="modal" onClick={(e) => e.stopPropagation()} style={{ maxWidth: 720, width: '95vw' }}>
            <div className="modal-head">
              <h2>Change plan</h2>
              <button className="modal-close" onClick={() => setShowUpgrade(false)}>
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none"><path d="M18 6 6 18M6 6l12 12" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/></svg>
              </button>
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 14, marginTop: 8 }}>
              {PLANS.map((plan) => (
                <div
                  key={plan.id}
                  style={{
                    padding: '20px 18px',
                    borderRadius: 'var(--radius)',
                    border: `1.5px solid ${plan.current ? 'var(--accent)' : 'var(--border-default)'}`,
                    background: plan.current ? 'color-mix(in oklab, var(--accent) 5%, transparent)' : 'var(--bg-card)',
                    display: 'flex',
                    flexDirection: 'column',
                    gap: 14,
                  }}
                >
                  <div>
                    <div style={{ fontWeight: 700, fontSize: 15, marginBottom: 4 }}>{plan.label}</div>
                    <div style={{ display: 'flex', alignItems: 'baseline', gap: 4 }}>
                      <span style={{ fontSize: 26, fontFamily: 'var(--font-display)', fontWeight: 700 }}>{plan.price}</span>
                      <span style={{ fontSize: 13, color: 'var(--text-tertiary)' }}>{plan.period}</span>
                    </div>
                  </div>
                  <ul style={{ listStyle: 'none', padding: 0, margin: 0, display: 'flex', flexDirection: 'column', gap: 8 }}>
                    {plan.features.map((f) => (
                      <li key={f} style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 12.5, color: 'var(--text-secondary)' }}>
                        <svg width="13" height="13" viewBox="0 0 24 24" fill="none"><path d="M5 13l4 4L19 7" stroke="var(--success)" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round"/></svg>
                        {f}
                      </li>
                    ))}
                  </ul>
                  <button
                    className={plan.current ? 'btn btn-ghost' : 'btn btn-primary'}
                    style={{ width: '100%', marginTop: 'auto', cursor: plan.current ? 'default' : 'pointer', opacity: plan.current ? 0.6 : 1 }}
                    disabled={plan.current}
                  >
                    {plan.current ? 'Current plan' : `Switch to ${plan.label}`}
                  </button>
                </div>
              ))}
            </div>
            <p style={{ fontSize: 12, color: 'var(--text-tertiary)', textAlign: 'center', marginTop: 20 }}>
              Upgrades are prorated. Downgrades take effect at next billing cycle.
            </p>
          </div>
        </div>
      )}
    </DashboardShell>
  );
}
