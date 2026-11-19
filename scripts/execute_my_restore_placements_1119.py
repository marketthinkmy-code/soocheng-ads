# -*- coding: utf-8 -*-
"""owner 2026-11-19 ~23:5x「你刚改的都复原」: undo execute_my_drop_an_1119.py (written 23:38 MYT before the cancel landed).
For the 9 MY ad sets it touched, write the targeting back WITHOUT any placement keys — exactly what the API returned for them
before 23:38 (no publisher_platforms / positions = their original placement setting). Every other targeting key is kept as it is now.
Statuses / budgets untouched. SG untouched. CONFIRM=true writes and reads back; otherwise dry-run."""
from __future__ import annotations

import os
import sys
import time

from adbot.commands import graph_client
from adbot.settings import REPO_ROOT, load_settings

sys.stdout.reconfigure(line_buffering=True)
CONFIRM = os.environ.get("CONFIRM", "").lower() in ("1", "true", "yes")
ADSETS = ["120251995666640329", "120251995661220329", "120251995652710329", "120251993987750329", "120251993979530329",
          "120251840426800329", "120251840061020329", "120251840057130329", "120251454700740329"]
PL_KEYS = ("publisher_platforms", "facebook_positions", "instagram_positions", "messenger_positions",
           "audience_network_positions", "threads_positions", "whatsapp_positions")
s = load_settings(REPO_ROOT / "config" / "config.my5.yaml")
g = graph_client(s)
assert s.meta.account_path == "act_2285351942292267"
print("APPLY" if CONFIRM else "DRY-RUN", "· 复原 9 组版位")
plan = []
for aid in ADSETS:
    a = g._request("GET", aid, params={"fields": "name,status,targeting,campaign{name}"})
    t = a.get("targeting") or {}
    now = {k: t[k] for k in PL_KEYS if k in t}
    nt = {k: v for k, v in t.items() if k not in PL_KEYS}
    print(f"■ {a['campaign']['name'].replace('(Webinarkit) ', '')} › {a['name']} · adset {aid} · 现在 {now or '无版位字段'} → 复原成 不指定版位")
    if now:
        plan.append((aid, a["name"], nt))
print(f"要复原 {len(plan)} 组")
if CONFIRM:
    for aid, name, nt in plan:
        try:
            g.update_targeting(aid, nt)
            print(f"   写入 {name} · adset {aid}")
        except Exception as exc:  # noqa: BLE001
            print(f"   ❌ {name} · adset {aid}: {str(exc)[:200]}")
        time.sleep(2)
    time.sleep(20)
    print("-- 读回")
    for aid in ADSETS:
        b = g._request("GET", aid, params={"fields": "name,status,effective_status,targeting"})
        left = {k: b["targeting"][k] for k in PL_KEYS if k in (b.get("targeting") or {})}
        print(f"   {'✅' if not left else '⚠️'} {b['name']} · adset {aid} → 版位字段 {left or '无（已复原）'} · ad set {b['status']} / {b['effective_status']}")
print("RESTORE DONE" + ("" if CONFIRM else " (dry-run)"))
