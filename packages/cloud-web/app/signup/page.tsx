'use client';

import { useState } from 'react';
import Link from 'next/link';
import { LogoMark } from '@/components/Logo';
import { signup } from '@/lib/capsule';

const STRENGTH_COLORS = ['var(--error)', 'var(--warn)', 'var(--warn)', 'var(--success)'];
const STRENGTH_LABELS = ['Weak password', 'Fair — add more variety', 'Good password', 'Strong password'];

function passwordScore(v: string): number {
  if (!v) return 0;
  let score = 0;
  if (v.length >= 8) score++;
  if (/[A-Z]/.test(v) && /[a-z]/.test(v)) score++;
  if (/\d/.test(v)) score++;
  if (/[^A-Za-z0-9]/.test(v)) score++;
  return score;
}

export default function SignupPage() {
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPass, setShowPass] = useState(false);
  const [termsChecked, setTermsChecked] = useState(false);
  const [loading, setLoading] = useState(false);

  const [nameErr, setNameErr] = useState(false);
  const [emailErr, setEmailErr] = useState(false);
  const [passErr, setPassErr] = useState(false);
  const [termsErr, setTermsErr] = useState(false);
  const [authErr, setAuthErr] = useState('');

  const score = passwordScore(password);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const nOk = name.trim().length > 1;
    const eOk = /^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(email.trim());
    const pOk = password.length >= 8;
    const tOk = termsChecked;
    setNameErr(!nOk);
    setEmailErr(!eOk);
    setPassErr(!pOk);
    setTermsErr(!tOk);
    setAuthErr('');
    if (!nOk || !eOk || !pOk || !tOk) return;

    setLoading(true);
    const { error } = await signup(email.trim(), password, name.trim());
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
          <Link className="brand" href="/">
            <LogoMark />
            <span className="wordmark">Capsule</span>
          </Link>
          <Link className="back" href="/login">Log in →</Link>
        </div>

        <div className="auth-center">
          <h1>Start capturing.</h1>
          <p className="sub">Create a free account — 1,000 captured sessions / month, no card required.</p>

          <form className="auth-fields" onSubmit={handleSubmit} noValidate>
            {authErr && (
              <div style={{ color: 'var(--error)', fontSize: 14, marginBottom: 16, padding: '12px 16px', background: 'rgba(255, 60, 60, 0.1)', borderRadius: 6, border: '1px solid rgba(255, 60, 60, 0.2)' }}>
                {authErr}
              </div>
            )}
            <div className={`field${nameErr ? ' show-err' : ''}`}>
              <label htmlFor="name">Full name</label>
              <input
                className="input"
                type="text"
                id="name"
                placeholder="Dana Okonkwo"
                autoComplete="name"
                value={name}
                onChange={(e) => { setName(e.target.value); setNameErr(false); }}
              />
              <span className="field-err">Please enter your name.</span>
            </div>

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
              <span className="field-err">Enter a valid work email address.</span>
            </div>

            <div className={`field${passErr ? ' show-err' : ''}`}>
              <label htmlFor="pass">Password</label>
              <div className="input-group">
                <input
                  className="input"
                  type={showPass ? 'text' : 'password'}
                  id="pass"
                  placeholder="At least 8 characters"
                  autoComplete="new-password"
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
              <div className="strength">
                <div className="strength-bars">
                  {[0, 1, 2, 3].map((i) => (
                    <span
                      key={i}
                      style={{ background: i < score ? STRENGTH_COLORS[score - 1] : undefined }}
                    />
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

            <label className="checkbox" style={{ color: termsErr ? 'var(--error)' : undefined }}>
              <input
                type="checkbox"
                checked={termsChecked}
                onChange={(e) => { setTermsChecked(e.target.checked); setTermsErr(false); }}
              />
              <span className="box">
                <svg width="11" height="11" viewBox="0 0 24 24" fill="none">
                  <path d="M5 13l4 4 10-10" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round"/>
                </svg>
              </span>
              <span>
                I agree to the{' '}
                <a href="/terms" target="_blank" rel="noopener noreferrer" style={{ color: 'var(--text-primary)' }} onClick={(e) => e.stopPropagation()}>Terms</a>
                {' '}and{' '}
                <a href="/privacy" target="_blank" rel="noopener noreferrer" style={{ color: 'var(--text-primary)' }} onClick={(e) => e.stopPropagation()}>Privacy Policy</a>.
              </span>
            </label>

            <button type="submit" className="btn btn-primary btn-lg" style={{ marginTop: 6 }} disabled={loading}>
              {loading ? 'Creating account…' : 'Create account'}
            </button>
          </form>

          <p className="auth-foot">
            Already have an account? <Link href="/login">Log in</Link>
          </p>
        </div>

        <div className="auth-legal">
          By creating an account you agree to receive product updates. Unsubscribe anytime.
        </div>
      </div>

      {/* RIGHT: decorative aside */}
      <div className="auth-aside">
        <div className="auth-aside-grid" />
        <div className="auth-aside-glow" />
        <div className="aside-content">
          <span className="eyebrow">From zero to replay</span>
          <h2 style={{ fontFamily: 'var(--font-display)', fontSize: 30, marginTop: 18, lineHeight: 1.15 }}>
            Wrap your agent in three lines.
          </h2>
          <p style={{ color: 'var(--text-secondary)', fontSize: 14.5, marginTop: 12, maxWidth: 380 }}>
            Install the SDK, ship to production, and every run is captured as a replayable{' '}
            <span className="mono" style={{ color: 'var(--text-primary)' }}>.capsule</span> automatically.
          </p>
          <div className="install-strip">
            <span className="p">$</span> <span className="c">pip install capsule-trace</span>
          </div>
          <ul className="aside-bullets">
            <li>
              <span className="ck">
                <svg width="19" height="19" viewBox="0 0 24 24" fill="none">
                  <path d="M5 13l4 4 10-10" stroke="currentColor" strokeWidth="2.1" strokeLinecap="round" strokeLinejoin="round"/>
                </svg>
              </span>
              Deterministic replay — reproduce any failure exactly
            </li>
            <li>
              <span className="ck">
                <svg width="19" height="19" viewBox="0 0 24 24" fill="none">
                  <path d="M5 13l4 4 10-10" stroke="currentColor" strokeWidth="2.1" strokeLinecap="round" strokeLinejoin="round"/>
                </svg>
              </span>
              Branch at any step to test a fix before you ship
            </li>
            <li>
              <span className="ck">
                <svg width="19" height="19" viewBox="0 0 24 24" fill="none">
                  <path d="M5 13l4 4 10-10" stroke="currentColor" strokeWidth="2.1" strokeLinecap="round" strokeLinejoin="round"/>
                </svg>
              </span>
              EU AI Act audit trails, signed and exportable
            </li>
          </ul>
        </div>
      </div>
    </div>
  );
}
