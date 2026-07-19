import React from 'react';
import { interpolate, spring, useCurrentFrame, useVideoConfig } from 'remotion';
import { T } from '../theme';

// YC-style lower third: direct, technical, no fluff. Sits bottom-left over
// footage. Copy blurs + slides into place and blurs back out — never a hard
// pop. Timing windows are unchanged; only the motion is refined.
export const LowerThird: React.FC<{
  text: string;
  from: number;
  to: number;
  strong?: string;
}> = ({ text, from, to, strong }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  if (frame < from - 1 || frame > to + 1) return null;

  const enter = spring({ frame: frame - from, fps, config: { damping: 20, stiffness: 150 } });
  const exitT = interpolate(frame, [to - 12, to], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  const opacity = enter * (1 - exitT);
  const slideIn = (1 - enter) * 26; // px from left/below
  const slideOut = exitT * 14;
  const blurIn = (1 - enter) * 7;
  const blurOut = exitT * 6;
  const blur = Math.max(blurIn, blurOut);

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
        opacity,
        transform: `translate(${slideIn - slideOut}px, ${slideIn * 0.5}px)`,
        filter: blur > 0.1 ? `blur(${blur.toFixed(2)}px)` : undefined,
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
        backdropFilter: 'blur(3px)',
      }}
    >
      {content}
    </div>
  );
};
