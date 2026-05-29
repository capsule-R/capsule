/**
 * Capsule API client — handles auth tokens and authenticated fetch.
 *
 * Tokens are stored as plain (non-httpOnly) cookies so the middleware can
 * read them server-side from the Cookie header on every navigation request.
 * They are still scoped to the same origin (SameSite=Lax; path=/).
 */

const API_BASE =
  process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

export const TOKEN_COOKIE   = 'capsule_token';
export const REFRESH_COOKIE = 'capsule_refresh';

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
  // Add Secure flag on HTTPS (production). Omit on HTTP (local dev) so the
  // cookie is still set — browsers silently drop Secure cookies on plain HTTP.
  const secure = window.location.protocol === 'https:' ? '; Secure' : '';
  document.cookie =
    `${name}=${encodeURIComponent(value)}; path=/; max-age=${maxAgeSeconds}; SameSite=Lax${secure}`;
}

function deleteCookie(name: string): void {
  const secure = window.location.protocol === 'https:' ? '; Secure' : '';
  document.cookie = `${name}=; path=/; max-age=0; SameSite=Lax${secure}`;
}

// ── Token management ──────────────────────────────────────────

export function getToken(): string | null {
  return getCookie(TOKEN_COOKIE);
}

export function setTokens(access: string, refresh: string): void {
  const month = 60 * 60 * 24 * 30;
  setCookie(TOKEN_COOKIE,   access,  month);
  setCookie(REFRESH_COOKIE, refresh, month);
}

export function clearTokens(): void {
  deleteCookie(TOKEN_COOKIE);
  deleteCookie(REFRESH_COOKIE);
}

export function logout(): void {
  clearTokens();
  window.location.href = '/login';
}

// ── Auth calls ────────────────────────────────────────────────

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  expires_in: number;
}

export interface UserProfile {
  id: string;
  email: string;
  full_name: string | null;
  avatar_url: string | null;
  created_at: string;
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

export async function forgotPassword(
  email: string,
): Promise<{ message: string; reset_token?: string }> {
  const res = await fetch(`${API_BASE}/auth/forgot-password`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email }),
  });
  return res.json();
}

export async function resetPassword(
  token: string,
  new_password: string,
): Promise<{ message?: string; error?: string }> {
  try {
    const res = await fetch(`${API_BASE}/auth/reset-password`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ token, new_password }),
    });
    const json = await res.json();
    if (!res.ok) return { error: json.detail ?? 'Reset failed' };
    return { message: json.message };
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

// ── User helpers ─────────────────────────────────────────────

let _userCache: UserProfile | null = null;

export async function getCurrentUser(): Promise<UserProfile | null> {
  if (_userCache) return _userCache;
  try {
    const res = await apiFetch('/auth/me');
    if (!res.ok) return null;
    _userCache = await res.json();
    return _userCache;
  } catch {
    return null;
  }
}

export function clearUserCache(): void {
  _userCache = null;
}

// ── Profile management ────────────────────────────────────────

export async function updateProfile(
  data: { full_name?: string; email?: string },
): Promise<{ data?: UserProfile; error?: string }> {
  try {
    const res = await apiFetch('/auth/me', {
      method: 'PATCH',
      body: JSON.stringify(data),
    });
    const json = await res.json();
    if (!res.ok) return { error: json.detail ?? 'Update failed' };
    _userCache = json as UserProfile;
    return { data: json };
  } catch {
    return { error: 'Network error — is the API running?' };
  }
}

export async function changePassword(
  current_password: string,
  new_password: string,
): Promise<{ message?: string; error?: string }> {
  try {
    const res = await apiFetch('/auth/change-password', {
      method: 'POST',
      body: JSON.stringify({ current_password, new_password }),
    });
    const json = await res.json();
    if (!res.ok) return { error: json.detail ?? 'Password change failed' };
    return { message: json.message };
  } catch {
    return { error: 'Network error — is the API running?' };
  }
}
