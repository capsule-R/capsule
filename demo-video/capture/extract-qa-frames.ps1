# Extracts review frames from the rendered MP4 (frame-accurate for H.264).
# Usage: pwsh -File capture/extract-qa-frames.ps1 [-Video out/capsule-yc-demo.mp4] [-OutDir out/qa-frames]
param(
  [string]$Video = "out/capsule-yc-demo.mp4",
  [string]$OutDir = "out/qa-frames"
)
$ErrorActionPreference = 'Stop'
New-Item -ItemType Directory -Force $OutDir | Out-Null
Get-ChildItem $OutDir -Filter *.png -ErrorAction SilentlyContinue | Remove-Item -Force

# time(sec) => label  (scene map: hook 0-6, install 6-14.2, capture 14.2-21.2,
# inspect 21.2-38.2, replay 38.2-52.4, closing 52.4-60)
$frames = [ordered]@{
  '00.5' = 'hook-line1-enter'
  '02.0' = 'hook-line2'
  '04.2' = 'hook-logo'
  '05.9' = 'cut-hook-out'
  '06.3' = 'cut-install-in'
  '07.5' = 'install-typing'
  '09.5' = 'install-pip-done'
  '10.8' = 'install-code-enter'
  '13.0' = 'install-code-overlay'
  '14.1' = 'cut-install-out'
  '14.5' = 'cut-capture-in'
  '16.0' = 'capture-typing'
  '18.0' = 'capture-error-lines'
  '20.3' = 'capture-session-id'
  '21.1' = 'cut-capture-out'
  '21.6' = 'cut-inspect-in'
  '22.5' = 'inspect-overview'
  '24.5' = 'inspect-sessions-list'
  '27.0' = 'inspect-detail-loaded'
  '30.5' = 'inspect-llm-step'
  '34.0' = 'inspect-error-step'
  '37.9' = 'cut-inspect-out'
  '38.6' = 'cut-replay-in'
  '39.8' = 'replay-overlay1'
  '42.5' = 'replay-running'
  '46.0' = 'replay-banner'
  '49.5' = 'replay-stdout'
  '52.2' = 'cut-replay-out'
  '53.8' = 'closing-lineA'
  '56.0' = 'closing-lineB'
  '58.0' = 'closing-lockup'
  '59.6' = 'closing-end'
}

foreach ($t in $frames.Keys) {
  $label = $frames[$t]
  npx remotion ffmpeg -v error -ss $t -i $Video -frames:v 1 "$OutDir/t$t-$label.png" 2>$null
}
Write-Host "Extracted $((Get-ChildItem $OutDir -Filter *.png).Count)/$($frames.Count) frames to $OutDir"
