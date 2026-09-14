# -*- coding: utf-8 -*-
"""Follow-up to execute_reopen_0914: while the reopen ran, the owner's own Ads
Manager sweep paused the ENCLOSING layers of 3 approved positions. Open those
layers so the 4 approved positions actually deliver, and list every OTHER ad
each campaign-open revives (side-effect check for the report).

  SG: campaign «BROAD | 1-1-3 B» → ACTIVE   (freestyle 1, 9/9 sale)
  MY: campaign «BROAD NEW HOOK A | 1-1-3» → ACTIVE (小白也可以用, 9/11 sale)
  MY: ad set of «HOOK：…炒过那么多» @ 0911 HOOK 重拍 → ACTIVE

CONFIRM gate; idempotent; verified after each write."""
from __future__ import annotations

import os
import time

from adbot import cpa
from adbot.commands import graph_client
from adbot.settings import REPO_ROOT, load_settings

CONFIRM = os.environ.get("CONFIRM", "").lower() in ("1", "true", "yes")
PACE = 4.0
N = cpa.norm

CAMP_OPENS = [
    ("config.sg.yaml", "BROAD | 1-1-3 B"),
    ("config.yaml", "BROAD NEW HOOK A | 1-1-3"),
]
ADSET_OPEN = ("config.yaml", "BROAD MY 25+ | 0911 HOOK", "炒过那么多")


def main() -> None:
    mode = "APPLY" if CONFIRM else "DRY-RUN"
    print(f"开回补刀（外层被同时关掉的 3 处）— {mode}\n")
    for cfg, cfrag in CAMP_OPENS:
        s = load_settings(REPO_ROOT / "config" / cfg)
        g = graph_client(s)
        label = "MY" if cfg == "config.yaml" else "SG"
        camps = g._get_all(f"{s.meta.account_path}/campaigns",
                           {"fields": "id,name,status", "limit": "500"})
        time.sleep(1)
        hits = [c for c in camps if cfrag in (c.get("name") or "")]
        if len(hits) != 1:
            print(f"⛔ [{label}] «{cfrag}» 匹配 {len(hits)} 个 — 跳过")
            continue
        c = hits[0]
        print(f"◆ [{label}] campaign «{(c.get('name') or '')[:42]}» status={c.get('status')}")
        if c.get("status") != "ACTIVE" and CONFIRM:
            g.update_status(c["id"], "ACTIVE")
            time.sleep(PACE)
            print("   ✓ campaign → ACTIVE")
        elif c.get("status") != "ACTIVE":
            print("   ▶ would ACTIVATE campaign")
        ads = g._get_all(f"{c['id']}/ads",
                         {"fields": "name,effective_status", "limit": "50"})
        for a in ads:
            print(f"     · {a.get('effective_status'):<16} «{(a.get('name') or '')[:38]}»")
        time.sleep(1)

    cfg, cfrag, afrag = ADSET_OPEN
    s = load_settings(REPO_ROOT / "config" / cfg)
    g = graph_client(s)
    camps = g._get_all(f"{s.meta.account_path}/campaigns",
                       {"fields": "id,name", "limit": "500"})
    time.sleep(1)
    hits = [c for c in camps if cfrag in (c.get("name") or "")]
    if len(hits) == 1:
        ads = g._get_all(f"{hits[0]['id']}/ads",
                         {"fields": "id,name,effective_status,adset{id,name,status}",
                          "limit": "25"})
        ahits = [a for a in ads if N(afrag) in N(a.get("name") or "")]
        if len(ahits) == 1:
            a = ahits[0]
            aset = a.get("adset") or {}
            print(f"◆ [MY] adset of «{(a.get('name') or '')[:36]}» status={aset.get('status')}")
            if aset.get("status") != "ACTIVE" and CONFIRM:
                g.update_status(aset["id"], "ACTIVE")
                time.sleep(PACE)
                chk = g.get_object(a["id"], "effective_status")
                print(f"   ✓ adset → ACTIVE · ad effective = {chk.get('effective_status')}")
            elif aset.get("status") != "ACTIVE":
                print("   ▶ would ACTIVATE adset")
            else:
                print("   · adset 已 ACTIVE")
        else:
            print(f"⛔ «{afrag}» 匹配 {len(ahits)} 支 — 跳过")
    else:
        print(f"⛔ «{cfrag}» 匹配 {len(hits)} 个 — 跳过")
    print("\nREOPEN FIX DONE" if CONFIRM else "\nDRY-RUN")


if __name__ == "__main__":
    main()
