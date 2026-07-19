import React from 'react';
import { AbsoluteFill, Img, interpolate, spring, staticFile, useCurrentFrame, useVideoConfig } from 'remotion';
import { SceneBg } from '../components/SceneBg';
import { LogoMark } from '../components/LogoMark';
import { T } from '../theme';

// 0:52–1:00 — the deterministic-success dashboard gently pushes in and
// dissolves into the thesis, then the Capsule lockup. Messaging unchanged.
export const Closing: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // ── dashboard still → brand crossfade ──
  const stillOut = interpolate(frame, [26, 62], [1, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  const stillScale = interpolate(frame, [0, 62], [1.03, 1.09], { extrapolateRight: 'clamp' });
  const stillBlur = interpolate(frame, [22, 62], [0, 7], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });
  const brandIn = interpolate(frame, [34, 60], [0, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });

  // ── thesis + lockup ──
  const aAt = 52;
  const bAt = 96;
  const lockupAt = 162;

  const aIn = spring({ frame: frame - aAt, fps, config: { damping: 18, stiffness: 120 } });
  const bIn = spring({ frame: frame - bAt, fps, config: { damping: 18, stiffness: 120 } });
  const lIn = spring({ frame: frame - lockupAt, fps, config: { damping: 16, stiffness: 100 } });
  const aDim = interpolate(frame, [bAt, bAt + 14], [1, 0.45], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });

  const typeStyle = (inT: number, up: number): React.CSSProperties => ({
    opacity: inT,
    transform: `translateY(${(1 - inT) * up}px)`,
    filter: inT < 0.98 ? `blur(${(1 - inT) * 6}px)` : undefined,
  });

  return (
    <AbsoluteFill style={{ backgroundColor: T.bgBase }}>
      {/* dashboard success still, gently pushing in */}
      {stillOut > 0.01 && (
        <AbsoluteFill style={{ opacity: stillOut }}>
          <Img
            src={staticFile('stills/success.jpg')}
            style={{
              width: '100%',
              height: '100%',
              objectFit: 'cover',
              transform: `scale(${stillScale})`,
              filter: `blur(${stillBlur.toFixed(2)}px)`,
            }}
          />
          <AbsoluteFill style={{ background: 'rgba(10,10,10,0.35)' }} />
        </AbsoluteFill>
      )}

      {/* brand */}
      <AbsoluteFill style={{ opacity: brandIn }}>
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
                  textAlign: 'center',
                  ...typeStyle(aIn * aDim, 24),
                }}
              >
                Traditional observability tells you{' '}
                <span style={{ color: T.textPrimary, fontWeight: 600 }}>what</span> happened.
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
                  textAlign: 'center',
                  lineHeight: 1.3,
                  ...typeStyle(bIn, 24),
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
                  ...typeStyle(lIn, 16),
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: 15 }}>
                  <LogoMark size={72} />
                  <span
                    style={{
                      fontFamily: T.fontDisplay,
                      fontWeight: 600,
                      fontSize: 50,
                      color: T.textPrimary,
                      letterSpacing: '-0.02em',
                    }}
                  >
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
      </AbsoluteFill>
    </AbsoluteFill>
  );
};
