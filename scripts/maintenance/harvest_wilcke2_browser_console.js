/* Harvest Wilcke II from danskmoent.dk — run in the BROWSER console.
 *
 * Why this exists: danskmoent.dk sits behind a WAF that answers curl (and any
 * plain HTTP client) with «455 Security Incident Detected», then escalates to
 * a «454 Checking your browser» JS challenge that a non-browser cannot answer.
 * A real browser tab passes it, so the fetches have to run there. See
 * docs/SOURCES.md §3 «Access».
 *
 * HOW TO RUN
 *   1. Open  danskmoent.dk/w2.htm  in your browser. Any danskmoent.dk page
 *      works; whether the address bar shows www. or not does not matter,
 *      because every path below is fetched relative to the open tab.
 *   2. Open the developer console:  ⌥⌘J (Chrome) / ⌥⌘C (Safari, after
 *      enabling Develop menu) / ⌥⌘K (Firefox).
 *   3. Paste this whole file, press Enter, and wait ~30 s. Progress prints
 *      as it goes.
 *   4. One file lands in Downloads: wilcke2_danskmoent.txt
 *
 * The output is every chapter's raw HTML concatenated, each preceded by a
 * delimiter line carrying its name, source URL and byte length, so the pieces
 * can be split apart again losslessly.
 *
 * Safari note: if the download is blocked, allow downloads from danskmoent.dk
 * when prompted, or run it in Chrome.
 */
(async () => {
  // Paths are RELATIVE on purpose. The site answers on both danskmoent.dk and
  // www.danskmoent.dk, and to a browser those are DIFFERENT ORIGINS — an
  // absolute «https://www.danskmoent.dk/…» fetched from a page loaded as
  // «https://danskmoent.dk/…» is cross-origin, and the server sends no
  // Access-Control-Allow-Origin, so every request dies with «Failed to fetch».
  // Relative paths resolve against whatever origin the tab is already on, so
  // they are same-origin either way. (Caught 2026-09-24, after the absolute
  // form returned 0 of 21.)
  if (!location.hostname.endsWith('danskmoent.dk')) {
    console.error('Open a danskmoent.dk page first (e.g. /w2.htm), then run this here.');
    return;
  }
  const PAGES = [
    ['w2_cover', '/w2.htm'],           // cover + Indholdsfortegnelse (page numbers)
    ['w2ref',  '/wilcke/w2ref.htm'],    // I. Tidsrummet 1588-1625        (s. 11)
    ['w2a1',   '/wilcke/w2a1.htm'],     // II + A. Københavns Mønt        (s. 47, 49)
    ['w2a2',   '/wilcke/w2a2.htm'],     //                                (s. 58)
    ['w2a3',   '/wilcke/w2a3.htm'],     //                                (s. 82)
    ['w2a4',   '/wilcke/w2a4.htm'],     //                                (s. 101)
    ['w2a5',   '/wilcke/w2a5.htm'],     //                                (s. 113)
    ['w2a6',   '/wilcke/w2a6.htm'],     //                                (s. 134)
    ['w2b1',   '/wilcke/w2b1.htm'],     // B. Kristiania Mønt             (s. 151)
    ['w2b2',   '/wilcke/w2b2.htm'],     //                                (s. 156)
    ['w2b3',   '/wilcke/w2b3.htm'],     //                                (s. 165)
    ['w2b4',   '/wilcke/w2b4.htm'],     //                                (s. 174)
    ['w2b5',   '/wilcke/w2b5.htm'],     //                                (s. 179)
    ['w2b6',   '/wilcke/w2b6.htm'],     //                                (s. 186)
    ['w2b7',   '/wilcke/w2b7.htm'],     //                                (s. 198)
    ['w2c1',   '/wilcke/w2c1.htm'],     // C. Glückstadts Mønt            (s. 208)
    ['w2c2',   '/wilcke/w2c2.htm'],     //                                (s. 218)
    ['w2c3',   '/wilcke/w2c3.htm'],     //                                (s. 245)
    ['w2c4',   '/wilcke/w2c4.htm'],     //                                (s. 251)
    ['w2c5',   '/wilcke/w2c5.htm'],     //                                (s. 256)
    ['w2d',    '/wilcke/w2d.htm'],      // D. Andre Møntsteder            (s. 261)
  ];

  // The pages declare no charset and are effectively ASCII (Danish letters are
  // HTML entities), but a handful of bytes are >127 — windows-1252 decodes
  // those losslessly where utf-8 would replace them.
  const dec = new TextDecoder('windows-1252');
  const MARK = '=====@@@ WILCKE2 CHAPTER @@@=====';
  const out = [];
  const bad = [];

  for (const [name, path] of PAGES) {
    const url = new URL(path, location.origin).href;   // same-origin by construction
    try {
      const r = await fetch(url, { cache: 'no-store', credentials: 'include' });
      const buf = await r.arrayBuffer();
      if (r.status !== 200 || buf.byteLength < 2000) {
        bad.push(`${name} http=${r.status} bytes=${buf.byteLength}`);
        console.warn('SKIP', name, r.status, buf.byteLength);
      } else {
        out.push(`${MARK} name=${name} url=${url} bytes=${buf.byteLength}\n` + dec.decode(buf));
        console.log('ok  ', name, buf.byteLength);
      }
    } catch (e) {
      bad.push(`${name} ERR ${e.message}`);
      console.warn('FAIL', name, e.message);
    }
    await new Promise(res => setTimeout(res, 800));   // be gentle with the host
  }

  const header =
    `# Wilcke II — Møntvæsenet under Christian IV og Frederik III 1625-1670 (København 1924)\n` +
    `# Captured from ${location.origin}/ on ${new Date().toISOString()}\n` +
    `# Chapters captured: ${out.length} of ${PAGES.length}\n` +
    (bad.length ? `# FAILED: ${bad.join(' | ')}\n` : `# FAILED: none\n`) +
    `# Split on the line starting «${MARK}».\n\n`;

  const blob = new Blob([header + out.join('\n')], { type: 'text/plain;charset=utf-8' });
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = 'wilcke2_danskmoent.txt';
  document.body.appendChild(a);
  a.click();
  a.remove();

  console.log(`%cDONE — ${out.length}/${PAGES.length} chapters, ${(blob.size/1024).toFixed(0)} KB → Downloads/wilcke2_danskmoent.txt`,
              'font-weight:bold');
  if (bad.length) console.log('Not captured:', bad);
})();
