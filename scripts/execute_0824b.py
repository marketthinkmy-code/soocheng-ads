# -*- coding: utf-8 -*-
"""Owner 2026-08-24 Q1/Q2/Q3 approvals:

  Q1 关吧 — pause the empty-shell campaigns + dead-delivery BEER:
       MY: TRAVEL / GOLF PICKBLEBALL / INVESTMENT / LUXURY GOODS / BEER ALCOHOL
       SG: AUG NEW E
  Q2 可  — 用我的方法 (120247525704130575): keep, revive the DRIVER ad only
       (campaign/adsets already held ACTIVE by guardian; siblings stay off).
  Q3 可  — SG GOLF PICKBLEBALL (120248220643620521): daily budget back to
       RM220. CAS-guarded: only applies if current budget is still RM50.

Plus a READ-ONLY diagnostic: list ads of the MY campaigns still running
winner-audience pools (FOOD DRINK PREMIUM / BROAD NEW HOOK A) to see whether
any high-哭穷率 creative (korea 59%) is live inside MY right now.

Idempotent; dry-run unless CONFIRM=true."""
from __future__ import annotations

import os
import time

from adbot import cpa
from adbot.commands import graph_client
from adbot.settings import REPO_ROOT, load_settings

CONFIRM = os.environ.get("CONFIRM", "").lower() in ("1", "true", "yes")
PACE = 8.0
N = cpa.norm

CLOSE = {
    "MY": ["STOCKBLOOM | TRAVEL | 1-1-3",
           "STOCKBLOOM | GOLF PICKBLEBALL | 1-1-3",
           "STOCKBLOOM | INVESTMENT | 1-1-3",
           "STOCKBLOOM | LUXURY GOODS | 1-1-3",
           "STOCKBLOOM | BEER ALCOHOL | 1-1-3"],
    "SG": ["[SG] STOCKBLOOM | AUG NEW E | 1-1-3"],
}
UMDF_CID = "120247525704130575"
UMDF_DRIVER = "video 1: 用我的方法，你也可以有将多"
GOLF_CID = "120248220643620521"
GOLF_EXPECT = 5000    # RM50 as seen 8/24 12:02
GOLF_NEW = 22000      # RM220
DIAG = ["STOCKBLOOM | FOOD DRINK PREMIUM | 1-1-4",
        "STOCKBLOOM | BROAD NEW HOOK A | 1-1-3"]


def main() -> None:
    mode = "APPLY (CONFIRM=true)" if CONFIRM else "DRY-RUN"
    print(f"Execute 8/24b (Q1 关壳+BEER · Q2 用我的方法 driver · Q3 GOLF 预算) — {mode}\n")

    for label, cfg in (("MY", "config.yaml"), ("SG", "config.sg.yaml")):
        s = load_settings(REPO_ROOT / "config" / cfg)
        g = graph_client(s)
        acct = s.meta.account_path
        print(f"═══ [{label}] {acct} ═══")
        camps = {c.get("name"): c for c in g._get_all(
            f"{acct}/campaigns",
            {"fields": "id,name,status,effective_status,daily_budget", "limit": "500"})}
        time.sleep(1.2)

        # ---- Q1 closes ----
        for name in CLOSE[label]:
            c = camps.get(name)
            if not c:
                print(f"  ?? «{name}» 不存在 — skip")
                continue
            st = c.get("effective_status")
            if st != "ACTIVE" and c.get("status") != "ACTIVE":
                print(f"  · «{name}» 已是 {st} — skip")
                continue
            if CONFIRM:
                try:
                    g.update_status(c["id"], "PAUSED")
                    print(f"  ⏸ closed «{name}»")
                    time.sleep(PACE)
                except Exception as e:
                    print(f"  ❌ «{name}»: {str(e)[:120]} — continuing")
            else:
                print(f"  ⏸ would close «{name}» [{st}]")

        if label == "MY":
            # ---- Q2: revive 用我的方法 driver only ----
            try:
                c = g._request("GET", UMDF_CID,
                               params={"fields": "name,status,daily_budget"})
                print(f"  ● Q2 «{c.get('name')}» [{c.get('status')}] "
                      f"RM{int(c.get('daily_budget') or 0)/100:.0f}/day")
                if CONFIRM and c.get("status") != "ACTIVE":
                    g.update_status(UMDF_CID, "ACTIVE")
                    print("     ▶ campaign → ACTIVE")
                    time.sleep(PACE)
                for aset in g._get_all(f"{UMDF_CID}/adsets",
                                       {"fields": "id,status", "limit": "10"}):
                    if aset.get("status") != "ACTIVE":
                        if CONFIRM:
                            g.update_status(aset["id"], "ACTIVE")
                            print("     ▶ adset → ACTIVE")
                            time.sleep(PACE)
                        else:
                            print("     ▶ would ACTIVE adset")
                for a in g._get_all(f"{UMDF_CID}/ads",
                                    {"fields": "id,name,status", "limit": "20"}):
                    if N(a.get("name") or "") == N(UMDF_DRIVER):
                        if a.get("status") == "ACTIVE":
                            print("     · driver 已 ACTIVE")
                        elif CONFIRM:
                            g.update_status(a["id"], "ACTIVE")
                            print(f"     ▶ driver «{a.get('name')}» → ACTIVE")
                            time.sleep(PACE)
                        else:
                            print(f"     ▶ would ACTIVE driver «{a.get('name')}»")
                    elif a.get("status") == "ACTIVE":
                        print(f"     (队友 «{(a.get('name') or '')[:26]}» ACTIVE — 不动)")
            except Exception as e:
                print(f"  ❌ Q2: {str(e)[:130]} — continuing")

            # ---- diagnostic: any korea live inside MY? ----
            print("  ── 诊断（read-only）：MY 在跑池子里的素材")
            for name in DIAG:
                c = camps.get(name)
                if not c:
                    print(f"     ?? «{name}» 不存在")
                    continue
                try:
                    ads = g._get_all(f"{c['id']}/ads",
                                     {"fields": "name,status,effective_status",
                                      "limit": "20"})
                    line = " · ".join(
                        f"{'▶' if a.get('effective_status') == 'ACTIVE' else '⏸'}"
                        f"{(a.get('name') or '')[:20]}" for a in ads)
                    print(f"     «{name[:38]}»: {line}")
                except Exception as e:
                    print(f"     ❌ {name}: {str(e)[:90]}")
                time.sleep(1.2)

        if label == "SG":
            # ---- Q3: GOLF budget 50 → 220 (CAS) ----
            try:
                c = g._request("GET", GOLF_CID,
                               params={"fields": "name,status,daily_budget"})
                cur = int(c.get("daily_budget") or 0)
                print(f"  ● Q3 «{c.get('name')}» [{c.get('status')}] 当前 RM{cur/100:.0f}/day")
                if cur == GOLF_NEW:
                    print("     · 已是 RM220 — skip")
                elif cur != GOLF_EXPECT:
                    print(f"     ⚠️ 当前 RM{cur/100:.0f} ≠ 预期 RM50（有人改过）— 不动，人工确认")
                elif CONFIRM:
                    g._request("POST", GOLF_CID, data={"daily_budget": str(GOLF_NEW)})
                    print(f"     ✅ RM50 → RM220/day")
                    time.sleep(PACE)
                else:
                    print(f"     ▶ would set RM50 → RM220/day")
            except Exception as e:
                print(f"  ❌ Q3: {str(e)[:130]} — continuing")
        print()

    print("EXECUTE 8/24b DONE." if CONFIRM else "DRY-RUN — review then confirm=true.")


if __name__ == "__main__":
    main()
