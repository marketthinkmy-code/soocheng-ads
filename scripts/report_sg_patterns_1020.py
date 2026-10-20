# -*- coding: utf-8 -*-
"""READ-ONLY 2026-10-20: what makes SG ads cheap AND convert? Last 90 days of SG ad-level spend + registrations
(old pixel COMPLETE_REGISTRATION + Webinarkit custom conversion) joined to Paid Student List SG sales (utm names).
Grouped by audience (campaign-name family), by creative (edition prefixes stripped), audience x creative, and by
age / gender / placement breakdowns of registrations. Prints names, counts and RM only — no buyer PII."""
from __future__ import annotations

import datetime as dt
import json
import re
import time
from collections import defaultdict

from adbot import cpa
from adbot.clients.sheets import SheetsClient
from adbot.commands import graph_client
from adbot.monitor_cpl import extract_results
from adbot.settings import REPO_ROOT, load_settings

OLD = "offsite_conversion.fb_pixel_complete_registration"
NEW = "offsite_conversion.custom.1614065190214320"
FAMILIES = ["LUXURY WATCHES", "LUXURY GOODS", "LAL", "BROAD", "ANDRO POOL", "GOLF", "TRAVEL", "PRIORITY BANKING",
            "INVESTMENT", "BROKERS", "DAY TRADING", "NEWS", "BEER", "OMAKASE", "RETARGET", "AUG NEW", "DIVING"]


def fam(name: str) -> str:
    n = (name or "").upper()
    for f in FAMILIES:
        if f in n:
            return "PURCHASE LAL" if f == "LAL" else f
    return "OTHER"


def cre(name: str) -> str:
    k = cpa.creative_key(name or "")
    k = re.sub(r"^video\s*\d*\s*[：:]\s*", "", k)
    return k[:28]


def main() -> None:
    s = load_settings(REPO_ROOT / "config" / "config.sg.yaml")
    g = graph_client(s)
    acct = s.meta.account_path
    today = (dt.datetime.utcnow() + dt.timedelta(hours=8)).date()
    win = {"since": (today - dt.timedelta(days=90)).isoformat(), "until": today.isoformat()}
    rows = g.account_insights(acct, level="ad", fields="campaign_name,ad_name,spend,impressions,inline_link_clicks,actions", time_range=win)
    vals = SheetsClient(s.secrets.google_sa_json).read_tab(s.cpa.spreadsheet_id, s.cpa.sales_tab)
    sales, _c, _h = cpa.parse_sales(vals, 2399.0)
    sg = [x for x in sales if "[sg]" in (x.campaign or "") and x.date and x.date >= today - dt.timedelta(days=90)]
    print(f"SG 90d: {len(rows)} ad rows · SG paid sales in sheet (90d): {len(sg)} · RM{sum(x.amount for x in sg):,.0f}")

    def agg(keyf):
        d = defaultdict(lambda: [0.0, 0.0, 0, 0, 0.0])
        for r in rows:
            k = keyf(r)
            sp = float(r.get("spend") or 0)
            d[k][0] += sp
            d[k][1] += extract_results(r.get("actions"), OLD) + extract_results(r.get("actions"), NEW)
            d[k][2] += int(r.get("inline_link_clicks") or 0)
        return d

    def sales_by(keyf_sale):
        d = defaultdict(lambda: [0, 0.0])
        for x in sg:
            k = keyf_sale(x)
            d[k][0] += 1; d[k][1] += x.amount
        return d

    for title, kr, ks in (("受众（campaign family）", lambda r: fam(r.get("campaign_name")), lambda x: fam(x.campaign)),
                          ("素材", lambda r: cre(r.get("ad_name")), lambda x: cre(x.ad))):
        A, S = agg(kr), sales_by(ks)
        keys = sorted(set(A) | set(S), key=lambda k: -(A[k][0] if k in A else 0))
        print(f"\n═══ {title} — 90d ═══")
        print(f"  {'key':<30} {'花费':>8} {'报名':>5} {'CPL':>5} {'成交':>4} {'收入':>8} {'CPA':>6} {'ROAS':>5}")
        for k in keys:
            sp, rg, lc = (A[k][0], A[k][1], A[k][2]) if k in A else (0, 0, 0)
            n, rev = (S[k][0], S[k][1]) if k in S else (0, 0)
            if sp < 30 and not n:
                continue
            print(f"  {k:<30} {sp:>8,.0f} {rg:>5.0f} {sp / rg if rg else 0:>5.0f} {n:>4} {rev:>8,.0f} {sp / n if n else 0:>6,.0f} {rev / sp if sp else 0:>5.1f}")

    AX = agg(lambda r: (fam(r.get("campaign_name")), cre(r.get("ad_name"))))
    SX = sales_by(lambda x: (fam(x.campaign), cre(x.ad)))
    print("\n═══ 受众 × 素材（有成交或花费≥RM150）═══")
    for k in sorted(set(AX) | set(SX), key=lambda k: -((SX[k][0] if k in SX else 0) * 1000 + (AX[k][0] if k in AX else 0))):
        sp, rg = (AX[k][0], AX[k][1]) if k in AX else (0, 0)
        n = SX[k][0] if k in SX else 0
        if n or sp >= 150:
            print(f"  {k[0]:<16} × {k[1]:<26} 花 RM{sp:>6,.0f} · 报名 {rg:>3.0f} · CPL {sp / rg if rg else 0:>4.0f} · 成交 {n}")

    for bd in ("age", "gender", "publisher_platform"):
        time.sleep(1.5)
        try:
            br = g._get_all(acct + "/insights", {"level": "account", "fields": "spend,actions", "breakdowns": bd,
                                                  "time_range": json.dumps({"since": (today - dt.timedelta(days=60)).isoformat(), "until": today.isoformat()})})
            print(f"\n═══ 60d by {bd} ═══")
            for r in sorted(br, key=lambda r: -float(r.get("spend") or 0)):
                sp = float(r.get("spend") or 0)
                rg = extract_results(r.get("actions"), OLD) + extract_results(r.get("actions"), NEW)
                print(f"  {str(r.get(bd)):<14} RM{sp:>7,.0f} · 报名 {rg:>4.0f} · CPL {sp / rg if rg else 0:>5.0f}")
        except Exception as e:                                       # noqa: BLE001
            print(f"  {bd} ❌ {str(e)[:120]}")
    print("\nSG PATTERNS DONE (read-only)")


if __name__ == "__main__":
    main()
