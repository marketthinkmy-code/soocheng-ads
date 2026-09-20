# -*- coding: utf-8 -*-
"""Owner 2026-09-20「确保 MY SG 开着的广告 30-day CPA 都有达标，才开着」.

Enforcement per the owner's own framework (30d strict sheet CPA; fair-verdict
guards: min_spend RM1,000 + 14d conversion window; hard line 1,200):

  MY 关:  freestyle: korea @ LUXURY GOODS 30-55   30d RM1,739 / 0 单
          video 2：你敢吗？ @ BROAD MY 25+ 0905    30d RM1,530 / 0 单
          freestyle 1 @ BROAD MY 25+ 0905          30d RM1,355 / 0 单
          video 8 (旧) @ DAY TRADING 0905          30d 1 单 CPA RM1,623 (>1200)
  SG 关:  video 8 (旧) @ BROAD SG 25+              30d RM1,028 / 0 单
          🌟 我只有一个目的 @ 🌟GOLF                30d 1 单 CPA RM1,215 (>1200 边缘)

Positions younger than 14 days or under RM1,000 30d spend are NOT judged and
stay (e.g. HOOK V8 @ BROAD 0911, 9 天大 — 判决日 ~9/25). Ad-level pauses only;
idempotent (already-paused = no-op). CONFIRM gate; verify pass at the end."""
from __future__ import annotations

import os
import time

from adbot.commands import graph_client
from adbot.settings import REPO_ROOT, load_settings

CONFIRM = os.environ.get("CONFIRM", "").lower() in ("1", "true", "yes")
PACE = 2.5

# (config, ad raw name, campaign substring, campaign starts with 🌟, reason)
KILLS = [
    ("config.yaml", "freestyle: korea", "LUXURY GOODS", False, "30d RM1739/0单"),
    ("config.yaml", "video 2：你敢吗？", "BROAD MY 25+", False, "30d RM1530/0单"),
    ("config.yaml", "freestyle 1", "BROAD MY 25+", False, "30d RM1355/0单"),
    ("config.yaml", "video 8：做么你 trading 不用看盘的？", "DAY TRADING", False,
     "30d CPA RM1623 >1200"),
    ("config.sg.yaml", "video 8：做么你 trading 不用看盘的？", "BROAD SG", False,
     "30d RM1028/0单"),
    ("config.sg.yaml", "🌟 video 2: 我只有一个目的", "GOLF", True,
     "30d CPA RM1215 >1200"),
]


def main() -> None:
    mode = "APPLY" if CONFIRM else "DRY-RUN"
    print(f"30d-CPA 清场（owner「达标才开着」）— {mode}\n")
    touched = []
    for cfg in ("config.yaml", "config.sg.yaml"):
        label = "MY" if cfg == "config.yaml" else "SG"
        s = load_settings(REPO_ROOT / "config" / cfg)
        g = graph_client(s)
        ads = g._get_all(
            f"{s.meta.account_path}/ads",
            {"fields": "id,name,status,effective_status,campaign{name}",
             "limit": "500"})
        time.sleep(1.2)
        print(f"═══ [{label}] ═══")
        for kcfg, ad_raw, csub, cstar, why in KILLS:
            if kcfg != cfg:
                continue
            hits = [a for a in ads
                    if (a.get("name") or "").strip() == ad_raw
                    and csub in ((a.get("campaign") or {}).get("name") or "")
                    and ((a.get("campaign") or {}).get("name") or "").startswith("🌟") == cstar]
            if len(hits) != 1:
                print(f"  ⚠️ SKIP «{ad_raw[:30]}» ({csub}): {len(hits)} 个匹配，不猜。")
                continue
            a = hits[0]
            desc = (f"关 «{ad_raw[:32]}» @ «{(a['campaign'].get('name') or '')[:34]}»"
                    f"（{why}）")
            if a.get("status") == "PAUSED":
                print(f"  ＝ 已是关的 {desc}")
                continue
            if CONFIRM:
                g.update_status(a["id"], "PAUSED")
                time.sleep(PACE)
                print(f"  ✔ {desc}")
                touched.append((cfg, a["id"], ad_raw))
            else:
                print(f"  [dry] {desc}")
        print()

    if CONFIRM and touched:
        print("── 复核 ──")
        for cfg, aid, name in touched:
            s = load_settings(REPO_ROOT / "config" / cfg)
            g = graph_client(s)
            o = g.get_object(aid, fields="effective_status")
            time.sleep(1.0)
            print(f"  «{name[:34]}» → {o.get('effective_status')}")
    print("\n30D-CPA ENFORCE DONE")


if __name__ == "__main__":
    main()
