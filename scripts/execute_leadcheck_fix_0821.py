# -*- coding: utf-8 -*-
"""Owner 2026-08-21 «跟你的 自行» — apply the leadcheck verdicts:

REOPEN (误杀的 CPL高/CPA低):
  · SG GOLF PICKBLEBALL (120248220643620521) chain + driver 我只有一个目的
  · MY «STOCKBLOOM | 用我的方法 | 1-1-1» (120247525704130575) chain + driver ad
  · SG AUG NEW D ad «Video 5：年纪大的人做不了交易？» (MY twin is the early star)
CLOSE:
  · SG «video 12：不选 forex 不选黄金» — every stored-ACTIVE instance (60d 0 sales)

Solo principle: only the named driver ad is woken; sibling ads keep their stored
status. Status flips only — no budget writes. Idempotent."""
from __future__ import annotations

import os
import time

from adbot import cpa
from adbot.commands import graph_client
from adbot.settings import REPO_ROOT, load_settings

CONFIRM = os.environ.get("CONFIRM", "").lower() in ("1", "true", "yes")
PACE = 8.0
N = cpa.norm

REOPEN = {
    "MY": [{"cid": "120247525704130575", "label": "用我的方法 (1-1-1)",
            "driver": "video 1: 用我的方法，你也可以有将多"}],
    "SG": [{"cid": "120248220643620521", "label": "GOLF (我只有一个目的)",
            "driver": "video 2: 我只有一个目的"}],
}
REOPEN_AD_ONLY = {
    "MY": [],
    "SG": [{"camp_name": "[SG] STOCKBLOOM | AUG NEW D | 1-1-3",
            "ad": "Video 5：年纪大的人做不了交易？"}],
}
CLOSE_ADS = {"MY": [], "SG": ["video 12：不选 forex 不选黄金"]}


def main() -> None:
    mode = "APPLY (CONFIRM=true)" if CONFIRM else "DRY-RUN"
    print(f"Leadcheck fix 8/21 — {mode}\n")
    for label, cfg in (("MY", "config.yaml"), ("SG", "config.sg.yaml")):
        s = load_settings(REPO_ROOT / "config" / cfg)
        g = graph_client(s)
        acct = s.meta.account_path
        print(f"═══ [{label}] {acct} ═══")
        try:
            for r in REOPEN[label]:
                c = g._request("GET", r["cid"], params={"fields": "name,status,daily_budget"})
                print(f"  ● 开回 {r['label']}  «{c.get('name')}» [{c.get('status')}] "
                      f"RM{int(c.get('daily_budget') or 0)/100:.0f}/day")
                if not CONFIRM:
                    continue
                if c.get("status") != "ACTIVE":
                    g.update_status(r["cid"], "ACTIVE")
                    print("     ▶ campaign → ACTIVE")
                    time.sleep(PACE)
                for aset in g._get_all(f"{r['cid']}/adsets",
                                       {"fields": "id,name,status", "limit": "10"}):
                    if aset.get("status") != "ACTIVE":
                        g.update_status(aset["id"], "ACTIVE")
                        print(f"     ▶ adset → ACTIVE")
                        time.sleep(PACE)
                for a in g._get_all(f"{r['cid']}/ads",
                                    {"fields": "id,name,status", "limit": "20"}):
                    if N(a.get("name") or "") == N(r["driver"]):
                        if a.get("status") != "ACTIVE":
                            g.update_status(a["id"], "ACTIVE")
                            print(f"     ▶ driver «{a.get('name')}» → ACTIVE")
                            time.sleep(PACE)
                        else:
                            print(f"     · driver already ACTIVE")
                    elif a.get("status") == "ACTIVE":
                        print(f"     (队友 «{(a.get('name') or '')[:24]}» 本来就 ACTIVE — 不动)")
                print(f"     ✅ live")

            if REOPEN_AD_ONLY[label] or CLOSE_ADS[label]:
                ads = g._get_all(
                    f"{acct}/ads",
                    {"fields": "id,name,status,campaign{name}", "limit": "300"})
                time.sleep(1)
                for t in REOPEN_AD_ONLY[label]:
                    hits = [a for a in ads
                            if N(a.get("name") or "") == N(t["ad"])
                            and (a.get("campaign") or {}).get("name") == t["camp_name"]]
                    if not hits:
                        print(f"  ⛔ 开回 «{t['ad'][:26]}»: 在 «{t['camp_name']}» 找不到")
                    for a in hits:
                        if a.get("status") == "ACTIVE":
                            print(f"  · «{a.get('name')}» 已经 ACTIVE — skip")
                        elif CONFIRM:
                            g.update_status(a["id"], "ACTIVE")
                            print(f"  ▶ 开回 ad {a['id']} «{a.get('name')}» ({t['camp_name']})")
                            time.sleep(PACE)
                        else:
                            print(f"  ▶ would 开回 «{a.get('name')}»")
                for name in CLOSE_ADS[label]:
                    hits = [a for a in ads
                            if N(a.get("name") or "") == N(name)
                            and a.get("status") == "ACTIVE"]
                    if not hits:
                        print(f"  · 关 «{name[:26]}»: 没有 stored-ACTIVE 实例")
                    for a in hits:
                        camp = (a.get("campaign") or {}).get("name", "?")
                        if CONFIRM:
                            g.update_status(a["id"], "PAUSED")
                            print(f"  ⏸ 关 ad {a['id']} «{a.get('name')}» in «{camp}»")
                            time.sleep(PACE)
                        else:
                            print(f"  ▶ would 关 «{a.get('name')}» in «{camp}»")
        except Exception as e:
            print(f"  ❌ [{label}] {str(e)[:140]} — continuing")
        print()
    print("FIX DONE." if CONFIRM else "DRY-RUN.")


if __name__ == "__main__":
    main()
