# -*- coding: utf-8 -*-
"""Owner 2026-09-20「建议开回的，你都帮我开」— undo the 5 SG closes the audit
flagged (3 were under the RM95 CPL line, 2 carry 30d CPA ≤~720):

  freestyle: korea @ BROAD A        (CPL 78 — was under the line)
  video 1：用我的方法 @ 🌟INVESTMENT  (CPL 92 — under the line)
  拼接：Video 1：用我的方法 @ LAL 0910 (CPL 86 — under the line)
  video 5：trading 早就… @ 🌟GOLF     (30d 2 单 CPA 721)
  🌟 freestyle 1 @ 🌟BROAD B          (30d 3 单 CPA 708) + carrier budget → RM70

NOT included: HOOK 盖电脑 @ GOLF (owner left it his call — stays down).
Declarative: open the ad + any PAUSED layers; any non-named ad a layer open
would revive gets ad-level paused first. Budget set to an absolute RM70
(idempotent by value). CONFIRM gate; verify pass at the end. SG only."""
from __future__ import annotations

import os
import time

from adbot.commands import graph_client
from adbot.settings import REPO_ROOT, load_settings

CONFIRM = os.environ.get("CONFIRM", "").lower() in ("1", "true", "yes")
PACE = 2.5
SINCE = "2026-09-18"

# (ad raw name, campaign substring, campaign starts with 🌟, expected window spend RM)
TARGETS = [
    ("freestyle: korea", "| BROAD |", False, 235),
    ("video 1：用我的方法", "INVESTMENT", True, 370),
    ("拼接：Video 1：用我的方法", "PURCHASE L", False, 343),
    ("video 5：trading 早就不是这样了！", "GOLF", True, 240),
    ("🌟 freestyle 1", "| BROAD |", True, 461),
]
BUDGET_SET = ("🌟 freestyle 1", 7000)   # carrier of this ad -> RM70/day


def act(g, entity_id, status, desc):
    if CONFIRM:
        g.update_status(entity_id, status)
        time.sleep(PACE)
        print(f"  ✔ {desc}")
    else:
        print(f"  [dry] {desc}")


def main() -> None:
    import datetime as dt
    mode = "APPLY" if CONFIRM else "DRY-RUN"
    today = (dt.datetime.utcnow() + dt.timedelta(hours=8)).date()
    print(f"SG 开回 5 支（owner 0920「建议开回的都开」）— {mode}\n")

    s = load_settings(REPO_ROOT / "config" / "config.sg.yaml")
    g = graph_client(s)
    ads = g._get_all(
        f"{s.meta.account_path}/ads",
        {"fields": "id,name,status,effective_status,"
                   "campaign{id,name,status,daily_budget},"
                   "adset{id,name,status,daily_budget}",
         "limit": "500"})
    time.sleep(1.2)
    win = {r.get("ad_id"): r for r in g.account_insights(
        s.meta.account_path, level="ad", fields="ad_id,spend",
        time_range={"since": SINCE, "until": today.isoformat()})}
    time.sleep(1.2)

    resolved = []
    for ad_raw, csub, cstar, sp_exp in TARGETS:
        tol = max(40.0, 0.25 * sp_exp)
        hits = [a for a in ads
                if (a.get("name") or "").strip() == ad_raw
                and csub in ((a.get("campaign") or {}).get("name") or "")
                and ((a.get("campaign") or {}).get("name") or "").startswith("🌟") == cstar
                and abs(float((win.get(a["id"]) or {}).get("spend") or 0) - sp_exp) <= tol]
        if len(hits) != 1:
            print(f"  ⚠️ SKIP «{ad_raw[:30]}» ({csub}): {len(hits)} 个匹配，不猜。")
            continue
        a = hits[0]
        resolved.append(a)
        print(f"  目标 «{ad_raw[:34]}» @ «{(a['campaign'].get('name') or '')[:40]}» "
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
    already = [a for a in resolved if a.get("status") == "ACTIVE"]
    for a in already:
        print(f"  ＝ ad 本身是开的 «{(a.get('name') or '')[:40]}»")

    tgt = next((a for a in resolved
                if (a.get("name") or "").strip() == BUDGET_SET[0]), None)
    if tgt:
        aset, camp = tgt.get("adset") or {}, tgt.get("campaign") or {}
        carrier = aset if aset.get("daily_budget") else camp
        kind = "adset" if aset.get("daily_budget") else "campaign"
        cur = int(carrier.get("daily_budget") or 0)
        if cur == BUDGET_SET[1]:
            print(f"  ＝ 预算已是 RM{cur / 100:.0f}")
        elif CONFIRM:
            g.update_daily_budget(carrier["id"], BUDGET_SET[1])
            time.sleep(PACE)
            print(f"  ✔ 降 {kind} 预算 RM{cur / 100:.0f} → RM{BUDGET_SET[1] / 100:.0f}"
                  f"（«{BUDGET_SET[0][:24]}» 的载体）")
        else:
            print(f"  [dry] 降 {kind} 预算 RM{cur / 100:.0f} → RM{BUDGET_SET[1] / 100:.0f}")

    if CONFIRM:
        print("\n── 复核 ──")
        for a in resolved:
            o = g.get_object(a["id"], fields="effective_status")
            time.sleep(1.0)
            print(f"  «{(a.get('name') or '')[:34]}» → {o.get('effective_status')}")
        if tgt:
            aset, camp = tgt.get("adset") or {}, tgt.get("campaign") or {}
            carrier = aset if aset.get("daily_budget") else camp
            o = g.get_object(carrier["id"], fields="daily_budget")
            print(f"  «🌟 freestyle 1» 载体 → RM{int(o.get('daily_budget') or 0) / 100:.0f}/天")
    print("\nSG REOPEN 0920 DONE")


if __name__ == "__main__":
    main()
