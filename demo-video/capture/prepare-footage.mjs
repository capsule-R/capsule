// Post-processes raw Playwright captures into Remotion-ready footage:
// 1. Detects the magenta sync-marker frame in each clip (frame-exact t0)
// 2. Converts beat wall-clock offsets into video-timeline seconds
// 3. Copies clips into public/footage and writes remotion/footage-manifest.json
//
// Uses Remotion's bundled full ffmpeg/ffprobe (npx remotion ffmpeg) — no
// system ffmpeg required.

import { execFileSync } from 'node:child_process';
import { mkdirSync, readFileSync, writeFileSync, copyFileSync, readdirSync, rmSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const __dir = dirname(fileURLToPath(import.meta.url));
const ROOT = join(__dir, '..');
const OUT = join(__dir, 'out');
const RAW = join(OUT, 'raw');
const PUB = join(ROOT, 'public', 'footage');
const TMP = join(OUT, 'marker-tmp');
mkdirSync(PUB, { recursive: true });

const rem = (args, opts = {}) =>
  execFileSync('npx', ['remotion', ...args], { cwd: ROOT, shell: true, encoding: 'utf8', ...opts });

const timings = JSON.parse(readFileSync(join(OUT, 'timings.json'), 'utf8'));
const manifest = { generatedAt: new Date().toISOString(), scenes: {} };

for (const [name, scene] of Object.entries(timings.scenes)) {
  const src = join(OUT, scene.file);

  // --- probe fps + duration
  const probe = JSON.parse(
    rem(['ffprobe', '-v', 'error', '-select_streams', 'v:0',
      '-show_entries', 'stream=r_frame_rate:format=duration', '-of', 'json', `"${src}"`]),
  );
  const [num, den] = probe.streams[0].r_frame_rate.split('/').map(Number);
  const fps = num / den;
  const durationSec = Number(probe.format?.duration ?? 0);

  // --- find the magenta marker frame (scan first ~8s as raw 8x8 RGB frames)
  rmSync(TMP, { recursive: true, force: true });
  mkdirSync(TMP, { recursive: true });
  const rawFile = join(TMP, `${name}.raw`);
  rem(['ffmpeg', '-v', 'error', '-i', `"${src}"`, '-t', '8',
    '-vf', 'scale=8:8', '-c:v', 'rawvideo', '-pix_fmt', 'rgb24', '-f', 'image2pipe', `"${rawFile}"`]);

  const raw = readFileSync(rawFile);
  const FRAME_BYTES = 8 * 8 * 3;
  let markerIdx = -1;
  for (let f = 0; f * FRAME_BYTES + FRAME_BYTES <= raw.length; f++) {
    let r = 0, g = 0, b = 0;
    const base = f * FRAME_BYTES;
    for (let i = 0; i < FRAME_BYTES; i += 3) {
      r += raw[base + i]; g += raw[base + i + 1]; b += raw[base + i + 2];
    }
    const n = FRAME_BYTES / 3;
    r /= n; g /= n; b /= n;
    if (r > 170 && b > 170 && g < 100) {
      markerIdx = f; // 0-based
      break;
    }
  }
  if (markerIdx < 0) {
    throw new Error(`Sync marker not found in ${name} — capture is unusable, re-record.`);
  }
  const markerSec = markerIdx / fps;

  // --- frame-exact beats: detect the bottom-right corner flashes.
  // Wall-clock offsets drift because Playwright's webm timeline compresses
  // during static holds; the flashes are ground truth on the video timeline.
  const cornerFile = join(TMP, `${name}-corner.raw`);
  rem(['ffmpeg', '-v', 'error', '-i', `"${src}"`,
    '-vf', 'crop=20:20:1900:1060,scale=1:1', '-c:v', 'rawvideo', '-pix_fmt', 'rgb24',
    '-f', 'image2pipe', `"${cornerFile}"`]);
  const corner = readFileSync(cornerFile);
  const segments = [];
  let inSeg = false;
  for (let f = 0; f * 3 + 2 < corner.length; f++) {
    const r = corner[f * 3], g = corner[f * 3 + 1], b = corner[f * 3 + 2];
    const hot = r > 150 && b > 100 && g < 90; // #FF00C8 flash or #FF00FF marker
    if (hot && !inSeg) { segments.push({ start: f, end: f }); inSeg = true; }
    else if (hot) segments[segments.length - 1].end = f;
    else inSeg = false;
  }
  // segments[0] must be the full-frame sync marker itself
  if (segments.length !== scene.beats.length + 1) {
    const segInfo = segments.map((s) => `${(s.start / fps).toFixed(2)}s(${s.end - s.start + 1}f)`).join(', ');
    const wallInfo = scene.beats.map((b) => `${b.name}@${(markerSec + b.t / 1000).toFixed(2)}s`).join(', ');
    throw new Error(
      `${name}: expected ${scene.beats.length + 1} corner segments (marker + beats), ` +
      `found ${segments.length} — re-record.\n  segments: ${segInfo}\n  wall-est: marker@${markerSec.toFixed(2)}s, ${wallInfo}`,
    );
  }
  if (Math.abs(segments[0].start - markerIdx) > 3) {
    throw new Error(`${name}: corner segment 0 (${segments[0].start}) does not match full-frame marker (${markerIdx}).`);
  }

  const beats = {};
  scene.beats.forEach((b, i) => {
    beats[b.name] = segments[i + 1].start / fps;
  });

  const pubFile = `footage/${name}.webm`;
  copyFileSync(src, join(ROOT, 'public', 'footage', `${name}.webm`));
  manifest.scenes[name] = { file: pubFile, fps, durationSec, markerSec, beats };
  console.log(
    `[prepare] ${name}: fps=${fps} marker@${markerSec.toFixed(2)}s ` +
    `visual_start@${beats.visual_start?.toFixed(2)}s scene_end@${beats.scene_end?.toFixed(2)}s dur=${durationSec.toFixed(2)}s`,
  );
}

rmSync(TMP, { recursive: true, force: true });
writeFileSync(join(ROOT, 'remotion', 'footage-manifest.json'), JSON.stringify(manifest, null, 2));
console.log('[prepare] wrote remotion/footage-manifest.json');
