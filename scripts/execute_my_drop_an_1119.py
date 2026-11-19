# -*- coding: utf-8 -*-
"""owner 2026-11-19 ~23:3x「MY 拿掉 AN」(AskUserQuestion, recommended option): remove the Audience Network placement from every
MY 5.0 ad set that is live (campaign + ad set ACTIVE, campaign name starts with (Webinarkit)) plus the 3 ad sets of the still-PAUSED
MY CBO · LUX BEER OMAKASE (campaign 120251995650640329). Evidence: 11/19 MY AN = RM135 (26% of spend) / 0 报名; 10/29 起 AN 28 报名 / 0 买家.
Only placement keys change: 'audience_network' leaves publisher_platforms and audience_network_positions is dropped; every other
targeting key (geo, age, interests, Advantage+ audience, other placements) is written back exactly as read. An ad set on automatic
placements (no publisher_platforms) gets facebook + instagram + messenger with all their positions. Statuses and budgets untouched.
SG is NOT touched. CONFIRM=true writes and reads back (placements + every ad's effective_status); otherwise dry-run."""
from __future__ import annotations

import json
import os
import time

from adbot.commands import graph_client
from adbot.settings import REPO_ROOT, load_settings

CONFIRM = os.environ.get("CONFIRM", "").lower() in ("1", "true", "yes")
MY_CBO = "120251995650640329"
PL_KEYS = ("publisher_platforms", "facebook_positions", "instagram_positions", "messenger_positions",
           "audience_network_positions", "threads_positions", "whatsapp_positions")

s = load_settings(REPO_ROOT / "config" / "config.my5.yaml")
g = graph_client(s)
assert s.meta.account_path == "act_2285351942292267", s.meta.account_path
print("APPLY" if CONFIRM else "DRY-RUN", "· MY 5.0 · 只改版位：拿掉 Audience Network")
asets = g._get_all(s.meta.account_path + "/adsets", {"fields": "id,name,status,effective_status,targeting,campaign{id,name,status}",
                                                    "limit": "500"})
pick = [a for a in asets if a["campaign"]["name"].lower().startswith("(webinarkit)")
        and ((a["campaign"]["status"] == "ACTIVE" and a["status"] == "ACTIVE") or a["campaign"]["id"] == MY_CBO)]
print(f"选到 {len(pick)} 个 ad set")
todo = []
for a in pick:
    t = dict(a["targeting"])
    pp = t.get("publisher_platforms")
    print(f"\n■ {a['campaign']['name'].replace('(Webinarkit) ', '')} › {a['name']} · adset {a['id']} · campaign {a['campaign']['status']} / ad set {a['status']}")
    print("   现在: " + " · ".join(f"{k}={t.get(k)}" for k in PL_KEYS if k in t) if pp else "   现在: 自动版位（Advantage+ placements，含 AN）")
    if pp and "audience_network" not in pp:
        print("   ✅ 已经没有 AN → 不动")
        continue
    nt = dict(t)
    if pp:
        nt["publisher_platforms"] = [p for p in pp if p != "audience_network"]
    else:
        nt["publisher_platforms"] = ["facebook", "instagram", "messenger"]
    nt.pop("audience_network_positions", None)
    print("   改成: " + " · ".join(f"{k}={nt.get(k)}" for k in PL_KEYS if k in nt))
    other = {k for k in set(t) | set(nt) if k not in PL_KEYS and t.get(k) != nt.get(k)}
    assert not other, ("non-placement keys would change", other)
    todo.append((a, nt))

print(f"\n要改 {len(todo)} 个 ad set")
if CONFIRM:
    for a, nt in todo:
        g.update_targeting(a["id"], nt)
        time.sleep(2)
    time.sleep(30)
    print("\n-- 读回")
    for a, _ in todo:
        b = g.get_object(a["id"], "name,status,effective_status,targeting{publisher_platforms,audience_network_positions}")
        pp = (b.get("targeting") or {}).get("publisher_platforms")
        ok = pp and "audience_network" not in pp and not (b.get("targeting") or {}).get("audience_network_positions")
        print(f"   {'✅' if ok else '⚠️'} {a['name']} · adset {a['id']} → 版位 {pp} · ad set {b['status']} / 实际 {b['effective_status']}")
        for ad in g._get_all(a["id"] + "/ads", {"fields": "name,status,effective_status", "limit": "50"}):
            print(f"        {ad['name']} · ad {ad['id']} — ad {ad['status']} → 实际 {ad['effective_status']}")
print("\nMY DROP AN DONE" + ("" if CONFIRM else " (dry-run)"))
