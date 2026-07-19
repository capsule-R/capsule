param(
  [string]$Video = "out/capsule-yc-demo.mp4",
  [string]$OutDir = "out/qa-v2"
)
$ErrorActionPreference = 'Stop'
New-Item -ItemType Directory -Force $OutDir | Out-Null
Get-ChildItem $OutDir -Filter *.png -ErrorAction SilentlyContinue | Remove-Item -Force

$frames = [ordered]@{
  '00.3' = 'hook-line1-in'
  '01.6' = 'hook-line1-blur-check'
  '03.0' = 'hook-line2'
  '04.3' = 'hook-logo-overshoot'
  '05.7' = 'hook-dim-out'
  '05.95'= 'cut-hook-install'
  '06.5' = 'install-pip-typing'
  '08.5' = 'install-pip-typed'
  '10.2' = 'install-pip-success'
  '11.0' = 'install-code-blurin'
  '13.0' = 'install-code-steady'
  '14.1' = 'cut-install-capture'
  '14.6' = 'capture-typing'
  '16.5' = 'capture-error-appear'
  '18.5' = 'capture-error-lines'
  '20.5' = 'capture-session-id'
  '21.1' = 'cut-capture-inspect'
  '21.5' = 'inspect-overview-zoom'
  '23.3' = 'inspect-precut-navclick'
  '23.8' = 'inspect-postcut-sessions'
  '24.5' = 'inspect-spotlight-failed'
  '25.7' = 'inspect-callout-failed'
  '26.1' = 'inspect-hero-click-zoom'
  '26.4' = 'inspect-postcut-detail'
  '28.0' = 'inspect-detail-hold'
  '29.7' = 'inspect-llm-zoom'
  '30.5' = 'inspect-llm-spotlight'
  '31.5' = 'inspect-llm-callout-10x'
  '32.9' = 'inspect-error-zoom'
  '34.5' = 'inspect-error-spotlight'
  '36.5' = 'inspect-scene-end'
  '36.8' = 'cut-inspect-replay'
  '37.5' = 'replay-wide'
  '38.6' = 'replay-zoomin-button'
  '39.2' = 'replay-click-pulse'
  '39.6' = 'replay-callout-label'
  '41.0' = 'replay-running'
  '43.05'= 'replay-banner-confirm'
  '43.6' = 'replay-banner-spotlight'
  '44.95'= 'replay-stdout-zoom'
  '45.6' = 'replay-stdout-callout'
  '48.0' = 'replay-stdout-hold'
  '50.3' = 'replay-scene-end'
  '50.8' = 'closing-still-crossfade'
  '52.0' = 'closing-brand-in'
  '53.8' = 'closing-lineA'
  '56.2' = 'closing-lineB'
  '58.7' = 'closing-lockup'
  '59.8' = 'closing-end'
}

foreach ($t in $frames.Keys) {
  $label = $frames[$t]
  npx remotion ffmpeg -v error -ss $t -i $Video -frames:v 1 "$OutDir/t$t-$label.png" 2>$null
}
Write-Host "Extracted $((Get-ChildItem $OutDir -Filter *.png).Count)/$($frames.Count) frames to $OutDir"
