// One-off: screenshot the landing page #demo section for visual verification.
import { chromium } from 'playwright';
import { spawn, execSync } from 'node:child_process';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const __dir = dirname(fileURLToPath(import.meta.url));
const WEB_DIR = join(__dir, '..', '..', 'packages', 'cloud-web');
const PORT = 3101;

const proc = spawn(`npx next start --port ${PORT}`, { cwd: WEB_DIR, shell: true, stdio: 'ignore' });
const deadline = Date.now() + 90_000;
let up = false;
while (Date.now() < deadline && !up) {
  try { up = (await fetch(`http://localhost:${PORT}/`)).ok; } catch {}
  if (!up) await new Promise((r) => setTimeout(r, 500));
}
if (!up) throw new Error('server not ready');

const browser = await chromium.launch({ headless: true, args: ['--hide-scrollbars'] });
const page = await browser.newPage({ viewport: { width: 1600, height: 1000 } });
await page.goto(`http://localhost:${PORT}/#demo`, { waitUntil: 'networkidle' });
await page.evaluate(() => document.fonts.ready);
await page.locator('#demo').scrollIntoViewIfNeeded();
await page.waitForTimeout(1200); // reveal animation
await page.screenshot({ path: join(__dir, 'out', 'landing-demo-section.png') });
await browser.close();
try { execSync(`taskkill /pid ${proc.pid} /T /F`, { stdio: 'ignore' }); } catch {}
console.log('shot saved');
