# -*- coding: utf-8 -*-
"""owner 2026-11-10 21:xx「00:00 开」— switch the 6 NEW VIDEO campaigns (built PAUSED on 11/10) to ACTIVE at 11/11 00:00 MYT.
Only these 6 campaign ids; names asserted; refuses to write before 2026-11-11 00:00 MYT. Ban gate on every ad. Ad sets / ads were
created ACTIVE under the PAUSED campaigns, so only the campaign level changes. Reads back campaign + every ad's effective status.
CONFIRM=true writes."""
from __future__ import annotations

import datetime as dt
import os
import time

from adbot import compliance
from adbot.commands import graph_client
from adbot.settings import REPO_ROOT, load_settings

CONFIRM = os.environ.get("CONFIRM", "").lower() in ("1", "true", "yes")
CAMPS = {"config.my5.yaml": ["120251840045110329", "120251840064210329", "120251840367640329"],
         "config.sg.yaml": ["120250544490730521", "120250544550400521", "120250544649500521"]}
NOW = dt.datetime.utcnow() + dt.timedelta(hours=8)


def T(fn, *a, **k):
    for i in range(10):
        try:
            return fn(*a, **k)
        except Exception as e:                                           # noqa: BLE001
            if "throttled" not in str(e) and "request limit" not in str(e).lower():
                raise
            print(f"      … 限流，等 60s（{i + 1}/10）"); time.sleep(60)
    raise RuntimeError("throttled")


print(f"现在 {NOW:%m-%d %H:%M} MYT · {'APPLY' if CONFIRM else 'DRY-RUN'}")
if CONFIRM:
    assert NOW >= dt.datetime(2026, 11, 11, 0, 0), "owner said 00:00 — refusing to open before 2026-11-11 00:00 MYT"
for cfg, ids in CAMPS.items():
    s = load_settings(REPO_ROOT / "config" / cfg)
    g = graph_client(s)
    for cid in ids:
        c = T(g.get_object, cid, "name,status,effective_status")
        assert "NEW VIDEO" in c["name"] and "1-5-1 | 1110" in c["name"], c
        ads = T(g._get_all, cid + "/ads", {"fields": "name,status,effective_status,adset{name,status}", "limit": "20"})
        hits = compliance.filter_banned([a["name"] for a in ads], s.compliance.banned_creatives)
        assert not hits and len(ads) == 5, f"{cid}: banned {hits} / ads {len(ads)}"
        rej = [a for a in ads if a["effective_status"] in ("DISAPPROVED", "WITH_ISSUES")]
        print(f"  «{c['name']}» {cid} · 现在 {c['status']}/{c['effective_status']} · 5 支广告 · 被拒 {len(rej)}")
        for a in rej:
            print(f"      ⚠️ 被拒 «{c['name']}» › «{a['adset']['name']}» · ad {a['id']} «{a['name']}» {a['effective_status']}")
        if CONFIRM and c["status"] != "ACTIVE":
            T(g.update_status, cid, "ACTIVE"); time.sleep(3)
        if CONFIRM:
            b = T(g.get_object, cid, "status,effective_status")
            ads = T(g._get_all, cid + "/ads", {"fields": "name,effective_status,adset{name}", "limit": "20"})
            st = {}
            for a in ads:
                st[a["effective_status"]] = st.get(a["effective_status"], 0) + 1
            print(f"    ✅ 回读 {b['status']}/{b['effective_status']} · 广告状态 {st}")
            for a in ads:
                if a["effective_status"] in ("DISAPPROVED", "WITH_ISSUES"):
                    print(f"      ⚠️ 被拒 «{c['name']}» › «{a['adset']['name']}» · ad {a['id']} «{a['name']}» {a['effective_status']}")
print("ACTIVATE NEWVIDEO DONE" + ("" if CONFIRM else " (dry-run)"))
