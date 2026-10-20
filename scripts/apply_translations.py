#!/usr/bin/env python3
"""מוסיף תרגום לעברית למודעות שכבר נמצאות בצמרת, לפי state/translations.json.

  python3 -I scripts/apply_translations.py

state/translations.json: { "<library_id>": {"lang": "רוסית", "he": "<תרגום>"} }
לכל מודעה עם תרגום שעוד לא מופיע בסיכום שלה: intel.update עם כותרת בעברית ותרגום בסוף הסיכום.
"""
import json, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import daily_run as d

tr = d.load_translations()
items = d.api({"action": "intel.list", "kind": "competitor_ad", "limit": 1000}).get("items", [])
done = 0
for it in items:
    lib = (it.get("source_url") or "").rsplit("id=", 1)[-1]
    t = tr.get(lib)
    if not t or "תרגום לעברית" in (it.get("summary") or ""):
        continue
    d.api({"action": "intel.update", "id": it["id"], "title": t["he"].split("\n")[0][:120],
           "summary": (it.get("summary") or "") + d.translation_html(t["he"])})
    done += 1
print(f"translated {done}")
