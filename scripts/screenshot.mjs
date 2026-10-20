// צילום מסך של עמודים (מודעות, עמודי נחיתה). שימוש:
//   node scripts/screenshot.mjs <תיקיית_יעד> <url> [url ...]
// לכל קישור שומר: <slug>.png (מסך ראשון, לכרטיס), <slug>.full.png (כל העמוד, עד 8000px)
// ו־<slug>.txt (כתובת סופית, כותרת וטקסט גלוי — לניתוח). כשהרשת חוסמת — מדפיס FAIL וממשיך.
import { createRequire } from 'node:module';
import { execSync } from 'node:child_process';
import { mkdirSync, writeFileSync } from 'node:fs';
import { join } from 'node:path';

// playwright מותקן גלובלית בסביבה; טוענים אותו משם אם אין התקנה מקומית.
const require = createRequire(import.meta.url);
let chromium;
try { ({ chromium } = require('playwright')); }
catch { ({ chromium } = require(join(execSync('npm root -g').toString().trim(), 'playwright'))); }

const [outDir, ...urls] = process.argv.slice(2);
if (!outDir || urls.length === 0) {
  console.error('usage: node scripts/screenshot.mjs <out_dir> <url> [url ...]');
  process.exit(2);
}
mkdirSync(outDir, { recursive: true });

const slug = (u) => u.replace(/^https?:\/\//, '').replace(/[^a-zA-Z0-9]+/g, '_').slice(0, 90);

const browser = await chromium.launch({ executablePath: process.env.CHROMIUM_PATH || undefined });
const ctx = await browser.newContext({ viewport: { width: 1280, height: 900 }, locale: 'he-IL', ignoreHTTPSErrors: false });
let failed = 0;
for (const url of urls) {
  const page = await ctx.newPage();
  const base = join(outDir, slug(url));
  try {
    await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 45000 });
    await page.waitForLoadState('networkidle', { timeout: 15000 }).catch(() => {});
    await page.waitForTimeout(2500);
    await page.screenshot({ path: `${base}.png` });
    const height = await page.evaluate(() => document.documentElement.scrollHeight);
    await page.screenshot({ path: `${base}.full.png`, fullPage: true,
      clip: height > 8000 ? { x: 0, y: 0, width: 1280, height: 8000 } : undefined });
    const text = await page.evaluate(() => document.body?.innerText ?? '');
    writeFileSync(`${base}.txt`, `URL: ${page.url()}\nTITLE: ${await page.title()}\n\n${text.slice(0, 20000)}`);
    console.log(`OK ${url} -> ${base}.png`);
  } catch (e) {
    failed++;
    console.log(`FAIL ${url} :: ${String(e.message).split('\n')[0]}`);
  } finally {
    await page.close();
  }
}
await browser.close();
process.exit(failed === urls.length ? 1 : 0);
