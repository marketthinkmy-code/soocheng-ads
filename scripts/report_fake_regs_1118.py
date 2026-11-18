# -*- coding: utf-8 -*-
"""READ-ONLY (owner 11/18「Stockbloom 的好像被人针对，都是马来人…这个要关掉什么？毕竟这个浪费钱了」 + Register screenshot:
rows dated 13/11 whose Experience field = first name typed twice, emails unrelated to the name).
Flags suspected bot registrations in the Register tab and counts them — NO names / emails / phones printed.
  A) header (non-PII columns) + how many rows per day 10/29→today, suspected vs clean, per Source;
  B) suspected rows by UTM campaign › ad set › ad (which ad positions the bot traffic came through), and by UTM source/medium;
  C) Meta-reported registrations per placement per day (MY 5.0 + SG) 11/05→today — is one placement (e.g. Audience Network) carrying them?
Suspect rule S1: Experience == (first word of Name) × 2  (e.g. "AbcAbc"); S2: email local part shares no 3+ letter token with the name."""
from __future__ import annotations

import datetime as dt
import json
import re
from collections import Counter, defaultdict

from adbot import cpa
from adbot.clients.sheets import SheetsClient
from adbot.commands import graph_client
from adbot.monitor_cpl import extract_results
from adbot.settings import REPO_ROOT, load_settings

D0 = dt.date(2026, 10, 29)
TODAY = (dt.datetime.utcnow() + dt.timedelta(hours=8)).date()
tr = lambda a, b: json.dumps({"since": a.isoformat(), "until": b.isoformat()})
s0 = load_settings(REPO_ROOT / "config" / "config.sg.yaml")
sc = SheetsClient(s0.secrets.google_sa_json)
v = sc.read_tab(s0.cpa.spreadsheet_id, "Register")
hi = next(i for i, r in enumerate(v[:10]) if "Email" in r)
hdr = v[hi]
rows = [dict(zip(hdr, r)) for r in v[hi + 1:]]
print(f"现在 {dt.datetime.utcnow() + dt.timedelta(hours=8):%m-%d %H:%M} MYT · Register 共 {len(rows)} 行")
print("  表头(不含个资栏): " + str([h for h in hdr if h and not re.search("name|email|phone|mail|电话|名字", h, re.I)]))


def s1(r):
    nm = (r.get("Name") or "").strip()
    fw = nm.split()[0] if nm.split() else ""
    ex = (r.get("Experience") or "").strip()
    return bool(fw) and ex == fw * 2


def s2(r):
    toks = {t.lower() for t in re.findall(r"[A-Za-z]{3,}", r.get("Name") or "")}
    loc = (r.get("Email") or "").split("@")[0].lower()
    return bool(toks) and bool(loc) and not any(t in loc for t in toks)


cc = lambda p: "SG" if re.sub(r"\D", "", p or "").startswith("65") else ("MY" if re.sub(r"\D", "", p or "").startswith(("60", "01")) else "?")
byday = defaultdict(Counter)
bypos = Counter()
bysrc = Counter()
first_bad = None
for r in rows:
    d = cpa.parse_date(r.get("Created date", ""))
    if not d or d < D0:
        continue
    a, b = s1(r), s2(r)
    tag = "S1" if a else ("S2" if b else "ok")
    byday[d][tag] += 1
    byday[d]["cc_" + cc(r.get("Phone Number"))] += 1
    if a:
        first_bad = first_bad or d
        bypos[(r.get("UTM Campaign") or "空", r.get("UTM Ads Set") or "空", r.get("UTM Ads Name") or "空")] += 1
        bysrc[(r.get("Source") or "空", r.get("UTM Source") or r.get("UTM source") or "", r.get("UTM Medium") or r.get("UTM medium") or "")] += 1
print("\n== A) 每天报名：S1=Experience 是名字打两次（几乎肯定是机器人） · S2=电邮和名字无关（较弱） · ok")
for d in sorted(byday):
    c = byday[d]
    tot = c["S1"] + c["S2"] + c["ok"]
    print(f"   {d:%m-%d %a} 共 {tot:3d} · S1 {c['S1']:3d} · S2 {c['S2']:3d} · ok {c['ok']:3d} · 电话 MY {c['cc_MY']} / SG {c['cc_SG']} / ? {c['cc_?']}")
print(f"   第一笔 S1：{first_bad}")
print("\n== B) S1 来源（UTM campaign › ad set › ad）")
for (c_, s_, a_), n in bypos.most_common(40):
    print(f"   {n:3d} · {c_} › {s_} › {a_}")
print("   -- Source / UTM source / medium")
for k, n in bysrc.most_common(10):
    print(f"   {n:3d} · {k}")

print("\n== C) Meta 报名按版位（每天）")
for label, cfg, code in (("MY 5.0", "config.my5.yaml", "1048291251556714"), ("SG", "config.sg.yaml", "1614065190214320")):
    s = load_settings(REPO_ROOT / "config" / cfg)
    g, acct, tok = graph_client(s), s.meta.account_path, f"offsite_conversion.custom.{code}"
    out = defaultdict(dict)
    for r in g._get_all(acct + "/insights", {"fields": "spend,impressions,inline_link_clicks,actions", "level": "account",
                                             "breakdowns": "publisher_platform,platform_position", "time_increment": "1",
                                             "time_range": tr(dt.date(2026, 11, 5), TODAY), "limit": "1000"}):
        rg = extract_results(r.get("actions"), tok)
        out[r["date_start"]][f"{r['publisher_platform']}/{r['platform_position']}"] = (float(r.get("spend") or 0), rg,
                                                                                     float(r.get("inline_link_clicks") or 0), float(r.get("impressions") or 0))
    print(f"  ######## {label}（只列有报名的版位：报名/花费/CTR）")
    for d in sorted(out):
        parts = [f"{k} {v[1]:.0f}报名/RM{v[0]:.0f}/CTR{v[2] / v[3] * 100 if v[3] else 0:.1f}%" for k, v in sorted(out[d].items(), key=lambda kv: -kv[1][1]) if v[1]]
        an = sum(v[0] for k, v in out[d].items() if k.startswith("audience_network"))
        print(f"   {d[5:]} " + " · ".join(parts) + f"  ‖ AN 花费 RM{an:.0f}")
print("\nFAKE REGS 1118 DONE (read-only)")
