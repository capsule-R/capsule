'use client';

import { useState } from 'react';
import Link from 'next/link';
import { LogoMark } from '@/components/Logo';
import { forgotPassword } from '@/lib/capsule';

export default function ForgotPasswordPage() {
  const [email, setEmail] = useState('');
  const [emailErr, setEmailErr] = useState(false);
  const [loading, setLoading] = useState(false);
  const [submitted, setSubmitted] = useState(false);
  const [devToken, setDevToken] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const ok = /^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(email.trim());
    setEmailErr(!ok);
    if (!ok) return;

    setLoading(true);
    const result = await forgotPassword(email.trim());
    setLoading(false);
    setSubmitted(true);
    // Dev environments return the token directly so you can test without email
    if (result.reset_token) setDevToken(result.reset_token);
  };

  return (
    <div className="auth">
      <div className="auth-form-side">
        <div className="auth-top">
          <a className="brand" href="/">
            <LogoMark />
            <span className="wordmark">Capsule</span>
          </a>
          <Link className="back" href="/login">Back to login →</Link>
        </div>

        <div className="auth-center">
          <h1>Reset password.</h1>
          <p className="sub">
            Enter your email and we&apos;ll send you a link to set a new password.
          </p>

          {submitted ? (
            <div style={{ marginTop: 24 }}>
              <div style={{ background: 'rgba(0, 255, 128, 0.08)', border: '1px solid rgba(0, 255, 128, 0.2)', padding: '20px 24px', borderRadius: 8 }}>
                <h3 style={{ color: 'var(--success)', marginBottom: 8, fontSize: 15 }}>Check your email</h3>
                <p style={{ color: 'var(--text-secondary)', fontSize: 13.5, lineHeight: 1.6 }}>
                  If an account exists for <strong style={{ color: 'var(--text-primary)' }}>{email}</strong>, you&apos;ll receive a reset link shortly.
                </p>
              </div>

              {/* Dev-mode: show the token so the flow is testable without email */}
              {devToken && (
                <div style={{ marginTop: 16, padding: '16px', background: 'color-mix(in oklab, var(--warn) 8%, transparent)', border: '1px solid color-mix(in oklab, var(--warn) 25%, transparent)', borderRadius: 8 }}>
                  <div style={{ fontSize: 11, fontFamily: 'var(--font-mono)', color: 'var(--warn)', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 8 }}>
                    Dev mode — reset token (not shown in production)
                  </div>
                  <a
                    href={`/reset-password?token=${encodeURIComponent(devToken)}`}
                    style={{ fontFamily: 'var(--font-mono)', fontSize: 12.5, color: 'var(--text-secondary)', wordBreak: 'break-all', textDecoration: 'underline' }}
                  >
                    /reset-password?token={devToken.slice(0, 40)}…
                  </a>
                  <br />
                  <Link
                    href={`/reset-password?token=${encodeURIComponent(devToken)}`}
                    className="btn btn-primary btn-sm"
                    style={{ marginTop: 12, display: 'inline-block' }}
                  >
                    Open reset link →
                  </Link>
                </div>
              )}

              <Link href="/login" className="btn btn-ghost btn-lg" style={{ marginTop: 16, display: 'block', textAlign: 'center' }}>
                Back to login
              </Link>
            </div>
          ) : (
            <form className="auth-fields" onSubmit={handleSubmit} noValidate style={{ marginTop: 24 }}>
              <div className={`field${emailErr ? ' show-err' : ''}`}>
                <label htmlFor="email">Email address</label>
                <input
                  className="input"
                  type="email"
                  id="email"
                  placeholder="dana@helix.ai"
                  autoComplete="email"
                  value={email}
                  onChange={(e) => { setEmail(e.target.value); setEmailErr(false); }}
                  autoFocus
                />
                <span className="field-err">Enter a valid email address.</span>
              </div>

              <button
                type="submit"
                className="btn btn-primary btn-lg"
                style={{ marginTop: 6 }}
                disabled={loading}
              >
                {loading ? 'Sending…' : 'Send reset link'}
              </button>
            </form>
          )}
        </div>

        <div className="auth-legal">
          Protected by SOC 2 Type II controls · SSO available on Enterprise.
        </div>
      </div>

      {/* RIGHT: decorative aside */}
      <div className="auth-aside">
        <div className="auth-aside-grid" />
        <div className="auth-aside-glow" />
        <div className="aside-content">
          <span className="eyebrow">Account security</span>
          <h2 style={{ fontFamily: 'var(--font-display)', fontSize: 28, marginTop: 18, lineHeight: 1.2 }}>
            Your sessions are safe.
          </h2>
          <p style={{ color: 'var(--text-secondary)', fontSize: 14.5, marginTop: 12, maxWidth: 360, lineHeight: 1.6 }}>
            Capsule uses Argon2id password hashing and signed JWT tokens.
            Reset links expire in 1 hour and can only be used once.
          </p>
          <ul className="aside-bullets" style={{ marginTop: 28 }}>
            <li>
              <span className="ck">
                <svg width="19" height="19" viewBox="0 0 24 24" fill="none">
                  <path d="M5 13l4 4 10-10" stroke="currentColor" strokeWidth="2.1" strokeLinecap="round" strokeLinejoin="round"/>
                </svg>
              </span>
              Argon2id password hashing
            </li>
            <li>
              <span className="ck">
                <svg width="19" height="19" viewBox="0 0 24 24" fill="none">
                  <path d="M5 13l4 4 10-10" stroke="currentColor" strokeWidth="2.1" strokeLinecap="round" strokeLinejoin="round"/>
                </svg>
              </span>
              1-hour expiring reset tokens
            </li>
            <li>
              <span className="ck">
                <svg width="19" height="19" viewBox="0 0 24 24" fill="none">
                  <path d="M5 13l4 4 10-10" stroke="currentColor" strokeWidth="2.1" strokeLinecap="round" strokeLinejoin="round"/>
                </svg>
              </span>
              SOC 2 Type II access controls
            </li>
          </ul>
        </div>
      </div>
    </div>
  );
}
