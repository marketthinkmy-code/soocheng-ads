# -*- coding: utf-8 -*-
"""Owner-approved 2026-08-11 («do all» on the 8/11 复盘 action list):

1. ACTIVATE the two BROAD MJ campaigns built earlier today — all three layers
   (campaign + ad set + both video ads) were created PAUSED, so each layer is set
   ACTIVE and the final ad effective_status is verified.
2. 用我的方法 (SG INVESTMENT) exact 60-day CPA: pull the ad's 60d spend + count its
   strict-matched sheet sales, print CPA vs the tiers — DATA ONLY, no reopen action
   (that decision stays with the owner).

Idempotent; dry-run unless CONFIRM=true (part 2 is read-only and runs in both modes).
"""
from __future__ import annotations

import datetime as dt
import os
import time

from adbot import cpa
from adbot.clients.graph import GraphError
from adbot.commands import graph_client
from adbot.settings import REPO_ROOT, load_settings

CONFIRM = os.environ.get("CONFIRM", "").lower() in ("1", "true", "yes")
PACE = 4.0

BROAD_MJ = [
    {"label": "SG", "cfg": "config.sg.yaml",
     "campaign": "120248835876710521", "adset": "120248835880300521",
     "ads": [("120248835884410521", "Video 1：赚美金，一定要接美国客户？"),
             ("120248835890070521", "Video 2：市场不考你的英文")]},
    {"label": "MY", "cfg": "config.yaml",
     "campaign": "120248248921210575", "adset": "120248248922280575",
     "ads": [("120248248924620575", "Video 1：赚美金，一定要接美国客户？"),
             ("120248248926530575", "Video 2：市场不考你的英文")]},
]

YWDFF_AD = "120248256492180521"          # «video 1：用我的方法» in [SG] INVESTMENT 1-1-3
YWDFF_CAMP_KEY = "[sg] stockbloom | investment | 1-1-3"
YWDFF_AD_KEY = "video 1：用我的方法"
TODAY = dt.date(2026, 8, 11)


def set_active(g, obj_id: str, kind: str) -> None:
    cur = g.get_object(obj_id, "effective_status").get("effective_status")
    if cur == "ACTIVE":
        print(f"   ✓ {kind} {obj_id} already ACTIVE")
        return
    if not CONFIRM:
        print(f"   ▶ would ACTIVATE {kind} {obj_id} (now {cur})")
        return
    g.update_status(obj_id, "ACTIVE")
    time.sleep(PACE)
    after = g.get_object(obj_id, "effective_status").get("effective_status")
    print(f"   ✅ {kind} {obj_id}  {cur} -> {after}")


def main() -> None:
    mode = "APPLY (CONFIRM=true)" if CONFIRM else "DRY-RUN (set confirm=true to apply)"
    print(f"do-all 0811 — {mode}\n")

    print("═══ 1) ACTIVATE BROAD MJ (campaign + adset + ads) ═══")
    for t in BROAD_MJ:
        s = load_settings(REPO_ROOT / "config" / t["cfg"])
        g = graph_client(s)
        print(f" [{t['label']}] {s.meta.account_path}")
        try:
            set_active(g, t["campaign"], "campaign")
            set_active(g, t["adset"], "adset")
            for ad_id, name in t["ads"]:
                set_active(g, ad_id, f"ad «{name[:28]}»")
            if CONFIRM:
                final = g.get_object(t["ads"][0][0], "effective_status").get("effective_status")
                print(f"   → delivery check ad1 effective_status = {final}"
                      + ("  ✅ live" if final == "ACTIVE" else "  ⚠️ not ACTIVE — check Ads Manager"))
        except GraphError as e:
            print(f"   ❌ [{t['label']}] {e} — continuing")
        print()

    print("═══ 2) 用我的方法 (SG) exact 60d CPA — read-only ═══")
    s = load_settings(REPO_ROOT / "config" / "config.sg.yaml")
    g = graph_client(s)
    try:
        ad = g.get_object(YWDFF_AD, "name,effective_status,created_time,campaign{name,effective_status}")
        camp = ad.get("campaign") or {}
        print(f"  ad «{ad.get('name')}»  status={ad.get('effective_status')}"
              f"  campaign «{camp.get('name')}» ({camp.get('effective_status')})")
        cutoff = TODAY - dt.timedelta(days=60)
        ins = g.get_ad_insight(YWDFF_AD, time_range={"since": cutoff.isoformat(),
                                                     "until": TODAY.isoformat()})
        spend60 = float((ins or {}).get("spend") or 0)

        from adbot.clients.sheets import SheetsClient
        values = SheetsClient(s.secrets.google_sa_json).read_tab(
            s.cpa.spreadsheet_id, s.cpa.sales_tab)
        sales, _c, _h = cpa.parse_sales(values, s.cpa.price_myr)
        strict = [x for x in sales if x.date and x.date > cutoff
                  and x.campaign == cpa.norm(YWDFF_CAMP_KEY) and x.ad == cpa.norm(YWDFF_AD_KEY)]
        by_name = [x for x in sales if x.date and x.date > cutoff and x.ad == cpa.norm(YWDFF_AD_KEY)]
        n = len(strict)
        val = cpa.cpa(spend60, n)
        print(f"  60d spend RM{spend60:.2f} · strict sales={n} ({[str(x.date) for x in strict]})"
              f" · name-only sales={len(by_name)}")
        if n:
            tier = ("healthy ≤800" if val <= 800 else
                    "monitor ≤960" if val <= 960 else
                    "pause-candidate ≤1200" if val <= 1200 else "over hard-stop 1200")
            print(f"  → CPA = RM{val:.0f}  [{tier}] · revenue RM{sum(x.amount for x in strict):.0f}"
                  f" · FE-ROAS {sum(x.amount for x in strict) / spend60:.2f}x" if spend60 else "")
            print(f"  → 若重开：CPA ≤1200 时监控的救援会保它；>1200 一小时内会被再关。")
        else:
            print("  → 60d 内无 strict 成交（异常——receipts 显示 7/29 与 8/6 各一单，请人工核对）")
    except GraphError as e:
        print(f"  ❌ {e}")

    print("\nDONE" if CONFIRM else "\nDRY-RUN DONE — set confirm=true to activate BROAD MJ.")


if __name__ == "__main__":
    main()
