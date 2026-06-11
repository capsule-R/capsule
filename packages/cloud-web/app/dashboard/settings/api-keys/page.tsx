'use client';

import { useState, useEffect } from 'react';
import { DashboardShell } from '@/components/DashboardShell';
import { apiFetch } from '@/lib/capsule';

interface ApiKey {
  id: string;
  name: string;
  key_prefix: string;
  created_at: string;
  last_used_at: string | null;
  expires_at: string | null;
}

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

function fmt(iso: string | null): string {
  if (!iso) return 'Never';
  const d = new Date(iso);
  const diff = Date.now() - d.getTime();
  const m = Math.floor(diff / 60000);
  if (m < 1) return 'just now';
  if (m < 60) return `${m}m ago`;
  const h = Math.floor(m / 60);
  if (h < 24) return `${h}h ago`;
  return d.toLocaleDateString();
}

export default function ApiKeysPage() {
  const [keys, setKeys] = useState<ApiKey[]>([]);
  const [workspaceId, setWorkspaceId] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [newName, setNewName] = useState('');
  const [creating, setCreating] = useState(false);
  const [createdKey, setCreatedKey] = useState<string | null>(null);
  const [revokeTarget, setRevokeTarget] = useState<string | null>(null);
  const [revoking, setRevoking] = useState(false);

  useEffect(() => {
    async function load() {
      try {
        const wsRes = await apiFetch('/workspaces');
        if (!wsRes.ok) return;
        const workspaces = await wsRes.json();
        if (workspaces.length === 0) return;
        const wsId = workspaces[0].id;
        setWorkspaceId(wsId);

        const keysRes = await apiFetch(`/workspaces/${wsId}/api-keys`);
        if (!keysRes.ok) return;
        setKeys(await keysRes.json());
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  const createKey = async () => {
    if (!newName.trim() || !workspaceId) return;
    setCreating(true);
    try {
      const res = await apiFetch(`/workspaces/${workspaceId}/api-keys`, {
        method: 'POST',
        body: JSON.stringify({ name: newName.trim() }),
      });
      const data = await res.json();
      if (!res.ok) { alert(data.detail ?? 'Failed to create key'); return; }
      setCreatedKey(data.full_key);
      setKeys((prev) => [data, ...prev]);
      setNewName('');
    } finally {
      setCreating(false);
    }
  };

  const revokeKey = async (id: string) => {
    if (!workspaceId) return;
    setRevoking(true);
    try {
      const res = await apiFetch(`/workspaces/${workspaceId}/api-keys/${id}`, { method: 'DELETE' });
      if (res.ok) setKeys((prev) => prev.filter((k) => k.id !== id));
    } finally {
      setRevoking(false);
      setRevokeTarget(null);
    }
  };

  return (
    <DashboardShell active="keys" title="API Keys" crumb="workspace / settings / api keys">
      <div className="page-head">
        <div>
          <h2>API Keys</h2>
          <p>Keys authenticate the Capsule SDK when capturing sessions.</p>
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
        </div>
        <pre className="cb-body"><span style={{ color: 'var(--replay)' }}>import</span> capsule_trace as capsule{'\n'}capsule.init(api_key=<span style={{ color: 'var(--success)' }}>&quot;csk_your_key_here&quot;</span>, workspace_id=<span style={{ color: 'var(--success)' }}>&quot;{workspaceId ?? 'ws_xxxxxxxx'}&quot;</span>)</pre>
      </div>

      {/* Keys table */}
      <h3 style={{ fontFamily: 'var(--font-body)', fontWeight: 600, fontSize: 14, color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: 12 }}>
        Active keys <span style={{ color: 'var(--text-tertiary)', fontWeight: 400 }}>({keys.length})</span>
      </h3>
      <div className="table-wrap">
        <table className="tbl">
          <thead>
            <tr>
              <th>Name</th><th>Key prefix</th><th className="hide-mobile">Created</th><th className="hide-mobile">Last used</th><th style={{ textAlign: 'right' }}>Actions</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr><td colSpan={5}><div className="empty">Loading…</div></td></tr>
            ) : keys.length === 0 ? (
              <tr><td colSpan={5}><div className="empty">No API keys yet. Create one to start capturing sessions.</div></td></tr>
            ) : keys.map((k) => (
              <tr key={k.id}>
                <td style={{ fontWeight: 600 }}>{k.name}</td>
                <td>
                  <code style={{ fontFamily: 'var(--font-mono)', fontSize: 13, color: 'var(--text-secondary)' }}>{k.key_prefix}…</code>
                </td>
                <td className="cell-sub hide-mobile">{fmt(k.created_at)}</td>
                <td className="cell-sub hide-mobile">{fmt(k.last_used_at)}</td>
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
                <div style={{ marginBottom: 24 }}>
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
                <div style={{ display: 'flex', gap: 10 }}>
                  <button className="btn btn-ghost" style={{ flex: 1 }} onClick={() => setShowModal(false)}>Cancel</button>
                  <button className="btn btn-primary" style={{ flex: 1 }} onClick={createKey} disabled={!newName.trim() || creating}>
                    {creating ? 'Creating…' : 'Create key'}
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
              <button className="btn" style={{ flex: 1, background: 'var(--error)', color: '#fff', border: 'none' }} onClick={() => revokeKey(revokeTarget!)} disabled={revoking}>
                {revoking ? 'Revoking…' : 'Revoke key'}
              </button>
            </div>
          </div>
        </div>
      )}
    </DashboardShell>
  );
}
