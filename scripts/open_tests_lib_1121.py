# -*- coding: utf-8 -*-
"""Shared logic for owner 2026-11-19 「方案 B，我排程自动开」 (test campaigns built PAUSED on 11/19):
  Sat 11/21 00:00 MYT → SG 1-1-3 BEST · Broad + MY CBO · LUX BEER OMAKASE   (execute_open_tests_1121.py)
  Sun 11/22 00:00 MYT → SG CBO · LAL INVEST LUX                              (execute_open_tests_1122.py)
  SG 1-1-3 LOW CPL stays PAUSED (not in either list).

Only the CAMPAIGN layer is switched on (ad sets / ads were built ACTIVE). An ad set / ad found PAUSED at run time was paused by someone
after the build → reported, never re-opened (owner manual close = 定案). Then reads back every ad's effective_status
(owner 11/18:「你要确保有开到」).
Refuses a campaign when: name / account / (Webinarkit) prefix don't match; any ad is banned / 🚫 / DISAPPROVED / WITH_ISSUES;
no ad set + ad is left ACTIVE. Refuses everything when the RM6,000 cycle spend cap (spend_cap) is already reached.
Refuses writes before the scheduled time. CONFIRM=true writes + reads back; otherwise dry-run."""
from __future__ import annotations

import datetime as dt
import os
import time

from adbot import compliance
from adbot.commands import graph_client
from adbot.monitor_cpl import spend_cap_status
from adbot.settings import REPO_ROOT, load_settings

CONFIRM = os.environ.get("CONFIRM", "").lower() in ("1", "true", "yes")
BAD_EFF = ("DISAPPROVED", "WITH_ISSUES")


def _now_myt() -> dt.datetime:
    return dt.datetime.utcnow() + dt.timedelta(hours=8)


def _bad(name: str, eff: str, s) -> bool:
    return compliance.is_banned(name, s.compliance.banned_creatives) or "🚫" in name or eff in BAD_EFF


def open_campaigns(targets, not_before: dt.datetime, label: str) -> None:
    """targets: [(cfg file, campaign id, name must contain)]"""
    now = _now_myt()
    print(f"现在 {now:%m-%d %H:%M} MYT · {'APPLY' if CONFIRM else 'DRY-RUN'} · {label}")
    if CONFIRM:
        assert now >= not_before, f"scheduled for {not_before:%m-%d %H:%M} MYT — refusing earlier"

    s_my = load_settings(REPO_ROOT / "config" / "config.my5.yaml")
    try:
        st = spend_cap_status(graph_client(s_my), s_my, now)
    except Exception as exc:  # noqa: BLE001
        st = None
        print(f"⚠️ 读不到周期花费（{exc}）")
        assert not CONFIRM, "can't verify the RM6,000 cap — refusing to open"
    if st:
        total, line = st
        print(f"周期花费（11/19 起两账户）RM{total:,.0f} / 关停线 RM{line:,.0f}")
        assert total < line, "spend cap already reached — monitor would pause everything; refusing to open"

    for cfg, cid, must in targets:
        s = load_settings(REPO_ROOT / "config" / cfg)
        g = graph_client(s)
        c = g.get_object(cid, "name,status,effective_status,daily_budget,account_id")
        print(f"\n■ {c['name']} · campaign {cid}")
        assert must in c["name"], (cid, c["name"])
        assert c["name"].lower().startswith("(webinarkit)"), ("not a Webinarkit campaign", c["name"])
        assert s.meta.account_path == "act_" + str(c["account_id"]), (cfg, c["account_id"])
        cb = int(c.get("daily_budget") or 0) / 100
        print(f"   现在 campaign {c['status']} → 实际 {c['effective_status']} · CBO RM{cb:g}" + ("" if cb == 100 else " ⚠️ 不是 RM100（不改，照现状）"))
        adsets = g._get_all(cid + "/adsets", {"fields": "name,status,effective_status", "limit": "100"})
        ads = g._get_all(cid + "/ads", {"fields": "name,status,effective_status,adset{id,name,status}", "limit": "200"})
        bad = [a for a in ads if _bad(a["name"], a["effective_status"], s)]
        for a in ads:
            print(f"   {a['adset']['name']} · {a['name']} · ad {a['id']} — ad set {a['adset']['status']} / ad {a['status']} → 实际 {a['effective_status']}")
        off = [x for x in adsets if x["status"] != "ACTIVE"] + [a for a in ads if a["status"] != "ACTIVE"]
        for x in off:
            print(f"   ⚠️ {x['name']} · {x['id']} 被人关了（建好时是开的）→ 不替他开")
        live = [a for a in ads if a["status"] == "ACTIVE" and a["adset"]["status"] == "ACTIVE" and not _bad(a["name"], a["effective_status"], s)]
        if bad:
            print("   ⛔ 有禁跑 / 被拒的 ad → 这个 campaign 不开：" + "；".join(f"{a['name']} · ad {a['id']} → {a['effective_status']}" for a in bad))
            continue
        if not live:
            print("   ⛔ 没有开着的 ad set + ad → 不开")
            continue
        if not CONFIRM:
            print(f"   (dry-run) 会把 campaign 开起来，{len(live)} 支 ad 会投放")
            continue
        if c["status"] != "ACTIVE":
            g.update_status(cid, "ACTIVE"); time.sleep(3)
        else:
            print("   campaign 已经是开的（不是我开的）→ 只读回")
        for i in range(8):
            time.sleep(6)
            rows = [g.get_object(a["id"], "name,status,effective_status,adset{status,effective_status},campaign{status}") for a in live]
            if all(r["effective_status"] == "ACTIVE" for r in rows):
                break
        for r in rows:
            ok = r["effective_status"] == "ACTIVE"
            print(f"   {'✅' if ok else '⚠️ 还没在投放'} {r['name']} · ad {r['id']} — 回读 campaign {r['campaign']['status']} / ad set {r['adset']['status']}"
                  f" / ad {r['status']} → 实际 {r['effective_status']}")

    print("\n-- 两个账户所有实际在投放的 ad（campaign 前面要有 (Webinarkit)）:")
    tot = {}
    for lab, cfg in (("MY", "config.my5.yaml"), ("SG", "config.sg.yaml")):
        s2 = load_settings(REPO_ROOT / "config" / cfg)
        g2 = graph_client(s2)
        rows = g2._get_all(s2.meta.account_path + "/ads", {"fields": "name,effective_status,adset{id,name,daily_budget},campaign{id,name,daily_budget}",
                                                          "limit": "500", "effective_status": '["ACTIVE","IN_PROCESS","PENDING_REVIEW"]'})
        for r in rows:
            ok = r["campaign"]["name"].lower().startswith("(webinarkit)")
            cbud = int(r["campaign"].get("daily_budget") or 0) // 100
            key, bud = (r["campaign"]["id"], cbud) if cbud else (r["adset"]["id"], int(r["adset"].get("daily_budget") or 0) // 100)
            tot[(lab, key)] = bud
            print(f"   {'✅' if ok else '❌ 不是 Webinarkit'} {lab} {r['campaign']['name']} › {r['adset']['name']} · {r['name']} · ad {r['id']} → {r['effective_status']}")
        if not rows:
            print(f"   {lab}: 0 支")
    my = sum(v for (lab, _), v in tot.items() if lab == "MY")
    sg = sum(v for (lab, _), v in tot.items() if lab == "SG")
    print(f"\n在投放的日预算合计约 RM{my + sg:,}（MY {my} / SG {sg}）")
    print(f"OPEN TESTS {label} DONE" + ("" if CONFIRM else " (dry-run)"))
