# -*- coding: utf-8 -*-
"""READ-ONLY 2026-10-22: where does the UTM chain break for Webinarkit buyers?
1) every ad in the Webinarkit campaigns (MY 5.0 + SG): creative url_tags present? link?
2) Register tab: header + rows per day since 10/14, and how many carry a UTM campaign (no PII)."""
from __future__ import annotations

import datetime as dt
import time
from collections import Counter

from adbot import cpa
from adbot.clients.sheets import SheetsClient
from adbot.commands import graph_client
from adbot.settings import REPO_ROOT, load_settings

PLAN = {
    "config.my5.yaml": ["120251454680840329", "120251454704570329", "120251454700150329", "120251454713670329", "120251500767290329"],
    "config.sg.yaml": ["120249918193090521", "120249918195380521", "120249918198320521", "120249918201630521", "120249964890710521"],
}


def main() -> None:
    for cfg, camps in PLAN.items():
        g = graph_client(load_settings(REPO_ROOT / "config" / cfg))
        print(f"\n######## {cfg}")
        for cid in camps:
            ads = g._get_all(cid + "/ads", {"fields": "name,effective_status,creative{url_tags,object_story_spec,asset_feed_spec}", "limit": "30"})
            for a in ads:
                cr = a.get("creative") or {}
                oss = cr.get("object_story_spec") or {}
                link = ((oss.get("video_data") or {}).get("call_to_action") or {}).get("value", {}).get("link") \
                    or (oss.get("link_data") or {}).get("link") or ""
                print(f"  {cid[-6:]} {a['name'][:24]:<24} {a['effective_status']:<16} tags={'✅' if cr.get('url_tags') else '❌'} "
                      f"{(cr.get('url_tags') or '')[:60]} · link {'?' in link and 'with-query' or ''}{link[-40:]}")
            time.sleep(1)
    s = load_settings(REPO_ROOT / "config" / "config.sg.yaml")
    vals = SheetsClient(s.secrets.google_sa_json).read_tab(s.cpa.spreadsheet_id, "Register")
    hi = next((i for i, r in enumerate(vals[:8]) if any("utm" in (c or "").lower() for c in r)), 0)
    h = vals[hi]
    print(f"\nRegister 表头: {h}")
    di = next((i for i, c in enumerate(h) if "date" in (c or "").lower() or "time" in (c or "").lower()), -1)
    ui = next((i for i, c in enumerate(h) if "utm" in (c or "").lower() and "campaign" in (c or "").lower()), -1)
    si = next((i for i, c in enumerate(h) if (c or "").lower() in ("source", "webinar", "event")), -1)
    days, withu, src = Counter(), Counter(), Counter()
    for r in vals[hi + 1:]:
        d = cpa.parse_date(r[di][:20]) if 0 <= di < len(r) else None
        if d and d >= dt.date(2026, 10, 14):
            days[d.isoformat()] += 1
            if 0 <= ui < len(r) and r[ui].strip():
                withu[d.isoformat()] += 1
            if 0 <= si < len(r):
                src[r[si][:30]] += 1
    print(f"Register 行数 {len(vals) - hi - 1} · 日期栏 {di} · UTM 栏 {ui}")
    print("  10/14 起每日报名(有UTM): " + " · ".join(f"{d} {n}({withu[d]})" for d, n in sorted(days.items())))
    print(f"  source 分布: {dict(src.most_common(8))}")
    print("\nUTM CHAIN DONE (read-only)")


if __name__ == "__main__":
    main()
