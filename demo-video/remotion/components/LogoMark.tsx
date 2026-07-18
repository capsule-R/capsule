import React from 'react';

// Exact copy of packages/cloud-web/components/Logo.tsx LogoMark.
export const LogoMark: React.FC<{ size?: number }> = ({ size = 44 }) => {
  const h = Math.round((size * 26) / 46);
  return (
    <svg width={size} height={h} viewBox="0 0 46 26" fill="none" aria-hidden="true">
      <rect x="0.5" y="0.5" width="45" height="25" rx="12.5" fill="#F5F5F5" />
      <path d="M20 8 L13 13 L20 18 Z" fill="#0A0A0A" />
      <path d="M28 8 L21 13 L28 18 Z" fill="#0A0A0A" fillOpacity="0.45" />
      <circle cx="35" cy="13" r="2.6" fill="#0A0A0A" fillOpacity="0.6" />
    </svg>
  );
};
