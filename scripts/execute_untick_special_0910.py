# -*- coding: utf-8 -*-
"""Owner 2026-09-10:「全部帮我 untick」— remove the FINANCIAL_PRODUCTS_SERVICES
special-ad-category declaration from the four 0910 campaigns (all still PAUSED,
zero delivery), then restore the 30-55 age targeting on the MY Luxury ad sets
that the category had blocked. SG ad-set-level regional regulated fields
(SINGAPORE_UNIVERSAL) are a separate regulation and stay untouched.
Older live campaigns are NOT touched. CONFIRM gate; idempotent."""
from __future__ import annotations

import json
import os
import time

from adbot.commands import graph_client
from adbot.settings import REPO_ROOT, load_settings

CONFIRM = os.environ.get("CONFIRM", "").lower() in ("1", "true", "yes")
PACE = 4.0

TARGETS = {
    "config.yaml": [
        ("120248787484510575", "MY BROAD 0910", False),
        ("120248787848460575", "MY LUXURY 0910", True),    # True → restore ages 30-55
    ],
    "config.sg.yaml": [
        ("120249341323780521", "SG BROAD 0910", False),
        ("120249341546230521", "SG LAL 0910", False),
    ],
}


def main() -> None:
    mode = "APPLY" if CONFIRM else "DRY-RUN"
    print(f"Untick special ad category on 0910 campaigns + restore Luxury 30-55 — {mode}\n")
    for cfg, items in TARGETS.items():
        s = load_settings(REPO_ROOT / "config" / cfg)
        g = graph_client(s)
        for cid, label, fix_age in items:
            cur = g.get_object(cid, "id,name,status,special_ad_categories")
            print(f"◆ {label} «{(cur.get('name') or '')[:44]}» "
                  f"special={cur.get('special_ad_categories')}")
            if not CONFIRM:
                print("   ▶ would set special_ad_categories=[]"
                      + ("; adsets → age 30-55" if fix_age else ""))
                continue
            if cur.get("special_ad_categories"):
                g._request("POST", cid, data={"special_ad_categories": json.dumps([])})
                print("   ✓ special_ad_categories → []")
                time.sleep(PACE)
            else:
                print("   · 已经没有申报 — skip")
            if fix_age:
                for a in g._get_all(f"{cid}/adsets",
                                    {"fields": "id,name,targeting", "limit": "25"}):
                    tgt = a.get("targeting") or {}
                    if tgt.get("age_min") == 30 and tgt.get("age_max") == 55:
                        print(f"   · adset {a['id']} 已是 30-55 — skip")
                        continue
                    tgt["age_min"], tgt["age_max"] = 30, 55
                    for attempt in (1, 2):
                        try:
                            g.update_targeting(a["id"], tgt)
                            print(f"   ✓ adset {a['id']} age → 30-55")
                            break
                        except Exception as e:
                            if attempt == 1 and "age" in str(e).lower():
                                # 类别刚清，Meta 需要时间传播 — 等 30s 再试一次
                                print(f"   ⚠️ adset {a['id']} age 被拒（类别传播中）— 30s 后重试")
                                time.sleep(30)
                            else:
                                print(f"   ❌ adset {a['id']} age 失败: {str(e)[:100]} — 跳过")
                                break
                    time.sleep(PACE)
            chk = g.get_object(cid, "special_ad_categories")
            print(f"   验证 special={chk.get('special_ad_categories') or []}")
    print("\nUNTICK DONE" if CONFIRM else "\nDRY-RUN — confirm=true to apply")


if __name__ == "__main__":
    main()
