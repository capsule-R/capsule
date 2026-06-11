'use client';

import { useRef, useState } from 'react';
import { uploadCapsuleFile, formatBytes, type UploadedSession } from '@/lib/capsule';
import { showToast } from '@/components/Toast';

interface UploadModalProps {
  workspaceId: string;
  open: boolean;
  onClose: () => void;
  onUploaded: (s: UploadedSession) => void;
}

export function UploadModal({ workspaceId, open, onClose, onUploaded }: UploadModalProps) {
  const [file, setFile] = useState<File | null>(null);
  const [agentName, setAgentName] = useState('');
  const [tags, setTags] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [dragging, setDragging] = useState(false);
  const [uploading, setUploading] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  if (!open) return null;

  const acceptFile = (f: File | undefined) => {
    if (!f) return;
    if (!f.name.toLowerCase().endsWith('.capsule')) {
      setError('Only .capsule files are accepted');
      setFile(null);
      return;
    }
    setError(null);
    setFile(f);
    setAgentName((prev) => prev || f.name.replace(/\.capsule$/i, ''));
  };

  const reset = () => {
    setFile(null);
    setAgentName('');
    setTags('');
    setError(null);
    setDragging(false);
    setUploading(false);
  };

  const close = () => {
    if (uploading) return;
    reset();
    onClose();
  };

  const submit = async () => {
    if (!file || uploading) return;
    setUploading(true);
    setError(null);
    const tagList = tags.split(',').map((t) => t.trim()).filter(Boolean);
    const { data, error: err, status } = await uploadCapsuleFile(
      workspaceId, file, agentName.trim(), tagList,
    );
    setUploading(false);
    if (data) {
      showToast('Session uploaded successfully', 'success');
      onUploaded(data);
      reset();
      onClose();
      return;
    }
    if (status === 413) setError('File too large for your current plan');
    else if (status === 401) setError('Authentication error — please log in again');
    else if (status === 409) setError(err ?? 'A session with this ID already exists');
    else setError('Upload failed. Please try again.');
  };

  return (
    <div className="modal-overlay" onClick={close}>
      <div className="modal" onClick={(e) => e.stopPropagation()}>
        <div className="modal-head">
          <h2>Upload .capsule</h2>
          <button className="modal-close" aria-label="Close" onClick={close}>
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
              <path d="M18 6 6 18M6 6l12 12" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
            </svg>
          </button>
        </div>

        {/* Drop zone */}
        <div
          onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
          onDragLeave={(e) => { e.preventDefault(); setDragging(false); }}
          onDrop={(e) => {
            e.preventDefault();
            setDragging(false);
            acceptFile(e.dataTransfer.files?.[0]);
          }}
          style={{
            border: `1px dashed ${dragging ? 'var(--text-secondary)' : 'var(--border-strong)'}`,
            background: dragging ? 'var(--bg-hover)' : 'var(--bg-card)',
            borderRadius: 10,
            padding: '28px 20px',
            textAlign: 'center',
            marginBottom: 16,
            transition: 'border-color .15s, background .15s',
          }}
        >
          {file ? (
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 10 }}>
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none">
                <rect x="4" y="3" width="16" height="18" rx="2.5" stroke="var(--text-secondary)" strokeWidth="1.6" />
                <path d="M8 8h8M8 12h8M8 16h5" stroke="var(--text-tertiary)" strokeWidth="1.6" strokeLinecap="round" />
              </svg>
              <span style={{ fontFamily: 'var(--font-mono)', fontSize: 13.5, color: 'var(--text-primary)' }}>
                {file.name}
              </span>
              <span style={{ fontFamily: 'var(--font-mono)', fontSize: 12, color: 'var(--text-tertiary)' }}>
                {formatBytes(file.size)}
              </span>
              <button
                aria-label="Remove file"
                onClick={() => setFile(null)}
                style={{ border: 'none', background: 'transparent', color: 'var(--text-tertiary)', cursor: 'pointer', display: 'grid', placeItems: 'center', padding: 2 }}
              >
                <svg width="13" height="13" viewBox="0 0 24 24" fill="none">
                  <path d="M18 6 6 18M6 6l12 12" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
                </svg>
              </button>
            </div>
          ) : (
            <>
              <div style={{ fontSize: 13.5, color: 'var(--text-secondary)', marginBottom: 12 }}>
                Drag &amp; drop a <span style={{ fontFamily: 'var(--font-mono)', color: 'var(--text-primary)' }}>.capsule</span> file here
              </div>
              <button className="btn btn-ghost btn-sm" onClick={() => inputRef.current?.click()}>
                Browse files
              </button>
              <input
                ref={inputRef}
                type="file"
                accept=".capsule"
                style={{ display: 'none' }}
                onChange={(e) => {
                  acceptFile(e.target.files?.[0]);
                  e.target.value = '';
                }}
              />
            </>
          )}
        </div>

        {/* Agent name */}
        <div style={{ marginBottom: 14 }}>
          <label style={{ display: 'block', fontSize: 13, fontWeight: 600, marginBottom: 7, color: 'var(--text-secondary)' }}>
            Agent name
          </label>
          <input
            className="input"
            placeholder="e.g. billing-agent"
            value={agentName}
            onChange={(e) => setAgentName(e.target.value)}
          />
        </div>

        {/* Tags */}
        <div style={{ marginBottom: 18 }}>
          <label style={{ display: 'block', fontSize: 13, fontWeight: 600, marginBottom: 7, color: 'var(--text-secondary)' }}>
            Tags <span style={{ fontWeight: 400, color: 'var(--text-tertiary)' }}>(optional, comma-separated)</span>
          </label>
          <input
            className="input"
            placeholder="production, refund"
            value={tags}
            onChange={(e) => setTags(e.target.value)}
          />
        </div>

        {error && (
          <div style={{ fontSize: 13, color: 'var(--error)', marginBottom: 14 }}>{error}</div>
        )}

        <div style={{ display: 'flex', gap: 10 }}>
          <button className="btn btn-ghost" style={{ flex: 1 }} onClick={close} disabled={uploading}>
            Cancel
          </button>
          <button
            className="btn btn-primary"
            style={{ flex: 1 }}
            onClick={submit}
            disabled={!file || !agentName.trim() || uploading}
          >
            {uploading ? 'Uploading…' : 'Upload'}
          </button>
        </div>
      </div>
    </div>
  );
}
