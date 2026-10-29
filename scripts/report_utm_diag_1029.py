# -*- coding: utf-8 -*-
"""READ-ONLY UTM diagnosis (owner 10/29「为什么那些 register 还是从旧的广告来？一定要找到解决方案」). No PII printed —
emails / phones only used in-run to link a person's rows.
For webinar_oct28 registrations in the Register tab:
  · UTM campaign names (top) — are they Webinarkit campaigns or old ones?
  · is the person a RETURNING registrant (same email/phone in an earlier Register row)?
  · for returning people: is their oct28 UTM identical to their FIRST-ever row's UTM (= first-touch carry-over)?
  · new vs returning × UTM present / old-campaign UTM / Webinarkit UTM / blank."""
from __future__ import annotations

import re
from collections import Counter

from adbot.clients.sheets import SheetsClient
from adbot.settings import REPO_ROOT, load_settings

s = load_settings(REPO_ROOT / "config" / "config.sg.yaml")
reg = SheetsClient(s.secrets.google_sa_json).read_tab(s.cpa.spreadsheet_id, "Register")
hi = next(i for i, r in enumerate(reg[:8]) if "UTM Campaign" in r)
h = reg[hi]
rows = [dict(zip(h, r)) for r in reg[hi + 1:]]
em = lambda v: (v or "").strip().lower()
tel = lambda v: re.sub(r"\D", "", v or "")[-8:]
first = {}                                  # person key -> first row index
for i, r in enumerate(rows):
    for k in (em(r.get("Email")), tel(r.get("Phone Number"))):
        if k and k not in first:
            first[k] = i


def kind(u: str) -> str:
    u = (u or "").strip().lower()
    if not u:
        return "空白"
    return "Webinarkit" if "webinarkit" in u else "旧 campaign"


tab, names, same_first = Counter(), Counter(), Counter()
for i, r in enumerate(rows):
    if "oct28" not in (r.get("Source") or "").lower():
        continue
    keys = [k for k in (em(r.get("Email")), tel(r.get("Phone Number"))) if k]
    f = min((first[k] for k in keys), default=i)
    returning = f < i
    u = (r.get("UTM Campaign") or "").strip()
    tab[("回头客" if returning else "新客", kind(u))] += 1
    names[u[:60] or "(空白)"] += 1
    if returning and u:
        fu = (rows[f].get("UTM Campaign") or "").strip()
        same_first["与第一次报名的 UTM 相同" if fu == u else "与第一次不同"] += 1
print("webinar_oct28 报名 · 新客/回头客 × UTM 类型:")
for k, v in sorted(tab.items()):
    print(f"   {k[0]} · {k[1]:<12} {v}")
print("\n回头客中带 UTM 的，是否等于他第一次报名时的 UTM:", dict(same_first))
print("\nUTM campaign 名字（前 15）:")
for n, v in names.most_common(15):
    print(f"   {v:>4}  {n}")
print("\nUTM DIAG DONE (read-only)")
