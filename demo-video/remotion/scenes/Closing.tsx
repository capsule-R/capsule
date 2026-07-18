import React from 'react';
import { AbsoluteFill, interpolate, spring, useCurrentFrame, useVideoConfig } from 'remotion';
import { SceneBg } from '../components/SceneBg';
import { LogoMark } from '../components/LogoMark';
import { T } from '../theme';

// 0:52–1:00 — the thesis, then the lockup.
export const Closing: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const aAt = 10;
  const bAt = 52;
  const lockupAt = 130;

  const aIn = spring({ frame: frame - aAt, fps, config: { damping: 16, stiffness: 110 } });
  const bIn = spring({ frame: frame - bAt, fps, config: { damping: 16, stiffness: 110 } });
  const lIn = spring({ frame: frame - lockupAt, fps, config: { damping: 15, stiffness: 100 } });
  const aDim = interpolate(frame, [bAt, bAt + 14], [1, 0.45], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });

  return (
    <SceneBg>
      <AbsoluteFill style={{ justifyContent: 'center', alignItems: 'center', gap: 30, paddingBottom: 30 }}>
        {frame >= aAt && (
          <div
            style={{
              fontFamily: T.fontDisplay,
              fontWeight: 500,
              fontSize: 44,
              letterSpacing: '-0.015em',
              color: T.textSecondary,
              opacity: aIn * aDim,
              transform: `translateY(${(1 - aIn) * 24}px)`,
              textAlign: 'center',
            }}
          >
            Traditional observability tells you <span style={{ color: T.textPrimary, fontWeight: 600 }}>what</span> happened.
          </div>
        )}
        {frame >= bAt && (
          <div
            style={{
              fontFamily: T.fontDisplay,
              fontWeight: 600,
              fontSize: 56,
              letterSpacing: '-0.02em',
              color: T.textPrimary,
              opacity: bIn,
              transform: `translateY(${(1 - bIn) * 24}px)`,
              textAlign: 'center',
              lineHeight: 1.3,
            }}
          >
            Capsule lets you <span style={{ color: T.warm }}>replay exactly</span> what happened.
          </div>
        )}
        {frame >= lockupAt && (
          <div
            style={{
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              gap: 20,
              marginTop: 40,
              opacity: lIn,
              transform: `translateY(${(1 - lIn) * 16}px)`,
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: 15 }}>
              <LogoMark size={72} />
              <span style={{ fontFamily: T.fontDisplay, fontWeight: 600, fontSize: 50, color: T.textPrimary, letterSpacing: '-0.02em' }}>
                Capsule
              </span>
            </div>
            <div
              style={{
                fontFamily: T.fontMono,
                fontSize: 25,
                color: T.monoText,
                backgroundColor: T.monoBg,
                border: `1px solid ${T.borderDefault}`,
                borderRadius: T.radiusSm,
                padding: '13px 26px',
              }}
            >
              <span style={{ color: T.textTertiary }}>$ </span>pip install capsule-trace
            </div>
          </div>
        )}
      </AbsoluteFill>
    </SceneBg>
  );
};
