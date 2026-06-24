'use client';

import { useState, useEffect, useRef } from 'react';
import Link from 'next/link';
import { LogoMark } from '@/components/Logo';

/* ─── Scroll-reveal hook ──────────────────────────────────── */
function useReveal() {
  useEffect(() => {
    const els = Array.from(document.querySelectorAll('.reveal'));
    let fired = false;
    const io = new IntersectionObserver(
      (entries) => {
        entries.forEach((e) => {
          if (e.isIntersecting) {
            fired = true;
            e.target.classList.add('in');
            io.unobserve(e.target);
          }
        });
      },
      { threshold: 0.12, rootMargin: '0px 0px -40px 0px' }
    );
    els.forEach((el) => io.observe(el));
    const t = setTimeout(() => {
      if (!fired) els.forEach((el) => el.classList.add('in'));
    }, 900);
    return () => { io.disconnect(); clearTimeout(t); };
  }, []);
}

/* ─── Nav ─────────────────────────────────────────────────── */
const NAV_LINKS = [
  { label: 'How it works', href: '#how' },
  { label: 'The .capsule file', href: '#capsule' },
  { label: 'Features', href: '#features' },
  { label: 'Compliance', href: '#compliance' },
  // billing disabled for launch
  // { label: 'Pricing', href: '#pricing' },
];

function Nav() {
  const [scrolled, setScrolled] = useState(false);
  const [menuOpen, setMenuOpen] = useState(false);
  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 12);
    onScroll();
    window.addEventListener('scroll', onScroll, { passive: true });
    return () => window.removeEventListener('scroll', onScroll);
  }, []);
  return (
    <>
      <nav style={{
        position: 'fixed', top: 0, left: 0, right: 0, zIndex: 100,
        background: scrolled ? 'color-mix(in oklab, var(--bg-base) 88%, transparent)' : 'transparent',
        backdropFilter: scrolled ? 'blur(12px)' : 'none',
        borderBottom: `1px solid ${scrolled ? 'var(--border-subtle)' : 'transparent'}`,
        transition: 'background .25s, border-color .25s',
      }}>
        <div className="lp-wrap" style={{ display: 'flex', alignItems: 'center', height: 64 }}>
          <Link className="brand" href="/" style={{ textDecoration: 'none' }}>
            <LogoMark size={38} />
            <span className="wordmark" style={{ fontSize: 17 }}>Capsule</span>
          </Link>
          <div style={{ flex: 1 }} />
          <div className="lp-nav-links" style={{ display: 'flex', alignItems: 'center', gap: 26, marginRight: 28 }}>
            {NAV_LINKS.map(({ label, href }) => (
              <a key={label} href={href} style={{ fontSize: 13.5, color: 'var(--text-secondary)', transition: 'color .12s' }}
                onMouseEnter={(e) => (e.currentTarget.style.color = 'var(--text-primary)')}
                onMouseLeave={(e) => (e.currentTarget.style.color = 'var(--text-secondary)')}>
                {label}
              </a>
            ))}
          </div>
          <div style={{ display: 'flex', gap: 10, alignItems: 'center' }}>
            <Link href="/login" className="btn btn-ghost btn-sm lp-nav-login">Log in</Link>
            <Link href="/signup" className="btn btn-primary btn-sm">Start free</Link>
            <button
              className="lp-hamburger"
              aria-label={menuOpen ? 'Close menu' : 'Open menu'}
              onClick={() => setMenuOpen((v) => !v)}
            >
              {menuOpen ? (
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none">
                  <path d="M6 6l12 12M6 18L18 6" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" />
                </svg>
              ) : (
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none">
                  <path d="M3 7h18M3 12h18M3 17h18" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" />
                </svg>
              )}
            </button>
          </div>
        </div>
      </nav>
      {/* Mobile dropdown menu */}
      <div className={`lp-mobile-menu${menuOpen ? ' open' : ''}`}>
        {NAV_LINKS.map(({ label, href }) => (
          <a key={label} href={href} onClick={() => setMenuOpen(false)}>{label}</a>
        ))}
        <div className="lp-mobile-menu-ctas">
          <Link href="/login" className="btn btn-ghost btn-sm" onClick={() => setMenuOpen(false)}>Log in</Link>
          <Link href="/signup" className="btn btn-primary btn-sm" onClick={() => setMenuOpen(false)}>Start free</Link>
        </div>
      </div>
    </>
  );
}

/* ─── Interactive replay inspector (monochrome) ───────────── */
const STEPS = [
  { badge: 'LLM · plan',          color: 'var(--text-primary)', tok: '1,284',       cost: '$0.0042', ms: '820ms', text: 'Decompose user request into ordered subtasks.' },
  { badge: 'tool · web.search',   color: 'var(--text-secondary)', tok: '—',         cost: '$0.0010', ms: '340ms', text: 'query: "Q3 refund policy EU"  →  4 results' },
  { badge: 'memory · write',      color: 'var(--text-secondary)', tok: '512',       cost: '—',       ms: '40ms',  text: 'store: policy_chunk_47 → working memory' },
  { badge: 'LLM · synthesize',    color: 'var(--text-primary)', tok: '2,011',       cost: '$0.0068', ms: '1.2s',  text: 'Draft response citing retrieved policy.' },
  { badge: 'tool · db.query',     color: 'var(--error)',        tok: '—',           cost: '—',       ms: '120ms', text: 'ERR: column "refund_window" not found', err: true },
  { badge: 'branch · fix-schema', color: 'var(--replay)',       tok: '—',           cost: '—',       ms: '—',     text: 'Forked at step 5 — patched query.sql' },
  { badge: 'LLM · recover',       color: 'var(--text-primary)', tok: '1,640',       cost: '$0.0051', ms: '910ms', text: 'Re-synthesize answer with corrected data.' },
  { badge: 'session · complete',  color: 'var(--success)',      tok: '6,451 total', cost: '$0.0171', ms: '3.4s',  text: 'Replay verified · hash match ✓' },
];

function Inspector() {
  const [idx, setIdx] = useState(0);
  const [playing, setPlaying] = useState(false);
  const timer = useRef<ReturnType<typeof setInterval> | null>(null);
  const total = STEPS.length;
  const s = STEPS[idx];

  const stop = () => {
    setPlaying(false);
    if (timer.current) { clearInterval(timer.current); timer.current = null; }
  };
  const play = () => {
    setPlaying(true);
    setIdx((i) => (i >= total - 1 ? 0 : i));
    timer.current = setInterval(() => {
      setIdx((i) => {
        if (i >= total - 1) { stop(); return i; }
        return i + 1;
      });
    }, 1100);
  };

  // autoplay once on mount
  useEffect(() => {
    const t = setTimeout(() => play(), 800);
    return () => { clearTimeout(t); if (timer.current) clearInterval(timer.current); };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const pct = total === 1 ? 0 : (idx / (total - 1)) * 100;

  return (
    <div className="lp-inspector-card" style={{ background: 'var(--bg-card)', borderRadius: 14, overflow: 'hidden', width: '100%' }}>
      {/* chrome */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 10, padding: '11px 15px', borderBottom: '1px solid var(--border-subtle)', background: 'var(--bg-elevated)' }}>
        <span style={{ fontFamily: 'var(--font-mono)', fontSize: 12, color: 'var(--text-tertiary)' }}>checkout-agent · sess_8f2a91c4</span>
        <span className="badge err" style={{ marginLeft: 'auto', fontSize: 10.5 }}><span className="d" />failed</span>
      </div>

      {/* step card */}
      <div style={{ padding: '20px', minHeight: 168 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 14 }}>
          <span style={{ fontFamily: 'var(--font-mono)', fontSize: 12, fontWeight: 500, color: s.color, padding: '3px 10px', borderRadius: 6, border: '1px solid var(--border-default)', background: 'var(--bg-elevated)' }}>
            {s.badge}
          </span>
          <span style={{ marginLeft: 'auto', fontFamily: 'var(--font-mono)', fontSize: 11.5, color: 'var(--text-tertiary)' }}>
            step {String(idx + 1).padStart(2, '0')} / {String(total).padStart(2, '0')}
          </span>
        </div>
        <p style={{ fontFamily: 'var(--font-mono)', fontSize: 13.5, lineHeight: 1.6, color: s.err ? 'var(--error)' : 'var(--mono-text)', minHeight: 44 }}>
          {s.text}
        </p>
        <div style={{ display: 'flex', gap: 26, marginTop: 16, paddingTop: 14, borderTop: '1px solid var(--border-subtle)' }}>
          {[['tokens', s.tok], ['cost', s.cost], ['latency', s.ms]].map(([k, v]) => (
            <div key={k}>
              <div style={{ fontSize: 10.5, color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '0.08em' }}>{k}</div>
              <div style={{ fontFamily: 'var(--font-mono)', fontSize: 13.5, color: 'var(--text-primary)', marginTop: 4 }}>{v}</div>
            </div>
          ))}
        </div>
      </div>

      {/* timeline scrubber */}
      <div style={{ padding: '14px 18px', borderTop: '1px solid var(--border-subtle)', background: 'var(--bg-elevated)' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <button
            onClick={() => (playing ? stop() : play())}
            aria-label={playing ? 'Pause' : 'Play'}
            style={{ width: 30, height: 30, borderRadius: 7, border: '1px solid var(--border-default)', background: 'var(--bg-base)', display: 'grid', placeItems: 'center', cursor: 'pointer', color: 'var(--text-primary)', flex: 'none' }}
          >
            {playing ? (
              <svg width="12" height="12" viewBox="0 0 14 14" fill="currentColor"><rect x="2.5" y="2" width="3" height="10" rx="1" /><rect x="8.5" y="2" width="3" height="10" rx="1" /></svg>
            ) : (
              <svg width="12" height="12" viewBox="0 0 14 14" fill="currentColor"><path d="M3 1.5v11l9-5.5z" /></svg>
            )}
          </button>
          <div
            onClick={(e) => {
              stop();
              const r = e.currentTarget.getBoundingClientRect();
              const ratio = Math.max(0, Math.min(1, (e.clientX - r.left) / r.width));
              setIdx(Math.round(ratio * (total - 1)));
            }}
            style={{ position: 'relative', flex: 1, height: 22, display: 'flex', alignItems: 'center', cursor: 'pointer' }}
          >
            <div style={{ position: 'absolute', left: 0, right: 0, height: 3, borderRadius: 3, background: 'var(--border-default)' }} />
            <div style={{ position: 'absolute', left: 0, width: `${pct}%`, height: 3, borderRadius: 3, background: 'var(--text-secondary)', transition: 'width .25s' }} />
            {STEPS.map((st, i) => (
              <span key={i} style={{
                position: 'absolute', left: `${total === 1 ? 0 : (i / (total - 1)) * 100}%`, transform: 'translateX(-50%)',
                width: i === idx ? 12 : 8, height: i === idx ? 12 : 8, borderRadius: '50%',
                background: i <= idx ? st.color : 'var(--bg-base)',
                border: `1.5px solid ${i <= idx ? st.color : 'var(--border-strong)'}`,
                transition: 'all .15s',
              }} />
            ))}
          </div>
          <span style={{ fontFamily: 'var(--font-mono)', fontSize: 11.5, color: 'var(--text-tertiary)', flex: 'none' }}>
            {String(idx + 1).padStart(2, '0')}/{String(total).padStart(2, '0')}
          </span>
        </div>
      </div>
    </div>
  );
}

/* ─── Install strip with copy ─────────────────────────────── */
function InstallStrip() {
  const [copied, setCopied] = useState(false);
  return (
    <div className="lp-install">
      <span className="p">$</span>
      <span>pip install capsule-trace</span>
      <button
        aria-label="Copy install command"
        onClick={() => {
          navigator.clipboard?.writeText('pip install capsule-trace');
          setCopied(true);
          setTimeout(() => setCopied(false), 1400);
        }}
      >
        {copied ? (
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none"><path d="M5 13l4 4 10-10" stroke="var(--success)" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round" /></svg>
        ) : (
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none"><rect x="9" y="9" width="11" height="11" rx="2" stroke="currentColor" strokeWidth="1.7" /><path d="M5 15V5a2 2 0 0 1 2-2h10" stroke="currentColor" strokeWidth="1.7" /></svg>
        )}
      </button>
    </div>
  );
}

/* ─── Data ────────────────────────────────────────────────── */
const HOW = [
  { n: '01', title: 'Capture', desc: 'One decorator wraps your agent. Every LLM call, tool use, and memory write is recorded — zero code changes.', code: '@capsule.trace\ndef agent(input):\n    ...' },
  { n: '02', title: 'Replay', desc: 'Re-run any failure deterministically from stored cassettes — no live API calls, bit-exact output.', code: '$ capsule-trace replay \\\n    sess_8f2a' },
  { n: '03', title: 'Branch', desc: 'Fork at any step. Swap a prompt, model, or tool response and run the alternative live.', code: '$ capsule-trace branch \\\n    --from-step 5' },
  { n: '04', title: 'Share', desc: 'Export a portable .capsule file and attach it to any bug report. Reproducible anywhere.', code: '$ capsule-trace export \\\n    --out bug.capsule' },
];

const FEATURES = [
  { title: 'Deterministic capture', desc: 'One pip install. Every LLM call, tool execution, and state mutation recorded automatically.',
    icon: <svg width="20" height="20" viewBox="0 0 24 24" fill="none"><rect x="3" y="4" width="18" height="16" rx="2.5" stroke="currentColor" strokeWidth="1.7" /><path d="M3 8.5h18M7 13h6M7 16.5h9" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" /></svg> },
  { title: 'Time-travel replay', desc: 'Scrub through any session with millisecond precision. Pause and inspect the exact world state.',
    icon: <svg width="20" height="20" viewBox="0 0 24 24" fill="none"><path d="M11 5 4 12l7 7M4 12h16" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round" /></svg> },
  { title: 'Branch & experiment', desc: 'Fork any session at any step. Swap a model or prompt, run the branch, compare outputs side-by-side.',
    icon: <svg width="20" height="20" viewBox="0 0 24 24" fill="none"><circle cx="6" cy="6" r="2.4" stroke="currentColor" strokeWidth="1.7" /><circle cx="18" cy="18" r="2.4" stroke="currentColor" strokeWidth="1.7" /><circle cx="6" cy="18" r="2.4" stroke="currentColor" strokeWidth="1.7" /><path d="M6 8.4v3.6a3 3 0 0 0 3 3h6.6" stroke="currentColor" strokeWidth="1.7" /></svg> },
  { title: 'Failure intelligence', desc: 'Automatic root-cause tagging for LLM timeouts, tool errors, context overflows, and schema mismatches.',
    icon: <svg width="20" height="20" viewBox="0 0 24 24" fill="none"><path d="M12 3l7 3v5c0 4.5-3 8-7 10-4-2-7-5.5-7-10V6z" stroke="currentColor" strokeWidth="1.6" strokeLinejoin="round" /></svg> },
  { title: 'Cost analytics', desc: 'Per-session and per-step token costs by model, project, and time range. Know where budget goes.',
    icon: <svg width="20" height="20" viewBox="0 0 24 24" fill="none"><circle cx="12" cy="12" r="8" stroke="currentColor" strokeWidth="1.7" /><path d="M12 7v5l3 2" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" /></svg> },
  { title: 'Framework-agnostic', desc: 'LangChain, LlamaIndex, AutoGen, raw OpenAI/Anthropic, or custom. If it calls an LLM, Capsule captures it.',
    icon: <svg width="20" height="20" viewBox="0 0 24 24" fill="none"><path d="M8 9l-4 3 4 3M16 9l4 3-4 3M13 6l-2 12" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round" /></svg> },
];

const COMPLIANCE = [
  { title: 'EU AI Act', desc: 'Article 12 logging — signed, exportable audit trails.',
    icon: <svg width="20" height="20" viewBox="0 0 24 24" fill="none"><circle cx="12" cy="12" r="9" stroke="currentColor" strokeWidth="1.6" /><path d="M12 7v5l3 2" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" /></svg> },
  { title: 'SOC 2 in progress', desc: 'Type II controls underway across security and availability.',
    icon: <svg width="20" height="20" viewBox="0 0 24 24" fill="none"><path d="M12 3l7 3v5c0 4.5-3 8-7 10-4-2-7-5.5-7-10V6z" stroke="currentColor" strokeWidth="1.6" strokeLinejoin="round" /><path d="M9 12l2 2 4-4" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" /></svg> },
  { title: 'GDPR', desc: 'Configurable PII redaction at capture time.',
    icon: <svg width="20" height="20" viewBox="0 0 24 24" fill="none"><rect x="5" y="10" width="14" height="10" rx="2" stroke="currentColor" strokeWidth="1.6" /><path d="M8 10V7a4 4 0 0 1 8 0v3" stroke="currentColor" strokeWidth="1.6" /></svg> },
  { title: 'Self-host', desc: 'Air-gapped Docker / VPC deployment, your keys.',
    icon: <svg width="20" height="20" viewBox="0 0 24 24" fill="none"><rect x="3" y="4" width="18" height="6" rx="1.5" stroke="currentColor" strokeWidth="1.6" /><rect x="3" y="14" width="18" height="6" rx="1.5" stroke="currentColor" strokeWidth="1.6" /><path d="M7 7h.01M7 17h.01" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" /></svg> },
];

// TODO: billing disabled for launch — pricing plans hidden
/*
const PLANS = [
  { name: 'Free', price: '$0', unit: '/ mo', desc: 'For trying deterministic replay locally.', cta: 'Start free', featured: false,
    features: ['Local SDK only', '1,000 sessions / mo', '7-day retention', 'Community support'] },
  { name: 'Hobby', price: '$49', unit: '/ mo', desc: 'For solo builders shipping to production.', cta: 'Start free', featured: false,
    features: ['Cloud storage', '3 team members', '30-day retention', 'Email support'] },
  { name: 'Pro', price: '$199', unit: '/ mo', desc: 'For teams debugging agents in production.', cta: 'Start 14-day trial', featured: true, pop: 'Popular',
    features: ['Unlimited sessions', '10 team members', '90-day retention', 'Priority support'] },
  { name: 'Enterprise', price: 'Custom', unit: '', desc: 'For regulated teams with compliance needs.', cta: 'Talk to sales', featured: false,
    features: ['Self-host / VPC deployment', 'SSO', 'Compliance reports', 'SLA'] },
];
*/

// billing disabled for launch: CHECK was only used by the pricing section
// const CHECK = (
//   <span className="ck"><svg width="16" height="16" viewBox="0 0 24 24" fill="none"><path d="M5 13l4 4 10-10" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round" /></svg></span>
// );

const ARROW = (
  <svg width="15" height="15" viewBox="0 0 16 16" fill="none"><path d="M3 8h10M9 4l4 4-4 4" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" /></svg>
);

/* ─── Landing page ────────────────────────────────────────── */
export default function LandingPage() {
  useReveal();
  return (
    <div style={{ background: 'var(--bg-base)', color: 'var(--text-primary)', minHeight: '100vh', overflowX: 'hidden' }}>
      <Nav />

      {/* ── HERO ── */}
      <section className="lp-hero">
        <div className="lp-hero-grid" />
        <div className="lp-wrap lp-hero-inner">
          <div>
            <span className="eyebrow reveal">Deterministic replay · time-travel debugging</span>
            <h1 className="lp-h1 reveal" style={{ marginTop: 22 }}>
              Rewind any agent.<br /><span className="g">Replay every decision.</span>
            </h1>
            <p className="lp-sub reveal">
              Capsule captures every LLM call, tool use, and state change your AI agent makes — and packages it into a portable <span className="mono" style={{ color: 'var(--text-primary)' }}>.capsule</span> file you can replay, branch, and share.
            </p>
            <div className="lp-hero-actions reveal">
              <Link href="/signup" className="btn btn-primary btn-lg">Start capturing free {ARROW}</Link>
              <a href="#how" className="btn btn-ghost btn-lg">See how it works</a>
            </div>
            <div className="reveal"><InstallStrip /></div>
            <div className="reveal" style={{ marginTop: 20 }}>
              <a
                href="https://www.producthunt.com/products/capsule-17?embed=true&utm_source=badge-featured&utm_medium=badge&utm_campaign=badge-capsule-17"
                target="_blank"
                rel="noopener noreferrer"
                className="ph-button"
              >
                {/* eslint-disable-next-line @next/next/no-img-element */}
                <img
                  alt="Capsule - The flight recorder for AI agents | Product Hunt"
                  src="https://api.producthunt.com/widgets/embed-image/v1/featured.svg?post_id=1178659&theme=dark&t=1782273810512"
                  width={250}
                  height={54}
                  style={{ display: 'block', borderRadius: 9 }}
                />
              </a>
            </div>
            <div className="lp-trustline reveal">
              <span>SOC 2 in progress</span><span className="dot" />
              <span>EU AI Act ready</span><span className="dot" />
              <span>Self-host available</span>
            </div>
          </div>
          <div className="reveal"><Inspector /></div>
        </div>
      </section>



      {/* ── HOW IT WORKS ── */}
      <section id="how" className="lp-section">
        <div className="lp-wrap">
          <div className="lp-shead reveal">
            <span className="eyebrow" style={{ marginBottom: 16 }}>How it works</span>
            <h2>Four steps from failure to fix.</h2>
            <p>Capsule turns a non-deterministic black box into something you can rewind, inspect, and reproduce on demand.</p>
          </div>
          <div className="lp-steps">
            {HOW.map((step) => (
              <div key={step.n} className="lp-step reveal">
                <span className="n">{step.n}</span>
                <h3>{step.title}</h3>
                <p>{step.desc}</p>
                <pre>{step.code}</pre>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── THE .capsule FILE ── */}
      <section id="capsule" className="lp-section bd">
        <div className="lp-wrap lp-capsule">
          <div className="lp-capfile reveal">
            <div className="fname">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none"><rect x="4" y="3" width="16" height="18" rx="2.5" stroke="var(--text-secondary)" strokeWidth="1.6" /><path d="M8 8h8M8 12h8M8 16h5" stroke="var(--text-tertiary)" strokeWidth="1.6" strokeLinecap="round" /></svg>
              <span className="nm">checkout-agent-fail.capsule</span>
              <span className="sz">2.4 MB</span>
            </div>
            <div className="lp-caprow"><span className="k">manifest</span><span>v1.0 · sha256 verified ✓</span></div>
            <div className="lp-caprow"><span className="k">events</span><span>23 steps · llm · tool · memory</span></div>
            <div className="lp-caprow"><span className="k">cassettes</span><span>11 stored responses · offline replay</span></div>
            <div className="lp-caprow"><span className="k">snapshots</span><span>3 memory states · zstd compressed</span></div>
            <div className="lp-caprow"><span className="k">integrity</span><span style={{ color: 'var(--success)' }}>hash match · deterministic ✓</span></div>
          </div>
          <div>
            <div className="lp-shead reveal" style={{ textAlign: 'left', margin: '0 0 32px' }}>
              <span className="eyebrow" style={{ marginBottom: 16 }}>The .capsule file</span>
              <h2>One file. The entire execution.</h2>
            </div>
            <ul className="lp-points">
              <li className="reveal"><h4>Self-describing & portable</h4><p>A single compressed archive holding every event, cassette, and snapshot. No external metadata, no database required.</p></li>
              <li className="reveal"><h4>Cryptographically verifiable</h4><p>SHA-256 integrity hashes guarantee the capsule replays bit-exact — the same on any machine, any Python version.</p></li>
              <li className="reveal"><h4>An open standard</h4><p>The format is fully specified and open-source. Attach a .capsule to a bug report the way you attach a screenshot today.</p></li>
            </ul>
          </div>
        </div>
      </section>

      {/* ── FEATURES ── */}
      <section id="features" className="lp-section">
        <div className="lp-wrap">
          <div className="lp-shead reveal">
            <span className="eyebrow" style={{ marginBottom: 16 }}>Features</span>
            <h2>Everything you need to understand your agents.</h2>
          </div>
          <div className="lp-steps">
            {FEATURES.map((f) => (
              <div key={f.title} className="lp-step reveal">
                <div style={{ width: 42, height: 42, borderRadius: 10, background: 'var(--bg-elevated)', border: '1px solid var(--border-default)', display: 'grid', placeItems: 'center', color: 'var(--text-secondary)' }}>{f.icon}</div>
                <h3>{f.title}</h3>
                <p>{f.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── CLI SHOWCASE ── */}
      <section className="lp-section bd">
        <div className="lp-wrap lp-capsule">
          <div>
            <div className="lp-shead reveal" style={{ textAlign: 'left', margin: '0 0 24px' }}>
              <span className="eyebrow" style={{ marginBottom: 16 }}>Built for engineers</span>
              <h2>Replay from your terminal.</h2>
              <p style={{ margin: '14px 0 0' }}>A complete CLI ships with the SDK. Capture, list, replay, branch, diff, and export — all scriptable with <span className="mono" style={{ color: 'var(--text-primary)' }}>--json</span> output.</p>
            </div>
            <Link href="/signup" className="btn btn-primary reveal">Get started {ARROW}</Link>
          </div>
          <div className="codebox reveal">
            <div className="cb-bar">
              <div style={{ display: 'flex', gap: 6 }}>
                <span style={{ width: 11, height: 11, borderRadius: '50%', background: 'var(--border-strong)' }} />
                <span style={{ width: 11, height: 11, borderRadius: '50%', background: 'var(--border-strong)' }} />
                <span style={{ width: 11, height: 11, borderRadius: '50%', background: 'var(--border-strong)' }} />
              </div>
              <span className="cb-tag" style={{ marginLeft: 8 }}>zsh</span>
            </div>
            <pre className="cb-body">
<span style={{ color: 'var(--text-tertiary)' }}>{'# replay a failed production session'}</span>{'\n'}
<span style={{ color: 'var(--replay)' }}>$</span> capsule-trace replay sess_8f2a91c4{'\n'}
{'  ✓ 23 steps · hash match · 0.31s\n\n'}
<span style={{ color: 'var(--text-tertiary)' }}>{'# branch at the failing step'}</span>{'\n'}
<span style={{ color: 'var(--replay)' }}>$</span> capsule-trace branch sess_8f2a91c4 --from-step 5{'\n'}
{'  ↳ branch fix-schema created\n\n'}
<span style={{ color: 'var(--text-tertiary)' }}>{'# export a portable bug report'}</span>{'\n'}
<span style={{ color: 'var(--replay)' }}>$</span> capsule-trace export sess_8f2a91c4 --out bug.capsule{'\n'}
<span style={{ color: 'var(--success)' }}>{'  ✓ wrote bug.capsule (2.4 MB)'}</span>
            </pre>
          </div>
        </div>
      </section>

      {/* ── COMPLIANCE ── */}
      <section id="compliance" className="lp-section">
        <div className="lp-wrap">
          <div className="lp-shead reveal">
            <span className="eyebrow" style={{ marginBottom: 16 }}>Compliance</span>
            <h2>Audit-ready from day one.</h2>
            <p>Every capsule is a signed, immutable record — built for regulated teams in fintech, insurance, and legal AI.</p>
          </div>
          <div className="lp-comp">
            {COMPLIANCE.map((c) => (
              <div key={c.title} className="lp-comp-badge reveal">
                <div className="ic">{c.icon}</div>
                <h4>{c.title}</h4>
                <p>{c.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── PRICING ── billing disabled for launch ──
      <section id="pricing" className="lp-section bd">
        <div className="lp-wrap">
          <div className="lp-shead reveal">
            <span className="eyebrow" style={{ marginBottom: 16 }}>Pricing</span>
            <h2>Start free. Scale when you ship.</h2>
          </div>
          <div className="lp-price">
            {PLANS.map((p) => (
              <div key={p.name} className={`lp-plan reveal${p.featured ? ' featured' : ''}`}>
                <div className="pn">{p.name}{p.pop && <span className="pop">{p.pop}</span>}</div>
                <div className="pr">{p.price}{p.unit && <span> {p.unit}</span>}</div>
                <div className="pd">{p.desc}</div>
                <ul>
                  {p.features.map((f) => (<li key={f}>{CHECK} {f}</li>))}
                </ul>
                <Link href="/signup" className={p.featured ? 'btn btn-primary' : 'btn btn-ghost'}>{p.cta}</Link>
              </div>
            ))}
          </div>
        </div>
      </section>
      */}

      {/* ── FINAL CTA ── */}
      <section className="lp-final">
        <div className="lp-wrap">
          <h2 className="reveal">Stop guessing why your agent broke.</h2>
          <p className="reveal">Capture your next production failure as a replayable .capsule — and rewind your way to the root cause.</p>
          <div className="reveal" style={{ display: 'flex', gap: 12, justifyContent: 'center', flexWrap: 'wrap' }}>
            <Link href="/signup" className="btn btn-primary btn-lg">Start capturing free {ARROW}</Link>
            <a href="#how" className="btn btn-ghost btn-lg">Read the docs</a>
          </div>
        </div>
      </section>

      {/* ── FOOTER ── */}
      <footer className="lp-foot">
        <div className="lp-wrap">
          <div className="lp-foot-top">
            <div className="lp-foot-brand">
              <Link className="brand" href="/" style={{ textDecoration: 'none' }}>
                <LogoMark size={42} />
                <span className="wordmark">Capsule</span>
              </Link>
              <p>Deterministic replay and time-travel debugging for AI agents.</p>
            </div>
            <div className="lp-foot-col">
              <h5>Product</h5>
              <a href="#how">How it works</a>
              <a href="#features">Features</a>
              <a href="#capsule">The .capsule file</a>
              {/* billing disabled for launch: <a href="#pricing">Pricing</a> */}
            </div>
            <div className="lp-foot-col">
              <h5>Developers</h5>
              <a href="#">Documentation</a>
              <a href="#">CLI reference</a>
              <a href="#">SDK (Python)</a>
              <a href="#">Changelog</a>
            </div>
            <div className="lp-foot-col">
              <h5>Company</h5>
              <a href="#compliance">Security</a>
              <a href="#compliance">Compliance</a>
              <a href="#">Careers</a>
              <a href="#">Contact</a>
              <Link href="/terms">Terms</Link>
              <Link href="/privacy">Privacy</Link>
            </div>
          </div>
          <div className="lp-foot-bottom">
            <span className="cp">© 2026 Capsule, Inc. · All rights reserved. · <a href="/terms" style={{ color: 'inherit' }}>Terms</a> · <a href="/privacy" style={{ color: 'inherit' }}>Privacy</a></span>
            <div className="socials">
              <a href="#" aria-label="GitHub"><svg width="17" height="17" viewBox="0 0 24 24" fill="currentColor"><path d="M12 2C6.5 2 2 6.6 2 12.2c0 4.5 2.9 8.3 6.8 9.6.5.1.7-.2.7-.5v-1.7c-2.8.6-3.4-1.4-3.4-1.4-.5-1.2-1.1-1.5-1.1-1.5-.9-.6.1-.6.1-.6 1 .1 1.5 1 1.5 1 .9 1.6 2.4 1.1 3 .9.1-.7.4-1.1.6-1.4-2.2-.3-4.6-1.1-4.6-5 0-1.1.4-2 1-2.7-.1-.3-.4-1.3.1-2.7 0 0 .8-.3 2.7 1a9.4 9.4 0 0 1 5 0c1.9-1.3 2.7-1 2.7-1 .5 1.4.2 2.4.1 2.7.6.7 1 1.6 1 2.7 0 3.9-2.4 4.7-4.6 5 .4.3.7.9.7 1.9v2.8c0 .3.2.6.7.5A10 10 0 0 0 22 12.2C22 6.6 17.5 2 12 2z" /></svg></a>
              <a href="#" aria-label="X"><svg width="15" height="15" viewBox="0 0 24 24" fill="currentColor"><path d="M18.2 2H21l-6.6 7.5L22 22h-6.3l-4.9-6.4L5.2 22H2.4l7-8L2 2h6.5l4.4 5.9L18.2 2zm-2.2 18h1.5L8 3.9H6.4L16 20z" /></svg></a>
              <a href="#" aria-label="Discord"><svg width="17" height="17" viewBox="0 0 24 24" fill="currentColor"><path d="M19.6 5.6A17 17 0 0 0 15.4 4l-.2.4a13 13 0 0 1 3.7 1.9c-3.7-1.7-8.1-1.7-11.9 0A13 13 0 0 1 10.7 4l-.2-.4A17 17 0 0 0 6.3 5.6C3.4 9.9 2.6 14.1 3 18.2A17 17 0 0 0 8.2 21l.4-1.1c-.7-.3-1.4-.6-2-1l.5-.4c3.6 1.7 7.6 1.7 11.2 0l.5.4c-.6.4-1.3.7-2 1l.4 1.1a17 17 0 0 0 5.2-2.8c.5-4.7-.8-8.9-3.8-12.6zM9.5 15.6c-1 0-1.8-.9-1.8-2s.8-2 1.8-2 1.8.9 1.8 2-.8 2-1.8 2zm5 0c-1 0-1.8-.9-1.8-2s.8-2 1.8-2 1.8.9 1.8 2-.8 2-1.8 2z" /></svg></a>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}
