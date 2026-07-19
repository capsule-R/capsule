import React from 'react';
import { interpolate, spring, useCurrentFrame, useVideoConfig } from 'remotion';
import { T } from '../theme';

// A rounded-rectangle highlight around a UI element plus a labelled pill with
// a short arrow pointing at it. Screen-space; fades + slides in and out.
export const Callout: React.FC<{
  from: number;
  to: number;
  x: number; // screen px (element rect, projected)
  y: number;
  w: number;
  h: number;
  label: string;
  side?: 'top' | 'bottom';
  fade?: number;
}> = ({ from, to, x, y, w, h, label, side = 'bottom', fade = 12 }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  if (frame < from - 1 || frame > to + 1) return null;

  const enter = spring({ frame: frame - from, fps, config: { damping: 20, stiffness: 170 } });
  const out = interpolate(frame, [to - fade, to], [1, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  const a = enter * out;
  const pad = 6;
  const bx = x - pad;
  const by = y - pad;
  const bw = w + pad * 2;
  const bh = h + pad * 2;

  // label pill placement
  const gap = 18;
  const labelY = side === 'bottom' ? by + bh + gap : by - gap - 40;
  const labelCx = bx + bw / 2;
  const slide = (1 - enter) * (side === 'bottom' ? -10 : 10);

  return (
    <div style={{ position: 'absolute', inset: 0, pointerEvents: 'none', opacity: a }}>
      {/* highlight rectangle */}
      <div
        style={{
          position: 'absolute',
          left: bx,
          top: by,
          width: bw,
          height: bh,
          border: `2px solid ${T.warm}`,
          borderRadius: 10,
          boxShadow: `0 0 0 1px rgba(232,227,219,0.15), 0 0 22px rgba(232,227,219,0.18)`,
          transform: `scale(${0.985 + 0.015 * enter})`,
          transformOrigin: 'center',
        }}
      />
      {/* connector */}
      <div
        style={{
          position: 'absolute',
          left: labelCx - 1,
          top: side === 'bottom' ? by + bh : labelY + 40,
          width: 2,
          height: gap,
          background: T.warm,
          opacity: 0.6,
        }}
      />
      {/* label pill */}
      <div
        style={{
          position: 'absolute',
          left: labelCx,
          top: labelY,
          transform: `translate(-50%, ${slide}px)`,
          background: 'rgba(17,17,17,0.94)',
          border: `1px solid ${T.warm}`,
          borderRadius: 8,
          padding: '8px 14px',
          fontFamily: T.fontMono,
          fontSize: 18,
          color: T.warm,
          whiteSpace: 'nowrap',
          boxShadow: '0 10px 30px rgba(0,0,0,0.5)',
        }}
      >
        {label}
      </div>
    </div>
  );
};
