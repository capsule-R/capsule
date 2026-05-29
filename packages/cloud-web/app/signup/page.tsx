'use client';

import { useState, useRef } from 'react';
import Link from 'next/link';
import { LogoMark } from '@/components/Logo';

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
    if (!nOk || !eOk || !pOk || !tOk) return;
    
    setLoading(true);
    
    const { createClient } = await import('@/lib/supabase/client');
    const supabase = createClient();
    
    const { error } = await supabase.auth.signUp({
      email,
      password,
      options: {
        data: {
          full_name: name,
        },
      },
    });

    if (error) {
      setLoading(false);
      setEmailErr(true);
      // Displaying or handling the actual error is good practice
      console.error(error);
      return;
    }

    // Automatically redirect to dashboard (Supabase will log them in if email confirmation is off)
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
          <Link className="back" href="/login">Log in →</Link>
        </div>

        <div className="auth-center">
          <h1>Start capturing.</h1>
          <p className="sub">Create a free account — 1,000 captured sessions / month, no card required.</p>

          <form className="auth-fields" onSubmit={handleSubmit} noValidate>
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
                <a href="#" style={{ color: 'var(--text-primary)' }}>Terms</a>
                {' '}and{' '}
                <a href="#" style={{ color: 'var(--text-primary)' }}>Privacy Policy</a>.
              </span>
            </label>

            <button type="submit" className="btn btn-primary btn-lg" style={{ marginTop: 6 }} disabled={loading}>
              {loading ? 'Creating account…' : 'Create account'}
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
            <span className="p">$</span> <span className="c">pip install capsule</span>
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
