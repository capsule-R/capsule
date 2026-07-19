import manifest from '../remotion/footage-manifest.json' with { type: 'json' };

const clipsForCuts = manifest.scenes;
const INSPECT_CUTS = [
  { outBeat: 'nav_click', inBeat: 'sessions_loaded', outPad: 0.0 },
  { outBeat: 'hero_click', inBeat: 'detail_loaded', outPad: 0.1 },
];
const REPLAY_CUTS = [];

const clipSegments = (clip, cuts, fps) => {
  const start = clip.beats.visual_start;
  const segs = [];
  let videoAt = start;
  let compAt = 0;
  for (const c of cuts) {
    const out = clip.beats[c.outBeat] + (c.outPad ?? 0.15);
    const frames = Math.round((out - videoAt) * fps);
    segs.push({ compFrom: compAt, videoFromSec: videoAt, frames });
    compAt += frames;
    videoAt = clip.beats[c.inBeat];
  }
  segs.push({ compFrom: compAt, videoFromSec: videoAt, frames: Math.round((clip.beats.scene_end - videoAt) * fps) });
  return segs;
};
const clipSpanFrames = (clip, cuts, fps) => clipSegments(clip, cuts, fps).reduce((a, s) => a + s.frames, 0);
const beatToFrame = (clip, cuts, fps, beat, offset = 0) => {
  const v = clip.beats[beat];
  const segs = clipSegments(clip, cuts, fps);
  for (const s of segs) {
    const end = s.videoFromSec + s.frames / fps;
    if (v <= end + 1e-6) {
      const clamped = Math.max(v, s.videoFromSec);
      return s.compFrom + Math.round((clamped - s.videoFromSec) * fps) + offset;
    }
  }
  const last = segs[segs.length - 1];
  return last.compFrom + last.frames + offset;
};

const span = (name, fallback) => {
  const c = clipsForCuts[name];
  if (!c) return fallback;
  return clipSpanFrames(c, name === 'inspect' ? INSPECT_CUTS : REPLAY_CUTS, 30);
};

let inspectDur = Math.min(span('inspect', 510), 520);
let replayDur = Math.min(span('replay', 426), 432);
let closingDur = 1800 - 636 - inspectDur - replayDur;
if (closingDur < 210) {
  let cut = 210 - closingDur;
  const cutI = Math.min(cut, Math.max(0, inspectDur - 480));
  inspectDur -= cutI;
  cut -= cutI;
  replayDur -= cut;
  closingDur = 210;
}
if (closingDur > 258) {
  const addI = Math.min(closingDur - 258, Math.max(0, span('inspect', 510) - inspectDur));
  inspectDur += addI;
  const addR = Math.min(closingDur - 258 - addI, Math.max(0, span('replay', 426) - replayDur));
  replayDur += addR;
  closingDur = 1800 - 636 - inspectDur - replayDur;
}

const CUTS = {
  hook: { from: 0, dur: 180 },
  install: { from: 180, dur: 246 },
  capture: { from: 426, dur: 210 },
  inspect: { from: 636, dur: inspectDur },
  replay: { from: 636 + inspectDur, dur: replayDur },
  closing: { from: 636 + inspectDur + replayDur, dur: closingDur },
};

const fps = 30;
const toSec = (f) => (f / fps).toFixed(2);

console.log('=== Scene boundaries (frames / seconds) ===');
for (const [name, c] of Object.entries(CUTS)) {
  console.log(`${name}: frame ${c.from}-${c.from + c.dur}  (${toSec(c.from)}s - ${toSec(c.from + c.dur)}s)`);
}

console.log('\n=== Inspect beats (comp frame -> seconds) ===');
for (const beat of Object.keys(manifest.scenes.inspect.beats)) {
  const f = CUTS.inspect.from + beatToFrame(clipsForCuts.inspect, INSPECT_CUTS, 30, beat);
  console.log(`  ${beat}: frame ${f} (${toSec(f)}s)`);
}

console.log('\n=== Replay beats (comp frame -> seconds) ===');
for (const beat of Object.keys(manifest.scenes.replay.beats)) {
  const f = CUTS.replay.from + beatToFrame(clipsForCuts.replay, REPLAY_CUTS, 30, beat);
  console.log(`  ${beat}: frame ${f} (${toSec(f)}s)`);
}
