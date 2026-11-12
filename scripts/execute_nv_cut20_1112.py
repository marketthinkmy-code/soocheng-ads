# -*- coding: utf-8 -*-
"""owner 2026-11-12「❌ 关 20 支（每支累计都已超过 RM80）」— NEW VIDEO judged on LIFETIME spend since 11/11 (owner's one-off
exception to the Thursday reset): pause these 20 ads at ad level (1 ad per ABO ad set → the ad set stops spending).
Each ad: campaign must contain «NEW VIDEO», ad set name must match. Reads back. CONFIRM=true writes."""
from __future__ import annotations

import os
import time

from adbot.commands import graph_client
from adbot.settings import REPO_ROOT, load_settings

CONFIRM = os.environ.get("CONFIRM", "").lower() in ("1", "true", "yes")
CUT = {"config.my5.yaml": {"120251840423900329": "Broad | MY 28+ · V1", "120251840436530329": "Broad | MY 28+ · V3",
                           "120251840442380329": "Broad | MY 28+ · V4", "120251840445280329": "Broad | MY 28+ · V5",
                           "120251840357760329": "Luxury Goods | MY 28+ · V3", "120251840366750329": "Luxury Goods | MY 28+ · V5",
                           "120251840049580329": "News | MY 28+ · V1", "120251840056430329": "News | MY 28+ · V3"},
       "config.sg.yaml": {"120250544536560521": "Broad | SG 28+ · V1", "120250544544090521": "Broad | SG 28+ · V3",
                          "120250544549430521": "Broad | SG 28+ · V5", "120250544692340521": "Golf Pickleball | SG 28+ · V2",
                          "120250544694440521": "Golf Pickleball | SG 28+ · V3", "120250544696280521": "Golf Pickleball | SG 28+ · V4",
                          "120250544697100521": "Golf Pickleball | SG 28+ · V5", "120250544640060521": "Travel | SG 28+ · V1",
                          "120250544641410521": "Travel | SG 28+ · V2", "120250544643790521": "Travel | SG 28+ · V3",
                          "120250544646460521": "Travel | SG 28+ · V4", "120250544648780521": "Travel | SG 28+ · V5"}}


def T(fn, *a, **k):
    for i in range(10):
        try:
            return fn(*a, **k)
        except Exception as e:                                           # noqa: BLE001
            if "throttled" not in str(e) and "request limit" not in str(e).lower() and "too many calls" not in str(e).lower():
                raise
            print(f"      … 限流，等 60s（{i + 1}/10）"); time.sleep(60)
    raise RuntimeError("throttled")


print("APPLY" if CONFIRM else "DRY-RUN")
n = 0
for cfg, ads in CUT.items():
    g = graph_client(load_settings(REPO_ROOT / "config" / cfg))
    print(f"\n######## {cfg}")
    for aid, aset in ads.items():
        a = T(g.get_object, aid, "name,status,effective_status,adset{name},campaign{name}")
        assert "NEW VIDEO" in a["campaign"]["name"] and a["adset"]["name"] == aset, (aid, a["campaign"]["name"], a["adset"]["name"], aset)
        print(f"  {a['campaign']['name']} › {a['adset']['name']} · {a['name']} · ad {aid} · {a['status']}/{a['effective_status']} → PAUSED")
        if CONFIRM and a["status"] != "PAUSED":
            T(g.update_status, aid, "PAUSED"); time.sleep(2); n += 1
    if CONFIRM:
        time.sleep(3)
        for aid in ads:
            b = T(g.get_object, aid, "status,effective_status")
            print(f"    ✅ 回读 ad {aid} · {b['status']}/{b['effective_status']}")
print(f"\n关 {n} 支" + ("\nNV CUT20 DONE" if CONFIRM else "\nNV CUT20 DONE (dry-run)"))
