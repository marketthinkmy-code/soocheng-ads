# -*- coding: utf-8 -*-
"""owner 2026-11-05「C」— DELETE only the 6 SG ads Meta rejected on 11/05 04:16 (all in old PAUSED campaigns).
Live copies of the same masters/captions are NOT touched (owner's decision, recorded in CLAUDE.md).
Each ad is asserted: exact name, effective_status DISAPPROVED, campaign not ACTIVE. CONFIRM=true writes."""
from __future__ import annotations

import os
import time

from adbot.commands import graph_client
from adbot.settings import REPO_ROOT, load_settings

CONFIRM = os.environ.get("CONFIRM", "").lower() in ("1", "true", "yes")
ADS = {"120249526327500521": "freestyle: korea", "120248816617020521": "🌟 video 5：盖电脑，喂！",
       "120249526323630521": "HOOK：Video 5：盖电脑，喂！", "120249258683810521": "video 1：用我的方法",
       "120249526323220521": "HOOK：Video 12：不选 forex 不选黄金", "120249526325670521": "video 2: 我只有一个目的"}
g = graph_client(load_settings(REPO_ROOT / "config" / "config.sg.yaml"))
for aid, name in ADS.items():
    a = g.get_object(aid, "name,effective_status,campaign{name,status},adset{name}")
    assert a["name"] == name and a["effective_status"] == "DISAPPROVED" and a["campaign"]["status"] != "ACTIVE", f"{aid}: {a}"
    print(f"  DELETE {a['campaign']['name']} › {a['adset']['name']} · {a['name']} · ad {aid} · {a['effective_status']}")
    if CONFIRM:
        g._request("POST", aid, data={"status": "DELETED"}); time.sleep(1)
        print(f"    ✅ {g.get_object(aid, 'status')['status']}")
print("SG DELETE REJECTED DONE" + ("" if CONFIRM else " (dry-run)"))
