import React from 'react';
import { useCurrentFrame, useVideoConfig } from 'remotion';
import { T } from '../theme';
import { Window } from './Window';

export type TermLine =
  | { cmd: string; at: number; typeMs?: number } // typed command with prompt
  | { out: string; at: number; color?: string }; // output line, appears at `at` ms

// A deterministic terminal: commands type char-by-char, output lines appear
// at fixed offsets (ms from sequence start).
export const Terminal: React.FC<{
  title?: string;
  lines: TermLine[];
  width?: number;
  minHeight?: number;
  fontSize?: number;
}> = ({ title = 'zsh — capsule', lines, width, minHeight, fontSize = 24 }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const ms = (frame / fps) * 1000;

  const rendered: React.ReactNode[] = [];
  let caretPlaced = false;

  lines.forEach((l, idx) => {
    if ('cmd' in l) {
      if (ms < l.at) return;
      const typeMs = l.typeMs ?? l.cmd.length * 34;
      const progress = Math.min(1, (ms - l.at) / typeMs);
      const chars = Math.round(progress * l.cmd.length);
      const done = progress >= 1;
      const isLast = idx === lines.length - 1 || lines.slice(idx + 1).every((n) => ms < n.at);
      const showCaret = !caretPlaced && (!done || isLast);
      if (showCaret) caretPlaced = true;
      rendered.push(
        <div key={idx} style={{ whiteSpace: 'pre-wrap' }}>
          <span style={{ color: T.textTertiary }}>$ </span>
          <span style={{ color: T.textPrimary }}>{l.cmd.slice(0, chars)}</span>
          {showCaret && (
            <span
              style={{
                display: 'inline-block',
                width: fontSize * 0.55,
                height: fontSize * 1.05,
                verticalAlign: 'text-bottom',
                backgroundColor: Math.floor(ms / 530) % 2 === 0 ? T.textPrimary : 'transparent',
                marginLeft: 2,
              }}
            />
          )}
        </div>,
      );
    } else {
      if (ms < l.at) return;
      const appear = Math.min(1, (ms - l.at) / 120);
      rendered.push(
        <div key={idx} style={{ whiteSpace: 'pre-wrap', color: l.color ?? T.monoText, opacity: appear }}>
          {l.out.length === 0 ? ' ' : l.out}
        </div>,
      );
    }
  });

  return (
    <Window title={title} width={width} minHeight={minHeight}>
      <div style={{ fontFamily: T.fontMono, fontSize, lineHeight: 1.72 }}>{rendered}</div>
    </Window>
  );
};
