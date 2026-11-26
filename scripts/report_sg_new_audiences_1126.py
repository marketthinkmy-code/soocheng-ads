# -*- coding: utf-8 -*-
"""READ-ONLY (owner 11/26「winning ads try different ads set / winning ad set try different ads … SG 还可以怎么建」).
Which interest audiences have NOT run in SG since 10/29, and is there a source ad set to clone targeting from?
Searches SG (act_893025326577600), then MY 5.0 / MY 3.0 for ad sets whose ad set or campaign name matches each keyword and that carry
interests (flexible_spec). Prints newest matches: account · campaign › ad set · id · created · status · interest count + first names ·
lifetime spend. Also SG spend since 10/29 per keyword. No writes."""
from __future__ import annotations

import datetime as dt
import json

from adbot.commands import graph_client
from adbot.settings import REPO_ROOT, load_settings

KEYS = [("Beer/Alcohol", ("beer", "alcohol")), ("Omakase/Wagyu", ("omakase", "wagyu")), ("Business Owner", ("business owner",)),
        ("News", ("news",)), ("Golf/Pickleball", ("golf", "pickle")), ("Engaged Shopper", ("engaged shopper",))]
ACCTS = ["act_893025326577600", "act_2285351942292267", "act_759339046918885"]
s = load_settings(REPO_ROOT / "config" / "config.sg.yaml")
g = graph_client(s)
rows = {}
for ac in ACCTS:
    try:
        rows[ac] = list(g._get_all(ac + "/adsets", {"fields": "name,created_time,effective_status,targeting,campaign{name}", "limit": "500"}))
    except Exception as exc:  # noqa: BLE001
        print(f"(读不到 {ac}: {str(exc)[:80]})")
        rows[ac] = []
ins = {}
try:
    for x in g._get_all("act_893025326577600/insights", {"level": "adset", "fields": "adset_id,spend",
                                                        "time_range": json.dumps({"since": "2026-10-29", "until": dt.date.today().isoformat()}), "limit": "500"}):
        ins[x["adset_id"]] = float(x.get("spend") or 0)
except Exception as exc:  # noqa: BLE001
    print(f"(SG insights 读不到: {str(exc)[:80]})")
for label, keys in KEYS:
    print(f"\n■ {label}")
    sg_spend = 0.0
    for ac in ACCTS:
        hits = []
        for x in rows[ac]:
            nm = (x["name"] + " " + (x.get("campaign") or {}).get("name", "")).lower()
            fs = (x.get("targeting") or {}).get("flexible_spec") or []
            if any(k in nm for k in keys) and fs:
                hits.append(x)
                if ac == "act_893025326577600":
                    sg_spend += ins.get(x["id"], 0.0)
        hits.sort(key=lambda x: x["created_time"], reverse=True)
        for x in hits[:3]:
            fs = x["targeting"]["flexible_spec"]
            names = [i.get("name") for grp in fs for k in ("interests", "behaviors", "work_positions", "industries") for i in grp.get(k, [])]
            t = x["targeting"]
            print(f"   {ac} · {x['campaign']['name'][:60]} › {x['name'][:40]} · adset {x['id']} · {x['created_time'][:10]} · {x['effective_status']}"
                  f" · 年龄 {t.get('age_min')}-{t.get('age_max')} · 兴趣 {len(names)}：{', '.join(n for n in names[:6] if n)}")
        if not hits:
            print(f"   {ac} · 没有")
    print(f"   SG 10/29 起这类 ad set 花费 RM{sg_spend:,.0f}")
print("\nSG NEW AUDIENCES DONE (read-only)")
