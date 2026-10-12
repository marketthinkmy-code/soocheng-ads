# -*- coding: utf-8 -*-
"""owner 2026-10-12「全部照你的建议」— step 1 (Mon) of the two-day scale-up for the Wed 14/10 live.

SG  (config.sg.yaml)   0911 HOOK 重拍 ad set RM120→200 · 0910 重拍 ad set RM50→100 · ANDRO POOL CBO RM50→100 ·
                       LUXURY GOODS untouched · 0905 用我的方法 reopened (ad→adset→campaign) at ad set RM50→100
MY 5.0 (config.my5.yaml) DAY TRADING CBO RM160→240 · BUSINESS OWNER RM120→160 · BROAD MY 30+ RM140→200

Every budget write first checks the carrier still holds the value it had when the plan was written; if the
team moved it in the meantime the item is SKIPPED and reported, never overwritten blindly. The 0905 reopen
checks the ban gate, the cpa.hold, and that every OTHER ad in that campaign is PAUSED at ad level before the
carriers are switched on (so nothing else rides along). CONFIRM=true writes; otherwise dry-run. No PII."""
from __future__ import annotations

import os
import time

from adbot import compliance
from adbot.commands import graph_client
from adbot.settings import REPO_ROOT, load_settings

CONFIRM = os.environ.get("CONFIRM", "").lower() == "true"
SG_AD_0905 = "video 1：用我的方法"
MY_CAMPAIGNS = {  # id: (label, expect_cents, target_cents)
    "120251329144280329": ("DAY TRADING", 16000, 24000),
    "120251329164100329": ("BUSINESS OWNER", 12000, 16000),
    "120251329174460329": ("BROAD MY 30+", 14000, 20000),
}
SG_ADSET_BUDGETS = {"0911 HOOK": (12000, 20000), "0910 重拍": (5000, 10000)}   # campaign-name key -> ad set budget
SG_CBO_BUDGETS = {"ANDRO POOL": (5000, 10000)}
done, skipped = [], []


def rm(cents) -> str:
    return f"RM{int(cents or 0) / 100:.0f}"


def set_budget(g, kind: str, label: str, ent: dict, expect: int, target: int) -> None:
    cur = int(ent.get("daily_budget") or 0)
    if cur == target:
        skipped.append(f"{label}: already {rm(cur)}")
        return
    if cur != expect:
        skipped.append(f"{label}: expected {rm(expect)} but found {rm(cur)} — someone moved it, left alone")
        return
    print(f"  {kind} «{(ent.get('name') or '')[:40]}» {rm(cur)} → {rm(target)}")
    if CONFIRM:
        g.update_daily_budget(ent["id"], target)
        done.append(f"{label}: {rm(cur)} → {rm(target)}")


def main() -> None:
    # ── SG ─────────────────────────────────────────────────────────────────────
    s = load_settings(REPO_ROOT / "config" / "config.sg.yaml")
    g = graph_client(s)
    acct = s.meta.account_path
    camps = g._get_all(acct + "/campaigns", {"fields": "id,name,status,effective_status,daily_budget", "limit": "200"})
    time.sleep(1.0)

    def find(key: str) -> dict:
        hits = [c for c in camps if key in (c.get("name") or "")]
        assert len(hits) == 1, f"{key}: expected 1 campaign, got {[c.get('name') for c in hits]}"
        return hits[0]

    print("═══ SG ═══")
    for key, (expect, target) in SG_ADSET_BUDGETS.items():
        c = find(key)
        sets = g._get_all(c["id"] + "/adsets", {"fields": "id,name,status,effective_status,daily_budget", "limit": "50"})
        live = [a for a in sets if a.get("status") == "ACTIVE"]
        assert len(live) == 1, f"{key}: expected 1 ACTIVE ad set, got {[(a.get('name'), a.get('status')) for a in sets]}"
        set_budget(g, "adset", key, live[0], expect, target)
        time.sleep(0.8)
    for key, (expect, target) in SG_CBO_BUDGETS.items():
        set_budget(g, "campaign", key, find(key), expect, target)
        time.sleep(0.8)

    # 0905 reopen
    c = find("| 0905")
    sets = g._get_all(c["id"] + "/adsets", {"fields": "id,name,status,effective_status,daily_budget", "limit": "50"})
    ads = g._get_all(c["id"] + "/ads", {"fields": "id,name,status,effective_status,adset_id", "limit": "100"})
    print(f"\n  0905 «{c.get('name')}» campaign {c.get('status')} / eff {c.get('effective_status')}")
    for a in sets:
        print(f"    adset «{(a.get('name') or '')[:30]}» {a.get('status')} / {rm(a.get('daily_budget'))}")
    target = [a for a in ads if (a.get("name") or "") == SG_AD_0905]
    assert len(target) == 1, f"0905: expected 1 «{SG_AD_0905}», got {len(target)}"
    ad = target[0]
    aset = next(a for a in sets if a["id"] == ad.get("adset_id"))
    others_live = [a for a in ads if a["id"] != ad["id"] and a.get("status") == "ACTIVE"]
    banned_live = [a for a in others_live if compliance.banned_reason(a.get("name") or "", s.compliance.banned_creatives)]
    print(f"    target ad «{SG_AD_0905}» {ad.get('status')} / eff {ad.get('effective_status')} · "
          f"ban gate {'⛔' if compliance.banned_reason(SG_AD_0905, s.compliance.banned_creatives) else 'clean'} · "
          f"hold {'yes' if any(h and h in SG_AD_0905 for h in s.cpa.hold) else 'NO'}")
    print(f"    other ads ad-level ACTIVE: {len(others_live)} (banned among them: {len(banned_live)})")
    for a in others_live:
        print(f"      ⚠️ «{(a.get('name') or '')[:40]}» {a.get('status')} / eff {a.get('effective_status')}")
    assert not compliance.banned_reason(SG_AD_0905, s.compliance.banned_creatives), "0905 target is banned?!"
    assert any(h and h in SG_AD_0905 for h in s.cpa.hold), "0905: cpa.hold missing — the monitor would hard-stop it again"
    if others_live:
        skipped.append(f"0905 reopen: {len(others_live)} other ad(s) ACTIVE at ad level — carriers NOT reactivated; owner to decide")
        reopen = False
    else:
        reopen = True
        print(f"    plan: ad → ACTIVE · adset «{(aset.get('name') or '')[:30]}» {aset.get('status')} → ACTIVE "
              f"({rm(aset.get('daily_budget'))} → RM100) · campaign {c.get('status')} → ACTIVE")
        if CONFIRM:
            if ad.get("status") != "ACTIVE":
                g.update_status(ad["id"], "ACTIVE"); time.sleep(0.8)
            if aset.get("status") != "ACTIVE":
                g.update_status(aset["id"], "ACTIVE"); time.sleep(0.8)
            if c.get("status") != "ACTIVE":
                g.update_status(c["id"], "ACTIVE"); time.sleep(0.8)
            done.append("0905 用我的方法: ad / adset / campaign → ACTIVE")
            set_budget(g, "adset", "0905 adset", aset, 5000, 10000)

    # ── MY 5.0 ─────────────────────────────────────────────────────────────────
    print("\n═══ MY 5.0 ═══")
    s2 = load_settings(REPO_ROOT / "config" / "config.my5.yaml")
    g2 = graph_client(s2)
    for cid, (label, expect, target_c) in MY_CAMPAIGNS.items():
        ent = g2.get_object(cid, "name,status,effective_status,daily_budget")
        set_budget(g2, "campaign", label, ent, expect, target_c)
        time.sleep(0.8)

    if not CONFIRM:
        print("\nDRY RUN — CONFIRM=true 才会写。" + (" 会跳过: " + " · ".join(skipped) if skipped else ""))
        print("SCALE STEP1 DONE (dry-run)")
        return

    # ── verify ─────────────────────────────────────────────────────────────────
    time.sleep(5.0)
    print("\n── 验证 ──")
    for key in list(SG_ADSET_BUDGETS) + ["| 0905"]:
        cc = find(key)
        for a in g._get_all(cc["id"] + "/adsets", {"fields": "id,name,status,effective_status,daily_budget", "limit": "50"}):
            print(f"  SG «{(cc.get('name') or '')[:38]}» adset «{(a.get('name') or '')[:24]}» {a.get('status')}/{a.get('effective_status')} {rm(a.get('daily_budget'))}")
        time.sleep(0.6)
    for key in SG_CBO_BUDGETS:
        cc = g.get_object(find(key)["id"], "name,status,daily_budget")
        print(f"  SG «{(cc.get('name') or '')[:38]}» CBO {rm(cc.get('daily_budget'))} {cc.get('status')}")
    if reopen:
        a2 = g.get_object(ad["id"], "name,status,effective_status")
        print(f"  SG 0905 ad «{a2.get('name')}» {a2.get('status')} / eff {a2.get('effective_status')}")
    for cid, (label, _e, _t) in MY_CAMPAIGNS.items():
        ent = g2.get_object(cid, "name,status,daily_budget")
        print(f"  MY «{(ent.get('name') or '')[:40]}» CBO {rm(ent.get('daily_budget'))} {ent.get('status')}")
    print("\n完成: " + (" · ".join(done) or "无"))
    if skipped:
        print("跳过: " + " · ".join(skipped))
    print("SCALE STEP1 DONE")


if __name__ == "__main__":
    main()
