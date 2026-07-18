# Capsule — YC Demo Video Pipeline

Renders a polished 60-second demo (`out/capsule-yc-demo.mp4`, 1920×1080@30fps)
from the **real Capsule product**: the actual Next.js dashboard driven by
Playwright with realistic demo data, composited with YC-style overlays,
terminal scenes, and the closing card in Remotion.

## One-time setup

```powershell
cd demo-video
npm install
npx playwright install chromium

# Build the real dashboard with a same-origin API base (mocked at capture time)
cd ..\packages\cloud-web
$env:NEXT_PUBLIC_API_URL='/api/v1'; npm run build
cd ..\..\demo-video
```

## Render the video

```powershell
npm run demo          # capture + prepare + render, end to end
# or step by step:
npm run capture       # boots the app, records real-app scenes, syncs beat timings
npm run render        # remotion render -> out/capsule-yc-demo.mp4
npm run preview       # remotion studio (interactive timeline preview)
```

QA frames: `pwsh -File capture/extract-qa-frames.ps1` → `out/qa-frames/*.png`.

## How it works

1. **capture/record-scenes.mjs** starts the production build (`next start`,
   port 3100), satisfies the auth middleware with a `capsule_token` cookie, and
   intercepts every `/api/v1/**` call with **capture/mock-api.mjs** — realistic
   fixtures matching the backend's exact response shapes (bare-ULID session ids,
   real event payload fields, the verbatim `capsule-trace replay` output).
   A smooth eased cursor (**capture/cursor.mjs**) is injected into the page and
   survives full-page navigations. Each scene starts with a 1-frame magenta
   sync marker; every interaction beat is timestamped.
2. **capture/prepare-footage.mjs** locates the sync marker frame-exactly
   (via Remotion's bundled ffmpeg), converts beat wall-times to video-timeline
   seconds, and writes `remotion/footage-manifest.json`.
3. **remotion/** is a 1800-frame composition: Hook → Install (terminal + one
   decorator) → Capture (prod failure) → Inspect (real app footage) → Replay
   (real app footage — the deterministic banner) → Closing. Lower-third copy is
   timed off recorded beats, so text always matches what's on screen. Fonts
   (Inter + Fragment Mono) are served from local woff2 files — no network.

## The demo narrative

`billing-agent` is asked to refund a duplicate **$124.90** charge; at step 4
gpt-4o emits `amount: 124900` (minor units for **$1,249.00**) and Stripe
rejects the refund. Non-deterministic in production — exactly reproducible
under Capsule's cassette replay: *"Replay complete — deterministic ✓, 5/5
steps, integrity ✓."*
