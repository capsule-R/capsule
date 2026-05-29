'use client';

import { useState } from 'react';
import { DashboardShell } from '@/components/DashboardShell';

interface ApiKey {
  id: string;
  name: string;
  prefix: string;
  created: string;
  lastUsed: string;
  scopes: string[];
  active: boolean;
}

const INITIAL_KEYS: ApiKey[] = [
  { id: 'k1', name: 'Production SDK', prefix: 'csk_prod_****', created: 'Mar 12, 2025', lastUsed: '2m ago', scopes: ['sessions:write', 'sessions:read'], active: true },
  { id: 'k2', name: 'CI Pipeline', prefix: 'csk_ci___****', created: 'Apr 1, 2025', lastUsed: '1d ago', scopes: ['sessions:write'], active: true },
  { id: 'k3', name: 'Analytics read', prefix: 'csk_ana__****', created: 'Apr 22, 2025', lastUsed: '7d ago', scopes: ['sessions:read'], active: true },
  { id: 'k4', name: 'Old staging key', prefix: 'csk_stg__****', created: 'Jan 3, 2025', lastUsed: '30d ago', scopes: ['sessions:write', 'sessions:read'], active: false },
];

const ALL_SCOPES = ['sessions:write', 'sessions:read', 'branches:read', 'workspaces:read'];

function CopyButton({ text }: { text: string }) {
  const [done, setDone] = useState(false);
  return (
    <button
      onClick={() => { navigator.clipboard.writeText(text); setDone(true); setTimeout(() => setDone(false), 1500); }}
      style={{ padding: '4px 10px', borderRadius: 6, border: '1px solid var(--border-default)', background: 'var(--bg-elevated)', fontSize: 12, fontFamily: 'var(--font-mono)', color: 'var(--text-secondary)', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: 5 }}
    >
      {done ? (
        <svg width="12" height="12" viewBox="0 0 24 24" fill="none"><path d="M5 13l4 4L19 7" stroke="var(--success)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/></svg>
      ) : (
        <svg width="12" height="12" viewBox="0 0 24 24" fill="none"><rect x="9" y="9" width="12" height="12" rx="2" stroke="currentColor" strokeWidth="1.8"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round"/></svg>
      )}
      {done ? 'Copied' : 'Copy'}
    </button>
  );
}

export default function ApiKeysPage() {
  const [keys, setKeys] = useState<ApiKey[]>(INITIAL_KEYS);
  const [showModal, setShowModal] = useState(false);
  const [newName, setNewName] = useState('');
  const [newScopes, setNewScopes] = useState<string[]>(['sessions:write', 'sessions:read']);
  const [createdKey, setCreatedKey] = useState<string | null>(null);
  const [revokeTarget, setRevokeTarget] = useState<string | null>(null);

  const createKey = () => {
    if (!newName.trim()) return;
    const fakeKey = 'csk_' + Math.random().toString(36).slice(2, 18);
    const newKey: ApiKey = {
      id: 'k' + Date.now(),
      name: newName.trim(),
      prefix: fakeKey.slice(0, 10) + '****',
      created: 'Just now',
      lastUsed: 'Never',
      scopes: newScopes,
      active: true,
    };
    setKeys((prev) => [newKey, ...prev]);
    setCreatedKey(fakeKey);
    setNewName('');
    setNewScopes(['sessions:write', 'sessions:read']);
  };

  const revokeKey = (id: string) => {
    setKeys((prev) => prev.map((k) => k.id === id ? { ...k, active: false } : k));
    setRevokeTarget(null);
  };

  const toggleScope = (s: string) => {
    setNewScopes((prev) => prev.includes(s) ? prev.filter((x) => x !== s) : [...prev, s]);
  };

  const activeKeys = keys.filter((k) => k.active);
  const revokedKeys = keys.filter((k) => !k.active);

  return (
    <DashboardShell active="keys" title="API Keys" crumb="workspace / settings / api keys">
      <div className="page-head">
        <div>
          <h2>API Keys</h2>
          <p>Keys authenticate the Capsule SDK when capturing sessions. Each key can be scoped to limit access.</p>
        </div>
        <button className="btn btn-primary btn-sm" onClick={() => { setCreatedKey(null); setShowModal(true); }}>
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none"><path d="M12 5v14M5 12h14" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/></svg>
          New API key
        </button>
      </div>

      {/* Install hint */}
      <div className="codebox" style={{ marginBottom: 24 }}>
        <div className="cb-bar">
          <span className="cb-tag">SDK init</span>
          <span className="cb-copy">copy</span>
        </div>
        <pre className="cb-body"><span style={{ color: 'var(--replay)' }}>import</span> capsule{'\n'}capsule.init(api_key=<span style={{ color: 'var(--success)' }}>&quot;csk_your_key_here&quot;</span>, workspace_id=<span style={{ color: 'var(--success)' }}>&quot;ws_xxxxxxxx&quot;</span>)</pre>
      </div>

      {/* Active keys table */}
      <h3 style={{ fontFamily: 'var(--font-body)', fontWeight: 600, fontSize: 14, color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: 12 }}>
        Active keys <span style={{ color: 'var(--text-tertiary)', fontWeight: 400 }}>({activeKeys.length})</span>
      </h3>
      <div className="table-wrap" style={{ marginBottom: 32 }}>
        <table className="tbl">
          <thead>
            <tr>
              <th>Name</th><th>Key</th><th>Scopes</th><th>Created</th><th>Last used</th><th style={{ textAlign: 'right' }}>Actions</th>
            </tr>
          </thead>
          <tbody>
            {activeKeys.length === 0 ? (
              <tr><td colSpan={6}><div className="empty">No active keys.</div></td></tr>
            ) : activeKeys.map((k) => (
              <tr key={k.id}>
                <td style={{ fontWeight: 600 }}>{k.name}</td>
                <td>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                    <code style={{ fontFamily: 'var(--font-mono)', fontSize: 13, color: 'var(--text-secondary)' }}>{k.prefix}</code>
                  </div>
                </td>
                <td>
                  <div style={{ display: 'flex', gap: 5, flexWrap: 'wrap' }}>
                    {k.scopes.map((s) => (
                      <span key={s} style={{ fontSize: 11, fontFamily: 'var(--font-mono)', color: 'var(--replay)', background: 'color-mix(in oklab, var(--replay) 10%, transparent)', border: '1px solid color-mix(in oklab, var(--replay) 25%, transparent)', borderRadius: 4, padding: '2px 7px' }}>{s}</span>
                    ))}
                  </div>
                </td>
                <td className="cell-sub">{k.created}</td>
                <td className="cell-sub">{k.lastUsed}</td>
                <td>
                  <div className="row-actions" style={{ justifyContent: 'flex-end' }}>
                    <button
                      onClick={() => setRevokeTarget(k.id)}
                      style={{ padding: '4px 12px', borderRadius: 6, border: '1px solid var(--border-default)', background: 'var(--bg-base)', fontSize: 12, fontFamily: 'var(--font-mono)', color: 'var(--error)', cursor: 'pointer' }}
                    >
                      Revoke
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Revoked keys */}
      {revokedKeys.length > 0 && (
        <>
          <h3 style={{ fontFamily: 'var(--font-body)', fontWeight: 600, fontSize: 14, color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: 12 }}>
            Revoked <span style={{ color: 'var(--text-tertiary)', fontWeight: 400 }}>({revokedKeys.length})</span>
          </h3>
          <div className="table-wrap">
            <table className="tbl">
              <thead><tr><th>Name</th><th>Key</th><th>Scopes</th><th>Created</th><th>Last used</th></tr></thead>
              <tbody>
                {revokedKeys.map((k) => (
                  <tr key={k.id} style={{ opacity: 0.45 }}>
                    <td style={{ fontWeight: 600 }}>{k.name}</td>
                    <td><code style={{ fontFamily: 'var(--font-mono)', fontSize: 13, color: 'var(--text-tertiary)' }}>{k.prefix}</code></td>
                    <td>
                      <div style={{ display: 'flex', gap: 5, flexWrap: 'wrap' }}>
                        {k.scopes.map((s) => (
                          <span key={s} style={{ fontSize: 11, fontFamily: 'var(--font-mono)', color: 'var(--text-tertiary)', background: 'var(--bg-elevated)', border: '1px solid var(--border-subtle)', borderRadius: 4, padding: '2px 7px' }}>{s}</span>
                        ))}
                      </div>
                    </td>
                    <td className="cell-sub">{k.created}</td>
                    <td className="cell-sub">{k.lastUsed}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}

      {/* Create modal */}
      {showModal && (
        <div className="modal-overlay" onClick={() => !createdKey && setShowModal(false)}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            {createdKey ? (
              <>
                <div className="modal-head">
                  <h2>Key created</h2>
                  <button className="modal-close" onClick={() => { setShowModal(false); setCreatedKey(null); }}>
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none"><path d="M18 6 6 18M6 6l12 12" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/></svg>
                  </button>
                </div>
                <div style={{ marginBottom: 20 }}>
                  <div style={{ padding: '14px 16px', background: 'color-mix(in oklab, var(--success) 8%, transparent)', border: '1px solid color-mix(in oklab, var(--success) 25%, transparent)', borderRadius: 'var(--radius-sm)', marginBottom: 16 }}>
                    <div style={{ fontSize: 12.5, color: 'var(--success)', marginBottom: 6 }}>✓ Copy this key now — it will never be shown again.</div>
                    <code style={{ fontFamily: 'var(--font-mono)', fontSize: 13.5, color: 'var(--text-primary)', wordBreak: 'break-all' }}>{createdKey}</code>
                  </div>
                  <CopyButton text={createdKey} />
                </div>
                <button className="btn btn-primary" style={{ width: '100%' }} onClick={() => { setShowModal(false); setCreatedKey(null); }}>Done</button>
              </>
            ) : (
              <>
                <div className="modal-head">
                  <h2>New API key</h2>
                  <button className="modal-close" onClick={() => setShowModal(false)}>
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none"><path d="M18 6 6 18M6 6l12 12" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/></svg>
                  </button>
                </div>
                <div style={{ marginBottom: 16 }}>
                  <label style={{ display: 'block', fontSize: 13, fontWeight: 600, marginBottom: 7, color: 'var(--text-secondary)' }}>Key name</label>
                  <input
                    className="input"
                    placeholder="e.g. Production SDK"
                    value={newName}
                    onChange={(e) => setNewName(e.target.value)}
                    onKeyDown={(e) => e.key === 'Enter' && createKey()}
                    autoFocus
                  />
                </div>
                <div style={{ marginBottom: 24 }}>
                  <label style={{ display: 'block', fontSize: 13, fontWeight: 600, marginBottom: 10, color: 'var(--text-secondary)' }}>Scopes</label>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                    {ALL_SCOPES.map((s) => (
                      <label key={s} style={{ display: 'flex', alignItems: 'center', gap: 10, cursor: 'pointer' }}>
                        <input
                          type="checkbox"
                          checked={newScopes.includes(s)}
                          onChange={() => toggleScope(s)}
                          style={{ width: 15, height: 15, accentColor: 'var(--accent)', cursor: 'pointer' }}
                        />
                        <span style={{ fontFamily: 'var(--font-mono)', fontSize: 13, color: 'var(--text-primary)' }}>{s}</span>
                      </label>
                    ))}
                  </div>
                </div>
                <div style={{ display: 'flex', gap: 10 }}>
                  <button className="btn btn-ghost" style={{ flex: 1 }} onClick={() => setShowModal(false)}>Cancel</button>
                  <button className="btn btn-primary" style={{ flex: 1 }} onClick={createKey} disabled={!newName.trim() || newScopes.length === 0}>
                    Create key
                  </button>
                </div>
              </>
            )}
          </div>
        </div>
      )}

      {/* Revoke confirm modal */}
      {revokeTarget && (
        <div className="modal-overlay" onClick={() => setRevokeTarget(null)}>
          <div className="modal" onClick={(e) => e.stopPropagation()} style={{ maxWidth: 400 }}>
            <div className="modal-head">
              <h2>Revoke key?</h2>
              <button className="modal-close" onClick={() => setRevokeTarget(null)}>
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none"><path d="M18 6 6 18M6 6l12 12" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/></svg>
              </button>
            </div>
            <p style={{ fontSize: 13.5, color: 'var(--text-secondary)', marginBottom: 24, lineHeight: 1.6 }}>
              Any SDK instances using <strong>{keys.find((k) => k.id === revokeTarget)?.name}</strong> will immediately lose access. This cannot be undone.
            </p>
            <div style={{ display: 'flex', gap: 10 }}>
              <button className="btn btn-ghost" style={{ flex: 1 }} onClick={() => setRevokeTarget(null)}>Cancel</button>
              <button className="btn" style={{ flex: 1, background: 'var(--error)', color: '#fff', border: 'none' }} onClick={() => revokeKey(revokeTarget)}>
                Revoke key
              </button>
            </div>
          </div>
        </div>
      )}
    </DashboardShell>
  );
}
