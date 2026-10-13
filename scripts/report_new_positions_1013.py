# -*- coding: utf-8 -*-
"""READ-ONLY: 2026-10-13 morning follow-up — delivery quality of the positions opened last night.

SG: every ad set that spent today (reach / frequency / CPM / link clicks / LPV / registrations, today and
yesterday) so the owner can see whether the 6 new positions are reaching new people or burning a tiny
audience; the three custom audiences they run on (approximate size). MY 5.0: the same per ad set, plus the
targeting of the ENGAGED SHOPPER ad set the team built last night (age / Advantage+ / special category).
No PII; prints RM / counts only."""
from __future__ import annotations

import json
import time

from adbot.commands import graph_client
from adbot.monitor_cpl import extract_results, result_action_type
from adbot.settings import REPO_ROOT, load_settings

SG_AUDIENCES = {
    "120249026332760521": "PURCHASE 1% LAL SG (seed: Paid Student List)",
    "120249853134410521": "LP 14d visitors not registered (SG) | 1012",
}
FIELDS = "adset_id,adset_name,campaign_name,spend,impressions,reach,frequency,cpm,inline_link_clicks,actions"


def main() -> None:
    for label, cfg in (("SG", "config.sg.yaml"), ("MY 5.0", "config.my5.yaml")):
        print(f"\n################ {label} ################")
        try:
            one(label, cfg)
        except Exception as exc:                                   # noqa: BLE001
            print(f"  ❌ {label} 读不到：{str(exc)[:200]}")
        time.sleep(2.0)
    print("\nNEW POSITIONS REPORT DONE (read-only)")


def one(label: str, cfg: str) -> None:
    s = load_settings(REPO_ROOT / "config" / cfg)
    g = graph_client(s)
    acct = s.meta.account_path
    token = result_action_type(s.meta.conversion_event)

    def rows(preset):
        time.sleep(1.3)
        return g.account_insights(acct, level="adset", fields=FIELDS, date_preset=preset)

    today = {r["adset_id"]: r for r in rows("today")}
    yday = {r["adset_id"]: r for r in rows("yesterday")}

    def line(r):
        if not r:
            return "—"
        sp = float(r.get("spend") or 0); imp = int(r.get("impressions") or 0); reach = int(r.get("reach") or 0)
        freq = float(r.get("frequency") or 0); cpm = float(r.get("cpm") or 0)
        lc = int(r.get("inline_link_clicks") or 0)
        lpv = extract_results(r.get("actions"), "landing_page_view")
        rg = extract_results(r.get("actions"), token)
        cpc = f"{sp / lc:.1f}" if lc else "—"
        return (f"RM{sp:>5.0f} · reach {reach:>5,} · freq {freq:4.2f} · CPM {cpm:5.1f} · 点击 {lc:>3} (RM{cpc}) "
                f"· LPV {lpv:>3.0f} · 报名 {rg:.0f}")

    ids = [k for k, _ in sorted(today.items(), key=lambda kv: -float(kv[1].get("spend") or 0))]
    print(f"═══ {label} 今天有花费的 ad set — 今天 / 昨天 ═══")
    for aid in ids:
        r = today[aid]
        print(f"\n  «{(r.get('adset_name') or '')[:30]}» @ {(r.get('campaign_name') or '')[16:50]}")
        print(f"     今天  {line(r)}")
        print(f"     昨天  {line(yday.get(aid))}")

    if label == "SG":
        print("\n═══ SG 新位用的受众 ═══")
        for aud_id, name in SG_AUDIENCES.items():
            time.sleep(1.2)
            try:
                a = g.get_object(aud_id, "name,subtype,approximate_count_lower_bound,approximate_count_upper_bound,delivery_status,time_updated")
                print(f"  «{(a.get('name') or name)[:48]}» {a.get('subtype')} · 约 {a.get('approximate_count_lower_bound')}–{a.get('approximate_count_upper_bound')} 人 · "
                      f"{(a.get('delivery_status') or {}).get('description', '')} · updated {a.get('time_updated')}")
            except Exception as exc:                               # noqa: BLE001
                print(f"  {name}: 读不到 {str(exc)[:100]}")
        time.sleep(1.2)
        lal = g._get_all(acct + "/customaudiences", {
            "fields": "id,name,subtype,approximate_count_lower_bound,approximate_count_upper_bound",
            "limit": "200"})
        for a in lal:
            if "5%" in (a.get("name") or "") and "PURCHASE" in (a.get("name") or "").upper():
                print(f"  «{(a.get('name') or '')[:48]}» {a.get('subtype')} · 约 {a.get('approximate_count_lower_bound')}–{a.get('approximate_count_upper_bound')} 人")
    else:
        time.sleep(1.2)
        sets = g._get_all(acct + "/adsets", {
            "fields": "id,name,status,effective_status,daily_budget,created_time,targeting,campaign{name,special_ad_categories,daily_budget}",
            "limit": "100"})
        for a in sets:
            if "ENGAGED" not in (a.get("name") or "").upper() and "ENGAGED" not in ((a.get("campaign") or {}).get("name") or "").upper():
                continue
            t = a.get("targeting") or {}
            flex = t.get("flexible_spec") or []
            ints = [i.get("name") for spec in flex for i in (spec.get("interests") or [])]
            beh = [i.get("name") for spec in flex for i in (spec.get("behaviors") or [])]
            print(f"\n═══ 团队昨晚建的 «{a.get('name')}» @ {((a.get('campaign') or {}).get('name') or '')[:44]} ═══")
            print(f"  {a.get('status')} / eff {a.get('effective_status')} · created {a.get('created_time')} · CBO RM{float(((a.get('campaign') or {}).get('daily_budget')) or 0)/100:.0f}")
            print(f"  special_ad_categories={(a.get('campaign') or {}).get('special_ad_categories')} · age {t.get('age_min')}-{t.get('age_max')} · "
                  f"age_range={t.get('age_range')} · advantage_audience={(t.get('targeting_automation') or {}).get('advantage_audience')}")
            print(f"  geo={json.dumps(t.get('geo_locations'), ensure_ascii=False)[:120]}")
            print(f"  interests={ints[:15]}")
            print(f"  behaviors={beh[:10]}")


if __name__ == "__main__":
    main()
