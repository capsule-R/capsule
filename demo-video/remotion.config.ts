import os from 'node:os';
import path from 'node:path';
import fs from 'node:fs';
import { Config } from '@remotion/cli/config';

// Reuse the Playwright-installed Chromium so rendering needs no extra
// browser download.
const chrome = path.join(
  os.homedir(),
  'AppData',
  'Local',
  'ms-playwright',
  'chromium-1148',
  'chrome-win',
  'chrome.exe',
);
if (fs.existsSync(chrome)) {
  Config.setBrowserExecutable(chrome);
}

Config.setVideoImageFormat('jpeg');
Config.setOverwriteOutput(true);
Config.setConcurrency(4);
