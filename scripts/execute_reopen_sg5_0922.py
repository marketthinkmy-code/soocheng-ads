# -*- coding: utf-8 -*-
"""Owner 2026-09-22「开回去，『关了但 30 天 CPA 其实达标』」— reopen all 5 from the
audit table (SG only):

  🌟不选 forex @ 🌟LUXURY WATCHES        30d CPA 601
  🌟盖电脑 @ 🌟PURCHASE LAL 5%           745
  🌟freestyle 1 @ 🌟PURCHASE LAL 5%      834
  重拍：Video 6：我跟你讲！ @ 0910 重拍   sold 9/17 on RM55 (campaign-level closed)
  video 1：用我的方法 @ BROAD SG 0905     904

Declarative: make each named ad deliver; open only PAUSED layers; any non-named
ad a layer open would revive is ad-level paused first (named-only rule — incl.
review-rejected siblings, harmless). All 5 carry 30d sales <= hard stop, so the
monitor's CPA rescue protects them. CONFIRM gate; verify pass at the end."""
from __future__ import annotations

import os
import time

from adbot.commands import graph_client
from adbot.settings import REPO_ROOT, load_settings

CONFIRM = os.environ.get("CONFIRM", "").lower() in ("1", "true", "yes")
PACE = 2.5
TARGETS = [  # (ad raw name, campaign substring, campaign starts with 🌟)
    ("🌟 video 12：不选 forex 不选黄金", "LUXURY WATCH", True),
    ("🌟 video 5：盖电脑，喂！", "PURCHASE LAL", True),
    ("🌟 freestyle 1", "PURCHASE LAL", True),
    ("重拍：Video 6：我跟你讲！", "0910 重拍", False),
    ("video 1：用我的方法", "BROAD SG 25+ | 0905", False),
]


def act(g, entity_id, status, desc):
    if CONFIRM:
        g.update_status(entity_id, status)
        time.sleep(PACE)
        print(f"  ✔ {desc}")
    else:
        print(f"  [dry] {desc}")


def main() -> None:
    mode = "APPLY" if CONFIRM else "DRY-RUN"
    print(f"SG 开回 5 支（owner「开回去，关了但 30d CPA 达标」）— {mode}\n")
    s = load_settings(REPO_ROOT / "config" / "config.sg.yaml")
    g = graph_client(s)
    ads = g._get_all(
        f"{s.meta.account_path}/ads",
        {"fields": "id,name,status,effective_status,"
                   "campaign{id,name,status},adset{id,name,status}", "limit": "500"})
    time.sleep(1.2)

    resolved = []
    for ad_raw, csub, cstar in TARGETS:
        hits = [a for a in ads
                if (a.get("name") or "").strip() == ad_raw
                and csub in ((a.get("campaign") or {}).get("name") or "")
                and ((a.get("campaign") or {}).get("name") or "").startswith("🌟") == cstar]
        if len(hits) != 1:
            print(f"  ⚠️ SKIP «{ad_raw[:30]}» ({csub}): {len(hits)} 个匹配，不猜。")
            continue
        a = hits[0]
        resolved.append(a)
        print(f"  目标 «{ad_raw[:32]}» @ «{(a['campaign'].get('name') or '')[:38]}» "
              f"(effective {a.get('effective_status')})")

    target_ids = {a["id"] for a in resolved}
    open_ads = [a for a in resolved if a.get("status") != "ACTIVE"]
    open_adsets, open_camps = {}, {}
    for a in resolved:
        aset, camp = a.get("adset") or {}, a.get("campaign") or {}
        if aset.get("status") == "PAUSED":
            open_adsets[aset["id"]] = aset
        if camp.get("status") == "PAUSED":
            open_camps[camp["id"]] = camp

    neutralize = []
    for a in ads:
        if a["id"] in target_ids or a.get("status") != "ACTIVE":
            continue
        aset, camp = a.get("adset") or {}, a.get("campaign") or {}
        set_live = aset.get("status") == "ACTIVE" or aset.get("id") in open_adsets
        camp_live = camp.get("status") == "ACTIVE" or camp.get("id") in open_camps
        was_live = aset.get("status") == "ACTIVE" and camp.get("status") == "ACTIVE"
        if set_live and camp_live and not was_live:
            neutralize.append(a)

    for a in neutralize:
        act(g, a["id"], "PAUSED",
            f"NEUTRALIZE ad «{(a.get('name') or '')[:34]}»（未点名，不跟车）")
    for a in open_ads:
        act(g, a["id"], "ACTIVE", f"OPEN ad «{(a.get('name') or '')[:40]}»")
    for aset in open_adsets.values():
        act(g, aset["id"], "ACTIVE", f"OPEN adset «{(aset.get('name') or '')[:40]}»")
    for camp in open_camps.values():
        act(g, camp["id"], "ACTIVE", f"OPEN campaign «{(camp.get('name') or '')[:40]}»")

    if CONFIRM:
        print("\n── 复核 ──")
        for a in resolved:
            o = g.get_object(a["id"], fields="effective_status")
            time.sleep(1.0)
            print(f"  «{(a.get('name') or '')[:34]}» → {o.get('effective_status')}")
    print("\nSG-5 REOPEN DONE")


if __name__ == "__main__":
    main()
