'use client';

import { useState } from 'react';
import Link from 'next/link';
import { LogoMark } from '@/components/Logo';

export default function LoginPage() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPass, setShowPass] = useState(false);
  const [keepLoggedIn, setKeepLoggedIn] = useState(true);
  const [loading, setLoading] = useState(false);
  const [emailErr, setEmailErr] = useState(false);
  const [passErr, setPassErr] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const emailOk = /^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(email.trim());
    const passOk = password.length > 0;
    setEmailErr(!emailOk);
    setPassErr(!passOk);
    if (!emailOk || !passOk) return;
    
    setLoading(true);
    
    const { createClient } = await import('@/lib/supabase/client');
    const supabase = createClient();
    
    const { error } = await supabase.auth.signInWithPassword({
      email,
      password,
    });

    if (error) {
      setLoading(false);
      setPassErr(true);
      // You might want to display the actual error message here
      console.error(error);
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
                <a href="#">Forgot password?</a>
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

            <label className="checkbox">
              <input
                type="checkbox"
                checked={keepLoggedIn}
                onChange={(e) => setKeepLoggedIn(e.target.checked)}
              />
              <span className="box">
                <svg width="11" height="11" viewBox="0 0 24 24" fill="none">
                  <path d="M5 13l4 4 10-10" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round"/>
                </svg>
              </span>
              <span>Keep me logged in for 30 days</span>
            </label>

            <button type="submit" className="btn btn-primary btn-lg" style={{ marginTop: 6 }} disabled={loading}>
              {loading ? 'Logging in…' : 'Log in'}
            </button>
          </form>

          <div className="auth-sep">OR</div>

          <div className="oauth">
            <button className="btn btn-ghost" type="button">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
                <path d="M12 2C6.5 2 2 6.6 2 12.2c0 4.5 2.9 8.3 6.8 9.6.5.1.7-.2.7-.5v-1.7c-2.8.6-3.4-1.4-3.4-1.4-.5-1.2-1.1-1.5-1.1-1.5-.9-.6.1-.6.1-.6 1 .1 1.5 1 1.5 1 .9 1.6 2.4 1.1 3 .9.1-.7.4-1.1.6-1.4-2.2-.3-4.6-1.1-4.6-5 0-1.1.4-2 1-2.7-.1-.3-.4-1.3.1-2.7 0 0 .8-.3 2.7 1a9.4 9.4 0 0 1 5 0c1.9-1.3 2.7-1 2.7-1 .5 1.4.2 2.4.1 2.7.6.7 1 1.6 1 2.7 0 3.9-2.4 4.7-4.6 5 .4.3.7.9.7 1.9v2.8c0 .3.2.6.7.5A10 10 0 0 0 22 12.2C22 6.6 17.5 2 12 2z"/>
              </svg>
              GitHub
            </button>
            <button className="btn btn-ghost" type="button">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
                <path d="M21.6 12.2c0-.7-.1-1.3-.2-2H12v3.8h5.4a4.6 4.6 0 0 1-2 3v2.5h3.2c1.9-1.7 3-4.3 3-7.3z" fill="#A0A0A0"/>
                <path d="M12 22c2.7 0 5-.9 6.6-2.4l-3.2-2.5c-.9.6-2 1-3.4 1-2.6 0-4.8-1.7-5.6-4.1H3.1v2.6A10 10 0 0 0 12 22z" fill="#A0A0A0"/>
                <path d="M6.4 14c-.2-.6-.3-1.3-.3-2s.1-1.4.3-2V7.4H3.1a10 10 0 0 0 0 9.2L6.4 14z" fill="#606060"/>
                <path d="M12 6c1.5 0 2.8.5 3.8 1.5l2.8-2.8A10 10 0 0 0 3.1 7.4L6.4 10c.8-2.4 3-4 5.6-4z" fill="#A0A0A0"/>
              </svg>
              Google SSO
            </button>
          </div>

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
