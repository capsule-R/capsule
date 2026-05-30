'use client';

import { useState, useEffect } from 'react';
import { DashboardShell } from '@/components/DashboardShell';
import {
  getCurrentUser,
  updateProfile,
  changePassword,
  clearUserCache,
  type UserProfile,
} from '@/lib/capsule';

// ── Inline notice component ───────────────────────────────────

function Notice({ type, message }: { type: 'success' | 'error'; message: string }) {
  const isSuccess = type === 'success';
  return (
    <div style={{
      padding: '11px 16px',
      borderRadius: 7,
      fontSize: 13.5,
      lineHeight: 1.5,
      border: `1px solid ${isSuccess ? 'rgba(0,255,128,0.22)' : 'rgba(255,60,60,0.22)'}`,
      background: isSuccess ? 'rgba(0,255,128,0.07)' : 'rgba(255,60,60,0.08)',
      color: isSuccess ? 'var(--success)' : 'var(--error)',
      marginTop: 14,
    }}>
      {message}
    </div>
  );
}

// ── Section card ─────────────────────────────────────────────

function Section({ title, description, children }: {
  title: string;
  description?: string;
  children: React.ReactNode;
}) {
  return (
    <div className="card" style={{ marginBottom: 16 }}>
      <div style={{ marginBottom: 22 }}>
        <h3 style={{ fontFamily: 'var(--font-body)', fontWeight: 700, fontSize: 15, marginBottom: description ? 5 : 0 }}>
          {title}
        </h3>
        {description && (
          <p style={{ fontSize: 13, color: 'var(--text-tertiary)', lineHeight: 1.5, margin: 0 }}>
            {description}
          </p>
        )}
      </div>
      {children}
    </div>
  );
}

// ── Profile section ───────────────────────────────────────────

function ProfileSection({ user }: { user: UserProfile }) {
  const [name, setName] = useState(user.full_name ?? '');
  const [email, setEmail] = useState(user.email);
  const [loading, setLoading] = useState(false);
  const [notice, setNotice] = useState<{ type: 'success' | 'error'; message: string } | null>(null);

  const dirty = name !== (user.full_name ?? '') || email !== user.email;

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setNotice(null);
    const payload: { full_name?: string; email?: string } = {};
    if (name !== (user.full_name ?? '')) payload.full_name = name.trim() || undefined;
    if (email !== user.email) payload.email = email.trim();
    const { error } = await updateProfile(payload);
    setLoading(false);
    if (error) {
      setNotice({ type: 'error', message: error });
    } else {
      clearUserCache();
      setNotice({ type: 'success', message: 'Profile updated successfully.' });
    }
  };

  return (
    <Section
      title="Profile"
      description="Your display name and email address."
    >
      <form onSubmit={handleSave} noValidate>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16, marginBottom: 16 }}>
          <div className="field">
            <label htmlFor="gs-name">Display name</label>
            <input
              className="input"
              id="gs-name"
              type="text"
              placeholder="Your full name"
              value={name}
              onChange={(e) => setName(e.target.value)}
              autoComplete="name"
            />
          </div>
          <div className="field">
            <label htmlFor="gs-email">Email address</label>
            <input
              className="input"
              id="gs-email"
              type="email"
              placeholder="you@example.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              autoComplete="email"
            />
          </div>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <button
            type="submit"
            className="btn btn-primary btn-sm"
            disabled={loading || !dirty}
          >
            {loading ? 'Saving…' : 'Save changes'}
          </button>
          {dirty && !loading && (
            <span style={{ fontSize: 12, color: 'var(--text-tertiary)' }}>Unsaved changes</span>
          )}
        </div>
        {notice && <Notice type={notice.type} message={notice.message} />}
      </form>
    </Section>
  );
}

// ── Password section ──────────────────────────────────────────

function PasswordSection() {
  const [current, setCurrent] = useState('');
  const [next, setNext] = useState('');
  const [confirm, setConfirm] = useState('');
  const [showCurrent, setShowCurrent] = useState(false);
  const [showNext, setShowNext] = useState(false);
  const [loading, setLoading] = useState(false);
  const [notice, setNotice] = useState<{ type: 'success' | 'error'; message: string } | null>(null);

  const mismatch = confirm.length > 0 && next !== confirm;
  const tooShort = next.length > 0 && next.length < 8;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (next !== confirm) { setNotice({ type: 'error', message: 'New passwords do not match.' }); return; }
    if (next.length < 8) { setNotice({ type: 'error', message: 'New password must be at least 8 characters.' }); return; }
    setLoading(true);
    setNotice(null);
    const { error, message } = await changePassword(current, next);
    setLoading(false);
    if (error) {
      setNotice({ type: 'error', message: error });
    } else {
      setCurrent('');
      setNext('');
      setConfirm('');
      setNotice({ type: 'success', message: message ?? 'Password changed successfully.' });
    }
  };

  const EyeIcon = () => (
    <svg width="17" height="17" viewBox="0 0 24 24" fill="none">
      <path d="M2 12s3.5-7 10-7 10 7 10 7-3.5 7-10 7-10-7-10-7z" stroke="currentColor" strokeWidth="1.6"/>
      <circle cx="12" cy="12" r="3" stroke="currentColor" strokeWidth="1.6"/>
    </svg>
  );

  return (
    <Section
      title="Password"
      description="Change your login password. You'll need your current password to confirm."
    >
      <form onSubmit={handleSubmit} noValidate>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 14, maxWidth: 420 }}>
          {/* Current password */}
          <div className="field">
            <label htmlFor="gs-current-pass">Current password</label>
            <div className="input-group">
              <input
                className="input"
                id="gs-current-pass"
                type={showCurrent ? 'text' : 'password'}
                placeholder="••••••••••••"
                autoComplete="current-password"
                value={current}
                onChange={(e) => setCurrent(e.target.value)}
              />
              <button type="button" className="in-btn" onClick={() => setShowCurrent((v) => !v)} aria-label="Toggle visibility">
                <EyeIcon />
              </button>
            </div>
          </div>

          {/* New password */}
          <div className="field">
            <label htmlFor="gs-new-pass">New password</label>
            <div className="input-group">
              <input
                className="input"
                id="gs-new-pass"
                type={showNext ? 'text' : 'password'}
                placeholder="At least 8 characters"
                autoComplete="new-password"
                value={next}
                onChange={(e) => setNext(e.target.value)}
                style={tooShort ? { borderColor: 'var(--error)' } : undefined}
              />
              <button type="button" className="in-btn" onClick={() => setShowNext((v) => !v)} aria-label="Toggle visibility">
                <EyeIcon />
              </button>
            </div>
            {tooShort && (
              <span style={{ fontSize: 12, color: 'var(--error)', marginTop: 4, display: 'block' }}>
                Must be at least 8 characters
              </span>
            )}
          </div>

          {/* Confirm new password */}
          <div className="field">
            <label htmlFor="gs-confirm-pass">Confirm new password</label>
            <div className="input-group">
              <input
                className="input"
                id="gs-confirm-pass"
                type="password"
                placeholder="Repeat new password"
                autoComplete="new-password"
                value={confirm}
                onChange={(e) => setConfirm(e.target.value)}
                style={mismatch ? { borderColor: 'var(--error)' } : undefined}
              />
            </div>
            {mismatch && (
              <span style={{ fontSize: 12, color: 'var(--error)', marginTop: 4, display: 'block' }}>
                Passwords do not match
              </span>
            )}
          </div>
        </div>

        <button
          type="submit"
          className="btn btn-primary btn-sm"
          style={{ marginTop: 18 }}
          disabled={loading || !current || !next || !confirm}
        >
          {loading ? 'Updating…' : 'Update password'}
        </button>
        {notice && <Notice type={notice.type} message={notice.message} />}
      </form>
    </Section>
  );
}

// ── Workspace section ─────────────────────────────────────────

function WorkspaceSection({ user }: { user: UserProfile }) {
  const joinDate = new Date(user.created_at).toLocaleDateString('en-US', {
    month: 'long', day: 'numeric', year: 'numeric',
  });

  return (
    <Section
      title="Account details"
      description="Read-only account identifiers."
    >
      <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '10px 14px', borderRadius: 7, background: 'var(--bg-elevated)', border: '1px solid var(--border-subtle)' }}>
          <span style={{ fontSize: 13, color: 'var(--text-tertiary)' }}>User ID</span>
          <span style={{ fontFamily: 'var(--font-mono)', fontSize: 12.5, color: 'var(--text-secondary)', letterSpacing: '0.02em' }}>{user.id}</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '10px 14px', borderRadius: 7, background: 'var(--bg-elevated)', border: '1px solid var(--border-subtle)' }}>
          <span style={{ fontSize: 13, color: 'var(--text-tertiary)' }}>Member since</span>
          <span style={{ fontSize: 13.5, color: 'var(--text-secondary)' }}>{joinDate}</span>
        </div>
      </div>
    </Section>
  );
}

// ── Danger zone ───────────────────────────────────────────────

function DangerSection() {
  const [confirmText, setConfirmText] = useState('');
  const [showConfirm, setShowConfirm] = useState(false);

  return (
    <div className="card" style={{ marginBottom: 16, borderColor: 'rgba(255,60,60,0.25)' }}>
      <div style={{ marginBottom: 20 }}>
        <h3 style={{ fontFamily: 'var(--font-body)', fontWeight: 700, fontSize: 15, color: 'var(--error)', marginBottom: 5 }}>
          Danger zone
        </h3>
        <p style={{ fontSize: 13, color: 'var(--text-tertiary)', lineHeight: 1.5, margin: 0 }}>
          Permanently delete your account and all associated data. This action cannot be undone.
        </p>
      </div>

      {!showConfirm ? (
        <button
          className="btn btn-ghost btn-sm"
          style={{ color: 'var(--error)', borderColor: 'rgba(255,60,60,0.3)' }}
          onClick={() => setShowConfirm(true)}
        >
          Delete account…
        </button>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 12, maxWidth: 380 }}>
          <p style={{ fontSize: 13, color: 'var(--text-secondary)', margin: 0 }}>
            Type <strong style={{ color: 'var(--text-primary)', fontFamily: 'var(--font-mono)' }}>delete my account</strong> to confirm.
          </p>
          <input
            className="input"
            placeholder="delete my account"
            value={confirmText}
            onChange={(e) => setConfirmText(e.target.value)}
            style={{ borderColor: 'rgba(255,60,60,0.3)' }}
          />
          <div style={{ display: 'flex', gap: 10 }}>
            <button
              className="btn btn-ghost btn-sm"
              style={{
                color: 'var(--error)',
                borderColor: 'rgba(255,60,60,0.3)',
                opacity: confirmText !== 'delete my account' ? 0.4 : 1,
              }}
              disabled={confirmText !== 'delete my account'}
              onClick={() => {
                // Account deletion requires backend support — direct user to contact support for now
                alert("To delete your account, please email support@capsule.dev. We'll process your request within 48 hours.");
                setShowConfirm(false);
                setConfirmText('');
              }}
            >
              Permanently delete
            </button>
            <button
              className="btn btn-ghost btn-sm"
              onClick={() => { setShowConfirm(false); setConfirmText(''); }}
            >
              Cancel
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

// ── Page ──────────────────────────────────────────────────────

export default function GeneralSettingsPage() {
  const [user, setUser] = useState<UserProfile | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getCurrentUser().then((u) => {
      setUser(u);
      setLoading(false);
    });
  }, []);

  return (
    <DashboardShell active="general" title="General" crumb="workspace / settings / general">
      <div className="page-head">
        <div>
          <h2>General settings</h2>
          <p>Manage your profile, password, and account.</p>
        </div>
      </div>

      {loading ? (
        <div style={{ padding: '48px 0', textAlign: 'center', color: 'var(--text-tertiary)', fontSize: 14 }}>
          Loading…
        </div>
      ) : !user ? (
        <div style={{ padding: '48px 0', textAlign: 'center', color: 'var(--error)', fontSize: 14 }}>
          Failed to load profile. Please refresh the page.
        </div>
      ) : (
        <>
          <ProfileSection user={user} />
          <PasswordSection />
          <WorkspaceSection user={user} />
          <DangerSection />
        </>
      )}
    </DashboardShell>
  );
}
