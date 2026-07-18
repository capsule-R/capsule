import React from 'react';
import { AbsoluteFill } from 'remotion';
import { T } from '../theme';

// Dark base + faint grid with radial falloff — the landing hero motif.
export const SceneBg: React.FC<{ children?: React.ReactNode }> = ({ children }) => (
  <AbsoluteFill style={{ backgroundColor: T.bgBase }}>
    <AbsoluteFill
      style={{
        backgroundImage:
          `linear-gradient(${T.borderSubtle} 1px, transparent 1px),` +
          `linear-gradient(90deg, ${T.borderSubtle} 1px, transparent 1px)`,
        backgroundSize: '72px 72px',
        opacity: 0.5,
        WebkitMaskImage: 'radial-gradient(ellipse 70% 60% at 50% 45%, black 30%, transparent 75%)',
        maskImage: 'radial-gradient(ellipse 70% 60% at 50% 45%, black 30%, transparent 75%)',
      }}
    />
    {children}
  </AbsoluteFill>
);
