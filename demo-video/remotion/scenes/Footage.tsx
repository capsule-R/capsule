import React from 'react';
import { AbsoluteFill, OffthreadVideo, Sequence, staticFile, useVideoConfig } from 'remotion';
import { LowerThird } from '../components/LowerThird';
import { T } from '../theme';

export interface ClipInfo {
  file: string;
  fps: number;
  durationSec: number;
  beats: Record<string, number>; // frame-exact seconds on the raw video timeline
}

export interface JumpCut {
  outBeat: string; // leave the raw timeline here (+outPad)…
  inBeat: string; // …and resume here — splices loading states out
  outPad?: number; // seconds kept after outBeat (e.g. to show the click ripple)
}

export interface OverlaySpec {
  fromBeat: string;
  toBeat: string;
  fromOffset?: number; // frames
  toOffset?: number;
  text: string;
  strong?: string;
}

/** Comp-frame spans for a clip with jump cuts applied. */
export const clipSegments = (clip: ClipInfo, cuts: JumpCut[], fps: number) => {
  const start = clip.beats.visual_start;
  const segs: { compFrom: number; videoFromSec: number; frames: number }[] = [];
  let videoAt = start;
  let compAt = 0;
  for (const c of cuts) {
    const out = clip.beats[c.outBeat] + (c.outPad ?? 0.15);
    const frames = Math.round((out - videoAt) * fps);
    segs.push({ compFrom: compAt, videoFromSec: videoAt, frames });
    compAt += frames;
    videoAt = clip.beats[c.inBeat];
  }
  segs.push({
    compFrom: compAt,
    videoFromSec: videoAt,
    frames: Math.round((clip.beats.scene_end - videoAt) * fps),
  });
  return segs;
};

/** Total comp frames the clip fills after cuts. */
export const clipSpanFrames = (clip: ClipInfo, cuts: JumpCut[], fps: number) =>
  clipSegments(clip, cuts, fps).reduce((a, s) => a + s.frames, 0);

/** Video-second beat → comp frame, accounting for spliced-out spans. */
export const beatToFrame = (clip: ClipInfo, cuts: JumpCut[], fps: number, beat: string, offset = 0) => {
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

// Plays a captured real-app clip at 1.0x, cut at the sync-marker beat, with
// loading states spliced out via jump cuts; lower thirds are timed off the
// frame-exact interaction beats so copy always matches what's on screen.
export const FootageScene: React.FC<{
  clip: ClipInfo | null;
  cuts?: JumpCut[];
  overlays: OverlaySpec[];
}> = ({ clip, cuts = [], overlays }) => {
  const { fps } = useVideoConfig();

  if (!clip || !clip.file) {
    return (
      <AbsoluteFill
        style={{
          backgroundColor: T.bgBase,
          justifyContent: 'center',
          alignItems: 'center',
          fontFamily: T.fontMono,
          fontSize: 28,
          color: T.textTertiary,
        }}
      >
        footage missing — run `npm run capture` first
      </AbsoluteFill>
    );
  }

  const segs = clipSegments(clip, cuts, fps);

  return (
    <AbsoluteFill style={{ backgroundColor: T.bgBase }}>
      {segs.map((s, i) => (
        <Sequence key={i} from={s.compFrom} durationInFrames={s.frames} layout="none">
          <AbsoluteFill>
            <OffthreadVideo
              src={staticFile(clip.file)}
              startFrom={Math.round(s.videoFromSec * fps)}
              muted
              style={{ width: '100%', height: '100%', objectFit: 'cover' }}
            />
          </AbsoluteFill>
        </Sequence>
      ))}
      {/* covers the 20px beat-flash corner; matches the page background */}
      <div
        style={{
          position: 'absolute',
          right: 0,
          bottom: 0,
          width: 26,
          height: 26,
          backgroundColor: T.bgBase,
        }}
      />
      {overlays.map((o, i) => (
        <LowerThird
          key={i}
          text={o.text}
          strong={o.strong}
          from={beatToFrame(clip, cuts, fps, o.fromBeat, o.fromOffset ?? 6)}
          to={beatToFrame(clip, cuts, fps, o.toBeat, o.toOffset ?? -6)}
        />
      ))}
    </AbsoluteFill>
  );
};
