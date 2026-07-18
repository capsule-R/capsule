// Realistic demo data served to the REAL Capsule dashboard via Playwright route
// interception. Shapes mirror the real backend (packages/cloud-api pydantic
// models) and the exact fields the frontend reads (lib/capsule.ts +
// app/dashboard/sessions/[id]/page.tsx mapping code).
//
// Authenticity notes:
// - Session IDs are bare 26-char ULIDs (SDK: str(ulid.new())).
// - Session status enum: in_progress | success | failed | cancelled.
// - Events carry event_id/session_id/step_index/timestamp like real
//   .capsule event files; the UI reads event_type/duration_ms/payload.
// - Replay verdict matches `capsule-trace replay --json` output fields.

const WS_ID = '01K0FQ2M4KTCX9RW6ZB3HJDVNP';
export const HERO_SESSION = '01K0J8R6PYQV9TCK2M4W7HNDF3';
const REPLAY_ID = '01K0J9T2Z8H4MQXW5VBRC6NPKY';

const iso = (msAgo) => new Date(Date.now() - msAgo).toISOString();
const MIN = 60_000, HOUR = 3_600_000, DAY = 86_400_000;

export const workspace = {
  id: WS_ID,
  name: 'Acme Engineering',
  slug: 'acme-eng',
  owner_id: '01K0APZQ7RM2XW4VB6NCJDHT9F',
  plan_tier: 'pro',
  retention_days: 90,
  storage_used_bytes: 734_003_200,
  storage_quota_bytes: 53_687_091_200,
  created_at: iso(97 * DAY),
};

export const user = {
  id: '01K0APZQ7RM2XW4VB6NCJDHT9F',
  email: 'alex@acme.dev',
  full_name: 'Alex Carter',
  avatar_url: null,
  created_at: iso(97 * DAY),
};

export const heroMeta = {
  id: HERO_SESSION,
  workspace_id: WS_ID,
  status: 'failed',
  agent_name: 'billing-agent',
  agent_version: '1.4.2',
  started_at: iso(8 * MIN + 5160),
  ended_at: iso(8 * MIN),
  step_count: 5,
  duration_ms: 5160,
  total_cost_usd: 0.0148,
  total_input_tokens: 1060,
  total_output_tokens: 105,
  storage_size_bytes: 1_648_000,
  tags: ['production', 'refund'],
  error_type: 'InvalidRequestError',
  error_message: 'Refund amount ($1,249.00) is greater than charge amount ($124.90)',
  uploaded_at: iso(8 * MIN),
  expires_at: iso(-90 * DAY),
  view_url: null,
};

// The story: billing-agent is asked to refund a duplicate $124.90 charge.
// At step 4 the LLM emits amount=124900 (minor units for $1,249.00 — 10x too
// large). Step 5 Stripe rejects it. Non-deterministic in production, exactly
// reproducible under Capsule replay.
const evt = (i, event_type, duration_ms, payload) => ({
  event_id: `01K0J8R7${'ABCDE'[i]}Q2W4V6BXCMNPKT`,
  session_id: HERO_SESSION,
  step_index: i,
  parent_event_id: null,
  event_type,
  timestamp: new Date(Date.now() - 8 * MIN - 5160 + [0, 1900, 2600, 2700, 4950][i]).toISOString(),
  duration_ms,
  payload,
});

export const heroEvents = [
  evt(0, 'llm_call', 1840, {
    provider: 'openai',
    model: 'gpt-4o',
    parameters: { temperature: 0.7, max_tokens: 512 },
    messages: [
      {
        role: 'system',
        content:
          'You are Acme’s billing agent. Resolve billing issues using the tools provided. Always verify charges before refunding.',
      },
      {
        role: 'user',
        content:
          'Customer cus_9XK42M reports a double charge on invoice INV-20260714-0031. Investigate and refund the duplicate.',
      },
    ],
    response: {
      content:
        'Plan:\n1. Look up customer cus_9XK42M and recent charges\n2. Confirm the duplicate charge on INV-20260714-0031\n3. Refund the duplicate charge only\n4. Save case context for audit',
      tool_calls: [],
      finish_reason: 'stop',
      usage: { prompt_tokens: 412, completion_tokens: 74, total_tokens: 486 },
    },
  }),
  evt(1, 'tool_call', 640, {
    tool_name: 'stripe.lookup_customer',
    tool_namespace: 'stripe',
    arguments: { customer_id: 'cus_9XK42M', expand: ['charges'] },
    result: {
      customer: { id: 'cus_9XK42M', name: 'Maya Chen', email: 'maya.chen@northwind.io' },
      charges: [
        { id: 'ch_3PZkQ8Lt2xGa1', amount: 12490, currency: 'usd', invoice: 'INV-20260714-0031', created: '2026-07-14T09:12:44Z' },
        { id: 'ch_3PZkQ9Lt2xGa2', amount: 12490, currency: 'usd', invoice: 'INV-20260714-0031', created: '2026-07-14T09:12:51Z', duplicate_of: 'ch_3PZkQ8Lt2xGa1' },
      ],
    },
  }),
  evt(2, 'memory_write', 30, {
    memory_type: 'scratchpad',
    tool_name: 'case_context',
    key: 'case_context',
    input: {
      key: 'case_context',
      customer: 'cus_9XK42M',
      duplicate_charge: 'ch_3PZkQ9Lt2xGa2',
      amount_usd: 124.9,
    },
    value: 'stored',
    value_type: 'json',
  }),
  evt(3, 'llm_call', 2210, {
    provider: 'openai',
    model: 'gpt-4o',
    parameters: { temperature: 0.7, max_tokens: 256 },
    messages: [
      {
        role: 'user',
        content:
          'Duplicate confirmed: ch_3PZkQ9Lt2xGa2 for $124.90 (12490 minor units). Emit the refund tool call as JSON.',
      },
    ],
    response: {
      content: '{"tool":"stripe.create_refund","charge":"ch_3PZkQ9Lt2xGa2","amount":124900}',
      tool_calls: [],
      finish_reason: 'stop',
      usage: { prompt_tokens: 648, completion_tokens: 31, total_tokens: 679 },
    },
  }),
  evt(4, 'tool_call', 440, {
    tool_name: 'stripe.create_refund',
    tool_namespace: 'stripe',
    arguments: { charge: 'ch_3PZkQ9Lt2xGa2', amount: 124900 },
    error: 'Refund amount ($1,249.00) is greater than charge amount ($124.90)',
    error_type: 'InvalidRequestError',
    stack_trace:
      'stripe.error.InvalidRequestError: Amount 124900 is greater than unrefunded amount on charge 12490\n    at APIRequestor._interpret_response (stripe/api_requestor.py:428)\n    at APIRequestor.request (stripe/api_requestor.py:155)\n    at Refund.create (stripe/api_resources/refund.py:24)\n    at billing_agent.tools.create_refund (agent/tools.py:87)',
  }),
];

const mkSession = (id, agent, status, steps, durMs, cost, agoMs) => ({
  id, workspace_id: WS_ID, status, agent_name: agent, agent_version: '1.4.2',
  started_at: iso(agoMs + durMs), ended_at: iso(agoMs), step_count: steps,
  duration_ms: durMs, total_cost_usd: cost,
  total_input_tokens: Math.round(steps * 480), total_output_tokens: Math.round(steps * 60),
  storage_size_bytes: 1_200_000 + steps * 90_000, tags: [],
  error_type: status === 'failed' ? 'ToolExecutionError' : null,
  error_message: status === 'failed' ? 'db.query returned schema mismatch' : null,
  uploaded_at: iso(agoMs), expires_at: iso(-90 * DAY), view_url: null,
});

export const sessions = [
  heroMeta,
  mkSession('01K0J6V3T8WNQXR2M5BC7HDKPY', 'support-triage', 'success', 12, 14_820, 0.0311, 42 * MIN),
  mkSession('01K0J4H9K2PFXW6VN8BRC3MDQT', 'checkout-agent', 'success', 9, 8_204, 0.0195, 2 * HOUR),
  mkSession('01K0HXT7R4DBQM2W5VK9NCJPHF', 'billing-agent', 'success', 6, 6_112, 0.0164, 5 * HOUR),
  mkSession('01K0HKM2Q9SCVX4W7RB6NDJTPZ', 'research-agent', 'success', 23, 41_390, 0.0872, 9 * HOUR),
  mkSession('01K0G8WF3JHXQV5M2NB9RCKDTY', 'support-triage', 'success', 11, 12_077, 0.0288, 26 * HOUR),
  mkSession('01K0DR5B7VTXWQ4M6NC2HJKPFZ', 'checkout-agent', 'failed', 14, 19_444, 0.0451, 2 * DAY),
  mkSession('01K0BD4N6XZQWV3M5RB8CKJHTP', 'billing-agent', 'success', 7, 7_351, 0.0179, 3 * DAY),
];

export const stats = {
  total: 128,
  failed: 6,
  total_cost_usd: 3.42,
  total_input_tokens: 2_814_600,
  total_output_tokens: 391_240,
  range_days: 7,
  daily: [14, 22, 9, 17, 31, 20, 15].map((count, i) => ({
    date: new Date(Date.now() - (6 - i) * DAY).toISOString().slice(0, 10),
    count,
  })),
};

// Verbatim format of `capsule-trace replay <id> --mode=cassette` (cli/main.py).
export const replayStdout = [
  `Replaying ${HERO_SESSION} (5 steps) in cassette mode...`,
  '',
  'Result: deterministic',
  '  Steps replayed:  5/5',
  '  Integrity check: ✓',
  '  [000] llm_call (cassette)',
  '  [001] tool_call (cassette)',
  '  [002] memory_write',
  '  [003] llm_call (cassette)',
  '  [004] tool_call (cassette)',
].join('\n');

/**
 * Install route interception on a Playwright BrowserContext so the real
 * dashboard renders this demo data. Works for both same-origin (/api/v1)
 * and cross-origin (http://localhost:8000/api/v1) API bases.
 * `state.replayPolls` drives the running -> completed progression.
 */
export async function installMockApi(context) {
  const state = { replayPolls: 0, replayStarted: false };
  const json = (route, body, status = 200) =>
    route.fulfill({
      status,
      contentType: 'application/json',
      headers: { 'access-control-allow-origin': '*' },
      body: JSON.stringify(body),
    });

  await context.route('**/api/v1/**', async (route) => {
    const req = route.request();
    const url = new URL(req.url());
    const path = url.pathname.replace(/^.*\/api\/v1/, '');
    const method = req.method();

    if (method === 'OPTIONS') {
      return route.fulfill({
        status: 204,
        headers: {
          'access-control-allow-origin': '*',
          'access-control-allow-methods': 'GET,POST,PATCH,DELETE,OPTIONS',
          'access-control-allow-headers': 'authorization,content-type',
        },
      });
    }

    if (path === '/auth/me') return json(route, user);
    if (path === '/workspaces') return json(route, [workspace]);
    if (path === `/workspaces/${WS_ID}/sessions/stats`) {
      const days = Number(url.searchParams.get('days') || 30);
      return json(route, { ...stats, range_days: days });
    }
    if (path === `/workspaces/${WS_ID}/sessions`) {
      return json(route, { items: sessions, total: sessions.length, cursor: null });
    }
    if (path === `/workspaces/${WS_ID}/sessions/${HERO_SESSION}`) return json(route, heroMeta);
    if (path === `/workspaces/${WS_ID}/sessions/${HERO_SESSION}/events`) return json(route, heroEvents);
    if (path === `/workspaces/${WS_ID}/sessions/${HERO_SESSION}/replay` && method === 'POST') {
      state.replayStarted = true;
      state.replayPolls = 0;
      return json(route, {
        id: REPLAY_ID,
        session_id: HERO_SESSION,
        status: 'queued',
        replay_mode: 'cassette',
        branch_from_step: null,
        created_at: new Date().toISOString(),
      }, 202);
    }
    if (path === `/replays/${REPLAY_ID}`) {
      state.replayPolls += 1;
      if (state.replayPolls < 2) {
        return json(route, { replay_id: REPLAY_ID, status: 'running', result: null, error: null });
      }
      return json(route, {
        replay_id: REPLAY_ID,
        status: 'completed',
        result: {
          is_deterministic: true,
          integrity_ok: true,
          replayed_steps: 5,
          original_steps: 5,
          stdout: replayStdout,
        },
        error: null,
      });
    }
    if (path === `/workspaces/${WS_ID}/branches`) return json(route, []);

    // Any other scripted session: generic meta, no step-level events.
    const m = path.match(/^\/workspaces\/[A-Z0-9]+\/sessions\/([A-Za-z0-9_-]+)$/);
    if (m) {
      const s = sessions.find((x) => x.id === m[1]);
      if (s) return json(route, s);
    }
    return json(route, { type: 'about:blank', title: 'Not Found', status: 404, detail: 'not mocked' }, 404);
  });

  return state;
}
