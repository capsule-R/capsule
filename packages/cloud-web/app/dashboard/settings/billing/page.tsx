'use client';

import { useState, useEffect } from 'react';
import { DashboardShell } from '@/components/DashboardShell';
import {
  getCurrentUser,
  getPrimaryWorkspace,
  getSessionStats,
  formatBytes,
  type WorkspaceInfo,
} from '@/lib/capsule';

// ── Plan catalogue (mirrors the public pricing page) ──────────

interface Plan {
  id: string;
  label: string;
  price: string;
  period: string;
  blurb: string;
  features: string[];
}

const PLANS: Plan[] = [
  {
    id: 'hobby', label: 'Hobby', price: '$0', period: '/mo',
    blurb: 'For side projects and trying out deterministic replay.',
    features: ['1,000 captured sessions / mo', '7-day retention', 'Replay & branch · CLI + web', 'Community support'],
  },
  {
    id: 'pro', label: 'Pro', price: '$49', period: '/mo',
    blurb: 'For teams debugging agents in production.',
    features: ['100,000 sessions / mo', '90-day retention · unlimited branches', 'Shared workspaces & bug-report links', 'Priority email support'],
  },
  {
    id: 'enterprise', label: 'Enterprise', price: 'Custom', period: '',
    blurb: 'For fintech & legal teams with compliance needs.',
    features: ['Unlimited sessions & retention', 'EU AI Act audit exports · SOC 2 report', 'Self-host / VPC deployment · SSO', 'Dedicated solutions engineer'],
  },
];

const CONTACT_EMAIL = 'founders@capsule.dev';

/** Map a backend plan_tier onto a catalogue entry. New workspaces default to
 *  'free', which is the entry-level Hobby plan. */
function planForTier(tier: string | undefined): Plan {
  const t = (tier ?? 'free').toLowerCase();
  if (t === 'pro') return PLANS[1];
  if (t === 'business' || t === 'enterprise') return PLANS[2];
  return PLANS[0]; // free / hobby / anything else
}

// ── Real storage usage bar ────────────────────────────────────

function StorageBar({ used, total, retentionDays }: { used: number; total: number; retentionDays: number }) {
  const pct = total > 0 ? Math.min(100, (used / total) * 100) : 0;
  const warn = pct >= 80;
  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', marginBottom: 8 }}>
        <span style={{ fontSize: 13.5, fontWeight: 600, color: 'var(--text-primary)' }}>Storage used</span>
        <span style={{ fontSize: 12.5, fontFamily: 'var(--font-mono)', color: warn ? 'var(--warn)' : 'var(--text-secondary)' }}>
          {formatBytes(used)} / {formatBytes(total)}
        </span>
      </div>
      <div style={{ height: 7, background: 'var(--bg-elevated)', borderRadius: 4, overflow: 'hidden' }}>
        <div style={{ width: `${pct}%`, height: '100%', background: warn ? 'var(--warn)' : 'var(--accent)', borderRadius: 4, transition: 'width 0.4s' }} />
      </div>
      <div style={{ fontSize: 11, color: 'var(--text-tertiary)', marginTop: 5, fontFamily: 'var(--font-mono)' }}>
        {pct.toFixed(0)}% used · sessions retained for {retentionDays} days
      </div>
    </div>
  );
}

function MiniStat({ label, value, sub }: { label: string; value: string; sub?: string }) {
  return (
    <div style={{ padding: '14px 16px', border: '1px solid var(--border-subtle)', borderRadius: 'var(--radius-sm)', background: 'var(--bg-elevated)' }}>
      <div style={{ fontSize: 12, color: 'var(--text-tertiary)' }}>{label}</div>
      <div style={{ fontFamily: 'var(--font-display)', fontWeight: 700, fontSize: 22, marginTop: 4 }}>{value}</div>
      {sub && <div style={{ fontSize: 11, color: 'var(--text-tertiary)', fontFamily: 'var(--font-mono)', marginTop: 2 }}>{sub}</div>}
    </div>
  );
}

// ── Page ──────────────────────────────────────────────────────

export default function BillingPage() {
  const [workspace, setWorkspace] = useState<WorkspaceInfo | null>(null);
  const [sessionCount, setSessionCount] = useState<number | null>(null);
  const [email, setEmail] = useState('');
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState(false);
  const [showPlans, setShowPlans] = useState(false);
  const [payNotice, setPayNotice] = useState(false);

  useEffect(() => {
    async function load() {
      const [ws, user] = await Promise.all([getPrimaryWorkspace(), getCurrentUser()]);
      if (user?.email) setEmail(user.email);
      if (ws.status === 'ok') {
        setWorkspace(ws.workspace);
        const stats = await getSessionStats(ws.workspace.id, 1);
        setSessionCount(stats?.total ?? 0);
      } else if (ws.status === 'error') {
        setLoadError(true);
      }
      setLoading(false);
    }
    load();
  }, []);

  const current = planForTier(workspace?.plan_tier);

  return (
    <DashboardShell active="billing" title="Billing & Plan" crumb="workspace / settings / billing">
      <div className="page-head">
        <div>
          <h2>Billing &amp; Plan</h2>
          <p>Your current plan, usage, and payment details.</p>
        </div>
      </div>

      {loading ? (
        <div className="empty">Loading billing…</div>
      ) : loadError ? (
        <div className="empty" style={{ color: 'var(--error)' }}>
          Couldn&apos;t load your workspace. Please refresh the page.
        </div>
      ) : !workspace ? (
        <div className="card" style={{ textAlign: 'center', padding: '40px 24px' }}>
          <div style={{ fontWeight: 700, fontSize: 16, marginBottom: 6 }}>No workspace yet</div>
          <p style={{ fontSize: 13.5, color: 'var(--text-tertiary)' }}>
            Create a workspace and capture a session to see plan and usage details here.
          </p>
        </div>
      ) : (
        <>
          {/* Current plan banner */}
          <div className="card" style={{ marginBottom: 16, display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 16 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
              <div style={{ width: 44, height: 44, borderRadius: 10, background: 'color-mix(in oklab, var(--accent) 10%, transparent)', border: '1px solid var(--border-default)', display: 'grid', placeItems: 'center', color: 'var(--accent)' }}>
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none"><rect x="3" y="5" width="18" height="14" rx="2.5" stroke="currentColor" strokeWidth="1.7"/><path d="M3 9.5h18" stroke="currentColor" strokeWidth="1.7"/><path d="M7 14.5h4" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round"/></svg>
              </div>
              <div>
                <div style={{ fontWeight: 700, fontSize: 16 }}>{current.label} plan</div>
                <div style={{ fontSize: 13, color: 'var(--text-tertiary)', marginTop: 2 }}>
                  {current.id === 'hobby'
                    ? 'Free during early access · no card required'
                    : current.id === 'enterprise'
                      ? 'Custom pricing'
                      : `${current.price}${current.period}`}
                </div>
              </div>
            </div>
            <div style={{ display: 'flex', gap: 10 }}>
              <button className="btn btn-ghost btn-sm" onClick={() => setShowPlans(true)}>Change plan</button>
            </div>
          </div>

          <div className="billing-grid" style={{ display: 'grid', gridTemplateColumns: '1.3fr 1fr', gap: 16, marginBottom: 16 }}>
            {/* Usage (real) */}
            <div className="card">
              <h3 style={{ fontFamily: 'var(--font-body)', fontWeight: 700, fontSize: 15, marginBottom: 22 }}>Usage</h3>
              <StorageBar
                used={workspace.storage_used_bytes}
                total={workspace.storage_quota_bytes}
                retentionDays={workspace.retention_days}
              />
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12, marginTop: 22 }}>
                <MiniStat label="Sessions captured" value={(sessionCount ?? 0).toLocaleString()} sub="all time" />
                <MiniStat label="Retention" value={`${workspace.retention_days} days`} sub="current plan" />
              </div>
            </div>

            {/* Payment method (honest — billing not yet enabled) */}
            <div className="card">
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 20 }}>
                <h3 style={{ fontFamily: 'var(--font-body)', fontWeight: 700, fontSize: 15 }}>Payment method</h3>
                <button className="btn btn-ghost btn-sm" onClick={() => setPayNotice((v) => !v)}>Add card</button>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: 14, padding: '16px', border: '1px dashed var(--border-default)', borderRadius: 'var(--radius-sm)', background: 'var(--bg-elevated)' }}>
                <div style={{ width: 40, height: 28, borderRadius: 5, background: 'var(--bg-base)', border: '1px solid var(--border-default)', display: 'grid', placeItems: 'center', flexShrink: 0, color: 'var(--text-tertiary)' }}>
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none"><rect x="3" y="6" width="18" height="12" rx="2" stroke="currentColor" strokeWidth="1.7"/><path d="M3 10h18" stroke="currentColor" strokeWidth="1.7"/></svg>
                </div>
                <div style={{ fontSize: 13, color: 'var(--text-tertiary)', lineHeight: 1.5 }}>
                  No payment method on file. Capsule is free during early access — you&apos;ll add a card here when paid plans launch.
                </div>
              </div>
              {payNotice && (
                <div style={{ marginTop: 12, padding: '10px 14px', borderRadius: 7, fontSize: 12.5, color: 'var(--replay)', background: 'color-mix(in oklab, var(--replay) 9%, transparent)', border: '1px solid color-mix(in oklab, var(--replay) 28%, transparent)' }}>
                  Card management is coming soon. Need an invoice now? Email{' '}
                  <a href={`mailto:${CONTACT_EMAIL}`} style={{ color: 'var(--text-primary)', textDecoration: 'underline' }}>{CONTACT_EMAIL}</a>.
                </div>
              )}

              <div style={{ marginTop: 20 }}>
                <h3 style={{ fontFamily: 'var(--font-body)', fontWeight: 700, fontSize: 15, marginBottom: 8 }}>Billing email</h3>
                <div style={{ fontSize: 13, color: 'var(--text-secondary)' }}>
                  Receipts and invoices will be sent to{' '}
                  <span style={{ fontFamily: 'var(--font-mono)', color: 'var(--text-primary)' }}>{email || '—'}</span>.
                </div>
                <div style={{ fontSize: 12, color: 'var(--text-tertiary)', marginTop: 4 }}>
                  Update it from your <a href="/dashboard/settings/general" style={{ color: 'var(--text-secondary)', textDecoration: 'underline' }}>account settings</a>.
                </div>
              </div>
            </div>
          </div>

          {/* Invoices (none yet) */}
          <h3 style={{ fontFamily: 'var(--font-body)', fontWeight: 700, fontSize: 15, marginBottom: 12 }}>Invoices</h3>
          <div className="card" style={{ textAlign: 'center', padding: '36px 24px' }}>
            <div style={{ color: 'var(--text-tertiary)', fontSize: 13.5 }}>
              No invoices yet. They&apos;ll appear here once you&apos;re on a paid plan.
            </div>
          </div>
        </>
      )}

      {/* Plan comparison modal — read-only / coming soon */}
      {showPlans && (
        <div className="modal-overlay" onClick={() => setShowPlans(false)}>
          <div className="modal" onClick={(e) => e.stopPropagation()} style={{ maxWidth: 760, width: '95vw' }}>
            <div className="modal-head">
              <h2>Plans</h2>
              <button className="modal-close" onClick={() => setShowPlans(false)}>
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none"><path d="M18 6 6 18M6 6l12 12" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/></svg>
              </button>
            </div>

            <div style={{ padding: '12px 16px', borderRadius: 8, marginBottom: 18, fontSize: 13, lineHeight: 1.55, color: 'var(--replay)', background: 'color-mix(in oklab, var(--replay) 9%, transparent)', border: '1px solid color-mix(in oklab, var(--replay) 28%, transparent)' }}>
              <strong style={{ color: 'var(--text-primary)' }}>Self-service plan changes are coming soon.</strong>{' '}
              We&apos;re bringing one-click upgrades shortly. To switch plans now, email{' '}
              <a href={`mailto:${CONTACT_EMAIL}`} style={{ color: 'var(--text-primary)', textDecoration: 'underline' }}>{CONTACT_EMAIL}</a>.
            </div>

            <div className="plan-grid" style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 14 }}>
              {PLANS.map((plan) => {
                const isCurrent = plan.id === current.id;
                return (
                  <div
                    key={plan.id}
                    style={{
                      padding: '20px 18px',
                      borderRadius: 'var(--radius)',
                      border: `1.5px solid ${isCurrent ? 'var(--accent)' : 'var(--border-default)'}`,
                      background: isCurrent ? 'color-mix(in oklab, var(--accent) 5%, transparent)' : 'var(--bg-card)',
                      display: 'flex', flexDirection: 'column', gap: 14,
                    }}
                  >
                    <div>
                      <div style={{ fontWeight: 700, fontSize: 15, marginBottom: 4, display: 'flex', alignItems: 'center', gap: 8 }}>
                        {plan.label}
                        {isCurrent && <span className="badge ok" style={{ textTransform: 'none' }}>current</span>}
                      </div>
                      <div style={{ display: 'flex', alignItems: 'baseline', gap: 4 }}>
                        <span style={{ fontSize: 26, fontFamily: 'var(--font-display)', fontWeight: 700 }}>{plan.price}</span>
                        {plan.period && <span style={{ fontSize: 13, color: 'var(--text-tertiary)' }}>{plan.period}</span>}
                      </div>
                      <div style={{ fontSize: 12, color: 'var(--text-tertiary)', marginTop: 6, lineHeight: 1.45 }}>{plan.blurb}</div>
                    </div>
                    <ul style={{ listStyle: 'none', padding: 0, margin: 0, display: 'flex', flexDirection: 'column', gap: 8 }}>
                      {plan.features.map((f) => (
                        <li key={f} style={{ display: 'flex', alignItems: 'flex-start', gap: 8, fontSize: 12.5, color: 'var(--text-secondary)', lineHeight: 1.4 }}>
                          <svg width="13" height="13" viewBox="0 0 24 24" fill="none" style={{ flexShrink: 0, marginTop: 2 }}><path d="M5 13l4 4L19 7" stroke="var(--success)" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round"/></svg>
                          {f}
                        </li>
                      ))}
                    </ul>
                    {isCurrent ? (
                      <button className="btn btn-ghost" style={{ width: '100%', marginTop: 'auto', opacity: 0.6, cursor: 'default' }} disabled>
                        Current plan
                      </button>
                    ) : plan.id === 'enterprise' ? (
                      <a className="btn btn-ghost" href={`mailto:${CONTACT_EMAIL}?subject=Capsule%20Enterprise`} style={{ width: '100%', marginTop: 'auto' }}>
                        Talk to sales
                      </a>
                    ) : (
                      <button className="btn btn-ghost" style={{ width: '100%', marginTop: 'auto', opacity: 0.6, cursor: 'not-allowed' }} disabled title="Self-service plan changes are coming soon">
                        Coming soon
                      </button>
                    )}
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      )}
    </DashboardShell>
  );
}
