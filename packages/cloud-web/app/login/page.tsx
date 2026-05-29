'use client';

import { useState } from 'react';
import Link from 'next/link';
import { LogoMark } from '@/components/Logo';
import { login } from '@/lib/capsule';

export default function LoginPage() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPass, setShowPass] = useState(false);
  const [loading, setLoading] = useState(false);
  const [emailErr, setEmailErr] = useState(false);
  const [passErr, setPassErr] = useState(false);
  const [authErr, setAuthErr] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const emailOk = /^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(email.trim());
    const passOk = password.length > 0;
    setEmailErr(!emailOk);
    setPassErr(!passOk);
    setAuthErr('');
    if (!emailOk || !passOk) return;

    setLoading(true);
    const { error } = await login(email.trim(), password);
    if (error) {
      setLoading(false);
      setAuthErr(error);
      return;
    }
    window.location.href = '/dashboard';
  };

  return (
    <div className="auth">
      {/* LEFT: form */}
      <div className="auth-form-side">
        <div className="auth-top">
          <a className="brand" href="/">
            <LogoMark />
            <span className="wordmark">Capsule</span>
          </a>
          <Link className="back" href="/signup">Create account →</Link>
        </div>

        <div className="auth-center">
          <h1>Welcome back.</h1>
          <p className="sub">Log in to replay, branch, and debug your agent sessions.</p>

          <form className="auth-fields" onSubmit={handleSubmit} noValidate>
            {authErr && (
              <div style={{ color: 'var(--error)', fontSize: 14, marginBottom: 16, padding: '12px 16px', background: 'rgba(255, 60, 60, 0.1)', borderRadius: 6, border: '1px solid rgba(255, 60, 60, 0.2)' }}>
                {authErr}
              </div>
            )}
            <div className={`field${emailErr ? ' show-err' : ''}`}>
              <label htmlFor="email">Work email</label>
              <input
                className="input"
                type="email"
                id="email"
                placeholder="dana@helix.ai"
                autoComplete="email"
                value={email}
                onChange={(e) => { setEmail(e.target.value); setEmailErr(false); }}
              />
              <span className="field-err">Enter a valid email address.</span>
            </div>

            <div className={`field${passErr ? ' show-err' : ''}`}>
              <div className="auth-row">
                <label htmlFor="pass">Password</label>
                <a href="/forgot-password" style={{ fontSize: 12.5, color: 'var(--text-tertiary)' }}>Forgot password?</a>
              </div>
              <div className="input-group">
                <input
                  className="input"
                  type={showPass ? 'text' : 'password'}
                  id="pass"
                  placeholder="••••••••••••"
                  autoComplete="current-password"
                  value={password}
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
              <span className="field-err">Password is required.</span>
            </div>

            <button type="submit" className="btn btn-primary btn-lg" style={{ marginTop: 6 }} disabled={loading}>
              {loading ? 'Logging in…' : 'Log in'}
            </button>
          </form>

          <p className="auth-foot">
            Don&apos;t have an account? <Link href="/signup">Sign up free</Link>
          </p>
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
          <blockquote className="aside-quote">
            &ldquo;We cut agent incident triage from{' '}
            <span className="g">half a day to twenty minutes.</span>{' '}
            A teammate just sends the{' '}
            <span className="mono" style={{ color: 'var(--text-primary)' }}>.capsule</span>{' '}
            and I replay the exact failure.&rdquo;
          </blockquote>
          <div className="aside-by">
            <div className="avatar">MR</div>
            <div>
              <div className="n">Marisol Reyes</div>
              <div className="r">Staff Engineer, Ledgerline</div>
            </div>
          </div>
          <div className="aside-card">
            <div className="ach">
              capsule replay sess_8f2a91c4
              <span className="live"><i />live</span>
            </div>
            <div className="aside-steps">
              <div className="aside-step">
                <span className="sd" style={{ background: 'var(--text-primary)' }} />
                <span className="sl">LLM · plan</span>
                <span className="sm">820ms · 1,284 tok</span>
              </div>
              <div className="aside-step">
                <span className="sd" style={{ background: 'var(--text-secondary)' }} />
                <span className="sl">tool · web.search</span>
                <span className="sm">340ms</span>
              </div>
              <div className="aside-step">
                <span className="sd" style={{ background: 'var(--error)' }} />
                <span className="sl" style={{ color: 'var(--error)' }}>tool · db.query</span>
                <span className="sm">err</span>
              </div>
              <div className="aside-step">
                <span className="sd" style={{ background: 'var(--replay)' }} />
                <span className="sl" style={{ color: 'var(--replay)' }}>branch · fix-schema</span>
                <span className="sm">forked</span>
              </div>
              <div className="aside-step">
                <span className="sd" style={{ background: 'var(--success)' }} />
                <span className="sl" style={{ color: 'var(--success)' }}>session · recovered</span>
                <span className="sm">hash ✓</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
