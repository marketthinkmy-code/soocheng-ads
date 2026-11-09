# -*- coding: utf-8 -*-
"""READ-ONLY (owner 11/9「my business owner 这两天怪怪的」): MY 5.0 BUSINESS OWNER campaign 120251454700150329 — per ad × day
since 10/29: spend, impressions, reach, frequency, CPM, CTR, landing-page views, Webinarkit registrations, CPL, reg/LPV;
plus the campaign's daily budget history (activity log) and the same metrics for BROAD MY korea as a control."""
from __future__ import annotations

import datetime as dt
import json

from adbot.commands import graph_client
from adbot.monitor_cpl import extract_results
from adbot.settings import REPO_ROOT, load_settings

TODAY = (dt.datetime.utcnow() + dt.timedelta(hours=8)).date()
S0 = dt.date(2026, 10, 29)
s = load_settings(REPO_ROOT / "config" / "config.my5.yaml")
g = graph_client(s)
acct, tok = s.meta.account_path, "offsite_conversion.custom.1048291251556714"
BO, BROAD = "120251454700150329", "120251454704570329"
F = "ad_id,ad_name,adset_name,spend,impressions,reach,frequency,inline_link_clicks,actions"
tr = json.dumps({"since": S0.isoformat(), "until": TODAY.isoformat()})


def line(r):
    sp, im, rc = float(r.get("spend") or 0), int(r.get("impressions") or 0), int(r.get("reach") or 0)
    lc = int(r.get("inline_link_clicks") or 0)
    lpv, rg = extract_results(r.get("actions"), "landing_page_view"), extract_results(r.get("actions"), tok)
    return (f"RM{sp:>5.0f} · imp {im:>6} · reach {rc:>6} · freq {float(r.get('frequency') or 0):.2f} · CPM {sp / im * 1000 if im else 0:>4.0f} · "
            f"CTR {lc / im * 100 if im else 0:.2f}% · LPV {lpv:>3.0f} · 报名 {rg:>2.0f} · CPL {(sp / rg) if rg else float('inf'):>5.0f} · "
            f"报名/LPV {(rg / lpv * 100) if lpv else 0:>3.0f}%")


for cid in (BO, BROAD):
    c = g.get_object(cid, "name,daily_budget,effective_status")
    print(f"\n################ «{c['name']}» · campaign {cid} · {c['effective_status']} · 现在 CBO RM{int(c.get('daily_budget') or 0) // 100}")
    rows = g._get_all(cid + "/insights", {"fields": F, "level": "campaign", "limit": "100", "time_range": tr, "time_increment": "1"})
    print("  campaign 每天:")
    for r in rows:
        print(f"   {r['date_start'][5:]} {line(r)}")
    ads = g._get_all(cid + "/insights", {"fields": F, "level": "ad", "limit": "500", "time_range": tr, "time_increment": "1"})
    by = {}
    for r in ads:
        by.setdefault((r["ad_id"], r["ad_name"], r["adset_name"]), []).append(r)
    for (aid, an, sn), rs in by.items():
        st = g.get_object(aid, "effective_status")["effective_status"]
        print(f"  {'🟢' if st == 'ACTIVE' else '🔴'} {sn} · {an} · ad {aid} · {st}")
        for r in sorted(rs, key=lambda x: x["date_start"]):
            if float(r.get("spend") or 0) > 0:
                print(f"     {r['date_start'][5:]} {line(r)}")
    since = int(dt.datetime.combine(S0, dt.time(0), tzinfo=dt.timezone.utc).timestamp())
    for x in g._get_all(acct + "/activities", {"fields": "event_time,event_type,actor_name,object_id,extra_data", "since": str(since), "limit": "1000"}):
        if x.get("object_id") == cid and "budget" in (x.get("event_type") or ""):
            t = (dt.datetime.fromisoformat(x["event_time"].replace("+0000", "+00:00")) + dt.timedelta(hours=8)).strftime("%m-%d %H:%M")
            print(f"  预算改动 {t} MYT [{x.get('actor_name')}] {x.get('extra_data')}")
print("\nBO DONE (read-only)")
