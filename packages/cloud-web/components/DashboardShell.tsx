'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { LogoMark } from './Logo';
import { getCurrentUser, logout, type UserProfile } from '@/lib/capsule';

const NAV_ITEMS = [
  {
    group: 'Workspace',
    items: [
      {
        id: 'overview', label: 'Overview', href: '/dashboard',
        icon: <svg width="18" height="18" viewBox="0 0 24 24" fill="none"><rect x="3" y="3" width="7.5" height="7.5" rx="1.6" stroke="currentColor" strokeWidth="1.7"/><rect x="13.5" y="3" width="7.5" height="7.5" rx="1.6" stroke="currentColor" strokeWidth="1.7"/><rect x="3" y="13.5" width="7.5" height="7.5" rx="1.6" stroke="currentColor" strokeWidth="1.7"/><rect x="13.5" y="13.5" width="7.5" height="7.5" rx="1.6" stroke="currentColor" strokeWidth="1.7"/></svg>,
      },
      {
        id: 'sessions', label: 'Sessions', href: '/dashboard/sessions',
        icon: <svg width="18" height="18" viewBox="0 0 24 24" fill="none"><rect x="3" y="4" width="18" height="16" rx="2.5" stroke="currentColor" strokeWidth="1.7"/><path d="M3 8.5h18M7 13h6M7 16.5h9" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round"/></svg>,
      },
      {
        id: 'branches', label: 'Branches', href: '/dashboard/branches',
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
  action?: { label: string; href?: string; onClick?: () => void };
  children: React.ReactNode;
}

function initials(name: string | null | undefined, email: string): string {
  if (name && name.trim()) {
    const parts = name.trim().split(/\s+/);
    if (parts.length >= 2) return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
    return parts[0].slice(0, 2).toUpperCase();
  }
  return email.slice(0, 2).toUpperCase();
}

export function DashboardShell({ active, title, crumb, action, children }: DashboardShellProps) {
  const [user, setUser] = useState<UserProfile | null>(null);
  const [showUserMenu, setShowUserMenu] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(false);

  useEffect(() => {
    getCurrentUser().then(setUser);
  }, []);

  const displayName = user?.full_name || user?.email?.split('@')[0] || '…';
  const displayEmail = user?.email || '';
  const avatarText = user ? initials(user.full_name, user.email) : '…';

  return (
    <div className="app">
      {/* Mobile sidebar overlay */}
      {sidebarOpen && (
        <div className="sidebar-drawer-overlay" onClick={() => setSidebarOpen(false)} />
      )}

      {/* Sidebar */}
      <aside className={`sidebar${sidebarOpen ? ' sidebar-open' : ''}`}>
        <div className="sb-brand">
          <a className="brand" href="/dashboard">
            <LogoMark />
            <span className="wordmark">Capsule</span>
          </a>
        </div>

        <nav className="sb-nav" onClick={() => setSidebarOpen(false)}>
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
                </Link>
              ))}
            </div>
          ))}

          <div className="nav-group" style={{ marginTop: 'auto' }}>
            <Link className={`nav-item${'docs' === active ? ' active' : ''}`} href="/dashboard/docs">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none"><path d="M6 3h8l5 5v13a1 1 0 0 1-1 1H6a1 1 0 0 1-1-1V4a1 1 0 0 1 1-1z" stroke="currentColor" strokeWidth="1.7" strokeLinejoin="round"/><path d="M14 3v5h5" stroke="currentColor" strokeWidth="1.7" strokeLinejoin="round"/></svg>
              <span>Documentation</span>
            </Link>
          </div>
        </nav>

        <div className="sb-foot">
          <div
            className="user-chip"
            style={{ position: 'relative', cursor: 'pointer' }}
            onClick={() => setShowUserMenu((v) => !v)}
          >
            <div className="avatar">{avatarText}</div>
            <div style={{ flex: 1, minWidth: 0 }}>
              <div className="un" style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{displayName}</div>
              <div className="ue" style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{displayEmail}</div>
            </div>
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" style={{ marginLeft: 'auto', flexShrink: 0 }}>
              <path d="M8 9l4-4 4 4M8 15l4 4 4-4" stroke="#606060" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round" />
            </svg>

            {showUserMenu && (
              <div
                style={{ position: 'absolute', bottom: '100%', left: 0, right: 0, marginBottom: 6, background: 'var(--bg-card)', border: '1px solid var(--border-default)', borderRadius: 'var(--radius-sm)', overflow: 'hidden', boxShadow: '0 8px 24px rgba(0,0,0,0.4)', zIndex: 50 }}
                onClick={(e) => e.stopPropagation()}
              >
                <Link
                  href="/dashboard/settings/general"
                  style={{ display: 'flex', alignItems: 'center', gap: 10, padding: '11px 14px', fontSize: 13.5, color: 'var(--text-secondary)', textDecoration: 'none' }}
                  onClick={() => setShowUserMenu(false)}
                >
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none"><circle cx="12" cy="8" r="4" stroke="currentColor" strokeWidth="1.7"/><path d="M4 20c0-4 3.6-7 8-7s8 3 8 7" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round"/></svg>
                  Account settings
                </Link>
                <div style={{ height: 1, background: 'var(--border-subtle)', margin: '0 14px' }} />
                <button
                  onClick={() => logout()}
                  style={{ display: 'flex', alignItems: 'center', gap: 10, width: '100%', padding: '11px 14px', fontSize: 13.5, color: 'var(--error)', background: 'none', border: 'none', cursor: 'pointer', textAlign: 'left' }}
                >
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none"><path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4M16 17l5-5-5-5M21 12H9" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round"/></svg>
                  Sign out
                </button>
              </div>
            )}
          </div>
        </div>
      </aside>

      {/* Main */}
      <main className="main">
        <header className="topbar">
          <button
            className="mobile-nav-toggle"
            aria-label="Toggle navigation"
            onClick={() => setSidebarOpen((v) => !v)}
          >
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none">
              <path d="M3 7h18M3 12h18M3 17h18" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" />
            </svg>
          </button>
          <div className="tb-title">
            {crumb && <span className="tb-crumb">{crumb}</span>}
            <h1>{title}</h1>
          </div>
          <div className="tb-spacer" />
          {action && (action.onClick ? (
            <button className="btn btn-primary btn-sm" onClick={action.onClick}>
              <svg width="15" height="15" viewBox="0 0 24 24" fill="none">
                <path d="M12 5v14M5 12h14" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
              </svg>
              {action.label}
            </button>
          ) : (
            <a className="btn btn-primary btn-sm" href={action.href}>
              <svg width="15" height="15" viewBox="0 0 24 24" fill="none">
                <path d="M12 5v14M5 12h14" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
              </svg>
              {action.label}
            </a>
          ))}
        </header>

        <div className="content">{children}</div>
      </main>
    </div>
  );
}
