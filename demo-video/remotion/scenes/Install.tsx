import React from 'react';
import { AbsoluteFill, interpolate, spring, useCurrentFrame, useVideoConfig } from 'remotion';
import { SceneBg } from '../components/SceneBg';
import { Terminal } from '../components/Terminal';
import { Window } from '../components/Window';
import { LowerThird } from '../components/LowerThird';
import { T } from '../theme';

// 0:06–0:14 — pip install, then the one-decorator integration.
// Pip output mirrors a real `pip install capsule-trace` transcript.
export const Install: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const codeAt = 108; // frames — editor slides over the terminal
  const codeEnter = spring({ frame: frame - codeAt, fps, config: { damping: 18, stiffness: 130 } });
  const termBlurOut = frame >= codeAt ? interpolate(codeEnter, [0, 1], [0, 3]) : 0;

  return (
    <SceneBg>
      <AbsoluteFill style={{ justifyContent: 'center', alignItems: 'center' }}>
        <div
          style={{
            opacity: frame >= codeAt ? interpolate(codeEnter, [0, 1], [1, 0.25]) : 1,
            filter: termBlurOut > 0.1 ? `blur(${termBlurOut.toFixed(2)}px)` : undefined,
          }}
        >
          <Terminal
            width={1240}
            minHeight={470}
            title="zsh"
            lines={[
              { cmd: 'pip install capsule-trace', at: 240, typeMs: 780 },
              { out: 'Collecting capsule-trace', at: 1350 },
              { out: '  Downloading capsule_trace-0.1.2-py3-none-any.whl (48 kB)', at: 1600 },
              { out: 'Installing collected packages: capsule-trace', at: 1950 },
              { out: 'Successfully installed capsule-trace-0.1.2', at: 2350, color: T.success },
            ]}
          />
        </div>

        {frame >= codeAt && (
          <AbsoluteFill style={{ justifyContent: 'center', alignItems: 'center' }}>
            <div
              style={{
                opacity: codeEnter,
                transform: `translateY(${(1 - codeEnter) * 34}px) scale(${0.97 + 0.03 * codeEnter})`,
                filter: (1 - codeEnter) > 0.02 ? `blur(${((1 - codeEnter) * 7).toFixed(2)}px)` : undefined,
              }}
            >
              <Window title="billing_agent.py" width={1240} minHeight={520}>
                <pre
                  style={{
                    fontFamily: T.fontMono,
                    fontSize: 25,
                    lineHeight: 1.75,
                    margin: 0,
                    color: T.monoText,
                  }}
                >
                  <span style={{ color: T.textTertiary }}>import</span> capsule_trace <span style={{ color: T.textTertiary }}>as</span> capsule{'\n'}
                  <span style={{ color: T.textTertiary }}>from</span> openai <span style={{ color: T.textTertiary }}>import</span> OpenAI{'\n'}
                  {'\n'}
                  <span
                    style={{
                      display: 'inline-block',
                      width: '100%',
                      backgroundColor: 'rgba(232, 227, 219, 0.07)',
                      borderLeft: `3px solid ${T.warm}`,
                      marginLeft: -14,
                      paddingLeft: 11,
                      color: T.warm,
                    }}
                  >
                    @capsule.trace(agent_name=<span style={{ color: T.textPrimary }}>"billing-agent"</span>)
                  </span>
                  {'\n'}
                  <span style={{ color: T.textTertiary }}>def</span> <span style={{ color: T.textPrimary }}>process_refund</span>(customer_id: str):{'\n'}
                  {'    '}client = OpenAI(){'\n'}
                  {'    '}<span style={{ color: T.textTertiary }}># your existing agent code — nothing else changes</span>{'\n'}
                  {'    '}...
                </pre>
              </Window>
            </div>
          </AbsoluteFill>
        )}

        <LowerThird text="One dependency." from={40} to={104} />
        <LowerThird text="One decorator. Your agent code doesn’t change." strong="One decorator." from={118} to={240} />
      </AbsoluteFill>
    </SceneBg>
  );
};
