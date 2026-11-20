# -*- coding: utf-8 -*-
"""READ-ONLY (owner 2026-11-20 ~10:4x「我都开好了，你去 study 我开着的广告，告诉我每日 ad budget」).
Both accounts (MY 5.0 + SG): every ad that is actually delivering (effective_status ACTIVE / IN_PROCESS / PENDING_REVIEW), grouped by its
budget carrier (CBO campaign or ABO ad set) → daily budget per account + total. Per ad: Thursday window 11/19→now (spend · 报名 · CPL) and
owner's pick window 10/29–11/04. Flags: banned / 🚫 / not (Webinarkit) / DISAPPROVED / WITH_ISSUES. Also scans ACTIVE campaigns for
banned or rejected ads that are ad-layer ACTIVE but held by a paused ad set (拆引信). Then cycle spend (spend_cap) → projection to Wed 15:00."""
import datetime as dt
import json
from collections import defaultdict

from adbot import compliance
from adbot.commands import graph_client
from adbot.monitor_cpl import extract_results, spend_cap_status
from adbot.settings import REPO_ROOT, load_settings

NOW = dt.datetime.utcnow() + dt.timedelta(hours=8)
END = dt.datetime(2026, 11, 25, 15, 0)
LIVE = '["ACTIVE","IN_PROCESS","PENDING_REVIEW"]'
ACCTS = (("MY", "config.my5.yaml", "1048291251556714"), ("SG", "config.sg.yaml", "1614065190214320"))
W1 = (dt.date(2026, 10, 29), dt.date(2026, 11, 4))
W2 = (dt.date(2026, 11, 19), NOW.date())
print(f"现在 {NOW:%m-%d %H:%M} MYT · 只读 · 周四起 = 11/19 起 · 挑选窗口 = 10/29–11/04")
grand = {}
for lab, cfg, cc in ACCTS:
    s = load_settings(REPO_ROOT / "config" / cfg)
    g = graph_client(s)
    acct = s.meta.account_path
    tok = f"offsite_conversion.custom.{cc}"

    def ins(w):
        out = {}
        for r in g._get_all(acct + "/insights", {"fields": "ad_id,spend,actions", "level": "ad", "limit": "500",
                                                "time_range": json.dumps({"since": w[0].isoformat(), "until": w[1].isoformat()})}):
            out[r["ad_id"]] = (float(r.get("spend") or 0), extract_results(r.get("actions"), tok))
        return out

    i1, i2 = ins(W1), ins(W2)
    fmt = lambda x: f"RM{x[0]:4.0f}/{x[1]:2.0f}" + (f" CPL {x[0] / x[1]:4.0f}" if x[1] else (" 0 报名 " if x[0] >= 1 else "         "))
    rows = g._get_all(acct + "/ads", {"fields": "name,status,effective_status,adset{id,name,daily_budget,status},campaign{id,name,daily_budget,status}",
                                      "limit": "500", "effective_status": LIVE})
    carriers = defaultdict(list)
    for r in rows:
        cb = int(r["campaign"].get("daily_budget") or 0) // 100
        if cb:
            key = ("CBO", r["campaign"]["id"], r["campaign"]["name"], cb)
        else:
            key = ("ABO", r["adset"]["id"], r["campaign"]["name"] + " › " + r["adset"]["name"], int(r["adset"].get("daily_budget") or 0) // 100)
        carriers[key].append(r)
    tot = sum(k[3] for k in carriers)
    grand[lab] = tot
    print(f"\n################ {lab} · 在投放 {len(rows)} 支 ad · 日预算 RM{tot:,}")
    for k in sorted(carriers, key=lambda k: k[2]):
        kind, kid, kname, bud = k
        print(f"\n■ {kname.replace('(Webinarkit) ', '')} · {'campaign' if kind == 'CBO' else 'adset'} {kid} · {kind} RM{bud}"
              + ("" if kname.lower().startswith("(webinarkit)") else "  ❌ 不是 (Webinarkit)"))
        for r in sorted(carriers[k], key=lambda r: -i2.get(r["id"], (0, 0))[0]):
            flag = []
            if compliance.is_banned(r["name"], s.compliance.banned_creatives):
                flag.append("⛔禁跑")
            if r["effective_status"] != "ACTIVE":
                flag.append(r["effective_status"])
            where = "" if kind == "ABO" else f"{r['adset']['name']} · "
            print(f"   {where}{r['name']} · ad {r['id']} {' '.join(flag)}")
            print(f"        周四起 {fmt(i2.get(r['id'], (0, 0)))} · 10/29–11/04 {fmt(i1.get(r['id'], (0, 0)))}")
    # 拆引信: banned / rejected ads with ad layer ACTIVE inside an ACTIVE campaign (held only by a paused ad set)
    armed = []
    for c in g._get_all(acct + "/campaigns", {"fields": "name,status", "limit": "500", "effective_status": '["ACTIVE"]'}):
        for a in g._get_all(c["id"] + "/ads", {"fields": "name,status,effective_status,adset{name,status}", "limit": "300"}):
            if a["status"] == "ACTIVE" and (compliance.is_banned(a["name"], s.compliance.banned_creatives)
                                           or a["effective_status"] in ("DISAPPROVED", "WITH_ISSUES")):
                armed.append(f"{c['name']} › {a['adset']['name']} · {a['name']} · ad {a['id']} → {a['effective_status']}")
    print(f"\n   开着的 campaign 里 ad 层开着的禁跑 / 被拒 ad：{len(armed)}")
    for x in armed:
        print("   ⚠️ " + x)

s_my = load_settings(REPO_ROOT / "config" / "config.my5.yaml")
st = spend_cap_status(graph_client(s_my), s_my, NOW)
day = grand["MY"] + grand["SG"]
print(f"\n日预算合计 RM{day:,}（MY {grand['MY']:,} / SG {grand['SG']:,}）")
if st:
    total, line = st
    hrs = (END - NOW).total_seconds() / 3600
    proj = total + day * hrs / 24
    hit = NOW + dt.timedelta(hours=(line - total) / day * 24) if day else None
    print(f"周期花费（11/19 起两账户）RM{total:,.0f} · 关停线 RM{line:,.0f} · 照这个预算到周三 15:00 约 RM{proj:,.0f}"
          + (f" → 约 {hit:%m-%d %a %H:%M} 碰线" if hit and hit < END else " → 不会碰线"))
print("\nLIVE BUDGET 1120 DONE (read-only)")
