# -*- coding: utf-8 -*-
"""Owner 2026-09-10 approved webinar-recovery budget plan (weekly caps ÷7 → daily),
plus the close list. Rule:「没提到就别碰」— unlisted chains stay untouched.

  MY budgets: AUG NEW D 314 · PURCHASE LAL 5% 257 · (DT 1-1-3 stays 200) ·
              Broad0905 korea adset 143 · DT0905 不用看盘 adset 86
  MY closes:  PRIORITY BANKING campaign · 用我的方法 1-1-1 campaign ·
              ad korea @ PURCHASE LAL 5% · adset korea @ LUXURY 0905
  SG budgets: PURCHASE LAL 5% 314 · PURCHASE LAL 1-5% 243 · RUNNING 286 ·
              Broad0905 用我的方法 adset 171 · LUXURY WATCHES 114 · BROAD B 100

Already-off items in the close list (我跟你讲 / 赚美金=求人 / Luxury你敢吗 /
Golf我只有一个目的) are verified dead, not re-touched. CONFIRM gate; idempotent."""
from __future__ import annotations

import os
import time

from adbot import cpa
from adbot.commands import graph_client
from adbot.settings import REPO_ROOT, load_settings

CONFIRM = os.environ.get("CONFIRM", "").lower() in ("1", "true", "yes")
PACE = 4.0
N = cpa.norm

# (kind, campaign fragment, sub fragment or None, new daily RM or "PAUSE")
PLAN = {
    "config.yaml": [
        ("camp_budget", "AUG NEW D | 1-1-3", None, 314),
        ("camp_budget", "PURCHASE LAL 5% | 1-1-4", None, 257),
        ("adset_budget", "BROAD MY 25+ | 0905", "korea", 143),
        ("adset_budget", "DAY TRADING | 0905", "不用看盘", 86),
        ("camp_pause", "PRIORITY BANKING", None, None),
        ("camp_pause", "用我的方法 | 1-1-1", None, None),
        ("ad_pause", "PURCHASE LAL 5% | 1-1-4", "korea", None),
        ("adset_pause", "LUXURY GOODS 30-55 | 0905", "korea", None),
    ],
    "config.sg.yaml": [
        ("camp_budget", "PURCHASE LAL 5% | 1-1-4", None, 314),
        ("camp_budget", "PURCHASE LAL 1-5% | 1-5-3", None, 243),
        ("camp_budget", "RUNNING | 1-1", None, 286),
        ("adset_budget", "BROAD SG 25+ | 0905", "用我的方法", 171),
        ("camp_budget", "LUXURY WATCHES", None, 114),
        ("camp_budget", "BROAD | 1-1-3 B", None, 100),
    ],
}


def main() -> None:
    mode = "APPLY" if CONFIRM else "DRY-RUN"
    print(f"0911 预算重分配 + 关停（weekly÷7）— {mode}\n")
    for cfg, items in PLAN.items():
        label = "MY" if cfg == "config.yaml" else "SG"
        s = load_settings(REPO_ROOT / "config" / cfg)
        g = graph_client(s)
        acct = s.meta.account_path
        camps = g._get_all(f"{acct}/campaigns",
                           {"fields": "id,name,status,daily_budget", "limit": "500"})
        time.sleep(1.2)

        def find_camp(frag):
            hits = [c for c in camps if frag in (c.get("name") or "")]
            return hits[0] if len(hits) == 1 else None

        print(f"══ [{label}] ══")
        for kind, cfrag, sub, amt in items:
            camp = find_camp(cfrag)
            if not camp:
                print(f"  ⛔ «{cfrag}» 匹配不到唯一 campaign — 跳过")
                continue
            try:
                if kind == "camp_budget":
                    cur = float(camp.get("daily_budget") or 0) / 100
                    if abs(cur - amt) < 1:
                        print(f"  · «{cfrag}» 已是 RM{amt}/day — skip")
                        continue
                    print(f"  {cfrag}: RM{cur:.0f} → RM{amt}/day"
                          + ("" if CONFIRM else "  (would)"))
                    if CONFIRM:
                        g._request("POST", camp["id"],
                                   data={"daily_budget": str(int(amt * 100))})
                        time.sleep(PACE)
                elif kind == "camp_pause":
                    if camp.get("status") == "PAUSED":
                        print(f"  · «{cfrag}» 已停 — skip")
                        continue
                    print(f"  PAUSE campaign «{cfrag}»" + ("" if CONFIRM else "  (would)"))
                    if CONFIRM:
                        g.update_status(camp["id"], "PAUSED")
                        time.sleep(PACE)
                elif kind in ("adset_budget", "adset_pause", "ad_pause"):
                    ads = g._get_all(
                        f"{camp['id']}/ads",
                        {"fields": "id,name,status,adset{id,name,daily_budget,status}",
                         "limit": "100"})
                    time.sleep(1)
                    hits = [a for a in ads if N(sub) in N(a.get("name") or "")]
                    if len(hits) != 1:
                        print(f"  ⛔ «{sub}» @ «{cfrag}» 匹配 {len(hits)} 支 — 跳过")
                        continue
                    a = hits[0]
                    aset = a.get("adset") or {}
                    if kind == "adset_budget":
                        cur = float(aset.get("daily_budget") or 0) / 100
                        if abs(cur - amt) < 1:
                            print(f"  · adset «{sub}»@«{cfrag}» 已是 RM{amt} — skip")
                            continue
                        print(f"  adset «{sub}»@«{cfrag}»: RM{cur:.0f} → RM{amt}/day"
                              + ("" if CONFIRM else "  (would)"))
                        if CONFIRM:
                            g._request("POST", aset["id"],
                                       data={"daily_budget": str(int(amt * 100))})
                            time.sleep(PACE)
                    elif kind == "adset_pause":
                        if aset.get("status") == "PAUSED":
                            print(f"  · adset «{sub}»@«{cfrag}» 已停 — skip")
                            continue
                        print(f"  PAUSE adset «{sub}»@«{cfrag}»"
                              + ("" if CONFIRM else "  (would)"))
                        if CONFIRM:
                            g.update_status(aset["id"], "PAUSED")
                            time.sleep(PACE)
                    else:
                        if a.get("status") == "PAUSED":
                            print(f"  · ad «{sub}»@«{cfrag}» 已停 — skip")
                            continue
                        print(f"  PAUSE ad «{a.get('name')}»@«{cfrag}»"
                              + ("" if CONFIRM else "  (would)"))
                        if CONFIRM:
                            g.update_status(a["id"], "PAUSED")
                            time.sleep(PACE)
            except Exception as e:
                print(f"  ❌ {kind} «{cfrag}»/«{sub}»: {str(e)[:110]} — continuing")
        print()
    print("PLAN 0911 DONE" if CONFIRM else "DRY-RUN — confirm=true to apply")


if __name__ == "__main__":
    main()
