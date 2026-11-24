# -*- coding: utf-8 -*-
"""READ-ONLY (WK 11/23「MY 这期不建，下期再调」→ prepare the next-cycle MY structure for WK to approve).
MY 5.0 only. Per audience × creative (母带 keyword), two windows:
  ① 10/29 → today (UTM reliable): spend · Meta regs · real regs (Register UTM, S1 bots off) · real CPL · sales · CPA · reg→sale %
  ② this cycle 11/19 → today: spend · Meta regs · real regs · real CPL
Sales = buyer's last ad-UTM registration on/before purchase → that position (same strict key as the monitor: campaign › ad set › ad).
Also: Paid rows dated ≥ 11/19 (new since last run) and where they attribute; every position's status + post id for the top combos.
Rejection history flags come from CLAUDE.md (SG 11/05 + 11/21 rejections, banned list). No PII."""
from __future__ import annotations

import datetime as dt
import json
import re
from collections import Counter, defaultdict

from adbot import compliance, cpa
from adbot.clients.sheets import SheetsClient
from adbot.commands import graph_client
from adbot.monitor_cpl import _mkey, extract_results
from adbot.settings import REPO_ROOT, load_settings

NOW = dt.datetime.utcnow() + dt.timedelta(hours=8)
TODAY = NOW.date()
U0, C0 = dt.date(2026, 10, 29), dt.date(2026, 11, 19)
tr = lambda a, b: json.dumps({"since": a.isoformat(), "until": b.isoformat()})
AUD = [("luxury", "Luxury"), ("beer", "Beer"), ("alcohol", "Beer"), ("omakase", "Omakase"), ("wagyu", "Omakase"),
       ("business owner", "Business Owner"), ("news", "News"), ("day trading", "Day Trading"), ("broad", "Broad")]
aud = lambda n: next((v for k, v in AUD if k in (n or "").lower()), "其它")
CRE = [("赚美金", "🚫赚美金"), ("年纪大", "年纪大"), ("盖电脑", "盖电脑"), ("用我的方法", "用我的方法"), ("korea", "korea"),
       ("我跟你讲", "我跟你讲"), ("不选", "不选 forex"), ("决定变少", "V4 决定变少"), ("炒了五年", "V2 炒了五年"),
       ("不适合你", "V5 不适合你"), ("一个目的", "V1 一个目的"), ("越认真盯盘", "V3 越认真盯盘")]
cre = lambda n: next((v for k, v in CRE if k in (n or "").lower()), "其它")
# rejection history (CLAUDE.md): SG 11/05 batch (owner exception C), SG 11/21 (owner appealing), banned family
REJ = {"korea": "SG 11/05 旧副本被拒（例外 C）", "盖电脑": "SG 11/05 旧副本被拒（例外 C）", "不选 forex": "SG 11/05 被拒（例外 C）；MY 10/08 被拒",
       "用我的方法": "SG 11/05 旧副本被拒（例外 C）", "V2 炒了五年": "SG 11/21 被拒 · 申诉中", "我跟你讲": "SG 11/21 被拒 · 申诉中",
       "🚫赚美金": "永久禁跑"}
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

s = load_settings(REPO_ROOT / "config" / "config.my5.yaml")
g = graph_client(s)
toks = ("offsite_conversion.custom.1048291251556714", "offsite_conversion.fb_pixel_complete_registration")
ins = {r["ad_id"]: r for r in g._get_all(s.meta.account_path + "/insights", {"level": "ad", "time_range": tr(U0, TODAY),
                                                                             "fields": "ad_id,spend,actions", "limit": "500"})}
insc = {r["ad_id"]: r for r in g._get_all(s.meta.account_path + "/insights", {"level": "ad", "time_range": tr(C0, TODAY),
                                                                              "fields": "ad_id,spend,actions", "limit": "500"})}
reg_of = lambda i: next((v for v in (extract_results((i or {}).get("actions"), t) for t in toks) if v), 0.0)
pos, lix = {}, {}
for a in g._get_all(s.meta.account_path + "/ads", {"fields": "name,status,effective_status,adset{name,status,daily_budget},"
                                                              "campaign{name,status,daily_budget},creative{effective_object_story_id}", "limit": "500"}):
    i, ic = ins.get(a["id"]), insc.get(a["id"])
    if not i:
        continue
    pos[a["id"]] = dict(a=a, aud=aud(a["adset"]["name"]), cre=cre(a["name"]), sp=float(i.get("spend") or 0), mr=reg_of(i),
                        sp_c=float((ic or {}).get("spend") or 0), mr_c=reg_of(ic), real=0, real_c=0, sales=[],
                        banned=compliance.is_banned(a["name"], s.compliance.banned_creatives) or "🚫" in a["name"],
                        post=(a.get("creative") or {}).get("effective_object_story_id") or "—")
    lix[(_mkey(a["campaign"]["name"]), _mkey(a["adset"]["name"]), loose(a["name"]))] = a["id"]

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
            if d >= C0:
                pos[aid]["real_c"] += 1
new_paid = Counter()
for p in paid:
    d = cpa.parse_date(p.get("Date", ""))
    if not d or d < U0:
        continue
    if d >= C0:
        new_paid["rows"] += 1
    if not who(p):
        if d >= C0:
            new_paid["no_contact"] += 1
        continue
    h = sorted({(dd, i): r for k in who(p) for dd, i, r in regs_by.get(k, []) if U0 <= dd <= d and (r.get("UTM Campaign") or "").strip()}.items())
    aid = find(h[-1][1]) if h else None
    if aid:
        pos[aid]["sales"].append(d)
        if d >= C0:
            new_paid["my_attr"] += 1
            new_paid[f"  → {pos[aid]['a']['campaign']['name']} › {pos[aid]['a']['adset']['name']} · {pos[aid]['a']['name']} · ad {aid}"] += 1
    elif d >= C0:
        new_paid["not_my_ad"] += 1


def line(tag, c):
    ns = len(c["sales"])
    cpl = c["sp"] / c["real"] if c["real"] else 0
    cplc = c["sp_c"] / c["real_c"] if c["real_c"] else 0
    return (f"{tag:<28} RM{c['sp']:>6,.0f} 真{c['real']:>3} CPL{cpl:>4.0f} 单{ns:>2} "
            f"{('CPA%5.0f' % (c['sp'] / ns)) if ns else 'CPA    —'} 转{(ns / c['real'] * 100 if c['real'] else 0):>4.1f}% | "
            f"本期 RM{c['sp_c']:>5,.0f} Meta{c['mr_c']:>3.0f} 真{c['real_c']:>3} CPL{cplc:>4.0f}")


def agg(key):
    out = defaultdict(lambda: dict(sp=0.0, mr=0.0, sp_c=0.0, mr_c=0.0, real=0, real_c=0, sales=[]))
    for p in pos.values():
        o = out[key(p)]
        for f in ("sp", "mr", "sp_c", "mr_c", "real", "real_c"):
            o[f] += p[f]
        o["sales"] += p["sales"]
    return out


order = lambda kv: (-len(kv[1]["sales"]), -(kv[1]["sp"]))
print(f"现在 {NOW:%m-%d %H:%M} MYT · MY 5.0 · ①10/29 起 ②本期 11/19 起 · 真 = 报名表去机器人 · 单 = 买前最后一次广告报名的位置（严格 campaign › ad set › ad）")
tot = agg(lambda p: "ALL")["ALL"]
print(line("MY 合计", tot))
print("\n== 受众 ==")
for k, c in sorted(agg(lambda p: p["aud"]).items(), key=order):
    if c["sp"] >= 30:
        print("  " + line(k, c))
print("\n== 素材 ==（拒审记录来自 CLAUDE.md）")
for k, c in sorted(agg(lambda p: p["cre"]).items(), key=order):
    if c["sp"] >= 30:
        print("  " + line(k, c) + (f"  ⚠ {REJ[k]}" if k in REJ else ""))
print("\n== 受众 × 素材 ==（花费 ≥ RM40）")
for k, c in sorted(agg(lambda p: (p["aud"], p["cre"])).items(), key=order):
    if c["sp"] >= 40:
        print("  " + line(f"{k[0]} × {k[1]}", c) + (f"  ⚠ {REJ[k[1]]}" if k[1] in REJ else ""))
print("\n== 位置（有单或 10/29 起花费 ≥ RM150）==")
for aid, p in sorted(pos.items(), key=lambda kv: (-len(kv[1]["sales"]), -kv[1]["sp"])):
    if not p["sales"] and p["sp"] < 150:
        continue
    a = p["a"]
    on = "在跑" if (a["status"], a["adset"]["status"], a["campaign"]["status"]) == ("ACTIVE",) * 3 else \
        f"关（campaign {a['campaign']['status']} / ad set {a['adset']['status']} / ad {a['status']}）"
    print(f"  {a['campaign']['name']} › {a['adset']['name']} · {a['name']} · ad {aid} · {on}{' · ⛔禁跑' if p['banned'] else ''}\n"
          f"      {line('', dict(p))}" + (" · 成交日 " + ", ".join(f"{d:%m/%d}" for d in sorted(p["sales"])) if p["sales"] else "")
          + f" · post {p['post']}")
print(f"\n== Paid 表 11/19 起新行 ==\n  共 {new_paid['rows']} 行 · 没电邮电话 {new_paid['no_contact']} · 认到 MY 广告位置 {new_paid['my_attr']} · "
      f"认不到（不是 MY 5.0 广告 / 没有带 UTM 的报名）{new_paid['not_my_ad']}")
for k, n in new_paid.items():
    if k.startswith("  →"):
        print(f"{k} ×{n}")
print("\nNEXT CYCLE MY DONE (read-only)")
