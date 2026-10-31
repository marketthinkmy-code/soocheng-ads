# -*- coding: utf-8 -*-
"""READ-ONLY UTM capture check for webinar_nov4 (after the 10/29 GHL tracking fix). No PII printed.
Register rows with Source containing nov4, by created day × UTM type (Webinarkit campaign / old campaign / blank),
plus top UTM campaign › ad set names. TEST rows (name/email containing 'test') skipped.
Then account spend + Meta registrations since 10/29 (pacing vs the ~RM5.1k plan)."""
from __future__ import annotations

import json
from collections import Counter

from adbot.clients.sheets import SheetsClient
from adbot.commands import graph_client
from adbot.monitor_cpl import extract_results
from adbot.settings import REPO_ROOT, load_settings

s = load_settings(REPO_ROOT / "config" / "config.sg.yaml")
reg = SheetsClient(s.secrets.google_sa_json).read_tab(s.cpa.spreadsheet_id, "Register")
hi = next(i for i, r in enumerate(reg[:8]) if "UTM Campaign" in r)
h = reg[hi]
rows = [dict(zip(h, r)) for r in reg[hi + 1:]]


def kind(u: str) -> str:
    u = (u or "").strip().lower()
    if not u:
        return "空白"
    return "Webinarkit" if "webinarkit" in u else "旧 campaign"


tab, names, skipped = Counter(), Counter(), 0
for r in rows:
    if "nov4" not in (r.get("Source") or "").lower():
        continue
    if any("test" in (v or "").lower() for k, v in r.items() if k and ("name" in k.lower() or "email" in k.lower())):
        skipped += 1
        continue
    u = (r.get("UTM Campaign") or "").strip()
    tab[((r.get("Created date") or "")[:10], kind(u))] += 1
    if u:
        names[f"{u[:50]} › {(r.get('UTM Ads Set') or '')[:30]}"] += 1
print(f"webinar_nov4 报名 · 日期 × UTM 类型（跳过 TEST {skipped} 行）:")
for k, v in sorted(tab.items()):
    print(f"   {k[0]} · {k[1]:<10} {v}")
tot = Counter()
for (d, t), v in tab.items():
    tot[t] += v
print("   合计:", dict(tot))
print("\nUTM campaign › ad set（前 15）:")
for n, v in names.most_common(15):
    print(f"   {v:>4}  {n}")

print("\n10/29 → 今天 花费 / Meta 报名:")
for label, cfg, cc in (("MY 5.0", "config.my5.yaml", "1048291251556714"), ("SG", "config.sg.yaml", "1614065190214320")):
    st = load_settings(REPO_ROOT / "config" / cfg)
    import datetime as dt
    today = (dt.datetime.utcnow() + dt.timedelta(hours=8)).date()
    days = [(dt.date(2026, 10, 29) + dt.timedelta(days=i)).isoformat() for i in range((today - dt.date(2026, 10, 29)).days + 1)]
    for since, until in ((d, d) for d in days):
        r = graph_client(st)._get_all(st.meta.account_path + "/insights", {"fields": "spend,actions", "time_range": json.dumps({"since": since, "until": until})})
        r = r[0] if r else {}
        sp, rg = float(r.get("spend") or 0), extract_results(r.get("actions"), f"offsite_conversion.custom.{cc}")
        print(f"   {label} {since[5:]}: RM{sp:,.0f} · 报名 {rg:.0f}" + (f" · CPL {sp / rg:.0f}" if rg else ""))
print("\nUTM NOV4 DONE (read-only)")
