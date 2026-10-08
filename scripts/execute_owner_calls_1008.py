# -*- coding: utf-8 -*-
"""owner 2026-10-08 看完 lifetime 后的两个决定（flip 常量再 dispatch；CONFIRM=true 才写）：
  CLOSE_PINJIE_V1 — 关 拼接：Video 1：用我的方法 @ PURCHASE LAL 1-5% | 0910 重拍
                     （ad + 它的 RM100 adset 一起关，免得留一个空壳 ACTIVE adset 在盘面上）
  BUMP_0911       — HOOK：Video 12：不选 forex 不选黄金 @ BROAD SG 25+ | 0911 的 adset RM50 → RM100
两个都幂等；执行后复查状态。"""
from __future__ import annotations

import os
import time

from adbot.commands import graph_client
from adbot.settings import REPO_ROOT, load_settings

CONFIRM = os.environ.get("CONFIRM", "").lower() == "true"
CLOSE_PINJIE_V1 = False
BUMP_0911 = False

PINJIE_AD = "120249406487260521"
PINJIE_ADSET = "120249406486090521"
ADSET_0911 = "120249390885590521"
BUMP_TO_CENTS = 10000


def main() -> None:
    s = load_settings(REPO_ROOT / "config" / "config.sg.yaml")
    g = graph_client(s)
    plan = []
    if CLOSE_PINJIE_V1:
        ad = g._request("GET", PINJIE_AD, params={"fields": "id,name,status,effective_status"})
        aset = g._request("GET", PINJIE_ADSET, params={"fields": "id,name,status,daily_budget"})
        for obj, kind in ((ad, "ad"), (aset, "adset")):
            if obj.get("status") == "PAUSED":
                plan.append((kind, obj["id"], obj.get("name"), "＝ 已经 PAUSED（跳过）", None))
            else:
                plan.append((kind, obj["id"], obj.get("name"), "关 → PAUSED", ("status", "PAUSED")))
        time.sleep(0.6)
    if BUMP_0911:
        aset = g._request("GET", ADSET_0911, params={"fields": "id,name,status,daily_budget"})
        cur = int(aset.get("daily_budget") or 0)
        if cur >= BUMP_TO_CENTS:
            plan.append(("adset", aset["id"], aset.get("name"), f"＝ 已是 RM{cur/100:.0f}（跳过）", None))
        else:
            plan.append(("adset", aset["id"], aset.get("name"),
                         f"RM{cur/100:.0f} → RM{BUMP_TO_CENTS/100:.0f}", ("budget", BUMP_TO_CENTS)))

    print("═══ 计划 ═══")
    for kind, oid, name, what, _ in plan:
        print(f"  {kind:<6} «{(name or '')[:40]}»  {what}")
    todo = [p for p in plan if p[4] is not None]
    if not plan:
        print("  （两个开关都是 False——没有要做的）")
    elif not todo:
        print("  没有要写的。")
    elif not CONFIRM:
        print(f"\nDRY RUN — CONFIRM=true 才执行这 {len(todo)} 个动作。")
    else:
        ok = fail = 0
        for kind, oid, name, what, (op, val) in todo:
            try:
                if op == "status":
                    g.update_status(oid, val)
                else:
                    g.update_daily_budget(oid, val)
                ok += 1
                print(f"  ✅ {kind} «{(name or '')[:40]}» {what}")
            except Exception as exc:                               # noqa: BLE001
                fail += 1
                print(f"  ❌ {kind} «{(name or '')[:40]}»: {str(exc)[:120]}")
            time.sleep(0.8)
        print(f"\n执行 {ok} 个，失败 {fail} 个。")
        time.sleep(3)
        for oid in {p[1] for p in todo}:
            obj = g._request("GET", oid, params={"fields": "id,name,status,effective_status,daily_budget"})
            db = obj.get("daily_budget")
            print(f"  复查 «{(obj.get('name') or '')[:40]}» status={obj.get('status')}"
                  f" eff={obj.get('effective_status')}" + (f" RM{float(db)/100:.0f}/d" if db else ""))
            time.sleep(0.6)
    print("OWNER CALLS DONE" + ("" if CONFIRM else " (dry-run)"))


if __name__ == "__main__":
    main()
