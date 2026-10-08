# -*- coding: utf-8 -*-
"""owner 2026-10-08 第二批决定（CONFIRM=true 才写；幂等；写后按对象类型重读）：
  1. 关 campaign «PURCHASE LAL 1-5% | 0910 重拍»（拼接 V1 关掉后剩下的空壳）+ 它那个只剩
     关着的 iPhone Duo 单图的 RM100 adset，一起 PAUSED。
  2. 「放全部 RM50」：0911 不选 forex 的 adset RM100 → RM50；LUXURY GOODS | 1-1-3 CBO RM70 → RM50。"""
from __future__ import annotations

import os
import time

from adbot.commands import graph_client
from adbot.settings import REPO_ROOT, load_settings

CONFIRM = os.environ.get("CONFIRM", "").lower() == "true"
TO_PAUSE = [
    ("campaign", "120249341546230521", "[SG] STOCKBLOOM | PURCHASE LAL 1-5% | 0910 重拍"),
    ("adset", "120249341553640521", "Purchase LAL 1-5% RM100 (只剩 iPhone Duo 单图)"),
]
TO_BUDGET = [
    ("adset", "120249390885590521", "Broad SG 30+ (0911 不选 forex)", 5000),
    ("campaign", "120248256443280521", "[SG] STOCKBLOOM | LUXURY GOODS | 1-1-3 CBO", 5000),
]


def main() -> None:
    s = load_settings(REPO_ROOT / "config" / "config.sg.yaml")
    g = graph_client(s)
    plan = []
    for kind, oid, label in TO_PAUSE:
        o = g._request("GET", oid, params={"fields": "id,name,status,effective_status"})
        if o.get("status") == "PAUSED":
            plan.append((kind, oid, label, "＝ 已经 PAUSED（跳过）", None))
        else:
            plan.append((kind, oid, label, f"{o.get('status')} → PAUSED", ("status", "PAUSED")))
        time.sleep(0.6)
    for kind, oid, label, cents in TO_BUDGET:
        o = g._request("GET", oid, params={"fields": "id,name,status,daily_budget"})
        cur = int(o.get("daily_budget") or 0)
        if cur == cents:
            plan.append((kind, oid, label, f"＝ 已是 RM{cur/100:.0f}（跳过）", None))
        else:
            plan.append((kind, oid, label, f"RM{cur/100:.0f} → RM{cents/100:.0f}", ("budget", cents)))
        time.sleep(0.6)

    print("═══ 计划 ═══")
    for kind, oid, label, what, _ in plan:
        print(f"  {kind:<9} «{label[:46]}»  {what}")
    todo = [p for p in plan if p[4] is not None]
    if not todo:
        print("  没有要写的。")
    elif not CONFIRM:
        print(f"\nDRY RUN — CONFIRM=true 才执行这 {len(todo)} 个动作。")
    else:
        ok = fail = 0
        for kind, oid, label, what, (op, val) in todo:
            try:
                (g.update_status if op == "status" else g.update_daily_budget)(oid, val)
                ok += 1
                print(f"  ✅ {kind} «{label[:46]}» {what}")
            except Exception as exc:                               # noqa: BLE001
                fail += 1
                print(f"  ❌ {kind} «{label[:46]}»: {str(exc)[:120]}")
            time.sleep(0.8)
        print(f"\n执行 {ok} 个，失败 {fail} 个。")
        time.sleep(3)
        for kind, oid, label, _w, _v in todo:
            o = g._request("GET", oid, params={
                "fields": "id,name,status,effective_status,daily_budget"})   # campaign/adset 都有 daily_budget
            db = o.get("daily_budget")
            print(f"  复查 {kind} «{label[:40]}» status={o.get('status')} eff={o.get('effective_status')}"
                  + (f" RM{float(db)/100:.0f}/d" if db else ""))
            time.sleep(0.6)
    print("OWNER CALLS 2 DONE" + ("" if CONFIRM else " (dry-run)"))


if __name__ == "__main__":
    main()
