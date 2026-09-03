# -*- coding: utf-8 -*-
"""Owner 2026-09-03 «图里的广告帮我开回去» — reopen the 8 sold chains from the
owner's sheet screenshot, exactly campaign→adset→ad (solo principle).

Tolerant fragment matching (the sheet has GOLF PICKLEBALL vs the live
campaign's PICKBLEBALL spelling, and RUNNING | 1-1 is the campaign's old
name — fragments hit the live objects). Ladder rows are band-specific via an
adset fragment so only the named band opens.

MY Wednesday guard: if run inside the weekly-off window (Wed 15:00 → Thu
00:00 MYT), MY chains are skipped — the sold-chain guardian reopens them at
Thursday 00:23 automatically. Idempotent; dry-run unless CONFIRM=true."""
from __future__ import annotations

import datetime as dt
import os
import time

from adbot.commands import graph_client
from adbot.settings import REPO_ROOT, load_settings

CONFIRM = os.environ.get("CONFIRM", "").lower() in ("1", "true", "yes")
PACE = 8.0

# (campaign fragment, adset fragment or "", ad-name needle) — union of the
# owner's two sheet screenshots (2026-09-03), old-account MTC rows excluded.
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
        ("BEER ALCOHOL | 1-1-3", "", "炒过那么多"),
    ],
}


def main() -> None:
    mode = "APPLY (CONFIRM=true)" if CONFIRM else "DRY-RUN"
    now_myt = dt.datetime.utcnow() + dt.timedelta(hours=8)
    print(f"Reopen 9/03（sheet 截图 8 条链）— {mode} @ {now_myt:%Y-%m-%d %H:%M} MYT\n")
    my_window = now_myt.weekday() == 2 and now_myt.hour >= 15

    for label, cfg in (("MY", "config.yaml"), ("SG", "config.sg.yaml")):
        print(f"═══ [{label}] ═══")
        if label == "MY" and my_window:
            print("  💤 周三全停窗口内 — MY 3 条不动，周四 00:23 成交链守护自动开回\n")
            continue
        s = load_settings(REPO_ROOT / "config" / cfg)
        g = graph_client(s)
        acct = s.meta.account_path
        ads = g._get_all(
            f"{acct}/ads",
            {"fields": "id,name,status,campaign{id,name,status},"
                       "adset{id,name,status}", "limit": "500"})
        time.sleep(1.2)

        flipped_c, flipped_as = set(), set()
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
                aset = a.get("adset") or {}
                todo = []
                if c.get("status") != "ACTIVE" and c.get("id") not in flipped_c:
                    todo.append(("campaign", c["id"]))
                if aset.get("status") != "ACTIVE" and aset.get("id") not in flipped_as:
                    todo.append(("adset", aset["id"]))
                if a.get("status") != "ACTIVE":
                    todo.append(("ad", a["id"]))
                tag = (f"«{(c.get('name') or '')[:36]}» › «{(aset.get('name') or '')[:24]}»"
                       f" › «{(a.get('name') or '')[:26]}»")
                if not todo:
                    print(f"  · 已在投 {tag}")
                    continue
                if not CONFIRM:
                    print(f"  ▶ would open [{'+'.join(t for t, _ in todo)}] {tag}")
                    continue
                try:
                    for level, oid in todo:
                        g.update_status(oid, "ACTIVE")
                        if level == "campaign":
                            flipped_c.add(oid)
                        if level == "adset":
                            flipped_as.add(oid)
                        time.sleep(PACE)
                    print(f"  ✅ opened [{'+'.join(t for t, _ in todo)}] {tag}")
                except Exception as e:
                    print(f"  ❌ {tag}: {str(e)[:110]} — continuing")
        print()
    print("REOPEN 9/03 DONE." if CONFIRM else "DRY-RUN — review then confirm.")


if __name__ == "__main__":
    main()
