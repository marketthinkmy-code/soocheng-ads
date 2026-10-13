# -*- coding: utf-8 -*-
"""owner 2026-10-13 08:50「全部照你建议」— the two writes from the morning report:
  (1) SG 0911 HOOK ad set (the set carrying «HOOK：Video 12：不选 forex 不选黄金») RM150 → RM195 (+30%).
  (2) SG «[SG] STOCKBLOOM | RETARGET LP 14D | 1-1-1 | 1012» campaign → PAUSED (RM49 reached 35 people, CPM 773,
      audience < 1,000: too small for RM40/day).
Everything else in the report is hold / wait-for-noon (LAL 1%, PRIORITY BANKING at the RM142 0-reg floor; MY 5.0 hold).
Guards: the ad set must still be RM150 and the RETARGET campaign must be the expected id/name, else SKIP.
CONFIRM=true writes; otherwise dry-run. No PII."""
from __future__ import annotations

import os
import time

from adbot.commands import graph_client
from adbot.settings import REPO_ROOT, load_settings

CONFIRM = os.environ.get("CONFIRM", "").lower() in ("1", "true", "yes")
C0911_KEY = "0911 HOOK"
C0911_AD = "HOOK：Video 12：不选 forex 不选黄金"
EXPECT, TARGET = 15000, 19500
RETARGET_CAMPAIGN = "120249853228160521"
RETARGET_KEY = "RETARGET LP 14D"
done, skipped = [], []


def rm(c) -> str:
    return f"RM{int(c or 0) / 100:.0f}"


def main() -> None:
    s = load_settings(REPO_ROOT / "config" / "config.sg.yaml")
    g = graph_client(s)
    acct = s.meta.account_path
    camps = g._get_all(acct + "/campaigns", {"fields": "id,name,status,effective_status,daily_budget", "limit": "200"})
    time.sleep(0.8)

    # (1) 0911 ad set RM150 → RM195
    hits = [c for c in camps if C0911_KEY in (c.get("name") or "")]
    live = [c for c in hits if c.get("status") == "ACTIVE"] or hits
    assert len(live) == 1, f"{C0911_KEY}: expected 1 campaign, got {[c.get('name') for c in hits]}"
    c0911 = live[0]
    ads = g._get_all(c0911["id"] + "/ads", {"fields": "id,name,status,adset_id", "limit": "100"})
    time.sleep(0.6)
    carriers = [a for a in ads if (a.get("name") or "") == C0911_AD and a.get("status") == "ACTIVE"]
    assert len(carriers) == 1, f"{C0911_KEY}: expected 1 ACTIVE «{C0911_AD}», got {len(carriers)}"
    aset = g.get_object(carriers[0]["adset_id"], "id,name,status,effective_status,daily_budget")
    cur = int(aset.get("daily_budget") or 0)
    tag = f"adset «{aset.get('name')}» @ «{(c0911.get('name') or '')[:40]}» {aset.get('status')} {rm(cur)}"
    if cur == TARGET:
        skipped.append(f"0911 already {rm(cur)}"); print(f"  = {tag} (already)")
    elif cur != EXPECT:
        skipped.append(f"0911 expected {rm(EXPECT)}, found {rm(cur)} — left alone"); print(f"  ! {tag} ≠ {rm(EXPECT)} — skip")
    else:
        print(f"  → {tag} → {rm(TARGET)}")
        if CONFIRM:
            g.update_daily_budget(aset["id"], TARGET); done.append(f"0911 ad set {rm(cur)}→{rm(TARGET)}"); time.sleep(0.8)

    # (2) RETARGET campaign → PAUSED
    rt = g.get_object(RETARGET_CAMPAIGN, "id,name,status,effective_status,daily_budget")
    rtag = f"campaign «{(rt.get('name') or '')[:48]}» {rt.get('status')} / eff {rt.get('effective_status')} {rm(rt.get('daily_budget'))}"
    if RETARGET_KEY not in (rt.get("name") or ""):
        skipped.append("RETARGET id/name mismatch — left alone"); print(f"  ! {rtag} — not the RETARGET campaign, skip")
    elif rt.get("status") == "PAUSED":
        skipped.append("RETARGET already PAUSED"); print(f"  = {rtag} (already PAUSED)")
    else:
        print(f"  → {rtag} → PAUSED")
        if CONFIRM:
            g.update_status(RETARGET_CAMPAIGN, "PAUSED"); done.append("RETARGET campaign → PAUSED"); time.sleep(0.8)

    if not CONFIRM:
        print("\nDRY RUN — CONFIRM=true 才会写。"); print("MORNING 1013 DONE (dry-run)"); return
    time.sleep(4.0)
    print("\n── 验证 ──")
    a2 = g.get_object(aset["id"], "id,name,status,daily_budget")
    print(f"  adset «{a2.get('name')}» {a2.get('status')} {rm(a2.get('daily_budget'))}")
    r2 = g.get_object(RETARGET_CAMPAIGN, "id,name,status,effective_status")
    print(f"  campaign «{(r2.get('name') or '')[:48]}» {r2.get('status')} / eff {r2.get('effective_status')}")
    time.sleep(0.8)
    live_budget = 0
    camps2 = g._get_all(acct + "/campaigns", {"fields": "id,name,status,effective_status,daily_budget", "limit": "200"})
    time.sleep(0.8)
    sets2 = g._get_all(acct + "/adsets", {"fields": "id,name,status,effective_status,daily_budget,campaign_id", "limit": "500"})
    cbo = {c["id"]: int(c.get("daily_budget") or 0) for c in camps2 if c.get("effective_status") == "ACTIVE" and c.get("daily_budget")}
    live_budget += sum(cbo.values())
    live_budget += sum(int(a.get("daily_budget") or 0) for a in sets2
                       if a.get("effective_status") == "ACTIVE" and a.get("daily_budget") and a.get("campaign_id") not in cbo)
    print(f"  SG 现在开着的日预算合计：{rm(live_budget)}/天")
    print("完成: " + (" · ".join(done) or "无") + ("  跳过: " + " · ".join(skipped) if skipped else ""))
    print("MORNING 1013 DONE")


if __name__ == "__main__":
    main()
