'use client';

import { useState, useEffect, useRef, type ReactNode } from 'react';
import { DashboardShell } from '@/components/DashboardShell';

const NAV = [
  { id: 'quickstart', label: 'Quick Start' },
  { id: 'sdk', label: 'SDK Reference' },
  { id: 'cli', label: 'CLI Reference' },
  { id: 'api', label: 'REST API' },
  { id: 'format', label: '.capsule Format' },
  { id: 'integrations', label: 'Integrations' },
  { id: 'config', label: 'Configuration' },
];

function Code({ children, lang = '' }: { children: string; lang?: string }) {
  const [copied, setCopied] = useState(false);
  return (
    <div style={{ position: 'relative', marginTop: 12, marginBottom: 4 }}>
      <pre style={{
        background: 'var(--mono-bg)',
        border: '1px solid var(--border-subtle)',
        borderRadius: 8,
        padding: '14px 16px',
        fontSize: 13,
        fontFamily: 'var(--font-mono)',
        color: 'var(--mono-text)',
        overflowX: 'auto',
        lineHeight: 1.65,
        whiteSpace: 'pre',
      }}>
        <code>{children}</code>
      </pre>
      <button
        onClick={() => { navigator.clipboard.writeText(children); setCopied(true); setTimeout(() => setCopied(false), 1800); }}
        style={{
          position: 'absolute', top: 10, right: 10,
          background: 'var(--bg-elevated)', border: '1px solid var(--border-default)',
          borderRadius: 5, padding: '3px 9px', fontSize: 11.5,
          color: 'var(--text-tertiary)', cursor: 'pointer',
          fontFamily: 'var(--font-body)',
        }}
      >
        {copied ? 'Copied' : 'Copy'}
      </button>
    </div>
  );
}

function Param({ name, type, required, children }: { name: string; type: string; required?: boolean; children: ReactNode }) {
  return (
    <div style={{ padding: '12px 0', borderBottom: '1px solid var(--border-subtle)', display: 'flex', gap: 16, flexWrap: 'wrap' }}>
      <div style={{ minWidth: 180 }}>
        <span style={{ fontFamily: 'var(--font-mono)', fontSize: 13, color: 'var(--text-primary)' }}>{name}</span>
        {required && <span style={{ marginLeft: 6, fontSize: 11, color: 'var(--error)', fontWeight: 500 }}>required</span>}
      </div>
      <div style={{ flex: 1, minWidth: 200 }}>
        <span style={{ fontFamily: 'var(--font-mono)', fontSize: 12, color: '#a78bfa', display: 'block', marginBottom: 4 }}>{type}</span>
        <span style={{ fontSize: 13.5, color: 'var(--text-secondary)', lineHeight: 1.6 }}>{children}</span>
      </div>
    </div>
  );
}

function H2({ id, children }: { id: string; children: ReactNode }) {
  return (
    <h2 id={id} style={{ fontSize: 22, fontWeight: 600, letterSpacing: '-0.02em', marginTop: 52, marginBottom: 16, paddingTop: 20, color: 'var(--text-primary)' }}>
      {children}
    </h2>
  );
}

function H3({ children }: { children: ReactNode }) {
  return (
    <h3 style={{ fontSize: 15.5, fontWeight: 600, letterSpacing: '-0.01em', marginTop: 32, marginBottom: 10, color: 'var(--text-primary)' }}>
      {children}
    </h3>
  );
}

function P({ children }: { children: ReactNode }) {
  return <p style={{ color: 'var(--text-secondary)', fontSize: 14.5, lineHeight: 1.75, marginBottom: 12 }}>{children}</p>;
}

function Chip({ children, color }: { children: string; color?: string }) {
  return (
    <span style={{
      display: 'inline-block', padding: '2px 8px',
      background: color ? `${color}22` : 'var(--bg-elevated)',
      border: `1px solid ${color ? `${color}44` : 'var(--border-default)'}`,
      borderRadius: 4, fontSize: 11.5, fontFamily: 'var(--font-mono)',
      color: color || 'var(--text-secondary)',
    }}>
      {children}
    </span>
  );
}

function Table({ headers, rows }: { headers: string[]; rows: (string | ReactNode)[][] }) {
  return (
    <div style={{ overflowX: 'auto', marginTop: 12, marginBottom: 4 }}>
      <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13.5 }}>
        <thead>
          <tr>
            {headers.map((h) => (
              <th key={h} style={{ textAlign: 'left', padding: '8px 12px', borderBottom: '1px solid var(--border-default)', color: 'var(--text-tertiary)', fontWeight: 500, fontSize: 12, letterSpacing: '0.04em', textTransform: 'uppercase' }}>{h}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, i) => (
            <tr key={i}>
              {row.map((cell, j) => (
                <td key={j} style={{ padding: '9px 12px', borderBottom: '1px solid var(--border-subtle)', color: 'var(--text-secondary)', verticalAlign: 'top', fontFamily: j === 0 ? 'var(--font-mono)' : undefined, fontSize: j === 0 ? 13 : 13.5 }}>{cell}</td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export default function DocsPage() {
  const [activeSection, setActiveSection] = useState('quickstart');
  const contentRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        for (const entry of entries) {
          if (entry.isIntersecting) {
            setActiveSection(entry.target.id);
            break;
          }
        }
      },
      { rootMargin: '-20% 0px -70% 0px' }
    );
    NAV.forEach(({ id }) => {
      const el = document.getElementById(id);
      if (el) observer.observe(el);
    });
    return () => observer.disconnect();
  }, []);

  return (
    <DashboardShell active="docs" title="Documentation">
      <div style={{ display: 'flex', gap: 0, minHeight: 'calc(100vh - 64px)', alignItems: 'flex-start' }}>

        {/* Left sticky nav */}
        <aside style={{
          width: 200,
          flexShrink: 0,
          position: 'sticky',
          top: 0,
          maxHeight: 'calc(100vh - 64px)',
          overflowY: 'auto',
          paddingTop: 32,
          paddingBottom: 32,
          borderRight: '1px solid var(--border-subtle)',
        }}>
          <nav style={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
            {NAV.map(({ id, label }) => (
              <a
                key={id}
                href={`#${id}`}
                onClick={(e) => { e.preventDefault(); document.getElementById(id)?.scrollIntoView({ behavior: 'smooth' }); setActiveSection(id); }}
                style={{
                  padding: '7px 16px',
                  fontSize: 13.5,
                  borderRadius: 6,
                  color: activeSection === id ? 'var(--text-primary)' : 'var(--text-secondary)',
                  background: activeSection === id ? 'var(--bg-elevated)' : 'transparent',
                  fontWeight: activeSection === id ? 500 : 400,
                  textDecoration: 'none',
                  transition: 'color 0.15s',
                }}
              >
                {label}
              </a>
            ))}
          </nav>
        </aside>

        {/* Main content */}
        <div ref={contentRef} style={{ flex: 1, maxWidth: 820, padding: '32px 40px 80px', overflowY: 'auto' }}>

          {/* ── QUICK START ── */}
          <H2 id="quickstart">Quick Start</H2>
          <P>Wrap any Python agent in three lines. Every run is captured as a replayable <code style={{ fontFamily: 'var(--font-mono)', fontSize: 13, color: 'var(--text-primary)' }}>.capsule</code> file automatically.</P>

          <H3>1. Install the SDK</H3>
          <Code lang="bash">pip install capsule-sdk</Code>
          <P>For provider auto-patching, install optional extras:</P>
          <Code lang="bash">pip install "capsule-sdk[openai]"          # OpenAI
pip install "capsule-sdk[anthropic]"       # Anthropic
pip install "capsule-sdk[langchain]"       # LangChain + LangGraph
pip install "capsule-sdk[openai,anthropic]" # multiple providers</Code>

          <H3>2. Wrap your agent</H3>
          <Code lang="python">import capsule

@capsule.trace(agent_name="my-agent", agent_version="1.0.0")
def run_agent(query: str) -> str:
    # your existing agent code — no other changes needed
    response = openai_client.chat.completions.create(...)
    return response.choices[0].message.content

# async agents are supported too
@capsule.trace(agent_name="async-agent")
async def run_async_agent(query: str) -> str:
    ...</Code>

          <H3>3. Connect to your workspace</H3>
          <P>Set your API key (found in <b>Settings → API Keys</b>) and workspace ID:</P>
          <Code lang="bash">export CAPSULE_API_KEY="csk_your_key_here"
export CAPSULE_WORKSPACE_ID="your_workspace_id"</Code>
          <P>Or pass them at trace time with <code style={{ fontFamily: 'var(--font-mono)', fontSize: 13 }}>auto_upload=True</code> for automatic upload after each run.</P>

          <H3>4. Run your agent</H3>
          <P>Every invocation is now captured. Check the Sessions tab in your dashboard to see replays, step-by-step traces, and cost breakdowns.</P>

          <H3>Context manager (manual sessions)</H3>
          <P>For more control, use the <code style={{ fontFamily: 'var(--font-mono)', fontSize: 13 }}>Session</code> context manager directly:</P>
          <Code lang="python">import capsule
from capsule import Session

with Session(agent_name="pipeline", tags=["prod"]) as session:
    # session.session_id available here
    result = run_step_one()
    run_step_two(result)

# session is finalized and exported to ~/.capsule/ on exit
capsule_path = session.export("./my_run.capsule")</Code>

          {/* ── SDK REFERENCE ── */}
          <H2 id="sdk">SDK Reference</H2>

          <H3>@capsule.trace</H3>
          <P>Decorator that wraps sync or async functions. Each invocation creates and finalizes a Session automatically.</P>
          <Code lang="python">@capsule.trace(
    agent_name="my-agent",       # shown in dashboard
    agent_version="2.1.0",       # optional semver
    tags=["prod", "gpt-4o"],     # filter in dashboard
    user_metadata={"user_id": "u_123"},  # arbitrary KV pairs
    redact=["api_key", "ssn"],   # keys to redact from payloads
    auto_upload=True,            # upload to cloud after each run
    storage_backend=None,        # custom backend (default: SQLite)
)
def my_agent(query: str) -> str: ...</Code>

          <div style={{ marginTop: 16 }}>
            <Param name="agent_name" type="str | None">Display name shown in the dashboard. Defaults to the decorated function name.</Param>
            <Param name="agent_version" type="str | None">Semver string stored in the session manifest. Useful for comparing versions.</Param>
            <Param name="tags" type="list[str] | None">Labels attached to every session from this agent. Filterable in the dashboard and CLI.</Param>
            <Param name="user_metadata" type="dict | None">Arbitrary key–value pairs stored in session metadata. Not redacted by default.</Param>
            <Param name="redact" type="list[str] | None">Key names to scrub from all event payloads before storage. Applied recursively.</Param>
            <Param name="auto_upload" type="bool">When <code style={{ fontFamily: 'var(--font-mono)', fontSize: 12 }}>True</code>, automatically uploads the session to the cloud workspace after finalization. Requires <code style={{ fontFamily: 'var(--font-mono)', fontSize: 12 }}>CAPSULE_API_KEY</code> and <code style={{ fontFamily: 'var(--font-mono)', fontSize: 12 }}>CAPSULE_WORKSPACE_ID</code> to be set.</Param>
          </div>

          <H3>Session class</H3>
          <P>Use <code style={{ fontFamily: 'var(--font-mono)', fontSize: 13 }}>Session</code> directly when you need lower-level control or want to capture events from multiple call sites.</P>
          <Code lang="python">from capsule import Session, get_current_session

# sync context manager
with Session(agent_name="pipeline", tags=["batch"]) as s:
    print(s.session_id)  # ULID string, e.g. "01J2..."

# async context manager
async with Session(agent_name="async-pipeline") as s:
    await run_steps()

# access the active session from anywhere in the call stack
current = get_current_session()  # returns Session | None</Code>

          <H3>Session methods</H3>
          <Table
            headers={['Method', 'Returns', 'Description']}
            rows={[
              ['session.session_id', 'str', 'Unique ULID identifier for this session.'],
              ['session.metadata', 'SessionMetadata', 'Current metadata snapshot (counts, cost, status).'],
              ['session.events', 'list[Event]', 'All captured events so far.'],
              ['session.capture_event(event)', 'None', 'Manually append an Event to the session.'],
              ['session.export(path)', 'Path', 'Write a .capsule file to disk. Returns the resolved Path.'],
              ['session.finalize(status, error)', 'None', 'Close the session with a given SessionStatus. Called automatically by the context manager.'],
            ]}
          />

          <H3>Event types</H3>
          <P>Capsule automatically captures these event types via provider patches. You can also emit them manually via <code style={{ fontFamily: 'var(--font-mono)', fontSize: 13 }}>session.capture_event()</code>.</P>
          <Table
            headers={['EventType', 'Captured from', 'Key payload fields']}
            rows={[
              ['LLM_CALL', 'OpenAI / Anthropic / Google patches', 'provider, model, messages, response, tokens, cost'],
              ['TOOL_CALL', 'LangChain Tool / manual', 'tool_name, arguments, result, duration_ms'],
              ['MEMORY_WRITE', 'Manual or LangGraph', 'memory_type, key, value'],
              ['MEMORY_READ', 'Manual or LangGraph', 'memory_type, key, result'],
              ['USER_MESSAGE', 'Manual', 'content, role'],
              ['ERROR', 'Auto on exception', 'error_type, message, traceback'],
            ]}
          />

          <H3>SessionStatus values</H3>
          <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', marginTop: 8 }}>
            <Chip color="#22C55E">SUCCESS</Chip>
            <Chip color="#EF4444">FAILED</Chip>
            <Chip color="#A0A0A0">CANCELLED</Chip>
            <Chip color="#F59E0B">IN_PROGRESS</Chip>
          </div>

          {/* ── CLI REFERENCE ── */}
          <H2 id="cli">CLI Reference</H2>
          <P>The <code style={{ fontFamily: 'var(--font-mono)', fontSize: 13 }}>capsule</code> CLI is included with the SDK. Sessions are stored locally in <code style={{ fontFamily: 'var(--font-mono)', fontSize: 13 }}>~/.capsule/sessions.db</code> (SQLite).</P>

          <H3>Session commands</H3>
          <Table
            headers={['Command', 'Description']}
            rows={[
              ['capsule list [--agent NAME] [--status STATUS] [--limit N] [--json]', 'List captured sessions with optional filters.'],
              ['capsule show <session_id> [--json]', 'Display full session details and step-by-step event trace.'],
              ['capsule replay <session_id|file> [--mode cassette|live] [--json]', 'Replay a session. cassette mode uses recorded LLM responses for deterministic replay. live mode re-runs against live APIs.'],
              ['capsule branch <session_id> --from-step N [--modify key=value]', 'Fork a session at step N. Use --modify to override a payload field before replaying.'],
              ['capsule diff <id1> <id2>', 'Side-by-side diff of two sessions (inputs, outputs, costs, step counts).'],
              ['capsule export <session_id> [-o output.capsule]', 'Export session to a .capsule file.'],
              ['capsule import <file.capsule>', 'Import a .capsule file into local storage.'],
              ['capsule delete <session_id> [--yes]', 'Delete a session. Prompts for confirmation unless --yes is passed.'],
            ]}
          />

          <H3>Cloud commands</H3>
          <Table
            headers={['Command', 'Description']}
            rows={[
              ['capsule upload <session_id> --api-key KEY --workspace ID', 'Upload a local session to your cloud workspace.'],
              ['capsule cloud login --url URL --api-key KEY --workspace ID', 'Save cloud credentials to ~/.capsule/config.toml.'],
              ['capsule cloud status', 'Show current cloud connection status and workspace info.'],
            ]}
          />

          <H3>Examples</H3>
          <Code lang="bash"># List last 10 failed sessions for the "research-agent"
capsule list --agent research-agent --status failed --limit 10

# Replay session 01J2... using cassettes (deterministic)
capsule replay 01J2ABC --mode cassette

# Branch at step 3 and override the system prompt
capsule branch 01J2ABC --from-step 3 --modify "messages[0].content=You are a concise assistant"

# Diff two sessions side by side
capsule diff 01J2ABC 01J2XYZ

# Upload to cloud
capsule upload 01J2ABC --api-key csk_xxx --workspace ws_yyy</Code>

          {/* ── REST API ── */}
          <H2 id="api">REST API</H2>
          <P>Base URL: <code style={{ fontFamily: 'var(--font-mono)', fontSize: 13 }}>https://api.capsule.dev/api/v1</code></P>
          <P>All authenticated endpoints require a Bearer token in the <code style={{ fontFamily: 'var(--font-mono)', fontSize: 13 }}>Authorization</code> header:</P>
          <Code lang="bash">curl -H "Authorization: Bearer csk_your_key" \
     https://api.capsule.dev/api/v1/workspaces</Code>

          <H3>Authentication</H3>
          <Table
            headers={['Method', 'Endpoint', 'Description']}
            rows={[
              ['POST', '/auth/signup', 'Create account. Body: {email, password, full_name?}'],
              ['POST', '/auth/login', 'Get access + refresh tokens. Body: {email, password}'],
              ['POST', '/auth/refresh', 'Exchange refresh token for a new access token.'],
              ['GET', '/auth/me', 'Return the authenticated user profile.'],
              ['PATCH', '/auth/me', 'Update profile. Body: {full_name?, email?}'],
              ['POST', '/auth/change-password', 'Body: {current_password, new_password}'],
              ['POST', '/auth/forgot-password', 'Send reset link. Body: {email}'],
              ['POST', '/auth/reset-password', 'Body: {token, new_password}'],
            ]}
          />

          <H3>Sessions</H3>
          <P>All session endpoints are scoped to a workspace: <code style={{ fontFamily: 'var(--font-mono)', fontSize: 13 }}>/workspaces/{'{'}{'}'}workspace_id{'{'}{'}'}/sessions</code></P>
          <Table
            headers={['Method', 'Endpoint', 'Description']}
            rows={[
              ['POST', '/sessions', 'Upload a .capsule file. Multipart: file (binary), metadata (JSON).'],
              ['GET', '/sessions', 'List sessions. Query: limit, cursor, agent_name, status.'],
              ['GET', '/sessions/stats?days=30', 'Aggregate stats (totals, failure rate, token spend) for N days.'],
              ['GET', '/sessions/{id}', 'Full session detail including metadata and event count.'],
              ['GET', '/sessions/{id}/events', 'All events for a session as a JSON array.'],
              ['GET', '/sessions/{id}/download', 'Download the original .capsule binary.'],
              ['DELETE', '/sessions/{id}', 'Delete a session. Returns 204.'],
              ['POST', '/sessions/{id}/replay', 'Trigger a replay. Body: {mode: "cassette"|"live", branch_from_step?, modifications?}'],
            ]}
          />

          <H3>API Keys</H3>
          <Table
            headers={['Method', 'Endpoint', 'Description']}
            rows={[
              ['POST', '/workspaces/{id}/api-keys', 'Create a key. Body: {name}. Returns full key once — store it securely.'],
              ['GET', '/workspaces/{id}/api-keys', 'List keys (prefix + metadata, never the full key).'],
              ['DELETE', '/workspaces/{id}/api-keys/{key_id}', 'Revoke a key. Returns 204.'],
            ]}
          />

          <H3>TokenResponse shape</H3>
          <Code lang="json">{"{"}"access_token": "eyJ...", "refresh_token": "eyJ...",
 "token_type": "bearer", "expires_in": 3600{"}"}</Code>

          {/* ── .CAPSULE FORMAT ── */}
          <H2 id="format">.capsule Format</H2>
          <P>A <code style={{ fontFamily: 'var(--font-mono)', fontSize: 13 }}>.capsule</code> file is a <b>zstd-compressed tar archive</b> containing a deterministic, integrity-checked snapshot of a session.</P>

          <H3>Archive structure</H3>
          <Code>{`my_run.capsule (zstd-compressed tar)
├── manifest.json          # version, integrity hashes, producer info
├── session.json           # SessionMetadata (agent, status, cost, token totals)
├── events/
│   ├── 0001-llm_call.json
│   ├── 0002-tool_call.json
│   └── ...
├── cassettes/
│   └── {cassette_id}.json # recorded API responses for replay
└── snapshots/
    ├── step-0001.json     # memory state after each step
    └── ...`}</Code>

          <H3>manifest.json</H3>
          <Code lang="json">{`{
  "capsule_version": "1.0",
  "format_spec_url": "https://capsule.dev/spec/v1.0",
  "created_at": "2026-05-30T12:00:00Z",
  "session_id": "01J2ABCDEF...",
  "integrity": {
    "algorithm": "sha256",
    "events_hash": "abc123...",
    "cassettes_hash": "def456...",
    "snapshots_hash": "ghi789..."
  },
  "compression": { "algorithm": "zstd", "level": 3 },
  "producer": {
    "sdk_name": "capsule-python",
    "sdk_version": "0.1.0",
    "platform": "linux",
    "python_version": "3.11.9"
  }
}`}</Code>

          <H3>File size limits by plan</H3>
          <Table
            headers={['Plan', 'Max file size', 'Sessions / month']}
            rows={[
              ['Hobby (free)', '100 MB', '1,000'],
              ['Pro', '500 MB', '50,000'],
              ['Enterprise', '5 GB', 'Unlimited'],
            ]}
          />

          {/* ── INTEGRATIONS ── */}
          <H2 id="integrations">Integrations</H2>
          <P>Capsule auto-patches supported providers when you use <code style={{ fontFamily: 'var(--font-mono)', fontSize: 13 }}>@capsule.trace</code>. No code changes to your LLM calls are required.</P>

          <H3>OpenAI</H3>
          <Code lang="python">pip install "capsule-sdk[openai]"</Code>
          <Code lang="python">import capsule
import openai

client = openai.OpenAI()  # auto-patched when capsule is imported

@capsule.trace(agent_name="openai-agent")
def run(query: str) -> str:
    resp = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": query}],
    )
    return resp.choices[0].message.content</Code>
          <P>Capsule patches <code style={{ fontFamily: 'var(--font-mono)', fontSize: 13 }}>openai.OpenAI</code> and <code style={{ fontFamily: 'var(--font-mono)', fontSize: 13 }}>openai.AsyncOpenAI</code>. Recorded cassettes enable deterministic replay without hitting the API.</P>

          <H3>Anthropic</H3>
          <Code lang="python">pip install "capsule-sdk[anthropic]"</Code>
          <Code lang="python">import capsule
import anthropic

client = anthropic.Anthropic()  # auto-patched

@capsule.trace(agent_name="claude-agent")
def run(query: str) -> str:
    msg = client.messages.create(
        model="claude-opus-4-8",
        max_tokens=1024,
        messages=[{"role": "user", "content": query}],
    )
    return msg.content[0].text</Code>

          <H3>LangChain</H3>
          <Code lang="python">pip install "capsule-sdk[langchain]"</Code>
          <Code lang="python">import capsule
from langchain_openai import ChatOpenAI
from langchain.agents import AgentExecutor

@capsule.trace(agent_name="lc-agent")
def run_chain(query: str) -> str:
    llm = ChatOpenAI(model="gpt-4o")
    # All LangChain Tool calls and LLM calls are captured automatically
    executor = AgentExecutor(agent=..., tools=[...], llm=llm)
    return executor.invoke({"input": query})["output"]</Code>

          <H3>LangGraph</H3>
          <Code lang="python">pip install "capsule-sdk[langchain]"  # includes langgraph hooks</Code>
          <Code lang="python">import capsule
from langgraph.graph import StateGraph

@capsule.trace(agent_name="langgraph-agent")
async def run_graph(state: dict) -> dict:
    graph = StateGraph(...)
    app = graph.compile()
    return await app.ainvoke(state)</Code>

          <H3>Manual event capture</H3>
          <P>For unsupported providers, emit events directly:</P>
          <Code lang="python">from capsule import get_current_session
from capsule.core.models import Event, EventType, ToolCallPayload
from datetime import datetime, timezone

session = get_current_session()
if session:
    session.capture_event(Event(
        event_id="evt_01J2...",
        session_id=session.session_id,
        step_index=session.next_step_index(),
        event_type=EventType.TOOL_CALL,
        timestamp=datetime.now(timezone.utc),
        duration_ms=142.5,
        payload=ToolCallPayload(
            tool_name="web_search",
            arguments={"query": "capsule replay debugger"},
            result={"snippets": [...]},
        ),
    ))</Code>

          {/* ── CONFIGURATION ── */}
          <H2 id="config">Configuration</H2>

          <H3>Environment variables</H3>
          <Table
            headers={['Variable', 'Default', 'Description']}
            rows={[
              ['CAPSULE_API_KEY', '—', 'Cloud API key (prefix csk_). Required for auto_upload and capsule upload.'],
              ['CAPSULE_WORKSPACE_ID', '—', 'Target workspace for uploads.'],
              ['CAPSULE_CLOUD_URL', 'https://api.capsule.dev', 'Override cloud API base URL (e.g. for self-hosted).'],
              ['CAPSULE_DISABLE', '0', 'Set to 1/true/yes to disable all capture. Useful in test environments.'],
              ['CAPSULE_ENABLED', '1', 'Alias for inverted CAPSULE_DISABLE.'],
            ]}
          />

          <H3>Disabling capture in tests</H3>
          <Code lang="bash"># pytest.ini or .env.test
CAPSULE_DISABLE=1</Code>
          <Code lang="python"># Or programmatically
import os
os.environ["CAPSULE_DISABLE"] = "1"

import capsule  # no-ops from here on</Code>

          <H3>Local storage</H3>
          <P>Sessions are stored in <code style={{ fontFamily: 'var(--font-mono)', fontSize: 13 }}>~/.capsule/sessions.db</code> (SQLite). Cloud credentials saved via <code style={{ fontFamily: 'var(--font-mono)', fontSize: 13 }}>capsule cloud login</code> are stored in <code style={{ fontFamily: 'var(--font-mono)', fontSize: 13 }}>~/.capsule/config.toml</code>.</P>
          <P>To reset local storage: <code style={{ fontFamily: 'var(--font-mono)', fontSize: 13 }}>rm ~/.capsule/sessions.db</code>. This does not affect sessions already uploaded to the cloud.</P>

          <div style={{ marginTop: 64, paddingTop: 32, borderTop: '1px solid var(--border-subtle)', display: 'flex', gap: 20, fontSize: 13.5, color: 'var(--text-tertiary)' }}>
            <span>Questions? Email <a href="mailto:support@capsule.dev" style={{ color: 'var(--text-secondary)' }}>support@capsule.dev</a></span>
            <span>·</span>
            <a href="/terms" style={{ color: 'var(--text-secondary)' }}>Terms</a>
            <span>·</span>
            <a href="/privacy" style={{ color: 'var(--text-secondary)' }}>Privacy</a>
          </div>

        </div>
      </div>
    </DashboardShell>
  );
}
