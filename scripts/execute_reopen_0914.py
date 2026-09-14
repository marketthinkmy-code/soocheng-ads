# -*- coding: utf-8 -*-
"""Owner 2026-09-14「照建议开」— reopen the 4 recent-sale positions:

  MY: ad «video：小白也可以用» @ BROAD NEW HOOK A (ad-level pause)
      ad «HOOK：…炒过那么多» @ 0911 HOOK 重拍 (ad-level pause; monitor 2nd-strike —
        safe to reopen only WITH the prefix-proof rescue patch on main)
  SG: ad set holding «video 1：用我的方法» @ BROAD SG 25+ | 0905 (adset pause)
      ad set holding «freestyle 1» @ BROAD | 1-1-3 B (adset pause)

Resolved by NAME at runtime (ids may have shifted when the owner re-paired the
HOOK ads). CONFIRM gate; idempotent; verified after each write."""
from __future__ import annotations

import os
import time

from adbot import cpa
from adbot.commands import graph_client
from adbot.settings import REPO_ROOT, load_settings

CONFIRM = os.environ.get("CONFIRM", "").lower() in ("1", "true", "yes")
PACE = 4.0
N = cpa.norm

# (config, campaign fragment, ad-name fragment, open which: "ad" | "adset")
TARGETS = [
    ("config.yaml", "BROAD NEW HOOK A | 1-1-3", "小白也可以用", "ad"),
    ("config.yaml", "BROAD MY 25+ | 0911 HOOK", "炒过那么多", "ad"),
    ("config.sg.yaml", "BROAD SG 25+ | 0905", "用我的方法", "adset"),
    ("config.sg.yaml", "BROAD | 1-1-3 B", "freestyle 1", "adset"),
]


def main() -> None:
    mode = "APPLY" if CONFIRM else "DRY-RUN"
    print(f"开回 4 支近期成交位（owner 0914「照建议开」）— {mode}\n")
    for cfg, cfrag, afrag, level in TARGETS:
        s = load_settings(REPO_ROOT / "config" / cfg)
        g = graph_client(s)
        label = "MY" if cfg == "config.yaml" else "SG"
        camps = g._get_all(f"{s.meta.account_path}/campaigns",
                           {"fields": "id,name", "limit": "500"})
        time.sleep(1)
        hits = [c for c in camps if cfrag in (c.get("name") or "")]
        if len(hits) != 1:
            print(f"⛔ [{label}] «{cfrag}» 匹配 {len(hits)} 个 campaign — 跳过")
            continue
        ads = g._get_all(f"{hits[0]['id']}/ads",
                         {"fields": "id,name,status,effective_status,"
                                    "adset{id,name,status,effective_status}",
                          "limit": "100"})
        time.sleep(1)
        ahits = [a for a in ads if N(afrag) in N(a.get("name") or "")]
        if len(ahits) != 1:
            print(f"⛔ [{label}] «{afrag}» @ «{cfrag}» 匹配 {len(ahits)} 支 — 跳过")
            continue
        a = ahits[0]
        aset = a.get("adset") or {}
        tgt_id = a["id"] if level == "ad" else aset.get("id")
        cur = a.get("status") if level == "ad" else aset.get("status")
        print(f"◆ [{label}] «{(a.get('name') or '')[:36]}» @ «{cfrag}»")
        print(f"   现状: ad {a.get('effective_status')} · adset {aset.get('effective_status')}"
              f" → 开 {level} ({tgt_id})")
        if cur == "ACTIVE":
            print("   · 已是 ACTIVE — skip")
            continue
        if not CONFIRM:
            print("   ▶ would ACTIVATE")
            continue
        g.update_status(tgt_id, "ACTIVE")
        time.sleep(PACE)
        chk = g.get_object(a["id"], "effective_status")
        print(f"   ✓ 开了 · ad effective_status = {chk.get('effective_status')}")
    print("\nREOPEN 0914 DONE" if CONFIRM else "\nDRY-RUN — confirm=true to apply")


if __name__ == "__main__":
    main()
