# -*- coding: utf-8 -*-
"""owner 11/25 23:2x (AskUserQuestion): at 11/26 00:00 I open — MY: BROAD MY 1017 (用我的方法 only; korea ad-level PAUSED 11/25),
CBO · LUX BEER OMAKASE 1-3-3 1120, BEST CPA · Broad 1-1-3 1120; SG: BROAD SG 1030 (+ ad-level reopen of 年纪大 ad 120250144813480521),
LOW CPL · Broad 1-1-3 1120. Guards (refuse everything if any fails): every campaign starts with (Webinarkit); the set of ads that would
deliver after opening == EXPECTED exactly (no extra ad slips in); none banned / 🚫 / rejected; cycle spend (spend_cap window) below the
stop line. CONFIRM=true writes: ad-level reopen first, then campaign layer; reads back every expected ad's effective_status."""
from __future__ import annotations

import datetime as dt
import os
import time

from adbot import compliance
from adbot.commands import graph_client
from adbot.monitor_cpl import spend_cap_status
from adbot.settings import REPO_ROOT, load_settings

CONFIRM = os.environ.get("CONFIRM", "").lower() in ("1", "true", "yes")
PLAN = {
    "MY": {"cfg": "config.my5.yaml",
           "camps": ["120251454704570329", "120251995650640329", "120251993979260329"],
           "reopen_ads": [],
           "expected": {"120251456458520329",
                        "120251995670340329", "120251995658960329", "120251995656940329", "120251995665060329",
                        "120251995664050329", "120251995675060329", "120251995663000329", "120251995668060329",
                        "120251993984490329", "120251993983160329"}},
    "SG": {"cfg": "config.sg.yaml",
           "camps": ["120250144810670521", "120250706566080521"],
           "reopen_ads": ["120250144813480521"],
           "expected": {"120250144813480521", "120250706571120521"}},
}
now = dt.datetime.utcnow() + dt.timedelta(hours=8)
print(f"现在 {now:%m-%d %H:%M} MYT · CONFIRM={CONFIRM}")
ok, ctx = True, {}
for label, p in PLAN.items():
    s = load_settings(REPO_ROOT / "config" / p["cfg"])
    g = graph_client(s)
    ctx[label] = (s, g)
    cap = spend_cap_status(g, s, now)
    print(f"\n[{label}] 周期花费：" + (f"RM{cap[0]:,.2f} / 关停线 RM{cap[1]:,.0f}" if cap else "窗口未开（11/26 00:00 起算）"))
    if cap and cap[0] >= cap[1]:
        print("  ❌ 已到关停线，拒绝开"); ok = False
    would = set()
    for cid in p["camps"]:
        c = g.get_object(cid, "name,status,daily_budget")
        if not c["name"].startswith("(Webinarkit)"):
            print(f"  ❌ 不是 (Webinarkit)：{c['name']}"); ok = False
        print(f"  {c['name']} · campaign {cid} · {c['status']} · CBO RM{float(c.get('daily_budget') or 0) / 100:.0f}")
        for a in g._get_all(f"{cid}/ads", {"fields": "name,status,effective_status,adset{name,status}", "limit": "100"}):
            runs = a["adset"]["status"] == "ACTIVE" and (a["status"] == "ACTIVE" or a["id"] in p["reopen_ads"])
            if not runs:
                continue
            would.add(a["id"])
            bad = compliance.is_banned(a["name"], s.compliance.banned_creatives) or "🚫" in a["name"] or a["effective_status"] in ("DISAPPROVED", "WITH_ISSUES")
            print(f"    会跑：{c['name']} › {a['adset']['name']} · {a['name']} · ad {a['id']}{' ❌禁跑/被拒' if bad else ''}"
                  f"{' （ad 层要开回）' if a['id'] in p['reopen_ads'] else ''}")
            ok = ok and not bad
    if would != p["expected"]:
        print(f"  ❌ 会跑的 ad 和预期不同：多 {sorted(would - p['expected'])} · 少 {sorted(p['expected'] - would)}"); ok = False
if not ok:
    raise SystemExit("REFUSED — 有检查没过，什么都没写")
if CONFIRM:
    for label, p in PLAN.items():
        s, g = ctx[label]
        for aid in p["reopen_ads"]:
            g._request("POST", aid, data={"status": "ACTIVE"}); time.sleep(1)
        for cid in p["camps"]:
            g._request("POST", cid, data={"status": "ACTIVE"}); time.sleep(1)
    time.sleep(20)
    for label, p in PLAN.items():
        s, g = ctx[label]
        print(f"\n[{label}] 回读")
        for cid in p["camps"]:
            print(f"  campaign {cid} → {g.get_object(cid, 'status')['status']}")
        for aid in sorted(p["expected"]):
            a = g.get_object(aid, "name,status,effective_status,adset{name,status},campaign{name,status}")
            print(f"  {a['campaign']['name']} › {a['adset']['name']} · {a['name']} · ad {aid} — campaign {a['campaign']['status']} / "
                  f"ad set {a['adset']['status']} / ad {a['status']} → {a['effective_status']}")
print("\nOPEN 1126 DONE" + ("" if CONFIRM else " (dry-run)"))
