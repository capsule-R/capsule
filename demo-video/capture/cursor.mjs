// Injects a macOS-style cursor overlay into the page and animates it smoothly.
// All motion is driven by requestAnimationFrame inside the page so it appears
// in Playwright's video capture. Timings are deterministic.

export const CURSOR_INIT = `
(() => {
  if (window.__capsuleCursor) return;
  const install = () => {
  if (window.__capsuleCursor) return;
  const el = document.createElement('div');
  el.id = '__capsule-cursor';
  el.innerHTML = \`<svg width="26" height="30" viewBox="0 0 26 30" fill="none" xmlns="http://www.w3.org/2000/svg">
    <path d="M2 1.5 L2 23 L7.5 18 L11 27 L15 25.4 L11.6 16.7 L19 16.2 Z"
      fill="white" stroke="black" stroke-width="1.6" stroke-linejoin="round"/>
  </svg>\`;
  Object.assign(el.style, {
    position: 'fixed', left: '0px', top: '0px', zIndex: '2147483647',
    pointerEvents: 'none', filter: 'drop-shadow(0 2px 5px rgba(0,0,0,0.45))',
    transform: 'translate(-2px, -2px)', willChange: 'left, top',
  });
  document.documentElement.appendChild(el);
  let sx = 960, sy = 540;
  try {
    const saved = JSON.parse(localStorage.getItem('__cursorPos') || 'null');
    if (saved) { sx = saved.x; sy = saved.y; }
  } catch {}
  window.__capsuleCursor = { el, x: sx, y: sy };
  el.style.left = sx + 'px'; el.style.top = sy + 'px';
  const save = () => { try { localStorage.setItem('__cursorPos', JSON.stringify({ x: window.__capsuleCursor.x, y: window.__capsuleCursor.y })); } catch {} };

  window.__cursorMoveTo = (tx, ty, ms) => new Promise((resolve) => {
    const c = window.__capsuleCursor;
    const sx = c.x, sy = c.y;
    const dx = tx - sx, dy = ty - sy;
    const start = performance.now();
    // easeInOutCubic — reads as a confident human hand
    const ease = (t) => (t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2);
    const step = (now) => {
      const t = Math.min(1, (now - start) / ms);
      const e = ease(t);
      // slight arc so long moves don't look robotic-linear
      const arc = Math.sin(Math.PI * t) * Math.min(24, Math.hypot(dx, dy) * 0.05);
      const nx = sx + dx * e;
      const ny = sy + dy * e - arc;
      c.el.style.left = nx + 'px';
      c.el.style.top = ny + 'px';
      c.x = nx; c.y = ny;
      if (t < 1) requestAnimationFrame(step);
      else { c.x = tx; c.y = ty; c.el.style.left = tx + 'px'; c.el.style.top = ty + 'px'; save(); resolve(); }
    };
    requestAnimationFrame(step);
  });

  window.__cursorClickFx = () => {
    const c = window.__capsuleCursor;
    const r = document.createElement('div');
    Object.assign(r.style, {
      position: 'fixed', left: (c.x - 18) + 'px', top: (c.y - 18) + 'px',
      width: '36px', height: '36px', borderRadius: '50%',
      border: '2.5px solid rgba(245, 245, 245, 0.9)',
      zIndex: '2147483646', pointerEvents: 'none',
      animation: '__capsuleRipple 420ms ease-out forwards',
    });
    if (!document.getElementById('__capsule-ripple-style')) {
      const s = document.createElement('style');
      s.id = '__capsule-ripple-style';
      s.textContent = '@keyframes __capsuleRipple { from { transform: scale(0.35); opacity: 0.95; } to { transform: scale(1.55); opacity: 0; } }';
      document.head.appendChild(s);
    }
    document.documentElement.appendChild(r);
    setTimeout(() => r.remove(), 500);
    // press feedback on the cursor itself
    c.el.style.transition = 'transform 90ms ease';
    c.el.style.transform = 'translate(-2px, -2px) scale(0.85)';
    setTimeout(() => { c.el.style.transform = 'translate(-2px, -2px) scale(1)'; }, 110);
  };
  // Beat flash: 20x20 swatch in the bottom-right corner, detected
  // frame-exactly by prepare-footage.mjs and covered by a dark patch in the
  // Remotion composition. Deterministic ground truth for overlay timing.
  window.__beatFlash = () => {
    const b = document.createElement('div');
    Object.assign(b.style, {
      position: 'fixed', right: '0px', bottom: '0px', width: '20px', height: '20px',
      backgroundColor: '#FF00C8', zIndex: '2147483647', pointerEvents: 'none',
    });
    document.documentElement.appendChild(b);
    setTimeout(() => b.remove(), 160);
  };
  };
  if (document.documentElement) install();
  else document.addEventListener('DOMContentLoaded', install);
})();
`;

/** Ensure the cursor exists on the current document (call after each navigation). */
export async function installCursor(page, x = 960, y = 540) {
  await page.evaluate(CURSOR_INIT);
  await page.evaluate(([px, py]) => {
    const c = window.__capsuleCursor;
    c.x = px; c.y = py;
    c.el.style.left = px + 'px';
    c.el.style.top = py + 'px';
  }, [x, y]);
}

/** Smoothly move the injected cursor to the center of a locator (or x/y), then optionally click for real. */
export async function cursorMove(page, target, { ms = 700, offsetX = 0, offsetY = 0 } = {}) {
  let x, y;
  if (typeof target === 'object' && 'x' in target) {
    ({ x, y } = target);
  } else {
    const box = await target.boundingBox();
    if (!box) throw new Error('cursorMove: target has no bounding box');
    x = box.x + box.width / 2 + offsetX;
    y = box.y + box.height / 2 + offsetY;
  }
  await page.evaluate(([tx, ty, dur]) => window.__cursorMoveTo(tx, ty, dur), [x, y, ms]);
  return { x, y };
}

export async function cursorClick(page, target, opts = {}) {
  const { x, y } = await cursorMove(page, target, opts);
  await page.waitForTimeout(opts.settle ?? 160);
  await page.evaluate(() => window.__cursorClickFx());
  await page.waitForTimeout(90);
  await page.mouse.click(x, y);
}

/** Human-feel pause helper (deterministic). */
export const beat = (page, ms) => page.waitForTimeout(ms);
