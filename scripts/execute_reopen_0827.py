# -*- coding: utf-8 -*-
"""Owner 2026-08-27 «开回，预算全部 setting 100» — after webinar_aug26 sold
through ads that had been closed/cut:

REOPEN (solo principle — only named things flip, siblings keep stored status):
  · SG LUXURY WATCHES campaign (不选forex sold aug26, 赚美金接美国客户 sold aug19)
      + reactivate the own-paused seller ad 赚美金，一定要接美国客户
  · SG AUG NEW D campaign (求人 sold aug26; its ad is still own-ACTIVE)
  · SG PURCHASE LAL 5%: reactivate ad 市场不考你的英文 (sold aug26)
  · MY PURCHASE LAL 1-5% ladder: reactivate the 2 paused 你敢吗 copies
      (incl. the paused band adset; own-ACTIVE band siblings return with it)

BUDGET → RM100/day on every CBO campaign in this fix:
  MY DAY TRADING · SG RUNNING · SG PURCHASE LAL 5% · SG LUXURY WATCHES ·
  SG AUG NEW D.  (MY ladder is ABO per-band — bands untouched.)

Idempotent; dry-run unless CONFIRM=true."""
from __future__ import annotations

import os
import time

from adbot import cpa
from adbot.commands import graph_client
from adbot.settings import REPO_ROOT, load_settings

CONFIRM = os.environ.get("CONFIRM", "").lower() in ("1", "true", "yes")
PACE = 8.0
NEW_BUDGET = 10000  # RM100
N = cpa.norm

REOPEN_CAMPS_SG = ["LUXURY WATCHES", "AUG NEW D"]          # name fragments
REACT_ADS = {
    "SG": [("LUXURY WATCHES", "赚美金，一定要接美国客户"),
           ("PURCHASE LAL 5%", "市场不考你的英文")],
    "MY": [("PURCHASE LAL 1-5%", "你敢吗")],
}
BUDGET_CAMPS = {
    "MY": ["DAY TRADING"],
    "SG": ["RUNNING", "PURCHASE LAL 5%", "LUXURY WATCHES", "AUG NEW D"],
}


def main() -> None:
    mode = "APPLY (CONFIRM=true)" if CONFIRM else "DRY-RUN"
    print(f"Reopen+budget 8/27 — {mode}\n")

    for label, cfg in (("MY", "config.yaml"), ("SG", "config.sg.yaml")):
        s = load_settings(REPO_ROOT / "config" / cfg)
        g = graph_client(s)
        acct = s.meta.account_path
        print(f"═══ [{label}] {acct} ═══")
        camps = [c for c in g._get_all(
            f"{acct}/campaigns",
            {"fields": "id,name,status,daily_budget", "limit": "500"})
            if "STOCKBLOOM" in (c.get("name") or "")]
        time.sleep(1.2)

        def find_camp(frag):
            hits = [c for c in camps if frag in (c.get("name") or "")]
            return hits[0] if len(hits) == 1 else None

        # ---- campaign reopens (SG only) ----
        if label == "SG":
            for frag in REOPEN_CAMPS_SG:
                c = find_camp(frag)
                if not c:
                    print(f"  ?? campaign «{frag}» 不唯一/找不到 — skip")
                    continue
                st = c.get("status")
                print(f"  ● 开回 «{c.get('name')}» [{st}]")
                if st != "ACTIVE":
                    if CONFIRM:
                        g.update_status(c["id"], "ACTIVE")
                        print("     ▶ campaign → ACTIVE")
                        time.sleep(PACE)
                    else:
                        print("     ▶ would ACTIVE campaign")
                for aset in g._get_all(f"{c['id']}/adsets",
                                       {"fields": "id,status", "limit": "10"}):
                    if aset.get("status") != "ACTIVE":
                        if CONFIRM:
                            g.update_status(aset["id"], "ACTIVE")
                            print("     ▶ adset → ACTIVE")
                            time.sleep(PACE)
                        else:
                            print("     ▶ would ACTIVE adset")

        # ---- named ad reactivations ----
        for camp_frag, needle in REACT_ADS[label]:
            c = find_camp(camp_frag)
            if not c:
                print(f"  ?? «{camp_frag}» 找不到 — skip")
                continue
            for a in g._get_all(
                    f"{c['id']}/ads",
                    {"fields": "id,name,status,adset{id,name,status}",
                     "limit": "40"}):
                if needle not in (a.get("name") or ""):
                    continue
                aset = a.get("adset") or {}
                tag = f"«{(a.get('name') or '')[:24]}» ({(aset.get('name') or '')[:30]})"
                if aset.get("status") != "ACTIVE":
                    if CONFIRM:
                        g.update_status(aset["id"], "ACTIVE")
                        print(f"     ▶ band adset → ACTIVE  ({(aset.get('name') or '')[:34]})")
                        time.sleep(PACE)
                    else:
                        print(f"     ▶ would ACTIVE band adset ({(aset.get('name') or '')[:34]})")
                if a.get("status") != "ACTIVE":
                    if CONFIRM:
                        g.update_status(a["id"], "ACTIVE")
                        print(f"     ▶ ad → ACTIVE  {tag}")
                        time.sleep(PACE)
                    else:
                        print(f"     ▶ would ACTIVE ad  {tag}")
                else:
                    print(f"     · ad 已 ACTIVE  {tag}")

        # ---- budgets → RM100 ----
        for frag in BUDGET_CAMPS[label]:
            c = find_camp(frag)
            if not c:
                print(f"  ?? 预算目标 «{frag}» 找不到 — skip")
                continue
            cur = int(c.get("daily_budget") or 0)
            if cur == NEW_BUDGET:
                print(f"  · 预算已是 RM100  «{c.get('name')}»")
                continue
            if not cur:
                print(f"  ⚠️ «{c.get('name')}» 无 campaign 预算(ABO?) — skip")
                continue
            if CONFIRM:
                g._request("POST", c["id"], data={"daily_budget": str(NEW_BUDGET)})
                print(f"  ✅ RM{cur/100:.0f} → RM100  «{c.get('name')}»")
                time.sleep(PACE)
            else:
                print(f"  ▶ would RM{cur/100:.0f} → RM100  «{c.get('name')}»")
        print()

    print("REOPEN+BUDGET DONE." if CONFIRM else "DRY-RUN — review then confirm.")


if __name__ == "__main__":
    main()
