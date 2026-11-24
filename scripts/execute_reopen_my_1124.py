# -*- coding: utf-8 -*-
"""owner 2026-11-24 (AskUserQuestion)「只开 MY，上限 RM6250」→ after PR #100 (spend_cap 6000 → 6250, stop line RM6,200) is on main,
reopen ONLY the 5 MY 5.0 campaigns the spend cap paused at 14:20 MYT, at the CAMPAIGN layer. SG stays paused.

Only campaigns whose last status change was the monitor's CAP-PAUSE are touched; ad sets / ads are never switched on
(anything paused there was closed by the monitor or the owner = 定案). Per campaign it refuses when: name / account /
(Webinarkit) prefix don't match; any banned / 🚫 / DISAPPROVED / WITH_ISSUES ad is still ad-level ACTIVE (上膛);
no ad set + ad is left ACTIVE. Refuses everything unless the cycle spend is under the new stop line (RM6,200).
Reads back every ad's effective_status (owner 11/18「你要确保有开到」). CONFIRM=true writes + reads back; otherwise dry-run."""
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
TARGETS = [  # (campaign id, name must contain) — the 5 MY campaigns CAP-PAUSED 11/24 14:20 (monitor log + activity log)
    ("120251454704570329", "BROAD MY | 1-1-5 | 1017"),
    ("120251840045110329", "NEW VIDEO · News | 1-5-1 | 1110"),
    ("120251993979260329", "BEST CPA · Broad | 1-1-3 | 1120"),
    ("120251993985380329", "LOW CPL · Broad | 1-1-3 | 1120"),
    ("120251995650640329", "CBO · LUX BEER OMAKASE | 1-3-3 | 1120"),
]

now = dt.datetime.utcnow() + dt.timedelta(hours=8)
s = load_settings(REPO_ROOT / "config" / "config.my5.yaml")
g = graph_client(s)
print(f"现在 {now:%m-%d %H:%M} MYT · {'APPLY' if CONFIRM else 'DRY-RUN'} · 只开 MY（上限 RM{s.spend_cap.cap_myr:,.0f}）")
assert s.spend_cap.cap_myr == 6250, f"config cap is {s.spend_cap.cap_myr}, expected 6250 (PR #100)"
st = spend_cap_status(g, s, now)
assert st, "spend cap window not open — refusing"
total, line = st
print(f"周期花费（11/19 起两账户）RM{total:,.2f} / 关停线 RM{line:,.0f} · 还剩 RM{line - total:,.2f}")
assert total < line, "spend already at the new stop line — monitor would re-pause; refusing"


def bad(a) -> bool:
    return compliance.is_banned(a["name"], s.compliance.banned_creatives) or "🚫" in a["name"] or a["effective_status"] in BAD_EFF


opened = []
for cid, must in TARGETS:
    c = g.get_object(cid, "name,status,effective_status,daily_budget,account_id")
    cb = int(c.get("daily_budget") or 0) // 100
    print(f"\n■ {c['name']} · campaign {cid} · {c['status']} → 实际 {c['effective_status']} · " + (f"CBO RM{cb}" if cb else "ABO"))
    assert must in c["name"], (cid, c["name"])
    assert c["name"].lower().startswith("(webinarkit)"), ("not a Webinarkit campaign", c["name"])
    assert s.meta.account_path == "act_" + str(c["account_id"]), c["account_id"]
    ads = g._get_all(cid + "/ads", {"fields": "name,status,effective_status,adset{id,name,status,daily_budget}", "limit": "200"})
    armed_bad = [a for a in ads if bad(a) and a["status"] == "ACTIVE"]
    live = [a for a in ads if a["status"] == "ACTIVE" and a["adset"]["status"] == "ACTIVE" and not bad(a)]
    for a in ads:
        tag = "⛔ 禁跑/被拒" if bad(a) else ("会投放" if a in live else "关着（不动）")
        ab = int(a["adset"].get("daily_budget") or 0) // 100
        print(f"   {a['adset']['name']}{f' (RM{ab})' if ab else ''} · {a['name']} · ad {a['id']} — ad set {a['adset']['status']} / ad {a['status']} → {tag}")
    if armed_bad:
        print("   ⛔ 有禁跑 / 被拒的 ad 在 ad 层开着 → 这个 campaign 不开")
        continue
    if not live:
        print("   ⛔ 没有开着的 ad set + ad → 不开")
        continue
    if not CONFIRM:
        print(f"   (dry-run) 会在 campaign 层开回，{len(live)} 支 ad 会投放")
        continue
    if c["status"] != "ACTIVE":
        g.update_status(cid, "ACTIVE")
        time.sleep(3)
    opened.append((cid, live))

for cid, live in opened:
    for _ in range(8):
        time.sleep(6)
        rows = [g.get_object(a["id"], "name,status,effective_status,adset{status},campaign{status,name}") for a in live]
        if all(r["effective_status"] == "ACTIVE" for r in rows):
            break
    for r in rows:
        ok = r["effective_status"] == "ACTIVE"
        print(f"   {'✅' if ok else '⚠️ 还没在投放'} {r['campaign']['name']} · {r['name']} · ad {r['id']} — campaign {r['campaign']['status']}"
              f" / ad set {r['adset']['status']} / ad {r['status']} → 实际 {r['effective_status']}")

for lab, cfg in (("MY", "config.my5.yaml"), ("SG", "config.sg.yaml")):
    s2 = load_settings(REPO_ROOT / "config" / cfg)
    rows = graph_client(s2)._get_all(s2.meta.account_path + "/campaigns", {"fields": "name,effective_status,daily_budget", "limit": "500",
                                                                           "effective_status": '["ACTIVE"]'})
    print(f"\n-- {lab} 开着的 campaign：{len(rows)} 个")
    for r in rows:
        cb = int(r.get("daily_budget") or 0) // 100
        print(f"   {r['name']} · {r['id']}" + (f" · CBO RM{cb}" if cb else " · ABO"))
print("REOPEN MY 1124 DONE" + ("" if CONFIRM else " (dry-run)"))
