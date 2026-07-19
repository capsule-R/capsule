import React from 'react';
import { AbsoluteFill, interpolate, useCurrentFrame } from 'remotion';

// Gently dims everything except an elliptical focal region — screen-space,
// so it tracks the (zooming) element it was projected onto. Fades in/out.
export const Spotlight: React.FC<{
  from: number;
  to: number;
  cx: number; // screen px
  cy: number;
  rw: number; // screen px radius
  rh: number;
  dim?: number; // max darkness of the surround (0..1)
  fade?: number; // frames
}> = ({ from, to, cx, cy, rw, rh, dim = 0.5, fade = 12 }) => {
  const frame = useCurrentFrame();
  if (frame < from - 1 || frame > to + 1) return null;

  const a =
    interpolate(frame, [from, from + fade], [0, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }) *
    interpolate(frame, [to - fade, to], [1, 0], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });

  return (
    <AbsoluteFill
      style={{
        opacity: a,
        pointerEvents: 'none',
        background: `radial-gradient(ellipse ${rw}px ${rh}px at ${cx}px ${cy}px, rgba(6,6,7,0) 0%, rgba(6,6,7,0) 52%, rgba(6,6,7,${dim}) 100%)`,
      }}
    />
  );
};
