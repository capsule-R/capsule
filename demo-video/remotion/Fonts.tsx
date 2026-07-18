import React, { useEffect, useState } from 'react';
import { continueRender, delayRender, staticFile } from 'remotion';

// Loads Inter + Fragment Mono from local woff2 files (public/fonts) and
// blocks rendering until the browser has them ready — no Google Fonts
// dependency, no FOUT in rendered frames.
export const Fonts: React.FC = () => {
  const [handle] = useState(() => delayRender('fonts'));

  useEffect(() => {
    let cancelled = false;
    (async () => {
      const css = await fetch(staticFile('fonts/fonts.css')).then((r) => r.text());
      const abs = css.replace(/url\(\.\/(f\d+\.woff2)\)/g, (_, f) => `url(${staticFile(`fonts/${f}`)})`);
      const style = document.createElement('style');
      style.textContent = abs;
      document.head.appendChild(style);
      await document.fonts.load('600 64px Inter');
      await document.fonts.load('500 26px Inter');
      await document.fonts.load('400 24px "Fragment Mono"');
      await document.fonts.ready;
      if (!cancelled) continueRender(handle);
    })();
    return () => {
      cancelled = true;
    };
  }, [handle]);

  return null;
};
