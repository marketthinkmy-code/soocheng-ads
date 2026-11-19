# -*- coding: utf-8 -*-
"""owner 2026-11-19 ~23:3x「MY 拿掉 AN」(AskUserQuestion, recommended option): remove the Audience Network placement from every
MY 5.0 ad set that is live (campaign + ad set ACTIVE, campaign name starts with (Webinarkit)) plus the 3 ad sets of the still-PAUSED
MY CBO · LUX BEER OMAKASE (campaign 120251995650640329). Evidence: 11/19 MY AN = RM135 (26% of spend) / 0 报名; 10/29 起 AN 28 报名 / 0 买家.
Only placement keys change: 'audience_network' leaves publisher_platforms and audience_network_positions is dropped; every other
targeting key (geo, age, interests, Advantage+ audience, other placements) is written back exactly as read. An ad set the API shows on automatic
placements gets explicit facebook + instagram + messenger + threads (all positions; IG Explore stays out where WK removed it today). Statuses and budgets untouched.
SG is NOT touched. CONFIRM=true writes and reads back (placements + every ad's effective_status); otherwise dry-run."""
from __future__ import annotations

import json
import os
import time

from adbot.commands import graph_client
from adbot.settings import REPO_ROOT, load_settings

CONFIRM = os.environ.get("CONFIRM", "").lower() in ("1", "true", "yes")
MY_CBO = "120251995650640329"
# WK removed Instagram Explore himself on 11/19 (activity log 15:53 MY 1-1-3, 17:00/17:06 MY CBO) — keep it removed there.
NO_EXPLORE = {"120251993979530329", "120251993987750329", "120251995652710329", "120251995661220329", "120251995666640329"}
# Meta API: Explore home needs Explore → with Explore out, Explore home goes too (11/19 23:4x 400 error).
IG_NO_EXPLORE = ["stream", "story", "reels", "profile_feed", "ig_search"]
PL_KEYS = ("publisher_platforms", "facebook_positions", "instagram_positions", "messenger_positions",
           "audience_network_positions", "threads_positions", "whatsapp_positions")

s = load_settings(REPO_ROOT / "config" / "config.my5.yaml")
g = graph_client(s)
assert s.meta.account_path == "act_2285351942292267", s.meta.account_path
print("APPLY" if CONFIRM else "DRY-RUN", "· MY 5.0 · 只改版位：拿掉 Audience Network")
asets = g._get_all(s.meta.account_path + "/adsets", {"fields": "id,name,status,effective_status,targeting,campaign{id,name,status}",
                                                    "limit": "500"})
pick = []
for a in asets:
    if not a["campaign"]["name"].lower().startswith("(webinarkit)"):
        continue
    if a["campaign"]["id"] == MY_CBO:
        pick.append(a); continue
    if a["campaign"]["status"] == "ACTIVE" and a["status"] == "ACTIVE":
        ads = g._get_all(a["id"] + "/ads", {"fields": "status", "limit": "50"})
        if any(x["status"] == "ACTIVE" for x in ads):
            pick.append(a)
print(f"选到 {len(pick)} 个 ad set（有 ad 在跑的 + MY CBO）")
todo = []
for a in pick:
    t = dict(a["targeting"])
    pp = t.get("publisher_platforms")
    print(f"\n■ {a['campaign']['name'].replace('(Webinarkit) ', '')} › {a['name']} · adset {a['id']} · campaign {a['campaign']['status']} / ad set {a['status']}")
    if pp:
        print("   现在: " + " · ".join(f"{k}={t.get(k)}" for k in PL_KEYS if k in t))
        if "audience_network" not in pp:
            print("   ✅ 已经没有 AN → 不动"); continue
        nt = dict(t)
        nt["publisher_platforms"] = [p for p in pp if p != "audience_network"]
        nt.pop("audience_network_positions", None)
    else:
        print("   现在: API 显示自动版位（含 AN）" + ("；WK 今天拿掉过 IG Explore" if a["id"] in NO_EXPLORE else ""))
        nt = dict(t)
        nt["publisher_platforms"] = ["facebook", "instagram", "messenger", "threads"]
        if a["id"] in NO_EXPLORE:
            nt["instagram_positions"] = IG_NO_EXPLORE
    print("   改成: " + " · ".join(f"{k}={nt.get(k)}" for k in PL_KEYS if k in nt))
    other = {k for k in set(t) | set(nt) if k not in PL_KEYS and t.get(k) != nt.get(k)}
    assert not other, ("non-placement keys would change", other)
    todo.append((a, nt))

print(f"\n要改 {len(todo)} 个 ad set")
if CONFIRM:
    done, failed = [], []
    for a, nt in todo:
        try:
            g.update_targeting(a["id"], nt); done.append(a)
        except Exception as exc:  # noqa: BLE001
            msg = str(exc)
            if "threads" in msg.lower() and "threads" in nt.get("publisher_platforms", []):
                nt = dict(nt); nt["publisher_platforms"] = [p for p in nt["publisher_platforms"] if p != "threads"]
                nt.pop("threads_positions", None)
                try:
                    g.update_targeting(a["id"], nt); done.append(a)
                    print(f"   ⚠️ {a['name']} · adset {a['id']}: threads 不能放 → 已改成不带 threads")
                except Exception as exc2:  # noqa: BLE001
                    failed.append((a, str(exc2)[:200]))
            else:
                failed.append((a, msg[:200]))
        time.sleep(2)
    for a, m in failed:
        print(f"   ❌ 没改到 {a['name']} · adset {a['id']}: {m}")
    todo = [(a, None) for a in done]
    time.sleep(30)
    print("\n-- 读回")
    for a, _ in todo:
        b = g._request("GET", a["id"], params={"fields": "name,status,effective_status,targeting"})
        tt = b.get("targeting") or {}
        pp = tt.get("publisher_platforms")
        ok = bool(pp) and "audience_network" not in pp and not tt.get("audience_network_positions")
        ex = "无 Explore" if tt.get("instagram_positions") and "explore" not in tt["instagram_positions"] else "IG 全部"
        print(f"   {'✅' if ok else '⚠️'} {a['name']} · adset {a['id']} → 版位 {pp} · {ex} · ad set {b['status']} / 实际 {b['effective_status']}")
        for ad in g._get_all(a["id"] + "/ads", {"fields": "name,status,effective_status", "limit": "50"}):
            print(f"        {ad['name']} · ad {ad['id']} — ad {ad['status']} → 实际 {ad['effective_status']}")
print("\nMY DROP AN DONE" + ("" if CONFIRM else " (dry-run)"))
