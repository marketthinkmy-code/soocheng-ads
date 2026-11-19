# -*- coding: utf-8 -*-
"""READ-ONLY (owner 11/19「你先准备给我 6 个近期跑到不错的，有成交的，低 CPL 的旧素材 & 新视频，并给我知道原因为什么，也给我 existing post id」).
Per creative (母带, grouped by keyword) since 10/29 (UTM reliable), MY 5.0 + SG, every position (any status):
spend · Meta regs · real regs (Register UTM, S1 bots removed) · real CPL · last cycle 11/12–11/18 real CPL · sales (buyer's last ad-UTM
registration on/before purchase → that position) · CPA · ban flag · each position with its existing post id (effective_object_story_id). No PII."""
from __future__ import annotations

import datetime as dt
import json
import re
from collections import defaultdict

from adbot import compliance, cpa
from adbot.clients.sheets import SheetsClient
from adbot.commands import graph_client
from adbot.monitor_cpl import _mkey, extract_results
from adbot.settings import REPO_ROOT, load_settings

TODAY = (dt.datetime.utcnow() + dt.timedelta(hours=8)).date()
U0, C0, C1 = dt.date(2026, 10, 29), dt.date(2026, 11, 12), dt.date(2026, 11, 18)
tr = lambda a, b: json.dumps({"since": a.isoformat(), "until": b.isoformat()})
CRE = [("赚美金", "🚫赚美金"), ("年纪大", "年纪大的人做不了交易？"), ("盖电脑", "盖电脑，喂！"), ("用我的方法", "用我的方法"),
       ("korea", "freestyle korea"), ("我跟你讲", "我跟你讲！"), ("不选", "不选 forex 不选黄金"), ("决定变少", "NV V4 决定变少，成绩才稳"),
       ("炒了五年", "NV V2 炒了五年，账户还是那个数"), ("不适合你", "NV V5 这条视频不适合你"), ("一个目的", "NV V1 我只有一个目的（续作）"),
       ("越认真盯盘", "NV V3 越认真盯盘的人，亏得越快")]
cre = lambda n: next((v for k, v in CRE if k in (n or "").lower()), None)
loose = lambda a: re.sub(r"[\W_]+", "", re.sub(r"^(?:video|image)\s*\d*\s*[：:]\s*", "", cpa.norm(a)))
s0 = load_settings(REPO_ROOT / "config" / "config.sg.yaml")
sc = SheetsClient(s0.secrets.google_sa_json)


def table(tab, must):
    v = sc.read_tab(s0.cpa.spreadsheet_id, tab)
    hi = next(i for i, r in enumerate(v[:10]) if must in r)
    return v[hi], [dict(zip(v[hi], r)) for r in v[hi + 1:]]


rh, reg = table("Register", "Email")
_, paid = table(s0.cpa.sales_tab, "UTM Campaign")
ad_col = next((h for h in rh if cpa._hkey(h) in ("utmadsname", "utmadname")), "UTM Ads Name")
who = lambda r: cpa.contact_keys(r.get("Email", ""), r.get("Phone Number", ""))
bot = lambda r: cpa.is_bot_registration(r.get("Name", ""), r.get("Experience", ""))

pos = {}          # ad id -> record
lix = {}          # (camp key, adset key, loose ad) -> ad id
for label, cfg, code in (("MY", "config.my5.yaml", "1048291251556714"), ("SG", "config.sg.yaml", "1614065190214320")):
    s = load_settings(REPO_ROOT / "config" / cfg)
    g = graph_client(s)
    toks = (f"offsite_conversion.custom.{code}", "offsite_conversion.fb_pixel_complete_registration")
    ins = {r["ad_id"]: r for r in g._get_all(s.meta.account_path + "/insights", {"level": "ad", "time_range": tr(U0, TODAY),
                                                                                 "fields": "ad_id,spend,actions", "limit": "500"})}
    for a in g._get_all(s.meta.account_path + "/ads", {"fields": "name,effective_status,created_time,adset{name},campaign{name},"
                                                                  "creative{effective_object_story_id,object_story_id}", "limit": "500"}):
        c = cre(a["name"])
        if not c:
            continue
        i = ins.get(a["id"], {})
        rg = next((v for v in (extract_results(i.get("actions"), t) for t in toks) if v), 0.0)
        cr = a.get("creative") or {}
        rec = dict(label=label, a=a, cre=c, sp=float(i.get("spend") or 0), mr=rg, real=0, real_c=0, sp_c=0.0, sales=[],
                   post=cr.get("effective_object_story_id") or cr.get("object_story_id") or "—",
                   banned=compliance.is_banned(a["name"], s.compliance.banned_creatives) or "🚫" in a["name"])
        pos[a["id"]] = rec
        lix[(_mkey(a["campaign"]["name"]), _mkey(a["adset"]["name"]), loose(a["name"]))] = a["id"]
    for r in g._get_all(s.meta.account_path + "/insights", {"level": "ad", "time_range": tr(C0, C1), "fields": "ad_id,spend", "limit": "500"}):
        if r["ad_id"] in pos:
            pos[r["ad_id"]]["sp_c"] = float(r.get("spend") or 0)

find = lambda r: lix.get((_mkey(cpa.norm(r.get("UTM Campaign"))), _mkey(cpa.norm(r.get("UTM Ads Set"))), loose(r.get(ad_col))))
regs_by = defaultdict(list)
for i, r in enumerate(reg):
    d = cpa.parse_date(r.get("Created date", ""))
    if not d:
        continue
    for k in who(r):
        regs_by[k].append((d, i, r))
    if d >= U0 and (r.get("UTM Campaign") or "").strip() and not bot(r):
        aid = find(r)
        if aid:
            pos[aid]["real"] += 1
            if C0 <= d <= C1:
                pos[aid]["real_c"] += 1
for n, p in enumerate(paid):
    d = cpa.parse_date(p.get("Date", ""))
    if not d or d < U0 or not who(p):
        continue
    h = sorted({(dd, i): r for k in who(p) for dd, i, r in regs_by.get(k, []) if U0 <= dd <= d and (r.get("UTM Campaign") or "").strip()}.items())
    if h:
        aid = find(h[-1][1])
        if aid:
            pos[aid]["sales"].append((d, p.get("Source") or "—"))

agg = defaultdict(lambda: dict(sp=0.0, mr=0.0, real=0, real_c=0, sp_c=0.0, sales=[], rows=[], banned=False))
for rec in pos.values():
    g_ = agg[rec["cre"]]
    for f in ("sp", "mr", "real", "real_c", "sp_c"):
        g_[f] += rec[f]
    g_["sales"] += rec["sales"]
    g_["rows"].append(rec)
    g_["banned"] |= rec["banned"]
print(f"现在 {dt.datetime.utcnow() + dt.timedelta(hours=8):%m-%d %H:%M} MYT · 10/29 起（UTM 可信）· 真报名 = 报名表、去机器人")
for c, g_ in sorted(agg.items(), key=lambda kv: (-len(kv[1]["sales"]), kv[1]["sp"] / max(kv[1]["real"], 1))):
    if g_["sp"] < 1:
        continue
    ns = len(g_["sales"])
    print(f"\n■ {c}{' ⛔禁跑' if g_['banned'] else ''} · 10/29 起 RM{g_['sp']:,.0f} · Meta 报名 {g_['mr']:.0f} · 真报名 {g_['real']} · 真 CPL {g_['sp'] / max(g_['real'], 1):,.0f}"
          f" · 上一期(11/12–18) RM{g_['sp_c']:,.0f}/{g_['real_c']} 真报名 · 成交 {ns}" + (f" · CPA RM{g_['sp'] / ns:,.0f}" if ns else "")
          + (" · 成交日 " + ", ".join(f"{d:%m/%d}" for d, _ in sorted(g_["sales"])) if ns else ""))
    for rec in sorted(g_["rows"], key=lambda r: (-len(r["sales"]), -r["sp"])):
        if rec["sp"] < 1 and not rec["sales"]:
            continue
        a = rec["a"]
        print(f"   {rec['label']} {a['campaign']['name']} › {a['adset']['name']} · {a['name']} · ad {a['id']} · {a['effective_status']}\n"
              f"       RM{rec['sp']:,.0f} · 真报名 {rec['real']} · 成交 {len(rec['sales'])} · post {rec['post']}")
print("\nTOP CREATIVES DONE (read-only)")
