# -*- coding: utf-8 -*-
"""owner 2026-11-02「做」— 赚美金 review rejected again → the 10/25 MY 5.0 test exception ends; 9/23 永久禁跑 applies.
  1) DELETE the rejected ad: LUXURY MY › Luxury | MY 28+ · Video：赚美金，一定要接美国客户？ · ad 120251454699130329
     (asserted: that exact position, effective_status DISAPPROVED).
  2) Every other copy of this master on MY 5.0 + SG (name contains «赚美金，一定要接美国客户»; «赚美金 = 求人？» is a different
     master and is NOT touched): ad-level PAUSED + «🚫 » prefix (10/8 rule — a re-opened carrier must not re-arm it).
Dry-run prints every position (campaign › ad set · ad id). CONFIRM=true writes."""
from __future__ import annotations

import os
import time

from adbot import compliance
from adbot.commands import graph_client
from adbot.settings import REPO_ROOT, load_settings

CONFIRM = os.environ.get("CONFIRM", "").lower() in ("1", "true", "yes")
KEY = "赚美金，一定要接美国客户"
REJECTED = "120251454699130329"

for label, cfg in (("MY 5.0", "config.my5.yaml"), ("SG", "config.sg.yaml")):
    s = load_settings(REPO_ROOT / "config" / cfg)
    g = graph_client(s)
    ads = [a for a in g._get_all(s.meta.account_path + "/ads", {"fields": "name,status,effective_status,campaign{name},adset{name}", "limit": "2000"})
           if KEY in (a.get("name") or "")]
    print(f"\n## {label}: {len(ads)} 支「{KEY}」")
    for a in ads:
        pos = f"{a['campaign']['name']} › {a['adset']['name']} · {a['name']} · ad {a['id']} · {a['status']}/{a['effective_status']}"
        if a["id"] == REJECTED:
            assert label == "MY 5.0" and "LUXURY MY" in a["campaign"]["name"] and a["adset"]["name"] == "Luxury | MY 28+" \
                and a["effective_status"] == "DISAPPROVED", f"rejected ad mismatch: {pos}"
            print(f"  DELETE  {pos}")
            if CONFIRM:
                g._request("POST", a["id"], data={"status": "DELETED"}); time.sleep(1)
                print("    ✅ DELETED")
            continue
        new = a["name"] if compliance.BAN_MARK in a["name"] else f"{compliance.BAN_MARK} {a['name']}"
        todo = [x for x, need in (("PAUSE", a["status"] != "PAUSED"), ("🚫", new != a["name"])) if need]
        print(f"  {'+'.join(todo) or 'ok':<9} {pos}")
        if CONFIRM and todo:
            data = {}
            if a["status"] != "PAUSED":
                data["status"] = "PAUSED"
            if new != a["name"]:
                data["name"] = new
            g._request("POST", a["id"], data=data); time.sleep(1)
            b = g.get_object(a["id"], "name,status")
            print(f"    ✅ «{b['name']}» {b['status']}")
print("\nZMJ BAN DONE" + ("" if CONFIRM else " (dry-run)"))
