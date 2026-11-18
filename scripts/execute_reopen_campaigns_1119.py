# -*- coding: utf-8 -*-
"""owner 2026-11-18 ~22:3x「等下 00:00 开完我今天 11:20am 左右关的广告」+ ~23:0x「你要确保有开到哦！有时候 campaign 开了，ad set/ ad 没有开到。」
At 11/19 00:00 MYT:
 1) CAMPAIGN layer ACTIVE for the 7 campaigns the owner paused on 11/18 11:21–11:22 (activity log, actor Thelyin Siew);
 2) for each EXPECTED ad — the 6 ads that were live before 11:20 + BUSINESS OWNER 盖电脑 (owner-approved 11/17, reconfirmed 11/18) —
    make sure ad set AND ad are ACTIVE too, then read back the ad's effective_status (what Meta actually delivers) and flag anything ≠ ACTIVE.
Nothing else is opened: ads paused by the monitor or by the owner earlier stay paused.
Safety gate: a banned / 🚫 / DISAPPROVED ad is never opened; a campaign with such an ad armed is not opened.
Refuses writes before 2026-11-19 00:00 MYT. CONFIRM=true writes + reads back; otherwise dry-run."""
from __future__ import annotations

import datetime as dt
import os
import time

from adbot import compliance
from adbot.commands import graph_client
from adbot.settings import REPO_ROOT, load_settings

CONFIRM = os.environ.get("CONFIRM", "").lower() in ("1", "true", "yes")
NOW = dt.datetime.utcnow() + dt.timedelta(hours=8)
CAMPS = {
    "config.my5.yaml": [("120251454713670329", "DAY TRADING | 1-1-5 | 1017"), ("120251840045110329", "NEW VIDEO · News | 1-5-1 | 1110"),
                        ("120251840367640329", "NEW VIDEO · Broad | 1-5-1 | 1110"), ("120251454700150329", "BUSINESS OWNER | 1-1-5 | 1017"),
                        ("120251454704570329", "BROAD MY | 1-1-5 | 1017")],
    "config.sg.yaml": [("120250144810670521", "BROAD SG | 1-1-5 | 1030"), ("120250544490730521", "NEW VIDEO · Broad | 1-5-1 | 1110")],
}
EXPECT = {  # ad id: (account cfg, ad-name must contain)
    "120251454717600329": ("config.my5.yaml", "年纪大"), "120251455974450329": ("config.my5.yaml", "korea"),
    "120251840059300329": ("config.my5.yaml", "决定变少"), "120251840063080329": ("config.my5.yaml", "不适合你"),
    "120251840432100329": ("config.my5.yaml", "炒了五年"), "120251454701640329": ("config.my5.yaml", "盖电脑"),
    "120250544546540521": ("config.sg.yaml", "决定变少"),
}
print(f"现在 {NOW:%m-%d %H:%M} MYT · {'APPLY' if CONFIRM else 'DRY-RUN'}")
if CONFIRM:
    assert NOW >= dt.datetime(2026, 11, 19, 0, 0), "owner said 00:00 — refusing before 2026-11-19 00:00 MYT"
bad_camps = set()
for cfg, camps in CAMPS.items():
    s = load_settings(REPO_ROOT / "config" / cfg)
    g = graph_client(s)
    print(f"\n######## {cfg} — 1) campaign 层")
    for cid, must in camps:
        c = g.get_object(cid, "name,status,daily_budget")
        assert must in c["name"], (cid, c["name"])
        ads = g._get_all(cid + "/ads", {"fields": "name,status,effective_status,adset{status}", "limit": "200"})
        bad = [a for a in ads if (a["status"] == "ACTIVE" or a["id"] in EXPECT)
               and (compliance.is_banned(a["name"], s.compliance.banned_creatives) or "🚫" in a["name"]
                    or a["effective_status"] in ("DISAPPROVED", "WITH_ISSUES"))]
        cb = int(c.get("daily_budget") or 0) / 100
        print(f"  {c['name']} · campaign {cid} · 现在 {c['status']}" + (f" · CBO RM{cb:g}" if cb else " · ABO"))
        if bad:
            bad_camps.add(cid)
            print("     ⛔ 有禁跑 / 被拒的 ad → 这个 campaign 不开：" + "；".join(f"{a['name']} · ad {a['id']}" for a in bad))
            continue
        if CONFIRM and c["status"] != "ACTIVE":
            g.update_status(cid, "ACTIVE"); time.sleep(2)
        if CONFIRM:
            print(f"     ✅ 回读 campaign {g.get_object(cid, 'status')['status']}")

print("\n######## 2) 应该在跑的 7 支：三层都开 + 读回实际投放状态")
tot = 0.0
for aid, (cfg, must) in EXPECT.items():
    s = load_settings(REPO_ROOT / "config" / cfg)
    g = graph_client(s)
    a = g.get_object(aid, "name,status,effective_status,adset{id,name,status,daily_budget},campaign{id,name,status,daily_budget}")
    aset, camp = a["adset"], a["campaign"]
    assert must in a["name"] and camp["id"] in {c for v in CAMPS.values() for c, _ in v}, (aid, a["name"], camp["name"])
    print(f"  {camp['name'].replace('(Webinarkit) ', '')} › {aset['name']} · {a['name']} · ad {aid}")
    print(f"     现在 campaign {camp['status']} / ad set {aset['status']} / ad {a['status']} → 实际 {a['effective_status']}")
    if camp["id"] in bad_camps or compliance.is_banned(a["name"], s.compliance.banned_creatives) or "🚫" in a["name"] \
            or a["effective_status"] in ("DISAPPROVED", "WITH_ISSUES"):
        print("     ⛔ 禁跑 / 被拒 → 不开")
        continue
    if CONFIRM:
        for oid, st in ((aset["id"], aset["status"]), (aid, a["status"])):
            if st != "ACTIVE":
                g.update_status(oid, "ACTIVE"); time.sleep(2)
        time.sleep(3)
        b = g.get_object(aid, "status,effective_status,adset{status,effective_status},campaign{status}")
        ok = b["effective_status"] == "ACTIVE"
        print(f"     {'✅' if ok else '⚠️ 还没在投放'} 回读 campaign {b['campaign']['status']} / ad set {b['adset']['status']} / ad {b['status']} → 实际 {b['effective_status']}")
    tot += int(aset.get("daily_budget") or 0) / 100
for cfg, camps in CAMPS.items():
    s = load_settings(REPO_ROOT / "config" / cfg)
    g = graph_client(s)
    for cid, _ in camps:
        if cid in bad_camps:
            continue
        cb = int(g.get_object(cid, "daily_budget").get("daily_budget") or 0) / 100
        if cb and any(graph_client(load_settings(REPO_ROOT / "config" / c2)).get_object(x, "campaign{id}")["campaign"]["id"] == cid
                      for x, (c2, _) in EXPECT.items() if c2 == cfg):
            tot += cb
print(f"\n会花钱的日预算合计约 RM{tot:,.0f}")
print("REOPEN 1119 DONE" + ("" if CONFIRM else " (dry-run)"))
