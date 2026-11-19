# -*- coding: utf-8 -*-
"""READ-ONLY (owner 11/19「分析上一轮广告（12-18 Nov），新广告是不是不给力，昨天成交很差，才一位，而且还是以前的广告报名的，
而不是 webinarkit campaign 带进来的」). No PII printed (no names / emails / phones).
 0) spreadsheet tabs (title · rows) — to find an attendance list if there is one.
 A) Paid rows dated 11/18 → today: Channel · Source · Paid UTM, and the buyer's registration history (date · Source · UTM position,
    Webinarkit or not). Answers: where did yesterday's buyer(s) come from?
 B) per live 10/21 → 11/18: registrations for that live (Register Source = webinar_<live>, S1 bots removed) split by origin
    (Webinarkit ad UTM / old-campaign UTM / blank), and sales dated live → live+6 split by the buyer's LAST registration origin.
 C) cycle 11/12–11/18 per Webinarkit position (NEW VIDEO vs older): Meta spend / regs, real registrations (S1 removed, Thu–Sun vs
    Mon–Wed), and every sale since 10/29 credited to the position (buyer's last registration, strict campaign › ad set › ad)."""
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
C0, C1 = dt.date(2026, 11, 12), dt.date(2026, 11, 18)
LIVES = [dt.date(2026, 10, 21), dt.date(2026, 10, 28), dt.date(2026, 11, 4), dt.date(2026, 11, 11), dt.date(2026, 11, 18)]
SRC = {dt.date(2026, 10, 21): "oct21", dt.date(2026, 10, 28): "oct28", dt.date(2026, 11, 4): "nov4",
       dt.date(2026, 11, 11): "nov11", dt.date(2026, 11, 18): "nov18"}
tr = lambda a, b: json.dumps({"since": a.isoformat(), "until": b.isoformat()})
s0 = load_settings(REPO_ROOT / "config" / "config.sg.yaml")
sc = SheetsClient(s0.secrets.google_sa_json)
SID = s0.cpa.spreadsheet_id

print(f"现在 {dt.datetime.utcnow() + dt.timedelta(hours=8):%m-%d %H:%M} MYT")
print("== 0) 表格分页")
meta = sc._svc.spreadsheets().get(spreadsheetId=SID, fields="sheets(properties(title,gridProperties(rowCount)))").execute()
print("   " + " · ".join(f"{s['properties']['title']}({s['properties']['gridProperties']['rowCount']})" for s in meta["sheets"]))


def table(tab, must):
    v = sc.read_tab(SID, tab)
    hi = next(i for i, r in enumerate(v[:10]) if must in r)
    return v[hi], [dict(zip(v[hi], r)) for r in v[hi + 1:]]


rh, reg = table("Register", "Email")
ph, paid = table(s0.cpa.sales_tab, "UTM Campaign")
print("   Register 栏位(非个资): " + str([h for h in rh if h and not re.search("name|email|phone|mail|电话|名字", h, re.I)]))


def s1(r):
    nm = (r.get("Name") or "").strip()
    fw = nm.split()[0] if nm.split() else ""
    return bool(fw) and (r.get("Experience") or "").strip() == fw * 2


ad_col = next((h for h in rh if cpa._hkey(h) in ("utmadsname", "utmadname")), "UTM Ads Name")
who = lambda r: cpa.contact_keys(r.get("Email", ""), r.get("Phone Number", ""))
wk = lambda c: "webinarkit" in (c or "").lower()
origin = lambda c: "Webinarkit 广告" if wk(c) else ("旧 campaign UTM" if (c or "").strip() else "空白")
regs_by = defaultdict(list)
for i, r in enumerate(reg):
    d = cpa.parse_date(r.get("Created date", ""))
    if not d:
        continue
    for k in who(r):
        regs_by[k].append((d, i, r))
hist = lambda keys: sorted({(d, i): r for k in keys for d, i, r in regs_by.get(k, [])}.items())

# ---------- A
print("\n== A) 11/18 起的 Paid 行（买家从哪里报名的）")
for p in paid:
    d = cpa.parse_date(p.get("Date", ""))
    if not d or d < dt.date(2026, 11, 18):
        continue
    ks = who(p)
    print(f"● {d} · Channel {p.get('Channel') or '—'} · Source {p.get('Source') or '—'} · Paid UTM {p.get('UTM Campaign') or '—'} › {p.get('UTM Ads Set') or '—'}"
          + ("" if ks else " · （没有电邮/电话，无法对报名表）"))
    h = [(dd, r) for (dd, _), r in hist(ks) if dd <= d]
    for dd, r in h[-6:]:
        print(f"     报名 {dd} · Source {r.get('Source') or '—'} · {origin(r.get('UTM Campaign'))}: {r.get('UTM Campaign') or '—'} › {r.get('UTM Ads Set') or '—'} · {r.get(ad_col) or '—'}"
              + (" ⚠️S1" if s1(r) else ""))
    if ks and not h:
        print("     报名表里找不到这个人")

# ---------- B
print("\n== B) 每场：该场报名（去机器人）按来源 · 成交按买家最后一次报名的来源")
for live in LIVES:
    tag = SRC[live]
    rr = [r for r in reg if (r.get("Source") or "").lower().endswith("webinar_" + tag) and not s1(r)]
    oc = Counter(origin(r.get("UTM Campaign")) for r in rr)
    sales = [p for p in paid if (lambda d: d and live <= d <= live + dt.timedelta(days=6))(cpa.parse_date(p.get("Date", "")))]
    so = Counter()
    for p in sales:
        ks = who(p)
        if not ks:
            so["无电邮电话"] += 1
            continue
        d = cpa.parse_date(p.get("Date", ""))
        h = [r for (dd, _), r in hist(ks) if dd <= d]
        so[origin(h[-1].get("UTM Campaign")) if h else "报名表找不到"] += 1
    print(f"   {live:%m/%d} webinar_{tag}: 报名 {len(rr)}（" + " · ".join(f"{k} {v}" for k, v in oc.most_common()) + f"）"
          f" → 成交(直播日起 7 天) {len(sales)}（" + " · ".join(f"{k} {v}" for k, v in so.most_common()) + "）")

# ---------- C
print("\n== C) 周期 11/12–11/18：每个 Webinarkit 位置")
pos = {}
for label, cfg, code in (("MY", "config.my5.yaml", "1048291251556714"), ("SG", "config.sg.yaml", "1614065190214320")):
    s = load_settings(REPO_ROOT / "config" / cfg)
    g = graph_client(s)
    tok = f"offsite_conversion.custom.{code}"
    for row in g._get_all(s.meta.account_path + "/insights", {"level": "ad", "time_range": tr(C0, C1),
                          "fields": "ad_id,ad_name,adset_name,campaign_name,spend,actions", "limit": "500"}):
        if not wk(row.get("campaign_name")):
            continue
        k = (_mkey(row["campaign_name"]), _mkey(row["adset_name"]), cpa.norm(row["ad_name"]))
        pos[k] = dict(label=label, c=row["campaign_name"], s=row["adset_name"], a=row["ad_name"], id=row["ad_id"],
                      sp=float(row.get("spend") or 0), mr=extract_results(row.get("actions"), tok),
                      real=0, early=0, late=0, bots=0, sales=set())
for r in reg:
    d = cpa.parse_date(r.get("Created date", ""))
    if not d or not (C0 <= d <= C1) or not wk(r.get("UTM Campaign")):
        continue
    k = (_mkey(cpa.norm(r.get("UTM Campaign"))), _mkey(cpa.norm(r.get("UTM Ads Set"))), cpa.norm(r.get(ad_col)))
    if k not in pos:
        continue
    if s1(r):
        pos[k]["bots"] += 1
        continue
    pos[k]["real"] += 1
    pos[k]["early" if d.weekday() in (3, 4, 5, 6) else "late"] += 1
for rid, p in enumerate(paid):
    d = cpa.parse_date(p.get("Date", ""))
    if not d or d < dt.date(2026, 10, 29):
        continue
    h = [r for (dd, _), r in hist(who(p)) if dt.date(2026, 10, 29) <= dd <= d and (r.get("UTM Campaign") or "").strip()]
    if h:
        r = h[-1]
        k = (_mkey(cpa.norm(r.get("UTM Campaign"))), _mkey(cpa.norm(r.get("UTM Ads Set"))), cpa.norm(r.get(ad_col)))
        if k in pos:
            pos[k]["sales"].add((d, p.get("Source") or "—"))
grp = defaultdict(lambda: Counter())
for v in sorted(pos.values(), key=lambda v: -v["sp"]):
    g = "NEW VIDEO" if "new video" in v["c"].lower() else "旧素材"
    for f in ("sp", "mr", "real", "early", "late", "bots"):
        grp[(v["label"], g)][f] += v[f]
    grp[(v["label"], g)]["sales"] += len(v["sales"])
    cpl = f"{v['sp'] / v['real']:.0f}" if v["real"] else "—"
    print(f"   {v['label']} {v['c'].replace('(Webinarkit) ', '')} › {v['s']} · {v['a']} · ad {v['id']}\n"
          f"        RM{v['sp']:,.0f} · Meta 报名 {v['mr']:.0f} · 真报名 {v['real']}（周四–日 {v['early']} / 周一–三 {v['late']}）· 机器人 {v['bots']} · 真 CPL {cpl}"
          f" · 10/29 起成交 {len(v['sales'])}" + (" " + str(sorted(v["sales"])) if v["sales"] else ""))
print("\n   -- 汇总")
for (label, g), c in sorted(grp.items()):
    print(f"   {label} {g}: RM{c['sp']:,.0f} · Meta 报名 {c['mr']:.0f} · 真报名 {c['real']}（周四–日 {c['early']} / 周一–三 {c['late']}）· 机器人 {c['bots']}"
          f" · 真 CPL {c['sp'] / c['real']:.0f}" + f" · 10/29 起成交 {c['sales']}" if c["real"] else f"   {label} {g}: RM{c['sp']:,.0f}")
print("\nCYCLE DEEP DONE (read-only)")
