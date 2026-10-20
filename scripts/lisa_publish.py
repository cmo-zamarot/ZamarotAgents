#!/usr/bin/env python3
"""מעלה כרטיסי השראה של ליסה לצמרת (עמוד השראה).

שימוש: python3 -I scripts/lisa_publish.py <cards.json> <shots_dir>
לכל כרטיס: מדלג אם ה־source_url כבר במערכת (intel.list) או ב־state/lisa/published.json,
מעלה <slug>.png (צילום ראשי) ו־<slug>.full.png (מדיה), ויוצר intel.create עם audience=marketing.
המפתח נקרא מ־ZAMERET_API_KEY בלבד ולא מודפס.
"""
import json
import os
import sys
import urllib.parse
import urllib.request

URL = "https://zameres.base44.app/api/apps/6ad66dc9b84e0b844217b719/functions/agent-api"
STATE = os.path.join(os.path.dirname(__file__), "..", "state", "lisa", "published.json")
KEY = os.environ["ZAMERET_API_KEY"]
UA = "zameret-agent-lisa/1.0 (curl-compatible)"


def call(body):
    req = urllib.request.Request(URL, data=json.dumps(body).encode(), method="POST",
                                 headers={"Content-Type": "application/json", "X-Api-Key": KEY, "User-Agent": UA})
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.load(r)


def upload(path):
    name = os.path.basename(path)
    q = urllib.parse.urlencode({"action": "files.upload", "name": name})
    with open(path, "rb") as f:
        data = f.read()
    req = urllib.request.Request(f"{URL}?{q}", data=data, method="POST",
                                 headers={"Content-Type": "image/png", "X-Api-Key": KEY, "User-Agent": UA})
    with urllib.request.urlopen(req, timeout=300) as r:
        return json.load(r)["file"]


def main(cards_path, shots):
    cards = json.load(open(cards_path))
    published = json.load(open(STATE)) if os.path.exists(STATE) else {}
    existing = {x.get("source_url") for x in call({"action": "intel.list", "audience": "marketing", "limit": 500}).get("items", [])}
    fields = ("kind", "title", "summary", "source_url", "source_name", "competitor_name", "location",
              "price_info", "headlines", "messages", "tags", "platform", "running_since")
    for c in cards:
        url = c["source_url"]
        if url in published or url in existing:
            print(f"SKIP (seen) {c['title']}")
            continue
        body = {"action": "intel.create", "audience": "marketing", **{k: c[k] for k in fields if c.get(k)}}
        top = os.path.join(shots, c["slug"] + ".png")
        full = os.path.join(shots, c["slug"] + ".full.png")
        if os.path.exists(top):
            body["image"] = upload(top)
        if os.path.exists(full):
            body["media"] = [upload(full)]
        res = call(body)
        if "error" in res:
            print(f"ERROR {c['title']}: {res['error']}")
            continue
        published[url] = {"title": c["title"], "app_url": res.get("app_url"),
                          "id": (res.get("intel") or {}).get("id"), "duplicate": res.get("duplicate", False)}
        print(f"{'DUP' if res.get('duplicate') else 'NEW'} {c['title']} -> {res.get('app_url')}")
        json.dump(published, open(STATE, "w"), ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
