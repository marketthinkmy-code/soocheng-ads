# -*- coding: utf-8 -*-
"""READ-ONLY (owner 11/12「你现在破例 不要看周四窗口归零，而是看新视频从开始跑，到现在」).
NEW VIDEO (6 campaigns) since launch 11/11 00:01 → now, per ad / per audience / per video:
spend · 报名 · CPL · split 11/11 vs 11/12 · CPM · link CTR · LPV · LPV→报名 rate · verdict with the RM80 rule on LIFETIME spend."""
from __future__ import annotations

import datetime as dt
import json
from collections import defaultdict

from adbot.commands import graph_client
from adbot.monitor_cpl import extract_results
from adbot.settings import REPO_ROOT, load_settings

L0 = dt.date(2026, 11, 11)
TODAY = (dt.datetime.utcnow() + dt.timedelta(hours=8)).date()
tr = lambda a, b: json.dumps({"since": a.isoformat(), "until": b.isoformat()})
V = {"一个目的": "V1 我只有一个目的", "炒了五年": "V2 炒了五年", "越认真盯盘": "V3 越认真盯盘", "决定变少": "V4 决定变少", "不适合你": "V5 不适合你"}
vid = lambda n: next((v for k, v in V.items() if k in n), n)
act = lambda acts, t: sum(float(a.get("value") or 0) for a in (acts or []) if a.get("action_type") == t)
print(f"现在 {dt.datetime.utcnow() + dt.timedelta(hours=8):%m-%d %H:%M} MYT · 新视频累计 11/11 → {TODAY} · 规则用累计花费：花满 RM80 才判；0 报名→关；CPL>80→关")
aud_t, vid_t = defaultdict(lambda: [0.0, 0.0, 0.0, 0.0, 0.0]), defaultdict(lambda: [0.0, 0.0])
for label, cfg, code in (("MY", "config.my5.yaml", "1048291251556714"), ("SG", "config.sg.yaml", "1614065190214320")):
    s = load_settings(REPO_ROOT / "config" / cfg)
    g, acct, tok = graph_client(s), s.meta.account_path, f"offsite_conversion.custom.{code}"
    base = {"fields": "campaign_name,adset_name,ad_name,ad_id,spend,impressions,inline_link_clicks,actions", "level": "ad", "limit": "1000",
            "filtering": json.dumps([{"field": "campaign.name", "operator": "CONTAIN", "value": "NEW VIDEO"}])}
    life = {r["ad_id"]: r for r in g._get_all(acct + "/insights", {**base, "time_range": tr(L0, TODAY)})}
    d1 = {r["ad_id"]: r for r in g._get_all(acct + "/insights", {**base, "time_range": tr(L0, L0)})}
    st = {a["id"]: a["effective_status"] for a in g._get_all(acct + "/ads", {"fields": "effective_status", "limit": "2000",
          "filtering": json.dumps([{"field": "campaign.name", "operator": "CONTAIN", "value": "NEW VIDEO"}])})}
    print(f"\n################ {label}")
    for r in sorted(life.values(), key=lambda r: (r["campaign_name"], r["adset_name"])):
        sp, rg = float(r.get("spend") or 0), extract_results(r.get("actions"), tok)
        im, lc, lpv = float(r.get("impressions") or 0), float(r.get("inline_link_clicks") or 0), act(r.get("actions"), "landing_page_view")
        a1 = d1.get(r["ad_id"], {}); s1, r1 = float(a1.get("spend") or 0), extract_results(a1.get("actions"), tok)
        aud = r["campaign_name"].split("NEW VIDEO · ")[1].split(" |")[0]
        if sp < 80:
            v = f"未满 RM80（还差 RM{80 - sp:.0f}）"
        elif rg == 0:
            v = "❌ 花满 RM80 · 0 报名 → 关"
        elif sp / rg > 80:
            v = f"❌ CPL {sp / rg:.0f} > 80 → 关"
        else:
            v = f"✅ CPL {sp / rg:.0f} ≤ 80 → 留"
        t = aud_t[f"{label} {aud}"]; t[0] += sp; t[1] += rg; t[2] += im; t[3] += lc; t[4] += lpv
        w = vid_t[vid(r["ad_name"])]; w[0] += sp; w[1] += rg
        print(f"  {label} NEW VIDEO · {aud} › {r['adset_name']} · ad {r['ad_id']} [{st.get(r['ad_id'], '?')}]\n"
              f"      累计 RM{sp:.0f} / {rg:.0f} 报名 (11/11 RM{s1:.0f}/{r1:.0f} · 11/12 RM{sp - s1:.0f}/{rg - r1:.0f}) · CPM {im and sp / im * 1000:.0f}"
              f" · CTR {im and lc / im:.2%} · LPV {lpv:.0f} → 报名率 {lpv and rg / lpv:.0%} → {v}")
print("\n== 受众（5 支视频合计）· 花费 · 报名 · CPL · CPM · CTR · LPV→报名")
for k, t in sorted(aud_t.items(), key=lambda kv: (kv[1][0] / kv[1][1]) if kv[1][1] else 9e9):
    print(f"  {k:24s} RM{t[0]:5.0f} · {t[1]:3.0f} · " + (f"CPL {t[0] / t[1]:4.0f}" if t[1] else "CPL   ∞") +
          f" · CPM {t[2] and t[0] / t[2] * 1000:3.0f} · CTR {t[2] and t[3] / t[2]:.2%} · {t[4] and t[1] / t[4]:.0%}")
print("\n== 视频（6 个受众合计）")
for k, w in sorted(vid_t.items(), key=lambda kv: (kv[1][0] / kv[1][1]) if kv[1][1] else 9e9):
    print(f"  {k:16s} RM{w[0]:5.0f} · {w[1]:3.0f} 报名 · " + (f"CPL {w[0] / w[1]:.0f}" if w[1] else "CPL ∞"))
print("\nNEWVIDEO LIFETIME DONE (read-only)")
