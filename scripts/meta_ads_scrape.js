#!/usr/bin/env node
// צילום וחילוץ מודעות פעילות מספריית המודעות של Meta (ישראל), בלי התחברות.
// שימוש:
//   node scripts/meta_ads_scrape.js page <page_id> <out_dir> [max]
//   node scripts/meta_ads_scrape.js q "<מילות חיפוש>" <out_dir> [max]
// פלט: <out_dir>/<library_id>.png לכל מודעה + JSON ל־stdout:
//   [{ library_id, source_url, started, page_name, text, link_caption, shot }]
// הערה: קישור ישיר למודעה בודדת (?id=) לא מציג כלום בלי התחברות — לכן טוענים את עמוד המפרסם / החיפוש.
const path = require('path');
const fs = require('fs');
const { execSync } = require('child_process');

function loadPlaywright() {
  try { return require('playwright'); } catch (_) {}
  const root = execSync('npm root -g').toString().trim();
  return require(path.join(root, 'playwright'));
}

const [mode, value, outDir, maxArg] = process.argv.slice(2);
if (!['page', 'q'].includes(mode) || !value || !outDir) {
  console.error('usage: meta_ads_scrape.js page <page_id>|q "<terms>" <out_dir> [max]');
  process.exit(2);
}
const max = parseInt(maxArg || '30', 10);
fs.mkdirSync(outDir, { recursive: true });

const base = 'https://www.facebook.com/ads/library/?active_status=active&ad_type=all&country=IL&media_type=all';
const url = mode === 'page'
  ? `${base}&search_type=page&view_all_page_id=${encodeURIComponent(value)}`
  : `${base}&search_type=keyword_unordered&q=${encodeURIComponent(value)}`;

const MONTHS = { 'ינו': 1, 'פבר': 2, 'מרץ': 3, 'מרס': 3, 'אפר': 4, 'מאי': 5, 'יונ': 6, 'יול': 7, 'אוג': 8, 'ספט': 9, 'אוק': 10, 'נוב': 11, 'דצמ': 12 };
function parseStarted(s) {
  const m = s && s.match(/(\d{1,2})\s+ב?([א-ת]{3})[א-ת׳']*\s+(\d{4})/);
  if (!m || !MONTHS[m[2]]) return null;
  return `${m[3]}-${String(MONTHS[m[2]]).padStart(2, '0')}-${m[1].padStart(2, '0')}`;
}

(async () => {
  const { chromium } = loadPlaywright();
  const browser = await chromium.launch({ args: ['--disable-blink-features=AutomationControlled'] });
  const ctx = await browser.newContext({
    viewport: { width: 1280, height: 1600 }, locale: 'he-IL', deviceScaleFactor: 1.5,
    userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36',
  });
  const page = await ctx.newPage();
  // בפייסבוק עובדים לאט: לכל היותר טעינה אחת לחצי דקה, גם בניסיון חוזר
  for (let attempt = 0; attempt < 3; attempt++) {
    if (attempt) await page.waitForTimeout(30000 * attempt);
    await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 60000 });
    // מחכים לכרטיס הראשון (או להודעה שאין מודעות)
    const ok = await page.waitForFunction(() => /מזהה ספרייה:|אין מודעות שמתאימות/.test(document.body.innerText),
      null, { timeout: 30000 }).then(() => true).catch(() => false);
    if (ok) break;
    console.error(`no results yet (attempt ${attempt + 1})`);
  }
  await page.waitForTimeout(2500);

  // גלילה עד שיש מספיק כרטיסים
  for (let i = 0; i < 15; i++) {
    const n = await page.locator('text=/מזהה ספרייה/').count();
    if (n >= max) break;
    await page.mouse.wheel(0, 3000);
    await page.waitForTimeout(2000);
  }

  // מסמנים כל כרטיס: עולים מ"מזהה ספרייה" עד האב שמכיל את כל המודעה
  const count = await page.evaluate(() => {
    const labels = [...document.querySelectorAll('span, div')].filter(
      (el) => el.childElementCount === 0 && /^מזהה ספרייה:/.test(el.textContent.trim()));
    let i = 0;
    for (const lab of labels) {
      let el = lab;
      while (el.parentElement) {
        const p = el.parentElement;
        if (p.querySelectorAll('*').length && [...p.querySelectorAll('span,div')].filter(
          (x) => x.childElementCount === 0 && /^מזהה ספרייה:/.test(x.textContent.trim())).length > 1) break;
        el = p;
      }
      el.setAttribute('data-zm-card', String(i++));
    }
    return i;
  });

  const out = [];
  for (let i = 0; i < Math.min(count, max); i++) {
    const card = page.locator(`[data-zm-card="${i}"]`);
    const text = (await card.innerText().catch(() => '')).trim();
    const id = (text.match(/מזהה ספרייה:\s*(\d+)/) || [])[1];
    if (!id || out.some((o) => o.library_id === id)) continue;
    const startedRaw = (text.match(/התחילה לפעול ב-?([^\n]+)/) || [])[1];
    const lines = text.split('\n').map((l) => l.trim()).filter(Boolean);
    const sIdx = lines.findIndex((l) => l === 'ממומן');
    const pageName = sIdx > 0 ? lines[sIdx - 1] : null;
    const body = sIdx >= 0 ? lines.slice(sIdx + 1).filter((l) => !/^(לפרטים|הרשמה|שליחת הודעה|למידע נוסף|FB\.ME|.*\.(COM|CO\.IL|ME))$/i.test(l)).join('\n') : '';
    const shot = path.join(outDir, `${id}.png`);
    await card.scrollIntoViewIfNeeded().catch(() => {});
    await page.waitForTimeout(600);
    await card.screenshot({ path: shot }).catch(() => {});
    out.push({
      library_id: id,
      source_url: `https://www.facebook.com/ads/library/?id=${id}`,
      started: parseStarted(startedRaw),
      page_name: pageName,
      text: body,
      shot: fs.existsSync(shot) ? shot : null,
    });
  }
  await browser.close();
  process.stdout.write(JSON.stringify(out, null, 1));
})().catch((e) => { console.error(e); process.exit(1); });
