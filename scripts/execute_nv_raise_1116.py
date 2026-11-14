# -*- coding: utf-8 -*-
"""owner 2026-11-14 ~18:0x「周一加」to my proposal: Monday 11/16 00:00 MYT raise two MY NEW VIDEO ad sets by 20%,
each only if its Sat+Sun (11/14–11/15) CPL is still ≤ RM30 (≥1 报名). Reason for Monday (not now): last live,
Mon–Wed registrants showed up 30% vs Thu–Sun 4%.

  · NEW VIDEO · News  › News | MY 28+ · V4  · ad 120251840059300329 (决定变少) — ad set RM50 → RM60
  · NEW VIDEO · Broad › Broad | MY 28+ · V2 · ad 120251840432100329 (炒了五年) — ad set RM60 → RM72

Each judged on its own. Also requires ad / ad set / campaign ACTIVE, not banned / DISAPPROVED, and the ad set budget
still at the expected old value (someone changed it → don't touch). Refuses writes before 2026-11-16 00:00 MYT.
CONFIRM=true writes and reads back; otherwise dry-run."""
from __future__ import annotations

import datetime as dt
import json
import os
import time

from adbot import compliance
from adbot.commands import graph_client
from adbot.monitor_cpl import extract_results
from adbot.settings import REPO_ROOT, load_settings

CONFIRM = os.environ.get("CONFIRM", "").lower() in ("1", "true", "yes")
NOW = dt.datetime.utcnow() + dt.timedelta(hours=8)
D0, D1, MAXCPL = dt.date(2026, 11, 14), dt.date(2026, 11, 15), 30.0
TOK = "offsite_conversion.custom.1048291251556714"
ADS = [  # ad id, campaign must, ad set must, ad name must, old cents, new cents
    ("120251840059300329", "NEW VIDEO · News", "News | MY 28+ · V4", "决定变少", 5000, 6000),
    ("120251840432100329", "NEW VIDEO · Broad", "Broad | MY 28+ · V2", "炒了五年", 6000, 7200),
]
tr = lambda a, b: json.dumps({"since": a.isoformat(), "until": b.isoformat()})

s = load_settings(REPO_ROOT / "config" / "config.my5.yaml")
g = graph_client(s)
print(f"现在 {NOW:%m-%d %H:%M} MYT · {'APPLY' if CONFIRM else 'DRY-RUN'} · 判断窗口 {D0:%m/%d}–{D1:%m/%d}（周六+周日）")
if CONFIRM:
    assert NOW >= dt.datetime(2026, 11, 16, 0, 0), "owner said Monday — refusing before 2026-11-16 00:00 MYT"
n = 0
for aid, cm, sm, am, old, new in ADS:
    a = g.get_object(aid, "name,status,effective_status,adset{id,name,status,daily_budget},campaign{id,name,status}")
    aset, camp = a["adset"], a["campaign"]
    assert cm in camp["name"] and sm in aset["name"] and am in a["name"], (aid, camp["name"], aset["name"], a["name"])
    rows = g._get_all(aid + "/insights", {"fields": "spend,actions", "time_range": tr(D0, D1)})
    sp = sum(float(r.get("spend") or 0) for r in rows)
    rg = sum(extract_results(r.get("actions"), TOK) for r in rows)
    cpl = sp / rg if rg else float("inf")
    cur = int(aset.get("daily_budget") or 0)
    print(f"  {camp['name']} › {aset['name']} · {a['name']} · ad {aid}")
    print(f"    ad {a['status']}/{a['effective_status']} · ad set {aset['id']} {aset['status']} RM{cur / 100:g} · campaign {camp['status']}")
    print(f"    周六+周日 RM{sp:.2f} / {rg:.0f} 报名 · CPL {cpl:.0f}")
    why = []
    if NOW < dt.datetime(2026, 11, 16, 0, 0):
        why.append("还没到周一 00:00，周日还没过完")
    if not (rg >= 1 and cpl <= MAXCPL):
        why.append(f"周六+周日不稳（{rg:.0f} 报名，CPL {cpl:.0f}，要 ≥1 报名且 ≤{MAXCPL:.0f}）")
    if compliance.is_banned(a["name"], s.compliance.banned_creatives) or "🚫" in a["name"]:
        why.append("禁跑素材")
    if a["effective_status"] != "ACTIVE" or aset["status"] != "ACTIVE" or camp["status"] != "ACTIVE":
        why.append("ad / ad set / campaign 不是全部 ACTIVE（有人关了？）")
    if cur != old:
        why.append(f"ad set 预算现在是 RM{cur / 100:g}，不是 RM{old / 100:g}（有人改过）→ 不动")
    if why:
        print("    ⏸ 不加：" + "；".join(why))
        continue
    print(f"    ✅ 稳 → ad set {aset['id']} RM{old / 100:g} → RM{new / 100:g}")
    if CONFIRM:
        g.update_daily_budget(aset["id"], new); time.sleep(2); n += 1
        print(f"      ✅ 回读 RM{int(g.get_object(aset['id'], 'daily_budget')['daily_budget']) / 100:g}")
print(f"加了 {n} 支" + ("" if CONFIRM else "（dry-run）") + "\nNV RAISE 1116 DONE")
