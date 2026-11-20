# -*- coding: utf-8 -*-
"""owner 2026-11-20「三支都保护，合并后开回」(AskUserQuestion, recommended option). The monitor closed these 3 ads at 10:40 MYT
(cpa_hard_stop) right after WK reopened them; PR #97 (merged dc0b15f) exempts exactly these ad IDs from the CPA hard stop until 11/25.
Re-opens ONLY the ad layer of the 3 (campaign + ad set are WK's and already ACTIVE — never touched here), then reads back effective_status
(owner 11/18「你要确保有开到」). Refuses an ad when: name / account mismatch; campaign not ACTIVE or not (Webinarkit); ad set not ACTIVE;
banned / 🚫 / DISAPPROVED / WITH_ISSUES; its ID missing from cpa.hold_ad_until (monitor would close it again). Refuses everything when
the RM5,950 cycle spend cap is already reached. CONFIRM=true writes + reads back; otherwise dry-run."""
from __future__ import annotations

import datetime as dt
import os
import sys
import time

from adbot import compliance
from adbot.commands import graph_client
from adbot.monitor_cpl import spend_cap_status
from adbot.settings import REPO_ROOT, load_settings

sys.stdout.reconfigure(line_buffering=True)
CONFIRM = os.environ.get("CONFIRM", "").lower() in ("1", "true", "yes")
NOW = dt.datetime.utcnow() + dt.timedelta(hours=8)
TARGETS = [("config.my5.yaml", "120251456191090329", "korea", "BROAD MY"),
           ("config.my5.yaml", "120251454702680329", "年纪大", "BUSINESS OWNER"),
           ("config.sg.yaml", "120249918410030521", "用我的方法", "PURCHASE LAL 5%")]
print(f"现在 {NOW:%m-%d %H:%M} MYT · {'APPLY' if CONFIRM else 'DRY-RUN'} · 只开 ad 层（3 支）")
s_my = load_settings(REPO_ROOT / "config" / "config.my5.yaml")
st = spend_cap_status(graph_client(s_my), s_my, NOW)
if st:
    print(f"周期花费 RM{st[0]:,.0f} / 关停线 RM{st[1]:,.0f}")
    assert st[0] < st[1], "spend cap reached — refusing"
done = []
for cfg, aid, must_ad, must_camp in TARGETS:
    s = load_settings(REPO_ROOT / "config" / cfg)
    g = graph_client(s)
    a = g.get_object(aid, "name,status,effective_status,account_id,adset{id,name,status},campaign{id,name,status}")
    print(f"\n■ {a['campaign']['name']} › {a['adset']['name']} · {a['name']} · ad {aid}")
    print(f"   现在 campaign {a['campaign']['status']} / ad set {a['adset']['status']} / ad {a['status']} → 实际 {a['effective_status']}")
    assert s.meta.account_path == "act_" + str(a["account_id"]), (cfg, a["account_id"])
    assert must_ad in a["name"] and must_camp in a["campaign"]["name"], (aid, a["name"], a["campaign"]["name"])
    assert str(aid) in (s.cpa.hold_ad_until or {}), f"{aid} not in cpa.hold_ad_until — monitor would close it again"
    print(f"   CPA 硬线豁免到 {s.cpa.hold_ad_until[str(aid)]}")
    why = []
    if not a["campaign"]["name"].lower().startswith("(webinarkit)"):
        why.append("不是 (Webinarkit)")
    if a["campaign"]["status"] != "ACTIVE":
        why.append("campaign 关着（owner 的，不替他开）")
    if a["adset"]["status"] != "ACTIVE":
        why.append("ad set 关着（不替他开）")
    if compliance.is_banned(a["name"], s.compliance.banned_creatives) or a["effective_status"] in ("DISAPPROVED", "WITH_ISSUES"):
        why.append("禁跑 / 被拒")
    if why:
        print("   ⛔ 不开：" + "；".join(why))
        continue
    if a["status"] == "ACTIVE":
        print("   ad 已经是开的 → 只读回")
    elif CONFIRM:
        g.update_status(aid, "ACTIVE")
        print("   → 已送出 ad ACTIVE")
    else:
        print("   (dry-run) 会把 ad 层开起来")
    done.append((g, aid))
if CONFIRM:
    for i in range(10):
        time.sleep(6)
        rows = [g.get_object(aid, "name,status,effective_status,adset{status},campaign{status}") for g, aid in done]
        if all(r["effective_status"] == "ACTIVE" for r in rows):
            break
    print("\n-- 读回")
    for r in rows:
        ok = r["effective_status"] == "ACTIVE"
        print(f"   {'✅' if ok else '⚠️ 还没在投放'} {r['name']} · ad {r['id']} — campaign {r['campaign']['status']} / ad set {r['adset']['status']}"
              f" / ad {r['status']} → 实际 {r['effective_status']}")
print("\nREOPEN CPA HOLD 3 DONE" + ("" if CONFIRM else " (dry-run)"))
