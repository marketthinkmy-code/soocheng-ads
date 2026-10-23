# -*- coding: utf-8 -*-
"""READ-ONLY 2026-10-23: a 10/21 webinar_oct21 buyer registered via UTM «MTC - News - 14/1/2026 / News / Video 4: 厌倦了等待»
(a ⛔ banned master). Is any ad account this token reaches running it — or anything with spend since 10/17 outside
the Webinarkit campaigns? Lists accounts, then per account: ads named like 厌倦了等待 / campaign «MTC - News» + spend."""
from __future__ import annotations

import json
import time

from adbot.commands import graph_client
from adbot.settings import REPO_ROOT, load_settings

s = load_settings(REPO_ROOT / "config" / "config.sg.yaml")
g = graph_client(s)
accts = g._get_all("me/adaccounts", {"fields": "name,account_id,account_status", "limit": "100"})
print(f"token reaches {len(accts)} ad accounts")
WIN = json.dumps({"since": "2026-10-14", "until": "2026-10-23"})
for a in accts:
    aid = "act_" + a["account_id"]
    try:
        rows = g._get_all(aid + "/insights", {"fields": "campaign_name,ad_name,spend,inline_link_clicks", "level": "ad", "time_range": WIN, "limit": "500"})
    except Exception as exc:                                             # noqa: BLE001
        print(f"  {a['name'][:40]:<40} status {a['account_status']} — insights err {str(exc)[:60]}"); continue
    hits = [r for r in rows if "厌倦" in (r.get("ad_name") or "") or "news" in (r.get("campaign_name") or "").lower()]
    other = sum(float(r.get("spend") or 0) for r in rows if "webinarkit" not in (r.get("campaign_name") or "").lower())
    print(f"  {a['name'][:40]:<40} status {a['account_status']} · 10/14-10/23 非 Webinarkit 花费 RM{other:.0f}")
    for r in hits:
        print(f"     ⚠️ «{r['campaign_name'][:50]}» / «{r['ad_name'][:40]}» RM{float(r.get('spend') or 0):.0f} clk {r.get('inline_link_clicks', 0)}")
    time.sleep(1)
print("FIND DONE (read-only)")
