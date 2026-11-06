# -*- coding: utf-8 -*-
"""owner 2026-11-06「A」— MY scale on the best-CPL carriers (since 10/29: DT korea 32 / 年纪大 25, BROAD MY korea 28):
  DAY TRADING 120251454713670329 RM165→200 · BROAD MY 120251454704570329 RM120→145. Names asserted first. CONFIRM=true writes.
Also READ-ONLY: targeting of WINNERS MY's two ad sets vs BROAD MY's ad set (overlap check for the owner's WINNERS question)."""
from __future__ import annotations

import os
import time

from adbot.commands import graph_client
from adbot.settings import REPO_ROOT, load_settings

CONFIRM = os.environ.get("CONFIRM", "").lower() in ("1", "true", "yes")
PLAN = [("120251454713670329", "DAY TRADING | 1-1-5 | 1017", 20000), ("120251454704570329", "BROAD MY | 1-1-5 | 1017", 14500)]
g = graph_client(load_settings(REPO_ROOT / "config" / "config.my5.yaml"))
for oid, must, cents in PLAN:
    o = g.get_object(oid, "name,daily_budget")
    assert must in o["name"] and "(Webinarkit)" in o["name"], f"{oid}: {o['name']}"
    print(f"  «{o['name']}» · campaign {oid} · RM{int(o.get('daily_budget') or 0) // 100} → RM{cents // 100}")
    if CONFIRM and int(o.get("daily_budget") or 0) != cents:
        g.update_daily_budget(oid, cents); time.sleep(1)
        print(f"    ✅ RM{int(g.get_object(oid, 'daily_budget')['daily_budget']) // 100}")
print("\n受众对比（只读）:")
for sid in ("120251454705570329", "120251533794220329", "120251533791330329"):
    a = g.get_object(sid, "name,status,daily_budget,campaign{name},targeting")
    t = a["targeting"]
    ints = [i.get("name") for sp in t.get("flexible_spec") or [] for i in sp.get("interests") or []]
    print(f"  {a['campaign']['name']} › {a['name']} · adset {sid} · {a['status']} · RM{int(a.get('daily_budget') or 0) // 100} · "
          f"geo {t.get('geo_locations', {}).get('countries')} · age {t.get('age_min')}-{t.get('age_max')} range {t.get('age_range')} · "
          f"adv+ {(t.get('targeting_automation') or {}).get('advantage_audience')} · locales {t.get('locales')} · 兴趣 {len(ints)} · "
          f"CA {[c.get('name', c.get('id')) for c in t.get('custom_audiences') or []]}")
print("MY SCALE DONE" + ("" if CONFIRM else " (dry-run)"))
