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

export function setTokens(access: string, refresh: string, accessExpiresIn = 3600): void {
  // Access token cookie expires with the token itself; refresh token lives 30 days.
  const month = 60 * 60 * 24 * 30;
  setCookie(TOKEN_COOKIE,   access,  accessExpiresIn);
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
    setTokens(json.access_token, json.refresh_token, json.expires_in);
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
    setTokens(json.access_token, json.refresh_token, json.expires_in);
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

let _refreshing: Promise<boolean> | null = null;

async function _tryRefresh(): Promise<boolean> {
  // Deduplicate concurrent refresh attempts — only one in-flight at a time.
  if (_refreshing) return _refreshing;
  const p = (async (): Promise<boolean> => {
    try {
      const refresh = getCookie(REFRESH_COOKIE);
      if (!refresh) return false;
      const res = await fetch(`${API_BASE}/auth/refresh`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${refresh}` },
      });
      if (!res.ok) return false;
      const data = await res.json();
      setTokens(data.access_token, data.refresh_token, data.expires_in);
      return true;
    } catch {
      return false;
    } finally {
      _refreshing = null;
    }
  })();
  _refreshing = p;
  return p;
}

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
  const res = await fetch(`${API_BASE}${path}`, { ...opts, headers });

  // On 401, attempt a token refresh once and retry the original request.
  if (res.status === 401 && token) {
    const refreshed = await _tryRefresh();
    if (refreshed) {
      const newToken = getToken();
      const retryHeaders = { ...headers };
      if (newToken) retryHeaders['Authorization'] = `Bearer ${newToken}`;
      return fetch(`${API_BASE}${path}`, { ...opts, headers: retryHeaders });
    }
    // Refresh failed — clear tokens so middleware redirects to /login.
    clearTokens();
    _userCache = null;
    if (typeof window !== 'undefined') window.location.href = '/login';
  }

  return res;
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

// ── Workspaces ────────────────────────────────────────────────

export interface WorkspaceInfo {
  id: string;
  name: string;
  slug: string;
  owner_id: string;
  plan_tier: string;
  retention_days: number;
  storage_used_bytes: number;
  storage_quota_bytes: number;
  created_at: string;
}

/** Result of resolving the user's primary workspace. */
export type WorkspaceResult =
  | { status: 'ok'; workspace: WorkspaceInfo }
  | { status: 'none' }      // authenticated but no workspace exists yet
  | { status: 'error' };    // network / API failure

export async function getPrimaryWorkspace(): Promise<WorkspaceResult> {
  try {
    const res = await apiFetch('/workspaces');
    if (!res.ok) return { status: 'error' };
    const list = (await res.json()) as WorkspaceInfo[];
    if (!Array.isArray(list) || list.length === 0) return { status: 'none' };
    return { status: 'ok', workspace: list[0] };
  } catch {
    return { status: 'error' };
  }
}

// ── Session stats (dashboard overview) ────────────────────────

export interface SessionStats {
  total: number;
  failed: number;
  total_cost_usd: number;
  total_input_tokens: number;
  total_output_tokens: number;
  range_days: number;
  daily: { date: string; count: number }[];
}

export async function getSessionStats(
  workspaceId: string,
  days: number,
): Promise<SessionStats | null> {
  try {
    const res = await apiFetch(`/workspaces/${workspaceId}/sessions/stats?days=${days}`);
    if (!res.ok) return null;
    return (await res.json()) as SessionStats;
  } catch {
    return null;
  }
}

// ── Capsule download ──────────────────────────────────────────

/** Download a session's raw `.capsule` archive (sends the auth header, then
 *  triggers a browser file download). */
export async function downloadSessionCapsule(
  workspaceId: string,
  sessionId: string,
): Promise<{ error?: string }> {
  try {
    const res = await apiFetch(`/workspaces/${workspaceId}/sessions/${sessionId}/download`);
    if (!res.ok) {
      const detail = await res.json().catch(() => null);
      return { error: detail?.detail ?? 'Download failed' };
    }
    const blob = await res.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${sessionId}.capsule`;
    document.body.appendChild(a);
    a.click();
    a.remove();
    URL.revokeObjectURL(url);
    return {};
  } catch {
    return { error: 'Network error — is the API running?' };
  }
}

// ── Capsule upload (multipart) ────────────────────────────────

export interface UploadedSession {
  id: string;
  workspace_id: string;
  agent_name: string;
  agent_version: string | null;
  started_at: string | null;
  duration_ms: number | null;
  status: string;
  step_count: number;
  total_cost_usd: number;
  storage_size_bytes: number;
  tags: string[];
  uploaded_at: string;
  view_url: string | null;
}

/** POST multipart without forcing a JSON content-type (browser sets the boundary). */
async function apiUploadForm(path: string, form: FormData): Promise<Response> {
  const token = getToken();
  const headers: Record<string, string> = {};
  if (token) headers['Authorization'] = `Bearer ${token}`;
  return fetch(`${API_BASE}${path}`, { method: 'POST', body: form, headers });
}

/** Upload a .capsule file. The backend expects multipart parts named
 *  `metadata` (JSON string) and `file` (the binary archive). */
export async function uploadCapsuleFile(
  workspaceId: string,
  file: File,
  agentName: string,
  tags: string[],
): Promise<{ data?: UploadedSession; error?: string; status?: number }> {
  // session_id must match ^[a-zA-Z0-9_-]+$ on the backend
  const sessionId = file.name
    .replace(/\.capsule$/i, '')
    .replace(/[^a-zA-Z0-9_-]/g, '-')
    .slice(0, 128) || 'session';

  const form = new FormData();
  form.append(
    'metadata',
    JSON.stringify({ session_id: sessionId, agent_name: agentName || sessionId, tags }),
  );
  form.append('file', file, file.name);

  try {
    const res = await apiUploadForm(`/workspaces/${workspaceId}/sessions`, form);
    if (res.status === 201) {
      return { data: (await res.json()) as UploadedSession, status: 201 };
    }
    const detail = await res.json().catch(() => null);
    return { error: detail?.detail ?? `Upload failed (${res.status})`, status: res.status };
  } catch {
    return { error: 'Network error — is the API running?' };
  }
}

// ── Replay ────────────────────────────────────────────────────

export interface ReplayResult {
  is_deterministic: boolean;
  replayed_steps: number;
  original_steps: number;
  stdout?: string;
}

export interface ReplayStatus {
  replay_id: string;
  status: 'queued' | 'running' | 'completed' | 'failed';
  result: ReplayResult | null;
  error: string | null;
}

export async function startReplay(
  workspaceId: string,
  sessionId: string,
): Promise<{ replayId?: string; error?: string }> {
  try {
    const res = await apiFetch(`/workspaces/${workspaceId}/sessions/${sessionId}/replay`, {
      method: 'POST',
      body: JSON.stringify({ mode: 'cassette' }),
    });
    const json = await res.json().catch(() => null);
    if (!res.ok) return { error: json?.detail ?? `Replay failed (${res.status})` };
    return { replayId: json.id ?? json.replay_id };
  } catch {
    return { error: 'Network error — is the API running?' };
  }
}

export async function getReplayStatus(replayId: string): Promise<ReplayStatus | null> {
  try {
    const res = await apiFetch(`/replays/${replayId}`);
    if (!res.ok) return null;
    return (await res.json()) as ReplayStatus;
  } catch {
    return null;
  }
}

// ── Branches ──────────────────────────────────────────────────

export async function createBranch(
  workspaceId: string,
  sessionId: string,
  fromStep: number,
  note: string,
): Promise<{ branchId?: string; error?: string }> {
  try {
    const res = await apiFetch(`/workspaces/${workspaceId}/sessions/${sessionId}/branch`, {
      method: 'POST',
      body: JSON.stringify({ from_step: fromStep, note: note || null }),
    });
    const json = await res.json().catch(() => null);
    if (!res.ok) return { error: json?.detail ?? `Branch failed (${res.status})` };
    return { branchId: json.branch_id };
  } catch {
    return { error: 'Network error — is the API running?' };
  }
}

// ── Formatting helpers ────────────────────────────────────────

/** Format a USD cost. Sub-cent values keep 4 dp so micro-costs aren't shown as $0.00. */
export function formatUSD(n: number | null | undefined): string {
  const v = Number(n ?? 0);
  if (!isFinite(v) || v <= 0) return '$0.00';
  if (v < 0.01) return `$${v.toFixed(4)}`;
  return `$${v.toFixed(2)}`;
}

export function formatBytes(bytes: number | null | undefined): string {
  const b = Number(bytes ?? 0);
  if (b <= 0) return '0 B';
  const units = ['B', 'KB', 'MB', 'GB', 'TB'];
  const i = Math.max(0, Math.min(units.length - 1, Math.floor(Math.log(b) / Math.log(1024))));
  const val = b / Math.pow(1024, i);
  return `${val >= 100 || i === 0 ? Math.round(val) : val.toFixed(1)} ${units[i]}`;
}

/** Deterministic color for an agent/project name (stable across renders). */
export function agentColor(name: string): string {
  const palette = ['var(--accent)', 'var(--replay)', 'var(--warn)', 'var(--success)'];
  let h = 0;
  for (let i = 0; i < name.length; i++) h = (h * 31 + name.charCodeAt(i)) >>> 0;
  return palette[h % palette.length];
}

export function relativeTime(iso: string | null | undefined): string {
  if (!iso) return '—';
  const t = new Date(iso).getTime();
  if (isNaN(t)) return '—';
  const diff = Date.now() - t;
  const m = Math.floor(diff / 60000);
  if (m < 1) return 'just now';
  if (m < 60) return `${m}m ago`;
  const h = Math.floor(m / 60);
  if (h < 24) return `${h}h ago`;
  const d = Math.floor(h / 24);
  if (d < 30) return `${d}d ago`;
  return new Date(iso).toLocaleDateString();
}
