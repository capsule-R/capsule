// Virtual camera for footage scenes: keyframed zoom + pan over a 1920×1080
// plane, with professional easing, a whisper of idle "breathing" so static
// holds feel alive, and screen-space projection so overlays track the zooming
// UI. All motion is deterministic (frame-driven).

export interface CamKey {
  f: number; // comp frame
  zoom: number; // 1.0 = full frame
  fx: number; // focal point x in video px (also the scale origin)
  fy: number; // focal point y in video px
}

export interface CamSample {
  zoom: number;
  fx: number;
  fy: number;
}

const clamp = (v: number, lo: number, hi: number) => Math.max(lo, Math.min(hi, v));
const lerp = (a: number, b: number, t: number) => a + (b - a) * t;

// easeInOutCubic — the workhorse curve for confident, non-linear camera moves.
export const easeInOutCubic = (t: number) =>
  t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2;

/** Sample the camera at a comp frame by easing between keyframes. */
export function sampleCam(frame: number, keys: CamKey[]): CamSample {
  if (keys.length === 0) return { zoom: 1, fx: 960, fy: 540 };
  if (frame <= keys[0].f) return { zoom: keys[0].zoom, fx: keys[0].fx, fy: keys[0].fy };
  const last = keys[keys.length - 1];
  if (frame >= last.f) return { zoom: last.zoom, fx: last.fx, fy: last.fy };

  let a = keys[0];
  let b = keys[1];
  for (let i = 0; i < keys.length - 1; i++) {
    if (frame >= keys[i].f && frame <= keys[i + 1].f) {
      a = keys[i];
      b = keys[i + 1];
      break;
    }
  }
  const span = Math.max(1, b.f - a.f);
  const e = easeInOutCubic(clamp((frame - a.f) / span, 0, 1));
  return {
    zoom: lerp(a.zoom, b.zoom, e),
    fx: lerp(a.fx, b.fx, e),
    fy: lerp(a.fy, b.fy, e),
  };
}

// Idle breathing — a barely-perceptible drift layered on top of the base
// sample so held shots never feel frozen. Amplitude is deliberately tiny.
export function breathe(frame: number, base: CamSample): CamSample {
  return {
    zoom: base.zoom * (1 + 0.0035 * Math.sin(frame / 42)),
    fx: base.fx + 5 * Math.sin(frame / 74),
    fy: base.fy + 4 * Math.cos(frame / 91),
  };
}

/** Project a point in video space to on-screen px under a camera sample. */
export function projectPoint(px: number, py: number, cam: CamSample): { x: number; y: number } {
  return {
    x: cam.fx + (px - cam.fx) * cam.zoom,
    y: cam.fy + (py - cam.fy) * cam.zoom,
  };
}

/** Motion-blur amount (px) from camera velocity — peaks mid-move, ~0 at rest. */
export function motionBlur(prev: CamSample, cur: CamSample): number {
  const dPan = Math.hypot(cur.fx - prev.fx, cur.fy - prev.fy) / 1920;
  const dZoom = Math.abs(cur.zoom - prev.zoom) * 3;
  const v = dPan + dZoom; // ~0..0.05 for our moves
  return clamp(v * 42, 0, 1.6);
}
