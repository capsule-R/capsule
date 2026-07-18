import React from 'react';
import { AbsoluteFill, Sequence, interpolate, useCurrentFrame } from 'remotion';
import manifest from './footage-manifest.json';
import { Fonts } from './Fonts';
import { Hook } from './scenes/Hook';
import { Install } from './scenes/Install';
import { Capture } from './scenes/Capture';
import { FootageScene, ClipInfo, JumpCut, clipSpanFrames } from './scenes/Footage';
import { Closing } from './scenes/Closing';
import { T } from './theme';

// ------------------------------------------------------------ timeline ----
// 60.0s @ 30fps = 1800 frames. Footage scenes play at 1.0x, so their slot
// lengths are derived from the actual clip beat spans (frame-exact); the
// closing card absorbs the remainder, kept between 7.0 and 8.6 seconds.
const clipsForCuts = manifest.scenes as unknown as Record<string, ClipInfo | null>;

// Splice the app's loading states out of the footage (cursor position is
// identical on both sides of each cut, so the splice is invisible).
const INSPECT_CUTS: JumpCut[] = [
  { outBeat: 'nav_click', inBeat: 'sessions_loaded', outPad: 0.15 },
  { outBeat: 'hero_click', inBeat: 'detail_loaded', outPad: 0.45 },
];
const REPLAY_CUTS: JumpCut[] = [];

const span = (name: string, fallback: number) => {
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
} as const;

const FadeEdges: React.FC<{ dur: number; inF?: number; outF?: number; children: React.ReactNode }> = ({
  dur,
  inF = 8,
  outF = 8,
  children,
}) => {
  const frame = useCurrentFrame();
  const opacity =
    interpolate(frame, [0, inF], [0, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }) *
    interpolate(frame, [dur - outF, dur], [1, 0], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });
  return (
    <AbsoluteFill style={{ backgroundColor: T.bgBase }}>
      <AbsoluteFill style={{ opacity }}>{children}</AbsoluteFill>
    </AbsoluteFill>
  );
};

const clips = manifest.scenes as unknown as Record<string, ClipInfo | null>;

export const Main: React.FC = () => (
  <AbsoluteFill style={{ backgroundColor: T.bgBase }}>
    <Fonts />

    <Sequence from={CUTS.hook.from} durationInFrames={CUTS.hook.dur} name="1 · Hook">
      <FadeEdges dur={CUTS.hook.dur}>
        <Hook />
      </FadeEdges>
    </Sequence>

    <Sequence from={CUTS.install.from} durationInFrames={CUTS.install.dur} name="2 · Install">
      <FadeEdges dur={CUTS.install.dur}>
        <Install />
      </FadeEdges>
    </Sequence>

    <Sequence from={CUTS.capture.from} durationInFrames={CUTS.capture.dur} name="3 · Capture">
      <FadeEdges dur={CUTS.capture.dur}>
        <Capture />
      </FadeEdges>
    </Sequence>

    <Sequence from={CUTS.inspect.from} durationInFrames={CUTS.inspect.dur} name="4 · Inspect (real app)">
      <FadeEdges dur={CUTS.inspect.dur} inF={10} outF={4}>
        <FootageScene
          clip={clips.inspect ?? null}
          cuts={INSPECT_CUTS}
          overlays={[
            {
              fromBeat: 'visual_start',
              toBeat: 'sessions_loaded',
              fromOffset: 10,
              text: 'The Capsule dashboard — every agent run, captured.',
              strong: 'every agent run',
            },
            {
              fromBeat: 'sessions_loaded',
              toBeat: 'detail_loaded',
              text: 'A production failure, 8 minutes ago.',
              strong: 'production failure',
            },
            {
              fromBeat: 'detail_loaded',
              toBeat: 'inspect_llm',
              text: 'The complete execution — every prompt, tool call, and token.',
            },
            {
              fromBeat: 'inspect_llm',
              toBeat: 'inspect_error',
              text: 'Step 4: the model hallucinated $1,249.00. The real charge: $124.90.',
              strong: '$1,249.00',
            },
            {
              fromBeat: 'inspect_error',
              toBeat: 'scene_end',
              text: 'Step 5: Stripe rejects it. That’s the bug.',
              strong: 'That’s the bug.',
            },
          ]}
        />
      </FadeEdges>
    </Sequence>

    <Sequence from={CUTS.replay.from} durationInFrames={CUTS.replay.dur} name="5 · Replay (the aha)">
      <FadeEdges dur={CUTS.replay.dur} inF={4} outF={8}>
        <FootageScene
          clip={clips.replay ?? null}
          cuts={REPLAY_CUTS}
          overlays={[
            {
              fromBeat: 'visual_start',
              toBeat: 'replay_click',
              fromOffset: 8,
              toOffset: 10,
              text: 'Now replay it — no API keys, no network, no randomness.',
              strong: 'replay it',
            },
            {
              fromBeat: 'replay_click',
              toBeat: 'replay_banner',
              fromOffset: 16,
              toOffset: -2,
              text: 'Re-executing every step from the .capsule file…',
            },
            {
              fromBeat: 'replay_banner',
              toBeat: 'stdout_view',
              fromOffset: 6,
              toOffset: 24,
              text: 'Deterministic — the exact same failure, every time.',
              strong: 'exact same failure',
            },
            {
              fromBeat: 'stdout_view',
              toBeat: 'scene_end',
              fromOffset: 32,
              text: '5/5 steps byte-identical. Integrity verified.',
              strong: 'byte-identical.',
            },
          ]}
        />
      </FadeEdges>
    </Sequence>

    <Sequence from={CUTS.closing.from} durationInFrames={CUTS.closing.dur} name="6 · Closing">
      <FadeEdges dur={CUTS.closing.dur} outF={12}>
        <Closing />
      </FadeEdges>
    </Sequence>
  </AbsoluteFill>
);
