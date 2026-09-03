# -*- coding: utf-8 -*-
"""Owner 2026-09-03 «帮我 rename，在前面加上 🌟 符号做个记录，以免我误关» —
prefix the 19 sold chains' campaigns and ads (the 9/03 sheet-screenshot set)
with "🌟 " as a visual do-not-close marker in Ads Manager.

Campaign + ad level only (owner asked for those two). Renames are metadata:
no status flips, no review re-entry, no learning reset. Matching-side safety
shipped first: cpa.norm strips 🌟, so the sold-chain guardian, the CPL/CPA
monitor's sale attribution and prefix scoping all keep matching starred names
against the unstarred UTMs in the sales sheet.

Idempotent (skips names already starting with 🌟); dry-run unless CONFIRM=true."""
from __future__ import annotations

import os
import time

from adbot.commands import graph_client
from adbot.settings import REPO_ROOT, load_settings

CONFIRM = os.environ.get("CONFIRM", "").lower() in ("1", "true", "yes")
PACE = 4.0
STAR = "🌟 "

# (campaign fragment, adset fragment or "", ad-name needle) — the sold chains
# from the owner's two 2026-09-03 sheet screenshots. BEER ALCOHOL dropped: its
# sold ad no longer exists, nothing to mark.
CHAINS = {
    "MY": [
        ("DAY TRADING | 1-1-3", "", "盖电脑"),
        ("DAY TRADING | 1-1-3", "", "炒过那么多"),
        ("PURCHASE LAL 5% | 1-1-4", "", "korea"),
        ("AUG NEW D | 1-1-3", "", "年纪大"),
        ("PURCHASE LAL 1-5%", "Purchase LAL 4-5%", "你敢吗"),
        ("PURCHASE LAL 1-5%", "Purchase LAL 3-4%", "你敢吗"),
        ("PURCHASE LAL 1-5%", "Purchase LAL 1-2%", "我跟你讲"),
    ],
    "SG": [
        ("RUNNING | 1-1", "", "你敢吗"),
        ("PURCHASE LAL 5% | 1-1-4", "", "市场不考你的英文"),
        ("PURCHASE LAL 5% | 1-1-4", "", "盖电脑"),
        ("LUXURY WATCHES", "", "不选 forex"),
        ("LUXURY WATCHES", "", "赚美金，一定要接美国客户"),
        ("BROAD NEW HOOK B", "", "indicator"),
        ("BROAD | 1-1-3 B", "", "freestyle 1"),
        ("AUG NEW D | 1-1-3", "", "求人"),
        ("PURCHASE LAL 1-5%", "Purchase LAL 1% ", "freestyle 1"),
        ("PRIORITY BANKING", "", "用我的方法"),
        ("INVESTMENT | 1-1-3", "", "freestyle 1"),
        ("GOLF PICK", "", "我只有一个目的"),
    ],
}


def main() -> None:
    mode = "APPLY (CONFIRM=true)" if CONFIRM else "DRY-RUN"
    print(f"🌟 rename 9/03（成交链 campaign+ad 加星记号）— {mode}\n")

    total = 0
    for label, cfg in (("MY", "config.yaml"), ("SG", "config.sg.yaml")):
        print(f"═══ [{label}] ═══")
        s = load_settings(REPO_ROOT / "config" / cfg)
        g = graph_client(s)
        acct = s.meta.account_path
        ads = g._get_all(
            f"{acct}/ads",
            {"fields": "id,name,campaign{id,name},adset{id,name}",
             "limit": "500"})
        time.sleep(1.2)

        camps: dict[str, str] = {}      # campaign id -> current name
        marks: dict[str, str] = {}      # ad id -> current name
        for camp_frag, aset_frag, needle in CHAINS[label]:
            hits = [a for a in ads
                    if camp_frag in ((a.get("campaign") or {}).get("name") or "")
                    and (not aset_frag or aset_frag in ((a.get("adset") or {}).get("name") or ""))
                    and needle in (a.get("name") or "")]
            if not hits:
                print(f"  ?? 找不到  «{camp_frag}» › «{needle}» — skip")
                continue
            for a in hits:
                c = a.get("campaign") or {}
                if c.get("id"):
                    camps[c["id"]] = c.get("name") or ""
                marks[a["id"]] = a.get("name") or ""

        def rename(oid: str, old: str, kind: str) -> None:
            nonlocal total
            if old.startswith("🌟"):
                print(f"  · 已有星  [{kind}] «{old[:44]}»")
                return
            new = STAR + old
            if not CONFIRM:
                print(f"  ▶ would rename [{kind}] «{old[:40]}» → «{new[:44]}»")
                return
            try:
                g._request("POST", oid, data={"name": new})
                total += 1
                print(f"  ✅ [{kind}] «{new[:48]}»")
                time.sleep(PACE)
            except Exception as e:
                print(f"  ❌ [{kind}] «{old[:36]}»: {str(e)[:100]} — continuing")

        for cid, cname in camps.items():
            rename(cid, cname, "campaign")
        for aid, aname in marks.items():
            rename(aid, aname, "ad")
        print()

    print(f"RENAME 9/03 DONE — {total} renames." if CONFIRM
          else "DRY-RUN — review then confirm.")


if __name__ == "__main__":
    main()
