'use client';

// TODO: billing disabled for launch
//
// The full Billing & Plan UI (plan catalogue, usage/storage bar, payment
// method, plan-comparison modal) is intentionally disabled for launch and
// replaced with the "coming soon" placeholder below. The original
// implementation is preserved in git history — restore it from there to
// re-enable billing.

import { DashboardShell } from '@/components/DashboardShell';

export default function BillingPage() {
  return (
    <DashboardShell active="billing" title="Billing & Plan" crumb="workspace / settings / billing">
      <div className="page-head">
        <div>
          <h2>Billing &amp; Plan</h2>
          <p>Your current plan, usage, and payment details.</p>
        </div>
      </div>

      <div className="card" style={{ textAlign: 'center', padding: '48px 24px' }}>
        <div style={{ fontWeight: 700, fontSize: 16, marginBottom: 6 }}>Coming soon</div>
        <p style={{ fontSize: 13.5, color: 'var(--text-tertiary)', maxWidth: 420, margin: '0 auto', lineHeight: 1.5 }}>
          Capsule is free during early access. Plans, usage, and billing will
          appear here when paid plans launch.
        </p>
      </div>
    </DashboardShell>
  );
}
