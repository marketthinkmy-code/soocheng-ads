# -*- coding: utf-8 -*-
"""owner 2026-11-13 10:0x「OK」to: MY NEW VIDEO · Broad › Broad | MY 28+ · V2 · ad 120251840432100329
(周四起 7 报名 CPL 14) — 「建议明天还稳的话，ad set 从 RM50 加到 RM60（加 20%）」.

Run on/after Saturday 11/14 00:00 MYT (judges the full day 11/13). 「还稳」 = all of:
  · 11/13 full day: ≥1 报名 and CPL ≤ RM30;
  · Thu-week (11/12 → today): CPL ≤ RM30;
  · ad / ad set / campaign all ACTIVE, ad not banned / DISAPPROVED, ad set budget still RM50.
Stable + CONFIRM=true → ad set daily budget RM50 → RM60, read back. Otherwise no write, prints why."""
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
TODAY = NOW.date()
AD, OLD, NEW, MAXCPL = "120251840432100329", 5000, 6000, 30.0
D13, W0 = dt.date(2026, 11, 13), dt.date(2026, 11, 12)
TOK = "offsite_conversion.custom.1048291251556714"
tr = lambda a, b: json.dumps({"since": a.isoformat(), "until": b.isoformat()})

s = load_settings(REPO_ROOT / "config" / "config.my5.yaml")
g = graph_client(s)
print(f"现在 {NOW:%m-%d %H:%M} MYT · {'APPLY' if CONFIRM else 'DRY-RUN'}")
a = g.get_object(AD, "name,status,effective_status,adset{id,name,status,daily_budget},campaign{id,name,status}")
aset, camp = a["adset"], a["campaign"]
assert "NEW VIDEO · Broad" in camp["name"] and "V2" in aset["name"] and "炒了五年" in a["name"], (camp["name"], aset["name"], a["name"])
print(f"  {camp['name']} › {aset['name']} · {a['name']} · ad {AD}")
print(f"  ad {a['status']}/{a['effective_status']} · ad set {aset['id']} {aset['status']} RM{int(aset.get('daily_budget') or 0) // 100}"
      f" · campaign {camp['status']}")


def m(a0, b0):
    rows = g._get_all(AD + "/insights", {"fields": "spend,actions", "time_range": tr(a0, b0)})
    sp = sum(float(r.get("spend") or 0) for r in rows)
    rg = sum(extract_results(r.get("actions"), TOK) for r in rows)
    return sp, rg


ds, dr = m(D13, D13)
ws, wr = m(W0, TODAY)
cpl = lambda sp, rg: sp / rg if rg else float("inf")
print(f"  11/13 全天 RM{ds:.2f} / {dr:.0f} 报名 · CPL {cpl(ds, dr):.0f}")
print(f"  周四起 RM{ws:.2f} / {wr:.0f} 报名 · CPL {cpl(ws, wr):.0f}")

why = []
if TODAY <= D13:
    why.append("还没到 11/14，11/13 还没过完")
if not (dr >= 1 and cpl(ds, dr) <= MAXCPL):
    why.append(f"11/13 全天不稳（{dr:.0f} 报名，CPL {cpl(ds, dr):.0f} > {MAXCPL:.0f} 或 0 报名）")
if cpl(ws, wr) > MAXCPL:
    why.append(f"周四起 CPL {cpl(ws, wr):.0f} > {MAXCPL:.0f}")
if compliance.is_banned(a["name"], s.compliance.banned_creatives) or "🚫" in a["name"]:
    why.append("禁跑素材")
if a["effective_status"] != "ACTIVE" or aset["status"] != "ACTIVE" or camp["status"] != "ACTIVE":
    why.append("ad / ad set / campaign 不是全部 ACTIVE（有人关了？）")
cur = int(aset.get("daily_budget") or 0)
if cur != OLD:
    why.append(f"ad set 预算现在是 RM{cur // 100}，不是 RM50（有人改过）→ 不动")

if why:
    print("  ⏸ 不加：" + "；".join(why))
else:
    print(f"  ✅ 稳 → ad set {aset['id']} RM{OLD // 100} → RM{NEW // 100}")
    if CONFIRM:
        g.update_daily_budget(aset["id"], NEW); time.sleep(2)
        print(f"    ✅ 回读 RM{int(g.get_object(aset['id'], 'daily_budget')['daily_budget']) // 100}")
print("BROAD V2 60 DONE" + ("" if CONFIRM else " (dry-run)"))
