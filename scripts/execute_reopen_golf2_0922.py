# -*- coding: utf-8 -*-
"""Owner 2026-09-22「开」— reopen the two closed ads whose 30d CPA passes:

  HOOK：Video 5：盖电脑，喂！ @ [SG] GOLF PICKLEBALL 0914   (30d CPA ~555)
  🌟 video 2: 我只有一个目的 @ 🌟 [SG] GOLF PICKBLEBALL    (30d CPA ~875, window shifted)

Ad-level opens into already-live GOLF carriers (no budget change). Both carry
30d sales <= hard stop, so the monitor's CPA rescue protects them from CPL
sweeps. CONFIRM gate; idempotent; verified after."""
from __future__ import annotations

import os
import time

from adbot.commands import graph_client
from adbot.settings import REPO_ROOT, load_settings

CONFIRM = os.environ.get("CONFIRM", "").lower() in ("1", "true", "yes")
TARGETS = [  # (ad raw name, campaign substring, campaign starts with 🌟)
    ("HOOK：Video 5：盖电脑，喂！", "GOLF", False),
    ("🌟 video 2: 我只有一个目的", "GOLF", True),
]


def main() -> None:
    s = load_settings(REPO_ROOT / "config" / "config.sg.yaml")
    g = graph_client(s)
    ads = g._get_all(
        f"{s.meta.account_path}/ads",
        {"fields": "id,name,status,effective_status,"
                   "campaign{name,status},adset{name,status}", "limit": "500"})
    time.sleep(1.2)
    for ad_raw, csub, cstar in TARGETS:
        hits = [a for a in ads
                if (a.get("name") or "").strip() == ad_raw
                and csub in ((a.get("campaign") or {}).get("name") or "")
                and ((a.get("campaign") or {}).get("name") or "").startswith("🌟") == cstar]
        if len(hits) != 1:
            print(f"⚠️ SKIP «{ad_raw[:30]}»: {len(hits)} 个匹配，不猜。")
            continue
        a = hits[0]
        camp, aset = a.get("campaign") or {}, a.get("adset") or {}
        desc = f"«{ad_raw[:32]}» @ «{(camp.get('name') or '')[:38]}»"
        if a.get("effective_status") == "ACTIVE":
            print(f"＝ 已在跑 {desc}")
            continue
        if aset.get("status") != "ACTIVE" or camp.get("status") != "ACTIVE":
            print(f"⚠️ SKIP {desc}: 层不是 ACTIVE (adset {aset.get('status')}, "
                  f"campaign {camp.get('status')}) — 只做 ad 级开，不动层。")
            continue
        if CONFIRM:
            g.update_status(a["id"], "ACTIVE")
            time.sleep(2.5)
            o = g.get_object(a["id"], fields="effective_status")
            print(f"✔ 开 {desc} → {o.get('effective_status')}")
        else:
            print(f"[dry] 开 {desc}")
    print("GOLF-2 REOPEN DONE")


if __name__ == "__main__":
    main()
