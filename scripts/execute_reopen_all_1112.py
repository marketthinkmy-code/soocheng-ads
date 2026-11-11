# -*- coding: utf-8 -*-
"""owner 2026-11-11 23:2x「帮我把我3pm左右关掉的广告 or 你认为值得开回去的广告 等下 00:00 帮我开回去」
(+ 15:4x「YES」to reopening the monitor-paused NEW VIDEO ads under the RM80 rule).

Thursday 11/12 00:00 MYT, in this order:
  1) ad layer first —
     · NEW VIDEO campaigns: every PAUSED ad back to ACTIVE (its ad set too if PAUSED);
     · EXTRA_ADS (my pick, each with an original-position sale since 10/29): back to ACTIVE, only if its ad set is ACTIVE;
     · ban gate: any 🚫 / banned_creatives ad that is ad-level ACTIVE under these campaigns → PAUSED (hard rule), reported.
  2) then the 9 campaigns WK hand-paused at 15:15 (MY) / 15:18 (SG) → ACTIVE.
  3) read back: campaign status, ad effective-status counts, daily budget that will deliver.
NOT touched: DAY TRADING (MY), PURCHASE LAL 5% / TRAVEL SG (SG) — WK paused those by hand earlier; no budget edits.
Refuses to write before 2026-11-12 00:00 MYT. CONFIRM=true writes; otherwise dry-run."""
from __future__ import annotations

import datetime as dt
import os
import time

from adbot import compliance
from adbot.commands import graph_client
from adbot.settings import REPO_ROOT, load_settings

CONFIRM = os.environ.get("CONFIRM", "").lower() in ("1", "true", "yes")
NOW = dt.datetime.utcnow() + dt.timedelta(hours=8)
CAMPS = {   # WK hand-paused these at campaign level on 11/11 (activity log, actor Thelyin Siew)
    "config.my5.yaml": {"120251840045110329": "NEW VIDEO · News", "120251840064210329": "NEW VIDEO · Luxury Goods",
                        "120251840367640329": "NEW VIDEO · Broad", "120251454704570329": "BROAD MY | 1-1-5 | 1017",
                        "120251454700150329": "BUSINESS OWNER | 1-1-5 | 1017"},
    "config.sg.yaml": {"120250544490730521": "NEW VIDEO · Broad", "120250544550400521": "NEW VIDEO · Travel",
                       "120250544649500521": "NEW VIDEO · Golf Pickleball", "120250144810670521": "BROAD SG | 1-1-5 | 1030"},
}
EXTRA_ADS = {   # monitor-paused old ads worth reopening (robust-UTM original-position sale since 10/29, CPA ≤ RM960)
    "config.my5.yaml": {"120251454701640329": "BUSINESS OWNER › 盖电脑 · 10/16起 RM158/7 · 原位成交 1 · CPA RM146"},
    "config.sg.yaml": {"120250144813920521": "BROAD SG › 用我的方法 · 10/16起 RM594/12 · 原位成交 1 · CPA RM594"},
}
BAD = ("DISAPPROVED", "WITH_ISSUES")


def T(fn, *a, **k):
    for i in range(10):
        try:
            return fn(*a, **k)
        except Exception as e:                                           # noqa: BLE001
            if "throttled" not in str(e) and "request limit" not in str(e).lower() and "too many calls" not in str(e).lower():
                raise
            print(f"      … 限流，等 60s（{i + 1}/10）"); time.sleep(60)
    raise RuntimeError("throttled")


def W(g, oid, status):
    if CONFIRM:
        T(g.update_status, oid, status); time.sleep(2)


print(f"现在 {NOW:%m-%d %H:%M} MYT · {'APPLY' if CONFIRM else 'DRY-RUN'}")
if CONFIRM:
    assert NOW >= dt.datetime(2026, 11, 12, 0, 0), "owner said 00:00 — refusing before 2026-11-12 00:00 MYT"
tot = {"ad": 0, "adset": 0, "camp": 0, "ban": 0}
for cfg, camps in CAMPS.items():
    s = load_settings(REPO_ROOT / "config" / cfg)
    g = graph_client(s)
    extra = EXTRA_ADS.get(cfg, {})
    print(f"\n################ {cfg}")
    for cid, expect in camps.items():
        c = T(g.get_object, cid, "name,status,effective_status,daily_budget")
        assert expect in c["name"], (cid, c["name"], expect)
        nv = "NEW VIDEO" in c["name"]
        ads = T(g._get_all, cid + "/ads", {"fields": "name,status,effective_status,adset{id,name,status,daily_budget}", "limit": "100"})
        print(f"  «{c['name']}» {cid} · {c['status']}/{c['effective_status']}")
        reopened_sets = set()
        for a in sorted(ads, key=lambda x: (x["adset"]["name"], x["name"])):
            st, ast = a["status"], a["adset"]["status"]
            ban = compliance.is_banned(a["name"], s.compliance.banned_creatives) or "🚫" in a["name"]
            tag = ""
            if ban:
                if st == "ACTIVE":
                    tag = " ⛔ 禁跑素材 ad 层上膛 → PAUSED"; W(g, a["id"], "PAUSED"); tot["ban"] += 1
                else:
                    tag = " ⛔ 禁跑，保持关"
            elif a["effective_status"] in BAD:
                tag = f" ⚠️ {a['effective_status']}，不开"
            elif st == "PAUSED" and (nv or a["id"] in extra):
                if ast != "ACTIVE" and not nv:
                    tag = " ⚠️ ad set 被关（人手？）→ 不开，交 WK"
                else:
                    if ast != "ACTIVE" and a["adset"]["id"] not in reopened_sets:
                        W(g, a["adset"]["id"], "ACTIVE"); reopened_sets.add(a["adset"]["id"]); tot["adset"] += 1
                    W(g, a["id"], "ACTIVE"); tot["ad"] += 1
                    tag = " → 开回" + (f"（{extra[a['id']]}）" if a["id"] in extra else "")
            elif st == "ACTIVE":
                tag = " · ad 层本来就开（campaign 开了就会跑）"
            print(f"      › «{a['adset']['name']}» [{ast}] · ad {a['id']} «{a['name']}» {st}/{a['effective_status']}{tag}")
        if c["status"] != "ACTIVE":
            W(g, cid, "ACTIVE"); tot["camp"] += 1
            print(f"    → campaign 开回")
    if CONFIRM:
        time.sleep(5)
        print("  -- 回读")
        day = 0
        for cid in camps:
            b = T(g.get_object, cid, "name,status,effective_status,daily_budget")
            rows = T(g._get_all, cid + "/ads", {"fields": "effective_status,adset{id,status,daily_budget}", "limit": "100"})
            cnt = {}
            for r in rows:
                cnt[r["effective_status"]] = cnt.get(r["effective_status"], 0) + 1
            if b.get("daily_budget"):
                bud = int(b["daily_budget"]) // 100 if cnt.get("ACTIVE") else 0
            else:
                bud = sum(int(x["daily_budget"]) // 100 for x in {r["adset"]["id"]: r["adset"] for r in rows
                          if r["effective_status"] == "ACTIVE" and r["adset"].get("daily_budget")}.values())
            day += bud
            print(f"    ✅ «{b['name']}» {cid} · {b['status']}/{b['effective_status']} · 广告 {cnt} · 会投放的日预算 RM{bud}")
        print(f"  ▶ {cfg} 开回后日预算合计 RM{day}")
print(f"\n开回 ad {tot['ad']} · ad set {tot['adset']} · campaign {tot['camp']} · 禁跑上膛拆掉 {tot['ban']}"
      + ("\nREOPEN ALL DONE" if CONFIRM else "\nREOPEN ALL DONE (dry-run)"))
