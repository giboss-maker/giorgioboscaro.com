// Usage: node test_site.js <site_dir> <base_url> <shots_dir>
const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

const [siteDir, base, shots] = process.argv.slice(2);
const EXTERNAL_OK = /googletagmanager|google-analytics|vimeo|gstatic|doubleclick|ERR_TUNNEL_CONNECTION_FAILED/;
const KNOWN_LIVE = /reading 'msie'|imagesLoaded is not a function|fancybox is not a function|isotope is not a function/;

(async () => {
  fs.mkdirSync(shots, { recursive: true });
  const locs = [...fs.readFileSync(path.join(siteDir, 'sitemap.xml'), 'utf8').matchAll(/<loc>https:\/\/www\.giorgioboscaro\.com([^<]*)<\/loc>/g)].map(m => m[1]);
  const browser = await chromium.launch();
  const problems = [];
  const links = new Set();
  const viewports = { desktop: { width: 1366, height: 900 }, mobile: { width: 390, height: 844 } };
  for (const [vpName, vp] of Object.entries(viewports)) {
    const ctx = await browser.newContext({ viewport: vp, deviceScaleFactor: 1 });
    for (const p of locs) {
      const page = await ctx.newPage();
      const errs = [];
      page.on('requestfailed', r => { if (!EXTERNAL_OK.test(r.url())) errs.push(`requestfailed ${r.url()}`); });
      page.on('response', r => { if (r.status() >= 400 && !EXTERNAL_OK.test(r.url())) errs.push(`HTTP ${r.status()} ${r.url()}`); });
      page.on('pageerror', e => { if (!KNOWN_LIVE.test(e.message)) errs.push(`pageerror ${e.message}`); });
      page.on('console', m => { if (m.type() === 'error' && !EXTERNAL_OK.test(m.text())) errs.push(`console ${m.text()}`); });
      const resp = await page.goto(base + p, { waitUntil: 'load' });
      await page.waitForTimeout(1500);
      if (resp.status() !== 200) errs.push(`status ${resp.status()}`);
      const info = await page.evaluate(() => ({
        broken: [...document.images].filter(i => i.getAttribute('src') && i.complete && i.naturalWidth === 0).map(i => i.src),
        hrefs: [...document.querySelectorAll('a[href]')].map(a => a.href),
        hscroll: document.documentElement.scrollWidth > window.innerWidth + 1,
        title: document.title.trim(),
        h: [...document.querySelectorAll('h1,h2')].length,
      }));
      info.broken.forEach(b => errs.push(`broken image ${b}`));
      if (info.hscroll && vpName === 'mobile') errs.push('horizontal scroll on mobile');
      info.hrefs.forEach(h => links.add(h));
      const name = (p.replace(/\//g, '_').replace(/^_|_$/g, '') || 'home') + `-${vpName}.png`;
      if (vpName === 'desktop' || ['/', '/portfolio/fulmine/', '/blog/'].includes(p))
        await page.screenshot({ path: path.join(shots, name), fullPage: true });
      console.log(`${errs.length ? 'FAIL' : 'ok  '} [${vpName}] ${p}  "${info.title}"`);
      errs.forEach(e => { console.log('     ' + e); problems.push(`${p} [${vpName}] ${e}`); });
      await page.close();
    }
    await ctx.close();
  }
  // internal link check (strip hash)
  const ctx = await browser.newContext();
  const checked = new Set();
  for (const h of links) {
    if (!h.startsWith(base)) continue;
    const u = h.split('#')[0];
    if (checked.has(u)) continue;
    checked.add(u);
    const r = await ctx.request.get(u);
    if (r.status() !== 200) { console.log(`BROKEN LINK ${r.status()} ${u}`); problems.push(`link ${u} -> ${r.status()}`); }
  }
  console.log(`\n${locs.length} pages x2 viewports, ${checked.size} internal link targets, ${problems.length} problems`);
  await browser.close();
  process.exit(problems.length ? 1 : 0);
})();
