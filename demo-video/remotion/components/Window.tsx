import React from 'react';
import { T } from '../theme';

// Shared terminal/editor window chrome, monochrome per brand.
export const Window: React.FC<{
  title: string;
  width?: number;
  minHeight?: number;
  children: React.ReactNode;
}> = ({ title, width = 1280, minHeight = 640, children }) => (
  <div
    style={{
      width,
      minHeight,
      backgroundColor: T.monoBg,
      border: `1px solid ${T.borderDefault}`,
      borderRadius: T.radius,
      boxShadow: '0 40px 120px rgba(0,0,0,0.55)',
      overflow: 'hidden',
      display: 'flex',
      flexDirection: 'column',
    }}
  >
    <div
      style={{
        height: 46,
        display: 'flex',
        alignItems: 'center',
        gap: 8,
        padding: '0 18px',
        borderBottom: `1px solid ${T.borderSubtle}`,
        backgroundColor: T.bgCard,
        flexShrink: 0,
      }}
    >
      {[0, 1, 2].map((i) => (
        <div key={i} style={{ width: 11, height: 11, borderRadius: 6, backgroundColor: T.borderStrong }} />
      ))}
      <span
        style={{
          marginLeft: 12,
          fontFamily: T.fontMono,
          fontSize: 15,
          color: T.textTertiary,
        }}
      >
        {title}
      </span>
    </div>
    <div style={{ padding: '28px 34px', flex: 1 }}>{children}</div>
  </div>
);
