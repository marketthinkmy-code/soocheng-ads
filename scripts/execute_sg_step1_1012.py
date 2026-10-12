# -*- coding: utf-8 -*-
"""owner 2026-10-12 ~19:40「SG 现在加」— SG step 1 of the approved three-day plan, tonight instead of Tue morning:
  0911 HOOK 重拍 ad set RM120→150 · 0910 重拍 ad set RM50→65 · 0905 ad set RM50→65 (the set holding «video 1：用我的方法»)
  ANDRO POOL CBO RM50→65 · LUXURY GOODS CBO RM80→100.   Total RM350 → RM445.
ABO ad sets are located through the ad they carry (0905 has five same-named ad sets), never by name alone.
Each write checks the carrier still holds the planned 'before' value; otherwise it is SKIPPED and reported.
CONFIRM=true writes; otherwise dry-run. No PII."""
from __future__ import annotations

import os
import time

from adbot.commands import graph_client
from adbot.settings import REPO_ROOT, load_settings

CONFIRM = os.environ.get("CONFIRM", "").lower() in ("1", "true", "yes")
# campaign-name key -> (ad name that lives in the ad set, expect cents, target cents)
ADSETS = {
    "0911 HOOK":            ("HOOK：Video 12：不选 forex 不选黄金", 12000, 15000),
    "0910 重拍":             ("重拍：Video 6：我跟你讲！",            5000,  6500),
    "BROAD SG 25+ | 0905":  ("video 1：用我的方法",                  5000,  6500),
}
CBOS = {"ANDRO POOL": (5000, 6500), "LUXURY GOODS": (8000, 10000)}
done, skipped = [], []


def rm(c) -> str:
    return f"RM{int(c or 0) / 100:.0f}"


def main() -> None:
    s = load_settings(REPO_ROOT / "config" / "config.sg.yaml")
    g = graph_client(s)
    acct = s.meta.account_path
    camps = g._get_all(acct + "/campaigns", {"fields": "id,name,status,effective_status,daily_budget", "limit": "200"})
    time.sleep(0.8)

    def find(key: str) -> dict:
        hits = [c for c in camps if key in (c.get("name") or "")]
        if len(hits) > 1:
            live = [c for c in hits if c.get("status") == "ACTIVE"]
            hits = live or hits
        assert len(hits) == 1, f"{key}: expected 1 campaign, got {[c.get('name') for c in hits]}"
        return hits[0]

    def write(kind: str, label: str, ent: dict, expect: int, target: int) -> None:
        cur = int(ent.get("daily_budget") or 0)
        tag = f"{kind} «{(ent.get('name') or '')[:36]}» {rm(cur)}"
        if cur == target:
            skipped.append(f"{label}: already {rm(cur)}"); print(f"  = {tag} (already)"); return
        if cur != expect:
            skipped.append(f"{label}: expected {rm(expect)}, found {rm(cur)} — left alone"); print(f"  ! {tag} ≠ expected {rm(expect)} — skip"); return
        print(f"  → {tag} → {rm(target)}")
        if CONFIRM:
            g.update_daily_budget(ent["id"], target); done.append(f"{label} {rm(cur)}→{rm(target)}"); time.sleep(0.8)

    targets = []
    for key, (ad_name, expect, target) in ADSETS.items():
        c = find(key)
        ads = g._get_all(c["id"] + "/ads", {"fields": "id,name,status,adset_id", "limit": "100"})
        time.sleep(0.6)
        live = [a for a in ads if (a.get("name") or "") == ad_name and a.get("status") == "ACTIVE"]
        assert len(live) == 1, f"{key}: expected 1 ACTIVE «{ad_name}», got {len(live)}"
        aset = g.get_object(live[0]["adset_id"], "id,name,status,daily_budget")
        write("adset", key, aset, expect, target)
        targets.append(("adset", aset["id"]))
    for key, (expect, target) in CBOS.items():
        c = find(key)
        write("campaign", key, c, expect, target)
        targets.append(("campaign", c["id"]))

    if not CONFIRM:
        print("\nDRY RUN — CONFIRM=true 才会写。"); print("SG STEP1 DONE (dry-run)"); return
    time.sleep(4.0)
    print("\n── 验证 ──")
    total = 0
    for kind, eid in targets:
        e = g.get_object(eid, "id,name,status,daily_budget")
        total += int(e.get("daily_budget") or 0)
        print(f"  {kind} «{(e.get('name') or '')[:36]}» {e.get('status')} {rm(e.get('daily_budget'))}")
    print(f"  SG 5 carriers total: {rm(total)}/day")
    print("完成: " + (" · ".join(done) or "无") + ("  跳过: " + " · ".join(skipped) if skipped else ""))
    print("SG STEP1 DONE")


if __name__ == "__main__":
    main()
