import React from 'react';
import { AbsoluteFill, interpolate, spring, useCurrentFrame, useVideoConfig } from 'remotion';
import { SceneBg } from '../components/SceneBg';
import { LogoMark } from '../components/LogoMark';
import { T } from '../theme';

const Line: React.FC<{
  children: React.ReactNode;
  at: number;
  dimAt?: number;
  size?: number;
  color?: string;
}> = ({ children, at, dimAt, size = 62, color = T.textPrimary }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const enter = spring({ frame: frame - at, fps, config: { damping: 18, stiffness: 130 } });
  const dim = dimAt !== undefined
    ? interpolate(frame, [dimAt, dimAt + 12], [1, 0.32], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' })
    : 1;
  if (frame < at) return null;
  const blur = (1 - enter) * 8;
  return (
    <div
      style={{
        fontFamily: T.fontDisplay,
        fontWeight: 600,
        fontSize: size,
        letterSpacing: '-0.02em',
        color,
        opacity: enter * dim,
        transform: `translateY(${(1 - enter) * 22}px)`,
        filter: blur > 0.1 ? `blur(${blur.toFixed(2)}px)` : undefined,
        textAlign: 'center',
        lineHeight: 1.25,
      }}
    >
      {children}
    </div>
  );
};

// 0:00–0:06 — the problem, then the name.
export const Hook: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const logoAt = 100;
  // slightly underdamped — a whisper of overshoot as the brand settles in,
  // never a bounce.
  const logoEnter = spring({ frame: frame - logoAt, fps, config: { damping: 13, stiffness: 120 } });
  const logoBlur = Math.max(0, (1 - logoEnter) * 6);

  return (
    <SceneBg>
      <AbsoluteFill style={{ justifyContent: 'center', alignItems: 'center', gap: 26, paddingBottom: 40 }}>
        <Line at={8} dimAt={logoAt}>Your AI agent failed in production.</Line>
        <Line at={44} dimAt={logoAt} color={T.textSecondary} size={46}>
          Run it again — you get a <span style={{ color: T.warm }}>different</span> failure.
        </Line>
        {frame >= logoAt && (
          <div
            style={{
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              gap: 22,
              marginTop: 34,
              opacity: logoEnter,
              transform: `scale(${0.94 + 0.06 * logoEnter})`,
              filter: logoBlur > 0.1 ? `blur(${logoBlur.toFixed(2)}px)` : undefined,
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: 20 }}>
              <LogoMark size={104} />
              <span
                style={{
                  fontFamily: T.fontDisplay,
                  fontWeight: 600,
                  fontSize: 72,
                  letterSpacing: '-0.02em',
                  color: T.textPrimary,
                }}
              >
                Capsule
              </span>
            </div>
            <div style={{ fontFamily: T.fontMono, fontSize: 27, color: T.textSecondary }}>
              Deterministic replay for AI agents
            </div>
          </div>
        )}
      </AbsoluteFill>
    </SceneBg>
  );
};
