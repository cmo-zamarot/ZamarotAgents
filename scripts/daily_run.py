#!/usr/bin/env python3
"""הריצה היומית של ג׳ני: מודעות מתחרים מ־Meta → קיר המודעות בצמרת.

  python3 -I scripts/daily_run.py [--max-per-page 15] [--dry-run]

1. מסנכרן את state/competitors.json ל־competitors.upsert.
2. לכל מתחרה עם meta_page_id: מצלם את המודעות הפעילות (scripts/meta_ads_scrape.js).
3. מדלג על מה שכבר קיים בצמרת (intel.list לפי source_url).
4. לכל מודעה חדשה: files.upload לצילום → intel.create (kind competitor_ad).
5. כותב סיכום ל־state/last_run.json. את ההודעה ל־#Sales כותבת ג׳ני על בסיס הסיכום.
"""
import argparse, json, os, re, subprocess, sys, datetime, time
from pathlib import Path

FB_GAP_SECONDS = 35
TRANSLATIONS = {}
NEEDS_TRANSLATION = []  # מודעות לא בעברית בלי תרגום — ג׳ני מתרגמת ומריצה scripts/apply_translations.py

ROOT = Path(__file__).resolve().parent.parent
ZAMERET = ROOT / "scripts" / "zameret.sh"
SCRAPER = ROOT / "scripts" / "meta_ads_scrape.js"
STATE = ROOT / "state"

# שם עיר כפי שמופיע במודעה (עברית/רוסית/אנגלית) → שם בעברית
PLACES = {
    "גדרה": "גדרה", "Гедер": "גדרה", "רחובות": "רחובות", "Реховот": "רחובות",
    "אשדוד": "אשדוד", "Ашдод": "אשדוד", "אשקלון": "אשקלון", "Ашкелон": "אשקלון",
    "ראשון לציון": "ראשון לציון", "Ришон": "ראשון לציון", "טאבו": None,
    "חדרה": "חדרה", "Хадер": "חדרה", "נתניה": "נתניה", "Нетани": "נתניה",
    "באר שבע": "באר שבע", "Беэр-Шев": "באר שבע", "קריית גת": "קריית גת", "Кирьят-Гат": "קריית גת",
    "יבנה": "יבנה", "Явне": "יבנה", "חריש": "חריש", "Хариш": "חריש", "עפולה": "עפולה",
    "חיפה": "חיפה", "Хайф": "חיפה", "תל אביב": "תל אביב", "Тель-Авив": "תל אביב",
    "רמלה": "רמלה", "לוד": "לוד", "קריית מלאכי": "קריית מלאכי", "שדרות": "שדרות",
    "בית שמש": "בית שמש", "מודיעין": "מודיעין", "רעננה": "רעננה", "הרצליה": "הרצליה",
    "כפר סבא": "כפר סבא", "הוד השרון": "הוד השרון", "פתח תקווה": "פתח תקווה",
    "נס ציונה": "נס ציונה", "קיסריה": "קיסריה", "זכרון יעקב": "זכרון יעקב", "טבריה": "טבריה",
    "גני תקווה": "גני תקווה", "כפר תבור": "כפר תבור", "כיסרא": "כיסרא", "ראשל\"צ": "ראשון לציון",
    "אור יהודה": "אור יהודה", "יהוד": "יהוד", "קריית שמונה": "קריית שמונה", "נהריה": "נהריה",
}


def api(payload):
    out = subprocess.run([str(ZAMERET), json.dumps(payload, ensure_ascii=False)],
                         capture_output=True, text=True, check=True).stdout
    data = json.loads(out)
    if isinstance(data, dict) and data.get("error"):
        raise RuntimeError(f"{payload.get('action')}: {data['error']}")
    return data


def upload(path):
    out = subprocess.run([str(ZAMERET), "--upload", str(path), Path(path).name],
                         capture_output=True, text=True, check=True).stdout
    return json.loads(out).get("file")


def scrape(page_id, out_dir, max_n):
    r = subprocess.run(["node", str(SCRAPER), "page", page_id, str(out_dir), str(max_n)],
                       capture_output=True, text=True, timeout=400)
    if r.stderr.strip():
        print(f"[{page_id}] {r.stderr.strip()[-300:]}", file=sys.stderr)
    if r.returncode != 0:
        return []
    return json.loads(r.stdout or "[]")


def language(text):
    if re.search(r"[А-Яа-я]{4,}", text):
        return "רוסית"
    if re.search(r"[א-ת]{3,}", text):
        return "עברית"
    if re.search(r"[A-Za-z]{4,}", text):
        return "אנגלית"
    return "לא ידוע"


def extract(ad):
    text = ad.get("text") or ""
    places = []
    for k, v in PLACES.items():
        if v and k in text and v not in places:
            places.append(v)
    compound = re.search(r"(?:מתחם|Метхам|מתחם)\s*(\d+)", text)
    prices = re.findall(r"(\d{1,3}(?:[,\s ]\d{3})+|\d{4,7})\s*(?:₪|ש\"ח|שקל)", text)
    prices += re.findall(r"₪\s*(\d{1,3}(?:[,\s ]\d{3})+)", text)
    nums = sorted({int(re.sub(r"\D", "", p)) for p in prices if re.sub(r"\D", "", p)})
    lines = [l for l in text.split("\n") if l.strip()]
    headline = lines[0][:120] if lines else ""
    return {
        "places": places,
        "compound": compound.group(1) if compound else None,
        "min_price": nums[0] if nums else None,
        "headline": headline,
        "lang": language(text),
        "lines": lines,
    }


def load_translations():
    f = STATE / "translations.json"
    return json.loads(f.read_text()) if f.exists() else {}


def translation_html(he):
    lines = "".join(f"<p>{l}</p>" for l in he.split("\n") if l.strip())
    return f"<p><b>תרגום לעברית:</b></p>{lines}"


def fmt_ils(n):
    return f"{n:,} ₪" if n else None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--max-per-page", type=int, default=15)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--only", help="page ids מופרדים בפסיק — להריץ רק עליהם")
    ap.add_argument("--work", default=os.environ.get("JENNY_WORK", "/tmp/jenny"))
    args = ap.parse_args()
    work = Path(args.work)
    work.mkdir(parents=True, exist_ok=True)

    TRANSLATIONS.update(load_translations())
    competitors = json.loads((STATE / "competitors.json").read_text())
    existing = {c["name"] for c in api({"action": "competitors.list"}).get("competitors", [])}
    for c in competitors:
        if c["name"] not in existing and not args.dry_run:
            api({"action": "competitors.upsert", "name": c["name"],
                 "description": c.get("page_name") or "",
                 "notes": c.get("notes") or (f"Meta page id: {c['meta_page_id']}" if c.get("meta_page_id") else ""),
                 "tags": ["נדל״ן", "קרקעות"]})

    known = {i.get("source_url") for i in api({"action": "intel.list", "kind": "competitor_ad", "limit": 1000}).get("items", [])}

    created, skipped, errors = [], 0, []
    only = set(args.only.split(",")) if args.only else None
    queue = [c for c in competitors if c.get("meta_page_id") and (not only or c["meta_page_id"] in only)]
    empty = []
    first = True
    for rnd in range(2):  # סבב שני רק למי שחזר ריק (בדרך כלל האטה של פייסבוק)
        if rnd:
            queue, empty = empty, []
            if not queue:
                break
            time.sleep(90)
        for c in queue:
            pid = c["meta_page_id"]
            if not first:  # בפייסבוק: לכל היותר חיפוש אחד לחצי דקה
                time.sleep(FB_GAP_SECONDS)
            first = False
            ads = scrape(pid, work / pid, args.max_per_page)
            if not ads:
                empty.append(c)
            before = len(created)
            created_n, skipped_n, errs = process(c, ads, known, api, args.dry_run, created)
            if not args.dry_run and (ads or rnd):  # מדווחים על כל מתחרה שנבדק, גם בלי חדש
                try:
                    api({"action": "competitors.checked", "name": c["name"], "ads_live": len(ads), "new_ads": len(created) - before})
                except Exception as e:
                    errors.append(f"competitors.checked {c['name']}: {e}")
            skipped += skipped_n
            errors += errs
    no_ads = [c["name"] for c in empty]

    result = {"date": datetime.date.today().isoformat(), "new": created, "skipped_existing": skipped,
              "no_active_ads_or_blocked": no_ads, "needs_translation": NEEDS_TRANSLATION, "errors": errors}
    if not args.dry_run:
        (STATE / "last_run.json").write_text(json.dumps(result, ensure_ascii=False, indent=1))
    print(json.dumps(result, ensure_ascii=False, indent=1))


def process(c, ads, known, api, dry_run, created):
    skipped, errors = 0, []
    for ad in ads:
        if ad["source_url"] in known:
            skipped += 1
            continue
        x = extract(ad)
        loc = ", ".join(x["places"]) + (f" (מתחם {x['compound']})" if x["compound"] else "") if x["places"] else "לא ידוע"
        price = f"החל מ־{fmt_ils(x['min_price'])} (לפי המודעה)" if x["min_price"] else "לא מופיע"
        summary = (f"<p>מודעה פעילה של {c['name']} ב־Meta"
                   + (f", רצה מאז {ad['started']}" if ad.get("started") else "") + ".</p>"
                   f"<p>מיקום: {loc}. מחיר כניסה: {price}. שפת המודעה: {x['lang']}.</p>"
                   "<p>הטענות במודעה הן לטענתם של המפרסם.</p>")
        tr = TRANSLATIONS.get(ad["library_id"], {}).get("he") if x["lang"] != "עברית" else None
        if tr:
            summary += translation_html(tr)
        item = {
            "action": "intel.create", "kind": "competitor_ad", "audience": "marketing",
            "platform": "meta", "competitor_name": c["name"], "source_name": "Meta Ad Library",
            "source_url": ad["source_url"],
            "title": (tr.split("\n")[0][:120] if tr else x["headline"]) or f"מודעה של {c['name']}",
            "headlines": [x["headline"]] if x["headline"] else [],
            "messages": x["lines"][:12], "location": loc if x["places"] else None,
            "price_info": price if x["min_price"] else None,
            "running_since": ad.get("started"), "summary": summary,
            "tags": [t for t in ["קרקע", *x["places"], x["lang"]] if t],
        }
        item = {k: v for k, v in item.items() if v not in (None, [], "")}
        if dry_run:
            created.append({"competitor": c["name"], **{k: item.get(k) for k in ("title", "location", "price_info", "running_since", "source_url")}, "lang": x["lang"]})
            continue
        try:
            if ad.get("shot"):
                f = upload(ad["shot"])
                if f:
                    item["image"] = f
            res = api(item)
            if res.get("duplicate"):
                skipped += 1
                continue
            known.add(ad["source_url"])
            if x["lang"] != "עברית" and not tr:
                NEEDS_TRANSLATION.append({"library_id": ad["library_id"], "intel_id": (res.get("intel") or {}).get("id"),
                                          "lang": x["lang"], "text": ad.get("text")})
            created.append({"competitor": c["name"], "title": item.get("title"), "location": item.get("location"),
                            "price_info": item.get("price_info"), "running_since": item.get("running_since"),
                            "lang": x["lang"], "source_url": ad["source_url"], "app_url": res.get("app_url")})
        except Exception as e:  # ממשיכים לשאר המודעות
            errors.append(f"{ad['source_url']}: {e}")

    return len(created), skipped, errors


if __name__ == "__main__":
    main()
