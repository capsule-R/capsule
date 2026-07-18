// Records real-app footage for the Capsule YC demo.
// - Boots the production Next.js build of packages/cloud-web (same-origin API base)
// - Intercepts all /api/v1 calls with realistic demo data (mock-api.mjs)
// - Drives the UI with a smooth injected cursor (cursor.mjs)
// - Flashes a magenta sync marker at t0 of each scene and logs beat offsets,
//   so Remotion can cut frame-exactly (prepare-footage.mjs resolves frames).
//
// Output: capture/out/raw/<scene>.webm + capture/out/timings.json

import { chromium } from 'playwright';
import { spawn, execSync } from 'node:child_process';
import { mkdirSync, writeFileSync, renameSync, readFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { installMockApi, HERO_SESSION } from './mock-api.mjs';
import { CURSOR_INIT, installCursor, cursorMove, cursorClick, beat } from './cursor.mjs';

const __dir = dirname(fileURLToPath(import.meta.url));
const OUT = join(__dir, 'out');
const RAW = join(OUT, 'raw');
mkdirSync(RAW, { recursive: true });

const WEB_DIR = join(__dir, '..', '..', 'packages', 'cloud-web');
const PORT = 3100;
const BASE = `http://localhost:${PORT}`;
const VIEW = { width: 1920, height: 1080 };

// ---------------------------------------------------------------- server ----
async function startServer() {
  const proc = spawn(`npx next start --port ${PORT}`, {
    cwd: WEB_DIR,
    shell: true,
    stdio: 'ignore',
    env: { ...process.env, NEXT_PUBLIC_API_URL: '/api/v1' },
  });
  const deadline = Date.now() + 90_000;
  while (Date.now() < deadline) {
    try {
      const res = await fetch(`${BASE}/login`);
      if (res.ok) return proc;
    } catch {}
    await new Promise((r) => setTimeout(r, 500));
  }
  throw new Error('Next.js server did not become ready on port ' + PORT);
}

function killTree(proc) {
  try { execSync(`taskkill /pid ${proc.pid} /T /F`, { stdio: 'ignore' }); } catch {}
}

// ---------------------------------------------------------------- scenes ----
const timings = { fpsHint: 25, scenes: {} };

async function withScene(browser, name, fn) {
  const context = await browser.newContext({
    viewport: VIEW,
    recordVideo: { dir: RAW, size: VIEW },
    deviceScaleFactor: 1,
  });
  await context.addCookies([
    { name: 'capsule_token', value: 'demo-video-token', domain: 'localhost', path: '/' },
    { name: 'capsule_refresh', value: 'demo-video-refresh', domain: 'localhost', path: '/' },
  ]);
  await context.addInitScript(() => {
    try { localStorage.setItem('capsule_onboarding_done', '1'); } catch {}
  });
  await context.addInitScript(CURSOR_INIT);
  const state = await installMockApi(context);

  // Deterministic fonts: serve Inter + Fragment Mono from local files so
  // capture never depends on Google Fonts availability or latency.
  const FONTS = join(__dir, '..', 'assets', 'fonts');
  await context.route('**/fonts.googleapis.com/**', (route) => {
    const m = route.request().url().match(/__fonts\/(f\d+\.woff2)/);
    if (m) {
      return route.fulfill({ status: 200, contentType: 'font/woff2', body: readFileSync(join(FONTS, m[1])) });
    }
    return route.fulfill({ status: 200, contentType: 'text/css', body: readFileSync(join(FONTS, 'fonts.css'), 'utf8') });
  });
  await context.route('**/fonts.gstatic.com/**', (route) => route.abort());
  // Kill analytics/badges so networkidle settles fast and nothing leaks out.
  await context.route('**/va.vercel-scripts.com/**', (route) => route.abort());
  await context.route('**/_vercel/insights/**', (route) => route.abort());
  await context.route('**/api.producthunt.com/**', (route) => route.abort());

  const page = await context.newPage();
  const beats = [];
  let t0 = 0;
  // Wall-clock time is recorded as a fallback, but the corner flash is the
  // authoritative signal: Playwright's webm timeline compresses during static
  // holds, so wall offsets drift ~1s by the end of a clip.
  const mark = async (n) => {
    beats.push({ name: n, t: Date.now() - t0 });
    try {
      await page.evaluate(() => window.__beatFlash && window.__beatFlash());
    } catch {}
  };

  // helper: flash full-screen sync marker (always trimmed from final cut)
  const syncMarker = async () => {
    t0 = Date.now();
    await page.evaluate(() => {
      const m = document.createElement('div');
      m.id = '__sync';
      Object.assign(m.style, {
        position: 'fixed', inset: '0', background: '#FF00FF', zIndex: '2147483647',
      });
      document.documentElement.appendChild(m);
      setTimeout(() => m.remove(), 240);
    });
    await page.waitForTimeout(400); // marker gone, page settled
    await mark('visual_start');
  };

  console.log(`[scene] ${name} — recording`);
  await fn({ page, state, mark, syncMarker });

  await mark('scene_end'); // flash before the tail so the encoder flushes it
  await page.waitForTimeout(1200);
  const video = page.video();
  await context.close(); // finalizes video file
  const tmpPath = await video.path();
  const finalPath = join(RAW, `${name}.webm`);
  renameSync(tmpPath, finalPath);
  timings.scenes[name] = { file: `raw/${name}.webm`, beats };
  console.log(`[scene] ${name} — saved (${beats.map((b) => `${b.name}@${b.t}ms`).join(', ')})`);
}

const ready = async (page) => {
  await page.waitForLoadState('networkidle');
  await page.evaluate(() => document.fonts.ready);
};

// ------------------------------------------------------------------ main ----
const server = await startServer();
console.log('[server] production app ready at', BASE);

const browser = await chromium.launch({
  headless: true,
  args: ['--force-color-profile=srgb', '--hide-scrollbars', '--disable-lcd-text'],
});

try {
  // SCENE A — overview → sessions list → failed session → inspect steps
  await withScene(browser, 'inspect', async ({ page, mark, syncMarker }) => {
    await page.goto(`${BASE}/dashboard`, { waitUntil: 'networkidle' });
    await ready(page);
    await page.waitForSelector('text=Recent sessions');
    await installCursor(page, 1250, 420);
    await syncMarker();

    await beat(page, 1400); // overview beauty shot (stats + bar chart)

    const sessionsNav = page.getByRole('link', { name: 'Sessions', exact: true });
    await cursorClick(page, sessionsNav, { ms: 850 });
    await mark('nav_click'); // jump-cut out point (loading state gets spliced out)
    await page.waitForSelector('tr.clickable');
    await mark('sessions_loaded'); // jump-cut in point: rows just rendered
    await ready(page);
    await beat(page, 1500);

    const heroRow = page.locator('tr.clickable').first();
    await cursorMove(page, heroRow, { ms: 750 });
    await beat(page, 350);
    const heroBox = await heroRow.boundingBox();
    await mark('hero_click'); // flash BEFORE navigation so it survives teardown
    await beat(page, 260);
    await page.evaluate(() => window.__cursorClickFx());
    await beat(page, 120);
    // full page navigation (window.location.href)
    await Promise.all([
      page.waitForURL(`**/dashboard/sessions/${HERO_SESSION}`, { waitUntil: 'networkidle' }),
      page.mouse.click(heroBox.x + heroBox.width / 2, heroBox.y + heroBox.height / 2),
    ]);
    await page.waitForSelector('text=tool_call · stripe.create_refund');
    await mark('detail_loaded'); // jump-cut in point: trace fully rendered
    await ready(page);
    await beat(page, 2100); // auto-selected failing step, red error box visible

    // inspect the hallucination step (2nd llm_call · gpt-4o row = step 4)
    const llmRow = page.locator('.sd-step-list').getByText('llm_call · gpt-4o').nth(1);
    await cursorClick(page, llmRow, { ms: 800 });
    await mark('inspect_llm');
    await beat(page, 2400); // response JSON shows amount: 124900

    // back to the failing tool call
    const errRow = page.locator('.sd-step-list').getByText('tool_call · stripe.create_refund');
    await cursorClick(page, errRow, { ms: 700 });
    await mark('inspect_error');
    await beat(page, 4000); // red ERROR box + stack trace
  });

  // SCENE B — the aha: deterministic replay
  await withScene(browser, 'replay', async ({ page, mark, syncMarker }) => {
    await page.goto(`${BASE}/dashboard/sessions/${HERO_SESSION}`, { waitUntil: 'networkidle' });
    await ready(page);
    await page.waitForSelector('text=tool_call · stripe.create_refund');
    await installCursor(page, 380, 500); // near where scene A's cursor ended (step list)
    await syncMarker();

    await beat(page, 1300);
    const replayBtn = page.getByRole('button', { name: 'Replay', exact: true });
    await cursorMove(page, replayBtn, { ms: 900 });
    await beat(page, 250);
    await mark('replay_click');
    await page.evaluate(() => window.__cursorClickFx());
    await beat(page, 120);
    await replayBtn.click();
    await page.waitForSelector('text=Replaying…');

    await page.waitForSelector('text=Replay complete — deterministic ✓', { timeout: 20_000 });
    await mark('replay_banner');
    await beat(page, 1200);

    // glide down to the verbatim CLI output in the banner
    const stdoutPre = page.locator('pre', { hasText: 'Result: deterministic' });
    await cursorMove(page, stdoutPre, { ms: 900, offsetY: -20 });
    await mark('stdout_view');
    await beat(page, 5800); // let the viewer read: 5/5 steps, integrity ✓
  });
} finally {
  await browser.close();
  killTree(server);
}

writeFileSync(join(OUT, 'timings.json'), JSON.stringify(timings, null, 2));
console.log('[done] wrote', join(OUT, 'timings.json'));
