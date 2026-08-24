# -*- coding: utf-8 -*-
"""Owner 2026-08-24 «执行» — the Thu→Mon review verdicts:

REOPEN
  MY: DAY TRADING chain (炒过那么多, CPL 30.6/CPA 347, 5th time) ·
      用我的方法 chain (CPA 354, 5th time)
  SG: every stored-PAUSED instance of korea / freestyle 1 / trading早就 / 盖电脑
      (+ their ADSET_PAUSED band ad sets), and the two AUG NEW stars
      求人 / 小白怎样赚美金 (AUG NEW campaigns only)
CLOSE
  SG: 不选forex (3rd pin — RM2.5k+ lifetime, 0 sales)
  MY: video 5: 你没有本钱 (FOOD DRINK) — RM694 this window, 60d CPA 2,722 > hard stop

All status flips, idempotent; reviving an ad inside a still-paused campaign is
inert and harmless."""
from __future__ import annotations

import os
import time

from adbot import cpa
from adbot.commands import graph_client
from adbot.settings import REPO_ROOT, load_settings

CONFIRM = os.environ.get("CONFIRM", "").lower() in ("1", "true", "yes")
PACE = 8.0
N = cpa.norm

CHAINS_MY = [
    {"cid": "120247921988670575", "label": "DAY TRADING (炒过那么多)",
     "driver": "video 12：炒过那么多，累而且不稳定"},
    {"cid": "120247525704130575", "label": "用我的方法 (1-1-1)",
     "driver": "video 1: 用我的方法，你也可以有将多"},
]
REOPEN_SG = [
    {"name": "freestyle: korea"},
    {"name": "freestyle 1"},
    {"name": "video 5：trading 早就不是这样了！"},
    {"name": "video 5：盖电脑，喂！"},
    {"name": "Video 10：赚美金 = 求人？", "camp_has": "AUG NEW"},
    {"name": "Video 6：马来西亚小白怎样赚美金？", "camp_has": "AUG NEW"},
]
CLOSE = {"SG": ["video 12：不选 forex 不选黄金"], "MY": ["video 5: 你没有本钱"]}


def main() -> None:
    mode = "APPLY (CONFIRM=true)" if CONFIRM else "DRY-RUN"
    print(f"Execute 8/24 — {mode}\n")

    for label, cfg in (("MY", "config.yaml"), ("SG", "config.sg.yaml")):
        s = load_settings(REPO_ROOT / "config" / cfg)
        g = graph_client(s)
        acct = s.meta.account_path
        print(f"═══ [{label}] {acct} ═══")
        try:
            if label == "MY":
                for r in CHAINS_MY:
                    c = g._request("GET", r["cid"], params={"fields": "name,status"})
                    print(f"  ● {r['label']} [{c.get('status')}]")
                    if not CONFIRM:
                        continue
                    if c.get("status") != "ACTIVE":
                        g.update_status(r["cid"], "ACTIVE")
                        print("     ▶ campaign → ACTIVE")
                        time.sleep(PACE)
                    for aset in g._get_all(f"{r['cid']}/adsets",
                                           {"fields": "id,status", "limit": "10"}):
                        if aset.get("status") != "ACTIVE":
                            g.update_status(aset["id"], "ACTIVE")
                            print("     ▶ adset → ACTIVE")
                            time.sleep(PACE)
                    for a in g._get_all(f"{r['cid']}/ads",
                                        {"fields": "id,name,status", "limit": "20"}):
                        if N(a.get("name") or "") == N(r["driver"]) \
                                and a.get("status") != "ACTIVE":
                            g.update_status(a["id"], "ACTIVE")
                            print(f"     ▶ driver → ACTIVE")
                            time.sleep(PACE)
                    print("     ✅ live")

            ads = g._get_all(
                f"{acct}/ads",
                {"fields": "id,name,status,effective_status,adset_id,campaign{name}",
                 "limit": "300"})
            time.sleep(1)

            if label == "SG":
                aset_flips = set()
                for t in REOPEN_SG:
                    nt = N(t["name"])
                    hits = [a for a in ads if N(a.get("name") or "") == nt
                            and (not t.get("camp_has")
                                 or t["camp_has"] in ((a.get("campaign") or {}).get("name") or ""))]
                    for a in hits:
                        camp = ((a.get("campaign") or {}).get("name") or "")[:30]
                        if a.get("status") == "PAUSED":
                            if CONFIRM:
                                g.update_status(a["id"], "ACTIVE")
                                print(f"  🔓 ad → ACTIVE «{a.get('name')[:28]}» ({camp})")
                                time.sleep(PACE)
                            else:
                                print(f"  ▶ would open ad «{a.get('name')[:28]}» ({camp})")
                        if a.get("effective_status") == "ADSET_PAUSED" and a.get("adset_id"):
                            aset_flips.add(a["adset_id"])
                for aset_id in sorted(aset_flips):
                    if CONFIRM:
                        g.update_status(aset_id, "ACTIVE")
                        print(f"  🔓 adset {aset_id} → ACTIVE")
                        time.sleep(PACE)
                    else:
                        print(f"  ▶ would open adset {aset_id}")

            for name in CLOSE.get(label, []):
                nt = N(name)
                hits = [a for a in ads if N(a.get("name") or "") == nt
                        and a.get("status") == "ACTIVE"]
                if not hits:
                    print(f"  · 关 «{name[:28]}»: 没有 stored-ACTIVE 实例")
                for a in hits:
                    camp = ((a.get("campaign") or {}).get("name") or "")[:30]
                    if CONFIRM:
                        g.update_status(a["id"], "PAUSED")
                        print(f"  ⏸ 关 «{a.get('name')[:28]}» ({camp})")
                        time.sleep(PACE)
                    else:
                        print(f"  ▶ would close «{a.get('name')[:28]}» ({camp})")
        except Exception as e:
            print(f"  ❌ [{label}] {str(e)[:140]} — continuing")
        print()
    print("EXECUTE 8/24 DONE." if CONFIRM else "DRY-RUN.")


if __name__ == "__main__":
    main()
