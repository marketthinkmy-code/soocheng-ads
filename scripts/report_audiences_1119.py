# -*- coding: utf-8 -*-
"""READ-ONLY (owner 11/19「你先分析给我怎么判断 “好的受众” 我才决定」). Per audience (ad set targeting group), MY 5.0 + SG, since 10/29:
spend · Meta regs · real regs (Register UTM, S1 bots off) · real CPL · sales (buyer's last ad-UTM registration → that ad's audience) ·
CPA · reg→sale % · when the audience last spent. Plus the Paid list's all-time sales by audience keyword (Paid row's own UTM ad set =
the source that first brought the buyer; pre-10/29 rows included). No PII."""
from __future__ import annotations

import datetime as dt
import json
import re
from collections import Counter, defaultdict

from adbot import cpa
from adbot.clients.sheets import SheetsClient
from adbot.commands import graph_client
from adbot.monitor_cpl import _mkey, extract_results
from adbot.settings import REPO_ROOT, load_settings

TODAY = (dt.datetime.utcnow() + dt.timedelta(hours=8)).date()
U0 = dt.date(2026, 10, 29)
tr = lambda a, b: json.dumps({"since": a.isoformat(), "until": b.isoformat()})
AUD = [("luxury", "Luxury Goods"), ("beer", "Beer/Alcohol"), ("alcohol", "Beer/Alcohol"), ("omakase", "Omakase/Wagyu"), ("wagyu", "Omakase/Wagyu"),
       ("business owner", "Business Owner"), ("news", "News"), ("travel", "Travel"), ("golf", "Golf/Pickleball"), ("pickle", "Golf/Pickleball"),
       ("investment", "Investment"), ("day trading", "Day Trading"), ("lal", "Purchase LAL"), ("purchase", "Purchase LAL"),
       ("engaged shopper", "Engaged Shopper"), ("broker", "Brokers"), ("broad", "Broad"), ("pool", "Broad")]
aud = lambda n: next((v for k, v in AUD if k in (n or "").lower()), "其它")
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

pos, lix = {}, {}
for label, cfg, code in (("MY", "config.my5.yaml", "1048291251556714"), ("SG", "config.sg.yaml", "1614065190214320")):
    s = load_settings(REPO_ROOT / "config" / cfg)
    g = graph_client(s)
    toks = (f"offsite_conversion.custom.{code}", "offsite_conversion.fb_pixel_complete_registration")
    for r in g._get_all(s.meta.account_path + "/insights", {"level": "ad", "time_range": tr(U0, TODAY), "limit": "500",
                        "fields": "ad_id,ad_name,adset_name,campaign_name,spend,actions,date_stop"}):
        rg = next((v for v in (extract_results(r.get("actions"), t) for t in toks) if v), 0.0)
        pos[r["ad_id"]] = dict(label=label, aud=aud(r["adset_name"]), sp=float(r.get("spend") or 0), mr=rg, real=0, sales=0,
                               camp=r["campaign_name"], aset=r["adset_name"])
        lix[(_mkey(r["campaign_name"]), _mkey(r["adset_name"]), loose(r["ad_name"]))] = r["ad_id"]
    last = {}
    for r in g._get_all(s.meta.account_path + "/insights", {"level": "adset", "time_range": tr(U0, TODAY), "time_increment": "1",
                        "fields": "adset_name,spend", "limit": "500"}):
        if float(r.get("spend") or 0) > 0:
            k = (label, aud(r["adset_name"]))
            last[k] = max(last.get(k, ""), r["date_start"])
    pos.setdefault("_last", {}).update(last)
last = pos.pop("_last")

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
for p in paid:
    d = cpa.parse_date(p.get("Date", ""))
    if not d or d < U0 or not who(p):
        continue
    h = sorted({(dd, i): r for k in who(p) for dd, i, r in regs_by.get(k, []) if U0 <= dd <= d and (r.get("UTM Campaign") or "").strip()}.items())
    if h:
        aid = find(h[-1][1])
        if aid:
            pos[aid]["sales"] += 1

agg = defaultdict(Counter)
for v in pos.values():
    k = (v["label"], v["aud"])
    for f in ("sp", "mr", "real", "sales"):
        agg[k][f] += v[f]
print(f"现在 {dt.datetime.utcnow() + dt.timedelta(hours=8):%m-%d %H:%M} MYT · 10/29 起 · 真报名 = 报名表、去机器人 · 成交 = 买家买前最后一次广告报名的受众")
print("账户 受众                花费    Meta报名 真报名 真CPL  成交  CPA     报名→成交  最后花钱")
for (label, a), c in sorted(agg.items(), key=lambda kv: (-kv[1]["sales"], kv[1]["sp"] / max(kv[1]["sales"], 0.001), -kv[1]["sp"])):
    if c["sp"] < 30:
        continue
    cpl = c["sp"] / c["real"] if c["real"] else 0
    print(f"  {label} {a:<16} RM{c['sp']:>6,.0f}  {c['mr']:>5.0f}   {c['real']:>4}  {cpl:>5.0f}   {c['sales']:>2}  "
          f"{('RM%5.0f' % (c['sp'] / c['sales'])) if c['sales'] else '   —   '}  {(c['sales'] / c['real'] * 100 if c['real'] else 0):>5.1f}%    {last.get((label, a), '—')}")

# all-time Paid list by audience keyword of the Paid row's own UTM ad set (+ campaign when ad set blank)
allt = Counter()
yr = Counter()
for p in paid:
    d = cpa.parse_date(p.get("Date", ""))
    src = (p.get("UTM Ads Set") or "") + " " + (p.get("UTM Campaign") or "")
    if not src.strip() or not d:
        continue
    a = aud(src)
    acct = "SG" if "[sg]" in src.lower() else "MY"
    allt[(acct, a)] += 1
    if d >= dt.date(2026, 4, 1):
        yr[(acct, a)] += 1
print("\nPaid 表历史成交（按 Paid 行自带 UTM 的受众；10/28 以前的 UTM = 买家第一次来源）：  全部 / 4 月起")
for (acct, a), n in allt.most_common(25):
    print(f"  {acct} {a:<16} {n:>4} / {yr[(acct, a)]:>3}")
print("\nAUDIENCES DONE (read-only)")
