# -*- coding: utf-8 -*-
"""READ-ONLY (owner 2026-11-20「因为 29/10 - 4/11 的成交不错（10人），所以我会开回 MY & SG 那段期间跑到不错的广告」 + SG Ads Manager
screenshot: BROAD SG 1030 Active · PURCHASE LAL 5% 1017「No ads」· TRAVEL SG 1030「No ads」· WINNERS 1020「Ad sets off」).
For every SG campaign whose campaign switch is ON (+ DAY TRADING SG 1023 for reference): each ad set + ad — three layers, effective_status,
banned / 🚫 / DISAPPROVED flag, and the owner's window 10/29–11/04 (spend · 报名 · CPL) next to Thursday-window 11/19→now. Nothing is written."""
import datetime as dt
import json

from adbot import compliance
from adbot.commands import graph_client
from adbot.monitor_cpl import extract_results
from adbot.settings import REPO_ROOT, load_settings

NOW = dt.datetime.utcnow() + dt.timedelta(hours=8)
TOK = "offsite_conversion.custom.1614065190214320"
W1 = (dt.date(2026, 10, 29), dt.date(2026, 11, 4))
W2 = (dt.date(2026, 11, 19), NOW.date())
s = load_settings(REPO_ROOT / "config" / "config.sg.yaml")
g = graph_client(s)
acct = s.meta.account_path
assert acct == "act_893025326577600", acct


def ins(w):
    out = {}
    for r in g._get_all(acct + "/insights", {"fields": "ad_id,spend,actions", "level": "ad", "limit": "500",
                                            "time_range": json.dumps({"since": w[0].isoformat(), "until": w[1].isoformat()})}):
        out[r["ad_id"]] = (float(r.get("spend") or 0), extract_results(r.get("actions"), TOK))
    return out


def fmt(x):
    sp, rg = x
    return f"RM{sp:5.0f}/{rg:2.0f}" + (f" CPL {sp / rg:4.0f}" if rg else ("  0 报名" if sp else "        "))


i1, i2 = ins(W1), ins(W2)
print(f"现在 {NOW:%m-%d %H:%M} MYT · SG · 只读 · 窗口 A = 10/29–11/04（owner 看的）· 窗口 B = 周四 11/19 起")
camps = g._get_all(acct + "/campaigns", {"fields": "name,status,effective_status,daily_budget", "limit": "500"})
pick = [c for c in camps if c["status"] == "ACTIVE" or "DAY TRADING SG | 1-1-5 | 1023" in c["name"]]
for c in sorted(pick, key=lambda c: c["name"]):
    cb = int(c.get("daily_budget") or 0) // 100
    print(f"\n■ {c['name']} · campaign {c['id']} · campaign {c['status']} → {c['effective_status']}" + (f" · CBO RM{cb}" if cb else " · ABO"))
    sets = {a["id"]: a for a in g._get_all(c["id"] + "/adsets", {"fields": "name,status,effective_status,daily_budget", "limit": "100"})}
    ads = g._get_all(c["id"] + "/ads", {"fields": "name,status,effective_status,adset_id", "limit": "300"})
    for sid, a in sets.items():
        ab = int(a.get("daily_budget") or 0) // 100
        print(f"   ▸ ad set {a['name']} · {sid} — {a['status']} → {a['effective_status']}" + (f" · RM{ab}" if ab else ""))
        for ad in [x for x in ads if x["adset_id"] == sid]:
            bad = []
            if compliance.is_banned(ad["name"], s.compliance.banned_creatives):
                bad.append("⛔禁跑")
            if ad["effective_status"] in ("DISAPPROVED", "WITH_ISSUES"):
                bad.append("⛔" + ad["effective_status"])
            a1, a2 = i1.get(ad["id"], (0.0, 0.0)), i2.get(ad["id"], (0.0, 0.0))
            print(f"       {ad['name']} · ad {ad['id']} — ad {ad['status']} → {ad['effective_status']} {' '.join(bad)}")
            print(f"            A {fmt(a1)} · B {fmt(a2)}")
print("\nSG REOPEN CHECK DONE (read-only)")
