# -*- coding: utf-8 -*-
"""Owner 2026-09-11「OK」— the three SG cuts from the spend review, plus the
Ad-errors diagnosis on the 0905 Broad campaign.

  1. PAUSE campaign «[SG] STOCKBLOOM | BROAD SG 25+ | 0910 重拍» — RM215.80 / 0
     registrations across all 4 ad sets; the LAL 0910 twin carries the creatives.
  2. 🌟 PURCHASE LAL 5% | 1-1-4 (CBO): RM314 → RM220/day (-30%, CPL 290 this week).
  3. 🌟 PURCHASE LAL 1-5% | 1-5-3 rung «LAL 1%» (ABO ad set): RM100 → RM70/day.
  4. READ-ONLY: list ads with issues in «BROAD SG 25+ | 0905» (the Ad errors badge).

CONFIRM gate; idempotent; each write re-verified."""
from __future__ import annotations

import os
import time

from adbot import cpa
from adbot.commands import graph_client
from adbot.settings import REPO_ROOT, load_settings

CONFIRM = os.environ.get("CONFIRM", "").lower() in ("1", "true", "yes")
PACE = 4.0
N = cpa.norm

PAUSE_CAMP_ID = "120249341323780521"
PAUSE_CAMP_NAME_FRAG = "BROAD SG 25+ | 0910"
CBO_FRAG, CBO_NEW = "PURCHASE LAL 5% | 1-1-4", 22000        # RM220
RUNG_CAMP_FRAG, RUNG_FRAG, RUNG_NEW = "PURCHASE LAL 1-5% | 1-5-3", "lal 1%", 7000  # RM70
DIAG_FRAG = "BROAD SG 25+ | 0905"


def main() -> None:
    mode = "APPLY" if CONFIRM else "DRY-RUN"
    print(f"SG 三刀 (0911) + Ad-errors 诊断 — {mode}\n")
    s = load_settings(REPO_ROOT / "config" / "config.sg.yaml")
    g = graph_client(s)
    acct = s.meta.account_path
    camps = g._get_all(f"{acct}/campaigns",
                       {"fields": "id,name,status,daily_budget", "limit": "500"})
    time.sleep(1.2)

    def one(frag):
        hits = [c for c in camps if frag in (c.get("name") or "")]
        return hits[0] if len(hits) == 1 else None

    # 1) pause BROAD 0910 重拍
    camp = next((c for c in camps if c["id"] == PAUSE_CAMP_ID), None)
    if not camp or PAUSE_CAMP_NAME_FRAG not in (camp.get("name") or ""):
        print(f"⛔ 刀1: campaign {PAUSE_CAMP_ID} 名字对不上 — 跳过")
    elif camp.get("status") == "PAUSED":
        print(f"· 刀1 «{camp['name'][:44]}» 已停 — skip")
    else:
        print(f"刀1 PAUSE «{camp['name'][:44]}»" + ("" if CONFIRM else "  (would)"))
        if CONFIRM:
            g.update_status(camp["id"], "PAUSED")
            time.sleep(PACE)
            chk = g.get_object(camp["id"], "status")
            print(f"   验证 status={chk.get('status')}")

    # 2) CBO cut LAL 5%
    camp = one(CBO_FRAG)
    if not camp:
        print(f"⛔ 刀2: «{CBO_FRAG}» 匹配不到唯一 campaign — 跳过")
    else:
        cur = float(camp.get("daily_budget") or 0) / 100
        if abs(cur - CBO_NEW / 100) < 1:
            print(f"· 刀2 «{CBO_FRAG}» 已是 RM{CBO_NEW/100:.0f} — skip")
        else:
            print(f"刀2 «{CBO_FRAG}»: RM{cur:.0f} → RM{CBO_NEW/100:.0f}/day"
                  + ("" if CONFIRM else "  (would)"))
            if CONFIRM:
                g.update_daily_budget(camp["id"], CBO_NEW)
                time.sleep(PACE)
                chk = g.get_object(camp["id"], "daily_budget")
                print(f"   验证 daily_budget=RM{float(chk.get('daily_budget') or 0)/100:.0f}")

    # 3) ABO rung cut LAL 1%
    camp = one(RUNG_CAMP_FRAG)
    if not camp:
        print(f"⛔ 刀3: «{RUNG_CAMP_FRAG}» 匹配不到唯一 campaign — 跳过")
    else:
        asets = g._get_all(f"{camp['id']}/adsets",
                           {"fields": "id,name,status,daily_budget", "limit": "25"})
        time.sleep(1)
        hits = [a for a in asets if N(RUNG_FRAG) in N(a.get("name") or "")
                and a.get("status") == "ACTIVE"]
        if len(hits) != 1:
            print(f"⛔ 刀3: «{RUNG_FRAG}» 匹配 {len(hits)} 个 ACTIVE ad set — 跳过")
        else:
            a = hits[0]
            cur = float(a.get("daily_budget") or 0) / 100
            if abs(cur - RUNG_NEW / 100) < 1:
                print(f"· 刀3 rung «{a['name'][:36]}» 已是 RM{RUNG_NEW/100:.0f} — skip")
            else:
                print(f"刀3 rung «{a['name'][:36]}»: RM{cur:.0f} → RM{RUNG_NEW/100:.0f}/day"
                      + ("" if CONFIRM else "  (would)"))
                if CONFIRM:
                    g.update_daily_budget(a["id"], RUNG_NEW)
                    time.sleep(PACE)
                    chk = g.get_object(a["id"], "daily_budget")
                    print(f"   验证 daily_budget=RM{float(chk.get('daily_budget') or 0)/100:.0f}")

    # 4) diagnose Ad errors on 0905 Broad (read-only)
    camp = one(DIAG_FRAG)
    print()
    if not camp:
        print(f"⛔ 诊断: «{DIAG_FRAG}» 匹配不到唯一 campaign")
    else:
        print(f"◆ Ad errors 诊断 «{camp['name'][:44]}»：")
        ads = g._get_all(
            f"{camp['id']}/ads",
            {"fields": "id,name,status,effective_status,issues_info,adset{name}",
             "limit": "100"})
        bad = 0
        for a in ads:
            eff = a.get("effective_status")
            issues = a.get("issues_info") or []
            if eff == "ACTIVE" and not issues:
                continue
            if a.get("status") == "PAUSED" and not issues:
                continue        # 手动关的不算问题
            bad += 1
            aset = (a.get("adset") or {}).get("name") or "?"
            print(f"  ⚠️ «{(a.get('name') or '')[:34]}» @ «{aset[:28]}» "
                  f"effective={eff}")
            for i in issues:
                print(f"     · {(i.get('error_summary') or '')[:60]} — "
                      f"{(i.get('error_message') or '')[:150]}")
        if not bad:
            print("  （没有带 issues 的广告——错误可能已自行消失）")

    print("\nSG CUTS 0911 DONE" if CONFIRM else "\nDRY-RUN — confirm=true to apply")


if __name__ == "__main__":
    main()
