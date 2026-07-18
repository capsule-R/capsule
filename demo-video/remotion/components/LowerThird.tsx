import React from 'react';
import { interpolate, spring, useCurrentFrame, useVideoConfig } from 'remotion';
import { T } from '../theme';

// YC-style lower third: direct, technical, no fluff. Sits bottom-left over
// footage; enters with a small spring, exits with a quick fade.
export const LowerThird: React.FC<{
  text: string;
  from: number; // frame (relative to parent sequence)
  to: number;
  strong?: string; // substring to emphasize in warm accent
}> = ({ text, from, to, strong }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  if (frame < from || frame > to) return null;

  const enter = spring({ frame: frame - from, fps, config: { damping: 18, stiffness: 160 } });
  const exit = interpolate(frame, [to - 8, to], [1, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  let content: React.ReactNode = text;
  if (strong && text.includes(strong)) {
    const [a, b] = text.split(strong);
    content = (
      <>
        {a}
        <span style={{ color: T.warm }}>{strong}</span>
        {b}
      </>
    );
  }

  return (
    <div
      style={{
        position: 'absolute',
        left: 48,
        bottom: 44,
        maxWidth: 860,
        opacity: enter * exit,
        transform: `translateY(${(1 - enter) * 22}px)`,
        backgroundColor: 'rgba(17, 17, 17, 0.92)',
        border: `1px solid ${T.borderDefault}`,
        borderLeft: `3px solid ${T.warm}`,
        borderRadius: T.radiusSm,
        padding: '16px 26px',
        fontFamily: T.fontDisplay,
        fontWeight: 500,
        fontSize: 27,
        letterSpacing: '-0.01em',
        lineHeight: 1.4,
        color: T.textPrimary,
        boxShadow: '0 18px 50px rgba(0,0,0,0.45)',
      }}
    >
      {content}
    </div>
  );
};
