# -*- coding: utf-8 -*-
"""Owner 2026-09-11「以後 年齡放 30 開始」— retrofit the still-PAUSED new ad sets
to age 30+ (the rule is forward-looking; running ad sets are not touched).

  Targets: 0911 HOOK 重拍 4 ad sets + MOBILE GADGETS MY ad set (all PAUSED).
  Handles both shapes: age_min/age_max (hard audience) and age_range
  (Advantage+ audience ON). CONFIRM gate; idempotent."""
from __future__ import annotations

import os
import time

from adbot.commands import graph_client
from adbot.settings import REPO_ROOT, load_settings

CONFIRM = os.environ.get("CONFIRM", "").lower() in ("1", "true", "yes")
PACE = 4.0

ADSETS = [
    ("120248807552670575", "HOOK V5 盖电脑"),
    ("120248807571680575", "HOOK V12 不选forex"),
    ("120248807586580575", "HOOK V8 不用看盘"),
    ("120248807600040575", "HOOK V12 炒过那么多"),
    ("120248794710940575", "MOBILE GADGETS MY"),
]


def main() -> None:
    mode = "APPLY" if CONFIRM else "DRY-RUN"
    print(f"新建 ad set 年龄 → 30 起（owner 0911）— {mode}\n")
    s = load_settings(REPO_ROOT / "config" / "config.yaml")
    g = graph_client(s)
    for aid, label in ADSETS:
        t = g.get_object(aid, "name,status,targeting")
        tgt = t.get("targeting") or {}
        cur_min = tgt.get("age_min")
        cur_rng = tgt.get("age_range")
        changed = False
        if cur_min is not None and cur_min != 30:
            tgt["age_min"] = 30
            changed = True
        if cur_rng and cur_rng[0] != 30:
            tgt["age_range"] = [30, cur_rng[1] if len(cur_rng) > 1 else 65]
            changed = True
        if cur_min is None and not cur_rng:
            tgt["age_min"] = 30
            changed = True
        print(f"◆ {label} ({t.get('status')})  age_min={cur_min} age_range={cur_rng}"
              + ("" if changed else "  · 已是 30 起 — skip"))
        if not changed or not CONFIRM:
            if changed and not CONFIRM:
                print("   ▶ would set 30 起")
            continue
        try:
            g.update_targeting(aid, tgt)
            time.sleep(PACE)
            chk = (g.get_object(aid, "targeting").get("targeting") or {})
            print(f"   ✓ now age_min={chk.get('age_min')} age_range={chk.get('age_range')}")
        except Exception as e:  # noqa: BLE001
            print(f"   ❌ {str(e)[:120]} — 跳过")
    print("\nAGE30 DONE" if CONFIRM else "\nDRY-RUN — confirm=true to apply")


if __name__ == "__main__":
    main()
