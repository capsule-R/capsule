'use client';

/**
 * Minimal toast system — no library. Pages render <ToastHost /> once;
 * anything can call showToast(). Module-level dispatch keeps it dependency-free.
 */

import { useEffect, useState } from 'react';

export type ToastKind = 'success' | 'error' | 'info';

export interface ToastAction {
  label: string;
  href: string;
}

interface ToastMsg {
  id: number;
  kind: ToastKind;
  text: string;
  action?: ToastAction;
}

type Listener = (t: ToastMsg) => void;

let _listener: Listener | null = null;
let _nextId = 1;
const _pending: ToastMsg[] = [];

export function showToast(text: string, kind: ToastKind = 'info', action?: ToastAction): void {
  const msg: ToastMsg = { id: _nextId++, kind, text, action };
  if (_listener) _listener(msg);
  else _pending.push(msg);
}

const KIND_COLOR: Record<ToastKind, string> = {
  success: 'var(--success)',
  error: 'var(--error)',
  info: 'var(--text-secondary)',
};

export function ToastHost() {
  const [toasts, setToasts] = useState<ToastMsg[]>([]);

  useEffect(() => {
    _listener = (t) => {
      setToasts((prev) => [...prev, t]);
      setTimeout(() => {
        setToasts((prev) => prev.filter((x) => x.id !== t.id));
      }, 5000);
    };
    if (_pending.length > 0) {
      const drained = _pending.splice(0, _pending.length);
      drained.forEach((t) => _listener?.(t));
    }
    return () => {
      _listener = null;
    };
  }, []);

  if (toasts.length === 0) return null;

  return (
    <div className="toast-container">
      {toasts.map((t) => (
        <div
          key={t.id}
          role="status"
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: 10,
            padding: '12px 16px',
            background: 'var(--bg-elevated)',
            border: '1px solid var(--border-strong)',
            borderRadius: 10,
            boxShadow: '0 12px 36px -12px rgba(0,0,0,.7)',
            fontSize: 13.5,
            color: 'var(--text-primary)',
          }}
        >
          <span
            style={{
              width: 8,
              height: 8,
              borderRadius: '50%',
              background: KIND_COLOR[t.kind],
              flexShrink: 0,
            }}
          />
          <span style={{ flex: 1 }}>{t.text}</span>
          {t.action && (
            <a
              href={t.action.href}
              style={{
                fontSize: 13,
                fontWeight: 600,
                color: 'var(--text-primary)',
                textDecoration: 'underline',
                textUnderlineOffset: 3,
                whiteSpace: 'nowrap',
              }}
            >
              {t.action.label}
            </a>
          )}
          <button
            aria-label="Dismiss"
            onClick={() => setToasts((prev) => prev.filter((x) => x.id !== t.id))}
            style={{
              border: 'none',
              background: 'transparent',
              color: 'var(--text-tertiary)',
              cursor: 'pointer',
              padding: 2,
              display: 'grid',
              placeItems: 'center',
            }}
          >
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none">
              <path d="M18 6 6 18M6 6l12 12" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
            </svg>
          </button>
        </div>
      ))}
    </div>
  );
}
