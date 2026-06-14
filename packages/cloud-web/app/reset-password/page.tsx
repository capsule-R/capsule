'use client';

import { useState, useEffect, Suspense } from 'react';
import Link from 'next/link';
import { useSearchParams } from 'next/navigation';
import { LogoMark } from '@/components/Logo';
import { resetPassword } from '@/lib/capsule';

const STRENGTH_COLORS = ['var(--error)', 'var(--warn)', 'var(--warn)', 'var(--success)'];
const STRENGTH_LABELS = ['Weak password', 'Fair — add more variety', 'Good password', 'Strong password'];

function passwordScore(v: string): number {
  if (!v) return 0;
  let s = 0;
  if (v.length >= 8) s++;
  if (/[A-Z]/.test(v) && /[a-z]/.test(v)) s++;
  if (/\d/.test(v)) s++;
  if (/[^A-Za-z0-9]/.test(v)) s++;
  return s;
}

function ResetForm() {
  const searchParams = useSearchParams();
  const token = searchParams.get('token') ?? '';

  const [password, setPassword] = useState('');
  const [showPass, setShowPass] = useState(false);
  const [passErr, setPassErr] = useState(false);
  const [loading, setLoading] = useState(false);
  const [done, setDone] = useState(false);
  const [error, setError] = useState('');

  const score = passwordScore(password);

  useEffect(() => {
    if (!token) setError('Missing or invalid reset link. Please request a new one.');
  }, [token]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (password.length < 8) { setPassErr(true); return; }
    setLoading(true);
    const result = await resetPassword(token, password);
    setLoading(false);
    if (result.error) { setError(result.error); return; }
    setDone(true);
  };

  return (
    <div className="auth-center">
      <h1>Set new password.</h1>
      <p className="sub">Choose a strong password for your Capsule account.</p>

      {done ? (
        <div style={{ marginTop: 24 }}>
          <div style={{ background: 'rgba(0, 255, 128, 0.08)', border: '1px solid rgba(0, 255, 128, 0.2)', padding: '20px 24px', borderRadius: 8 }}>
            <h3 style={{ color: 'var(--success)', marginBottom: 8, fontSize: 15 }}>Password updated</h3>
            <p style={{ color: 'var(--text-secondary)', fontSize: 13.5, lineHeight: 1.6 }}>
              Your password has been changed successfully. You can now sign in with your new password.
            </p>
          </div>
          <Link href="/login" className="btn btn-primary btn-lg" style={{ marginTop: 16, display: 'block', textAlign: 'center' }}>
            Sign in →
          </Link>
        </div>
      ) : (
        <form className="auth-fields" onSubmit={handleSubmit} noValidate style={{ marginTop: 24 }}>
          {error && (
            <div style={{ color: 'var(--error)', fontSize: 14, marginBottom: 16, padding: '12px 16px', background: 'rgba(255, 60, 60, 0.1)', borderRadius: 6, border: '1px solid rgba(255, 60, 60, 0.2)' }}>
              {error}
              {' '}
              {!token && <Link href="/forgot-password" style={{ color: 'var(--text-secondary)' }}>Request a new link.</Link>}
            </div>
          )}

          <div className={`field${passErr ? ' show-err' : ''}`}>
            <label htmlFor="pass">New password</label>
            <div className="input-group">
              <input
                className="input"
                type={showPass ? 'text' : 'password'}
                id="pass"
                placeholder="At least 8 characters"
                autoComplete="new-password"
                value={password}
                autoFocus
                onChange={(e) => { setPassword(e.target.value); setPassErr(false); }}
              />
              <button
                type="button"
                className="in-btn"
                aria-label="Show password"
                onClick={() => setShowPass((v) => !v)}
              >
                <svg width="17" height="17" viewBox="0 0 24 24" fill="none">
                  <path d="M2 12s3.5-7 10-7 10 7 10 7-3.5 7-10 7-10-7-10-7z" stroke="currentColor" strokeWidth="1.6"/>
                  <circle cx="12" cy="12" r="3" stroke="currentColor" strokeWidth="1.6"/>
                </svg>
              </button>
            </div>
            <div className="strength">
              <div className="strength-bars">
                {[0, 1, 2, 3].map((i) => (
                  <span key={i} style={{ background: i < score ? STRENGTH_COLORS[score - 1] : undefined }} />
                ))}
              </div>
              <div className="strength-label">
                {password.length === 0
                  ? 'Use 8+ characters with a mix of letters, numbers & symbols.'
                  : STRENGTH_LABELS[Math.max(0, score - 1)]}
              </div>
            </div>
            <span className="field-err">Password must be at least 8 characters.</span>
          </div>

          <button
            type="submit"
            className="btn btn-primary btn-lg"
            style={{ marginTop: 6 }}
            disabled={loading || !token}
          >
            {loading ? 'Updating…' : 'Update password'}
          </button>
        </form>
      )}
    </div>
  );
}

export default function ResetPasswordPage() {
  return (
    <div className="auth">
      <div className="auth-form-side">
        <div className="auth-top">
          <Link className="brand" href="/">
            <LogoMark />
            <span className="wordmark">Capsule</span>
          </Link>
          <Link className="back" href="/login">Back to login →</Link>
        </div>

        <Suspense fallback={<div className="auth-center"><p className="sub">Loading…</p></div>}>
          <ResetForm />
        </Suspense>

        <div className="auth-legal">
          Protected by SOC 2 Type II controls · SSO available on Enterprise.
        </div>
      </div>

      <div className="auth-aside">
        <div className="auth-aside-grid" />
        <div className="auth-aside-glow" />
        <div className="aside-content">
          <span className="eyebrow">Almost there</span>
          <h2 style={{ fontFamily: 'var(--font-display)', fontSize: 28, marginTop: 18, lineHeight: 1.2 }}>
            One last step.
          </h2>
          <p style={{ color: 'var(--text-secondary)', fontSize: 14.5, marginTop: 12, maxWidth: 360, lineHeight: 1.6 }}>
            Set your new password and you&apos;ll be back to replaying and debugging your agent sessions.
          </p>
        </div>
      </div>
    </div>
  );
}
