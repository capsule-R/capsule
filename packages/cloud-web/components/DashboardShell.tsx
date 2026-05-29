'use client';

import Link from 'next/link';
import { LogoMark } from './Logo';

const NAV_ITEMS = [
  {
    group: 'Workspace',
    items: [
      {
        id: 'overview', label: 'Overview', href: '/dashboard',
        icon: <svg width="18" height="18" viewBox="0 0 24 24" fill="none"><rect x="3" y="3" width="7.5" height="7.5" rx="1.6" stroke="currentColor" strokeWidth="1.7"/><rect x="13.5" y="3" width="7.5" height="7.5" rx="1.6" stroke="currentColor" strokeWidth="1.7"/><rect x="3" y="13.5" width="7.5" height="7.5" rx="1.6" stroke="currentColor" strokeWidth="1.7"/><rect x="13.5" y="13.5" width="7.5" height="7.5" rx="1.6" stroke="currentColor" strokeWidth="1.7"/></svg>,
      },
      {
        id: 'sessions', label: 'Sessions', href: '/dashboard/sessions', count: '1,284',
        icon: <svg width="18" height="18" viewBox="0 0 24 24" fill="none"><rect x="3" y="4" width="18" height="16" rx="2.5" stroke="currentColor" strokeWidth="1.7"/><path d="M3 8.5h18M7 13h6M7 16.5h9" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round"/></svg>,
      },
      {
        id: 'branches', label: 'Branches', href: '/dashboard/branches', count: '37',
        icon: <svg width="18" height="18" viewBox="0 0 24 24" fill="none"><circle cx="6" cy="6" r="2.4" stroke="currentColor" strokeWidth="1.7"/><circle cx="18" cy="18" r="2.4" stroke="currentColor" strokeWidth="1.7"/><circle cx="6" cy="18" r="2.4" stroke="currentColor" strokeWidth="1.7"/><path d="M6 8.4v3.6a3 3 0 0 0 3 3h6.6" stroke="currentColor" strokeWidth="1.7"/></svg>,
      },
    ],
  },
  {
    group: 'Settings',
    items: [
      {
        id: 'keys', label: 'API Keys', href: '/dashboard/settings/api-keys',
        icon: <svg width="18" height="18" viewBox="0 0 24 24" fill="none"><circle cx="8" cy="8" r="4.2" stroke="currentColor" strokeWidth="1.7"/><path d="M11 11l8 8M16 16l2-2M14 18l2-2" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round"/></svg>,
      },
      {
        id: 'billing', label: 'Billing & Plan', href: '/dashboard/settings/billing',
        icon: <svg width="18" height="18" viewBox="0 0 24 24" fill="none"><rect x="3" y="5" width="18" height="14" rx="2.5" stroke="currentColor" strokeWidth="1.7"/><path d="M3 9.5h18" stroke="currentColor" strokeWidth="1.7"/><path d="M7 14.5h4" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round"/></svg>,
      },
    ],
  },
];

interface DashboardShellProps {
  active: string;
  title: string;
  crumb?: string;
  action?: { label: string; href: string };
  children: React.ReactNode;
}

export function DashboardShell({ active, title, crumb, action, children }: DashboardShellProps) {
  return (
    <div className="app">
      {/* Sidebar */}
      <aside className="sidebar">
        <div className="sb-brand">
          <a className="brand" href="/dashboard">
            <LogoMark />
            <span className="wordmark">Capsule</span>
          </a>
        </div>

        <div className="sb-env">
          <button className="env-switch">
            <span className="dot" />
            <span className="et">production</span>
            <span className="es">checkout-agent</span>
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" style={{ marginLeft: 8 }}>
              <path d="M7 10l5 5 5-5" stroke="#606060" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" />
            </svg>
          </button>
        </div>

        <nav className="sb-nav">
          {NAV_ITEMS.map((group) => (
            <div key={group.group} className="nav-group">
              <div className="gl">{group.group}</div>
              {group.items.map((item) => (
                <Link
                  key={item.id}
                  href={item.href}
                  className={`nav-item${item.id === active ? ' active' : ''}`}
                >
                  {item.icon}
                  <span>{item.label}</span>
                  {item.count && <span className="count">{item.count}</span>}
                </Link>
              ))}
            </div>
          ))}

          <div className="nav-group" style={{ marginTop: 'auto' }}>
            <a className="nav-item" href="https://docs.capsule.dev" target="_blank" rel="noreferrer">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none"><path d="M6 3h8l5 5v13a1 1 0 0 1-1 1H6a1 1 0 0 1-1-1V4a1 1 0 0 1 1-1z" stroke="currentColor" strokeWidth="1.7" strokeLinejoin="round"/><path d="M14 3v5h5" stroke="currentColor" strokeWidth="1.7" strokeLinejoin="round"/></svg>
              <span>Documentation</span>
              <svg width="13" height="13" viewBox="0 0 24 24" fill="none" style={{ marginLeft: 'auto' }}>
                <path d="M7 17 17 7M9 7h8v8" stroke="#606060" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round" />
              </svg>
            </a>
          </div>
        </nav>

        <div className="sb-foot">
          <div className="user-chip">
            <div className="avatar">DK</div>
            <div>
              <div className="un">Dana Okonkwo</div>
              <div className="ue">dana@helix.ai</div>
            </div>
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" style={{ marginLeft: 'auto' }}>
              <path d="M8 9l4-4 4 4M8 15l4 4 4-4" stroke="#606060" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round" />
            </svg>
          </div>
        </div>
      </aside>

      {/* Main */}
      <main className="main">
        <header className="topbar">
          <div className="tb-title">
            {crumb && <span className="tb-crumb">{crumb}</span>}
            <h1>{title}</h1>
          </div>
          <div className="tb-spacer" />
          <div className="tb-search">
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none">
              <circle cx="10.5" cy="10.5" r="6.5" stroke="currentColor" strokeWidth="1.7" />
              <path d="M16 16l4 4" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" />
            </svg>
            <input placeholder="Search sessions, branches…" />
            <span className="kbd">⌘K</span>
          </div>
          <button className="btn btn-icon btn-ghost" aria-label="Notifications">
            <svg width="17" height="17" viewBox="0 0 24 24" fill="none">
              <path d="M18 8a6 6 0 1 0-12 0c0 7-3 8-3 8h18s-3-1-3-8M10.5 21a1.8 1.8 0 0 0 3 0" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round" />
            </svg>
          </button>
          {action && (
            <a className="btn btn-primary btn-sm" href={action.href}>
              <svg width="15" height="15" viewBox="0 0 24 24" fill="none">
                <path d="M12 5v14M5 12h14" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
              </svg>
              {action.label}
            </a>
          )}
        </header>

        <div className="content">{children}</div>
      </main>
    </div>
  );
}
