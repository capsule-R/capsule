import React from 'react';
import { interpolate, useCurrentFrame } from 'remotion';
import { T } from '../theme';

// A soft branded ring that expands and fades at a click moment, layered over
// the cursor's own ripple in the footage for extra emphasis. Screen-space.
export const ClickPulse: React.FC<{
  at: number;
  x: number; // screen px
  y: number;
  dur?: number;
}> = ({ at, x, y, dur = 20 }) => {
  const frame = useCurrentFrame();
  if (frame < at || frame > at + dur) return null;
  const t = (frame - at) / dur;
  const scale = interpolate(t, [0, 1], [0.35, 1.7]);
  const opacity = interpolate(t, [0, 0.15, 1], [0, 0.55, 0]);
  const size = 120;
  return (
    <div
      style={{
        position: 'absolute',
        left: x - size / 2,
        top: y - size / 2,
        width: size,
        height: size,
        borderRadius: '50%',
        border: `2px solid ${T.warm}`,
        transform: `scale(${scale})`,
        opacity,
        pointerEvents: 'none',
      }}
    />
  );
};

// A satisfying confirmation: a ring snaps outward and a check-dot pops. Used
// for the deterministic-replay success moment.
export const SuccessConfirm: React.FC<{
  at: number;
  x: number;
  y: number;
}> = ({ at, x, y }) => {
  const frame = useCurrentFrame();
  const dur = 26;
  if (frame < at || frame > at + dur + 40) return null;
  const t = Math.min(1, (frame - at) / dur);
  const ring = interpolate(t, [0, 1], [0.4, 1.9]);
  const ringOp = interpolate(t, [0, 0.2, 1], [0, 0.7, 0]);
  // check-dot overshoot
  const pop =
    t < 1
      ? interpolate(t, [0, 0.6, 0.8, 1], [0, 1.18, 0.94, 1])
      : 1;
  const size = 60;
  return (
    <div style={{ position: 'absolute', left: x, top: y, pointerEvents: 'none' }}>
      <div
        style={{
          position: 'absolute',
          left: -size / 2,
          top: -size / 2,
          width: size,
          height: size,
          borderRadius: '50%',
          border: `2px solid ${T.success}`,
          transform: `scale(${ring})`,
          opacity: ringOp,
        }}
      />
      <div
        style={{
          position: 'absolute',
          left: -16,
          top: -16,
          width: 32,
          height: 32,
          borderRadius: '50%',
          background: T.success,
          transform: `scale(${pop})`,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          boxShadow: `0 0 20px rgba(34,197,94,0.6)`,
        }}
      >
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none">
          <path d="M5 13l4 4 10-10" stroke="#08140b" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
      </div>
    </div>
  );
};
