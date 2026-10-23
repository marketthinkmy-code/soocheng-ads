# -*- coding: utf-8 -*-
"""READ-ONLY 2026-10-18: Webinarkit chains since launch (17 Oct 00:00) — per campaign and per ad: spend, link clicks,
landing views, registrations (custom conversion), CPL, CPM, budget; per day; review issues; budget/status changes
in the activity log since 10/16 12:00 UTC. No PII."""
from __future__ import annotations

import datetime as dt
import json
import time
from collections import defaultdict

from adbot.commands import graph_client
from adbot.monitor_cpl import extract_results
from adbot.settings import REPO_ROOT, load_settings

WIN = {"since": "2026-10-17", "until": (dt.datetime.utcnow() + dt.timedelta(hours=8)).date().isoformat()}
PLAN = {
    ("MY 5.0", "config.my5.yaml", "offsite_conversion.custom.1048291251556714", 60):
        ["120251454680840329", "120251454704570329", "120251454700150329", "120251454713670329", "120251500767290329", "120251533786300329", "120251533789970329"],
    ("SG", "config.sg.yaml", "offsite_conversion.custom.1614065190214320", 95):
        ["120249918193090521", "120249918195380521", "120249918198320521", "120249918201630521", "120249964890710521", "120250027167260521", "120250027169830521"],
}
F = "spend,impressions,inline_link_clicks,actions,cpm"


def m(r, token):
    sp = float(r.get("spend") or 0)
    return sp, int(r.get("impressions") or 0), int(r.get("inline_link_clicks") or 0), \
        extract_results(r.get("actions"), "landing_page_view"), extract_results(r.get("actions"), token)


def main() -> None:
    print(f"window {WIN}")
    for (label, cfg, token, line), camps in PLAN.items():
        s = load_settings(REPO_ROOT / "config" / cfg)
        g = graph_client(s)
        acct = s.meta.account_path
        print(f"\n################ {label}（线 RM{line}）################")
        T = [0.0, 0, 0, 0.0, 0.0]
        for cid in camps:
            c = g.get_object(cid, "name,status,effective_status,daily_budget")
            time.sleep(0.7)
            ins = g._get_all(cid + "/insights", {"fields": F, "time_range": json.dumps(WIN)})
            sp, imp, lc, lpv, rg = m(ins[0] if ins else {}, token)
            for i, v in enumerate((sp, imp, lc, lpv, rg)):
                T[i] += v
            cpl = f"{sp / rg:.0f}" if rg else "∞"
            print(f"\n  «{c['name'][13:60]}» {c['effective_status']} RM{int(c.get('daily_budget') or 0) // 100} · 花 RM{sp:.0f} · imp {imp} · "
                  f"CPM {sp / imp * 1000 if imp else 0:.0f} · 点击 {lc} · LPV {lpv:.0f} · 报名 {rg:.0f} · CPL {cpl}")
            time.sleep(0.7)
            days = g._get_all(cid + "/insights", {"fields": F, "time_range": json.dumps(WIN), "time_increment": "1"})
            print("     按日: " + " · ".join(f"{d['date_start'][5:]} RM{float(d.get('spend') or 0):.0f}/{extract_results(d.get('actions'), token):.0f}" for d in days))
            time.sleep(0.7)
            ads = g._get_all(cid + "/insights", {"fields": "adset_name,ad_name," + F, "level": "ad", "time_range": json.dumps(WIN)})
            for a in sorted(ads, key=lambda r: -float(r.get("spend") or 0)):
                asp, aimp, alc, alpv, arg = m(a, token)
                print(f"     {a['adset_name'][:14]:<14} {a['ad_name'][:26]:<26} RM{asp:>4.0f} · 点击 {alc:>3} · LPV {alpv:>3.0f} · 报名 {arg:.0f}")
            st = g._get_all(cid + "/ads", {"fields": "name,effective_status,ad_review_feedback", "limit": "20"})
            bad = [x for x in st if x.get("effective_status") not in ("ACTIVE", "PAUSED", "CAMPAIGN_PAUSED", "ADSET_PAUSED", "DELETED", "ARCHIVED")]
            for x in bad:
                print(f"     ⚠️ {x['effective_status']} «{x['name']}» {json.dumps(x.get('ad_review_feedback'), ensure_ascii=False)[:150]}")
        print(f"\n  {label} 合计：花 RM{T[0]:.0f} · imp {T[1]} · 点击 {T[2]} · LPV {T[3]:.0f} · 报名 {T[4]:.0f} · CPL {T[0] / T[4] if T[4] else 0:.0f}")
        since_ts = int(dt.datetime(2026, 10, 16, 12).timestamp())
        acts = g._get_all(acct + "/activities", {"fields": "event_time,event_type,actor_name,object_name,extra_data", "since": str(since_ts), "limit": "300"})
        keep = [x for x in acts if any(k in (x.get("event_type") or "") for k in ("budget", "run_status")) and (x.get("actor_name") or "") != "Meta"]
        print(f"\n  {label} 人工/脚本 改动（{len(keep)} 条，UTC）:")
        for x in keep[:40]:
            ed = x.get("extra_data") or ""
            try:
                ed = json.loads(ed); ed = f"{str(ed.get('old_value'))[:40]} → {str(ed.get('new_value'))[:40]}"
            except Exception:                                        # noqa: BLE001
                ed = str(ed)[:60]
            print(f"   {x['event_time'][5:16]} {(x.get('actor_name') or '')[:16]:<16} {x['event_type'][:28]:<28} «{(x.get('object_name') or '')[:40]}» {ed}")
    print("\nSINCE 1017 DONE (read-only)")


if __name__ == "__main__":
    main()
