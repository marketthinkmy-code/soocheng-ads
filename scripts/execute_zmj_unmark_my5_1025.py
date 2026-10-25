# -*- coding: utf-8 -*-
"""owner 2026-10-25「目前跑回去了，那些🚫 删掉，原本因为 rejected 而关掉的，都可以开，但开之前先评估」.
MY 5.0 ONLY (the owner's test exception, PR #81 — SG keeps the 赚美金 ban and its 🚫):
  1) every 赚美金，一定要接美国客户 ad on MY 5.0: drop the 🚫 from the name (the mark alone would make the monitor pause it);
  2) print each copy's status, campaign state and its spend / registrations (3 days and since 10/17) so the reopen
     decision is evaluated per copy. Reopening is a separate step. CONFIRM=true renames."""
from __future__ import annotations

import datetime as dt
import json
import os
import time

from adbot.commands import graph_client
from adbot.monitor_cpl import extract_results
from adbot.settings import REPO_ROOT, load_settings

CONFIRM = os.environ.get("CONFIRM", "").lower() in ("1", "true", "yes")
TOK = "offsite_conversion.custom.1048291251556714"
TODAY = (dt.datetime.utcnow() + dt.timedelta(hours=8)).date()


def ins(g, oid, since):
    r = g._get_all(oid + "/insights", {"fields": "spend,actions", "time_range": json.dumps({"since": since, "until": TODAY.isoformat()})})
    r = r[0] if r else {}
    return float(r.get("spend") or 0), extract_results(r.get("actions"), TOK)


def main() -> None:
    g = graph_client(load_settings(REPO_ROOT / "config" / "config.my5.yaml"))
    ads = g._get_all("act_2285351942292267/ads", {"fields": "name,status,effective_status,created_time,campaign{name,status},adset{name}", "limit": "500"})
    for a in ads:
        if "赚美金，一定要接美国客户" not in (a.get("name") or "") or a["effective_status"] in ("DELETED", "ARCHIVED"):
            continue
        s3, r3 = ins(g, a["id"], (TODAY - dt.timedelta(days=2)).isoformat()); time.sleep(0.3)
        sa, ra = ins(g, a["id"], "2026-10-17"); time.sleep(0.3)
        new = a["name"].replace("🚫", "").strip()
        print(f"  {a['id']} «{a['name']}» {a['status']}/{a['effective_status']} · camp {a['campaign']['status']} "
              f"«{a['campaign']['name'][:48]}» › {a['adset']['name']} · 3天 RM{s3:.0f}/{r3:.0f} · 10/17起 RM{sa:.0f}/{ra:.0f}"
              + (f" → rename «{new}»" if new != a["name"] else ""))
        if CONFIRM and new != a["name"]:
            g._request("POST", a["id"], data={"name": new}); time.sleep(0.8)
    print("UNMARK DONE" + ("" if CONFIRM else " (dry-run)"))


if __name__ == "__main__":
    main()
