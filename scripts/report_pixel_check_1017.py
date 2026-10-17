# -*- coding: utf-8 -*-
"""READ-ONLY 2026-10-17: is the Webinarkit dataset seeing thank-you page views? pixel stats by event and by URL
(last 24h), custom conversion last_fired_time. URLs printed host+path only (no query strings / PII)."""
from __future__ import annotations

import datetime as dt
import time
from urllib.parse import urlsplit

from adbot.commands import graph_client
from adbot.settings import REPO_ROOT, load_settings

PIXEL = "1338380974889410"
CCS = ["1048291251556714", "1614065190214320", "1869590394421967"]


def main() -> None:
    g = graph_client(load_settings(REPO_ROOT / "config" / "config.my5.yaml"))
    p = g.get_object(PIXEL, "name,last_fired_time,is_unavailable")
    print("pixel:", p)
    start = int((dt.datetime.utcnow() - dt.timedelta(hours=24)).timestamp())
    for agg in ("event", "url_by_rule", "url"):
        time.sleep(1)
        try:
            rows = g._get_all(PIXEL + "/stats", {"aggregation": agg, "start_time": str(start)})
            tot = {}
            for r in rows:
                for d in r.get("data") or []:
                    k = d.get("value") or ""
                    if agg != "event":
                        u = urlsplit(k); k = (u.netloc + u.path) if u.netloc else k
                    tot[k] = tot.get(k, 0) + int(d.get("count") or 0)
            print(f"\n== {agg} (24h) ==")
            for k, n in sorted(tot.items(), key=lambda kv: -kv[1])[:25]:
                print(f"  {n:>6}  {k[:110]}")
        except Exception as e:                                      # noqa: BLE001
            print(f"  {agg} ❌ {str(e)[:200]}")
    for cc in CCS:
        time.sleep(1)
        try:
            print("cc", cc, g.get_object(cc, "name,last_fired_time,rule,is_unavailable"))
        except Exception as e:                                      # noqa: BLE001
            print("cc", cc, "❌", str(e)[:150])
    print("PIXEL CHECK DONE")


if __name__ == "__main__":
    main()
