# Capsule — YC Demo Video Storyboard (60s @ 1920x1080, 30fps = 1800 frames)

Tone: direct, technical, zero fluff. Every overlay is a claim a developer can verify.

| # | Time | Scene | Content | Overlay copy |
|---|------|-------|---------|--------------|
| 1 | 0:00–0:06 | Hook (motion card) | Dark brand background. Problem statement types in, then product name. | "Your AI agent failed in production." → "Run it again — you get a *different* failure." → **Capsule — deterministic replay for AI agents** |
| 2 | 0:06–0:14 | Install + instrument (terminal + code) | Real terminal: `pip install capsule-trace` completes. Cut to editor card: real decorator on real example agent code. | "One dependency." / "One decorator. Your agent code doesn't change." |
| 3 | 0:14–0:21 | Capture (terminal) | Agent runs; SDK prints real capture output; session id appears; `.capsule` file written. | "Every LLM call, tool call, and memory op — captured." |
| 4 | 0:21–0:37 | Inspect (REAL app footage) | Dashboard sessions list → cursor clicks the failed session → trace timeline → expand the failing step, see exact prompt/response. | "The full execution, step by step." / "Here's the exact call that failed." |
| 5 | 0:37–0:52 | Replay — THE AHA (real app + terminal beat) | Cursor clicks Replay. Status runs → completes → outputs identical, deterministic verdict. No API key, no network. | "Replay it. No API calls. No randomness." / "Same failure. Every single time." |
| 6 | 0:52–1:00 | Closing card | Brand card, two lines land with weight, then logo + install command. | "Traditional observability tells you **what** happened." → "Capsule lets you **replay exactly** what happened." → `pip install capsule-trace` |

## Rules
- Footage scenes 4–5 come from the REAL Next.js app (Playwright, mocked API data, injected smooth cursor). No fake UI.
- Terminal scenes replicate the SDK's real output strings verbatim (pulled from `packages/sdk` source).
- Overlays: lower-third style, brand accent color, enter/exit with 8–12 frame spring, never cover the cursor's target.
- All timings deterministic; captured footage is timed to match scene windows exactly.
