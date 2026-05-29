/**
 * Capsule API client — handles auth tokens and authenticated fetch.
 * Tokens are stored as first-party cookies so middleware can read them
 * without JS (edge runtime).
 */

const API_BASE =
  process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

const TOKEN_COOKIE  = 'capsule_token';
const REFRESH_COOKIE = 'capsule_refresh';

// ── Cookie helpers ────────────────────────────────────────────

function getCookie(name: string): string | null {
  if (typeof document === 'undefined') return null;
  for (const part of document.cookie.split(';')) {
    const [k, ...rest] = part.trim().split('=');
    if (k === name) return decodeURIComponent(rest.join('='));
  }
  return null;
}

function setCookie(name: string, value: string, maxAgeSeconds: number): void {
  document.cookie = `${name}=${encodeURIComponent(value)}; path=/; max-age=${maxAgeSeconds}; SameSite=Lax`;
}

function deleteCookie(name: string): void {
  document.cookie = `${name}=; path=/; max-age=0`;
}

// ── Token management ──────────────────────────────────────────

export function getToken(): string | null {
  return getCookie(TOKEN_COOKIE);
}

export function setTokens(access: string, refresh: string): void {
  const week = 60 * 60 * 24 * 7;
  setCookie(TOKEN_COOKIE, access, week);
  setCookie(REFRESH_COOKIE, refresh, week);
}

export function clearTokens(): void {
  deleteCookie(TOKEN_COOKIE);
  deleteCookie(REFRESH_COOKIE);
}

// ── Auth calls ────────────────────────────────────────────────

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  expires_in: number;
}

export async function login(
  email: string,
  password: string,
): Promise<{ data?: TokenResponse; error?: string }> {
  try {
    const res = await fetch(`${API_BASE}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password }),
    });
    const json = await res.json();
    if (!res.ok) return { error: json.detail ?? 'Login failed' };
    setTokens(json.access_token, json.refresh_token);
    return { data: json as TokenResponse };
  } catch {
    return { error: 'Network error — is the API running?' };
  }
}

export async function signup(
  email: string,
  password: string,
  full_name: string,
): Promise<{ data?: TokenResponse; error?: string }> {
  try {
    const res = await fetch(`${API_BASE}/auth/signup`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password, full_name }),
    });
    const json = await res.json();
    if (!res.ok) return { error: json.detail ?? 'Signup failed' };
    setTokens(json.access_token, json.refresh_token);
    return { data: json as TokenResponse };
  } catch {
    return { error: 'Network error — is the API running?' };
  }
}

// ── Authenticated fetch ───────────────────────────────────────

export async function apiFetch(
  path: string,
  opts: RequestInit = {},
): Promise<Response> {
  const token = getToken();
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(opts.headers as Record<string, string> | undefined),
  };
  if (token) headers['Authorization'] = `Bearer ${token}`;
  return fetch(`${API_BASE}${path}`, { ...opts, headers });
}
