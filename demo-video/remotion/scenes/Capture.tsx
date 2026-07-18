import React from 'react';
import { AbsoluteFill } from 'remotion';
import { SceneBg } from '../components/SceneBg';
import { Terminal } from '../components/Terminal';
import { LowerThird } from '../components/LowerThird';
import { T } from '../theme';

const SID = '01K0J8R6PYQV9TCK2M4W7HNDF3';

// 0:14–0:21 — the agent fails in prod; Capsule captured everything.
export const Capture: React.FC = () => (
  <SceneBg>
    <AbsoluteFill style={{ justifyContent: 'center', alignItems: 'center' }}>
      <Terminal
        width={1420}
        minHeight={620}
        title="production — billing worker"
        lines={[
          { cmd: 'python billing_agent.py --customer cus_9XK42M', at: 160, typeMs: 700 },
          { out: '[billing-agent] investigating double charge on INV-20260714-0031', at: 1150 },
          { out: '[billing-agent] stripe.lookup_customer → 2 charges, 1 duplicate', at: 1500 },
          { out: '[billing-agent] stripe.create_refund → amount=124900', at: 1900 },
          { out: 'stripe.error.InvalidRequestError: Amount 124900 is greater than', at: 2350, color: T.error },
          { out: 'unrefunded amount on charge 12490', at: 2350, color: T.error },
          { out: '', at: 2900 },
          { out: `Captured session: ${SID}`, at: 3100, color: '#67E8F9' },
          { out: '  5 events · llm_call ×2 · tool_call ×2 · memory_write ×1', at: 3400, color: T.textTertiary },
          { out: '  → .capsule written · replay with: capsule replay ' + SID.slice(0, 10) + '…', at: 3700, color: T.textTertiary },
        ]}
      />
      <LowerThird
        text="Every LLM call, tool call, and memory op — captured automatically."
        strong="captured automatically."
        from={100}
        to={200}
      />
    </AbsoluteFill>
  </SceneBg>
);
