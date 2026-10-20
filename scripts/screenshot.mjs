// צילום מסך של עמודים (מודעות, עמודי נחיתה). שימוש:
//   node scripts/screenshot.mjs <תיקיית_יעד> <url> [url ...]
// שומר <slug>.png לכל קישור ומדפיס שורת סטטוס. כשהרשת חוסמת — מדפיס FAIL וממשיך.
import { createRequire } from 'node:module';
import { execSync } from 'node:child_process';
import { mkdirSync } from 'node:fs';
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
  const file = join(outDir, `${slug(url)}.png`);
  try {
    await page.goto(url, { waitUntil: 'networkidle', timeout: 45000 });
    await page.waitForTimeout(2500);
    await page.screenshot({ path: file, fullPage: true });
    console.log(`OK ${url} -> ${file}`);
  } catch (e) {
    failed++;
    console.log(`FAIL ${url} :: ${String(e.message).split('\n')[0]}`);
  } finally {
    await page.close();
  }
}
await browser.close();
process.exit(failed === urls.length ? 1 : 0);
