import React from 'react';
import { AbsoluteFill, OffthreadVideo, Sequence, staticFile, useCurrentFrame, useVideoConfig } from 'remotion';
import { LowerThird } from '../components/LowerThird';
import { Spotlight } from '../components/Spotlight';
import { Callout } from '../components/Callout';
import { ClickPulse, SuccessConfirm } from '../components/ClickPulse';
import { CamKey, sampleCam, breathe, projectPoint, motionBlur } from '../camera';
import { T } from '../theme';

export interface ClipInfo {
  file: string;
  fps: number;
  durationSec: number;
  beats: Record<string, number>; // frame-exact seconds on the raw video timeline
}

export interface JumpCut {
  outBeat: string;
  inBeat: string;
  outPad?: number;
}

export interface OverlaySpec {
  fromBeat: string;
  toBeat: string;
  fromOffset?: number;
  toOffset?: number;
  text: string;
  strong?: string;
}

// All coordinates below are in VIDEO space (1920×1080); the camera projects
// them to screen space per frame so effects track the zooming UI.
export interface ShotSpec {
  atBeat: string;
  offset?: number;
  zoom: number;
  fx: number;
  fy: number;
}
export interface SpotSpec {
  fromBeat: string;
  toBeat: string;
  fromOffset?: number;
  toOffset?: number;
  x: number;
  y: number;
  rw: number;
  rh: number;
  dim?: number;
}
export interface CalloutSpec {
  fromBeat: string;
  toBeat: string;
  fromOffset?: number;
  toOffset?: number;
  x: number;
  y: number;
  w: number;
  h: number;
  label: string;
  side?: 'top' | 'bottom';
}
export interface PulseSpec {
  atBeat: string;
  offset?: number;
  x: number;
  y: number;
}
export interface ConfirmSpec {
  atBeat: string;
  offset?: number;
  x: number;
  y: number;
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

export const FootageScene: React.FC<{
  clip: ClipInfo | null;
  cuts?: JumpCut[];
  overlays: OverlaySpec[];
  shots?: ShotSpec[];
  spotlights?: SpotSpec[];
  callouts?: CalloutSpec[];
  pulses?: PulseSpec[];
  confirms?: ConfirmSpec[];
}> = ({ clip, cuts = [], overlays, shots = [], spotlights = [], callouts = [], pulses = [], confirms = [] }) => {
  const { fps } = useVideoConfig();
  const frame = useCurrentFrame();

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

  const B = (beat: string, off = 0) => beatToFrame(clip, cuts, fps, beat, off);
  const segs = clipSegments(clip, cuts, fps);

  // ── camera ──────────────────────────────────────────────────────────────
  const keys: CamKey[] = shots.map((s) => ({ f: B(s.atBeat, s.offset ?? 0), zoom: s.zoom, fx: s.fx, fy: s.fy }));
  keys.sort((a, b) => a.f - b.f);
  const hasCam = keys.length > 0;
  const cam = hasCam ? breathe(frame, sampleCam(frame, keys)) : { zoom: 1, fx: 960, fy: 540 };
  const camPrev = hasCam ? breathe(frame - 1, sampleCam(frame - 1, keys)) : cam;
  const blur = hasCam ? motionBlur(camPrev, cam) : 0;
  const proj = (x: number, y: number) => projectPoint(x, y, cam);

  return (
    <AbsoluteFill style={{ backgroundColor: T.bgBase }}>
      {/* camera-transformed world: the footage + a patch over the beat-flash corner */}
      <AbsoluteFill
        style={{
          transform: `scale(${cam.zoom})`,
          transformOrigin: `${cam.fx}px ${cam.fy}px`,
          filter: blur > 0.05 ? `blur(${blur.toFixed(2)}px)` : undefined,
        }}
      >
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
        <div
          style={{ position: 'absolute', right: 0, bottom: 0, width: 26, height: 26, backgroundColor: T.bgBase }}
        />
      </AbsoluteFill>

      {/* subtle vignette that deepens slightly as we push in — adds depth */}
      <AbsoluteFill
        style={{
          pointerEvents: 'none',
          boxShadow: `inset 0 0 ${140 + (cam.zoom - 1) * 420}px rgba(0,0,0,${0.2 + (cam.zoom - 1) * 0.5})`,
        }}
      />

      {/* spotlights (screen-space, projected onto the zooming element) */}
      {spotlights.map((s, i) => {
        const p = proj(s.x, s.y);
        return (
          <Spotlight
            key={`sp${i}`}
            from={B(s.fromBeat, s.fromOffset ?? 0)}
            to={B(s.toBeat, s.toOffset ?? 0)}
            cx={p.x}
            cy={p.y}
            rw={s.rw * cam.zoom}
            rh={s.rh * cam.zoom}
            dim={s.dim}
          />
        );
      })}

      {/* callouts */}
      {callouts.map((c, i) => {
        const p = proj(c.x, c.y);
        return (
          <Callout
            key={`co${i}`}
            from={B(c.fromBeat, c.fromOffset ?? 0)}
            to={B(c.toBeat, c.toOffset ?? 0)}
            x={p.x}
            y={p.y}
            w={c.w * cam.zoom}
            h={c.h * cam.zoom}
            label={c.label}
            side={c.side}
          />
        );
      })}

      {/* click pulses */}
      {pulses.map((pl, i) => {
        const p = proj(pl.x, pl.y);
        return <ClickPulse key={`pu${i}`} at={B(pl.atBeat, pl.offset ?? 0)} x={p.x} y={p.y} />;
      })}

      {/* success confirmations */}
      {confirms.map((cf, i) => {
        const p = proj(cf.x, cf.y);
        return <SuccessConfirm key={`cf${i}`} at={B(cf.atBeat, cf.offset ?? 0)} x={p.x} y={p.y} />;
      })}

      {/* lower thirds (fixed screen-space — reads as a layer above the UI) */}
      {overlays.map((o, i) => (
        <LowerThird
          key={`lt${i}`}
          text={o.text}
          strong={o.strong}
          from={B(o.fromBeat, o.fromOffset ?? 6)}
          to={B(o.toBeat, o.toOffset ?? -6)}
        />
      ))}
    </AbsoluteFill>
  );
};
