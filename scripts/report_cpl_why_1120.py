# -*- coding: utf-8 -*-
"""READ-ONLY (owner 2026-11-20「查一下这一期 CPL 为什么到 121」).
Same elapsed window in each cycle — Thursday 00:00 → Friday HH:00 MYT (HH = now) — for the cycles starting 10/29, 11/05, 11/12, 11/19.
① Funnel per account per cycle (Meta account insights, hourly): spend · CPM · link CTR · cost per link click · LPV · cost per LPV · LPV→报名 ·
   Meta 报名 · Register bots · real 报名 · real CPL.  ② Tracking check: Meta 报名 per day vs Register rows per day (ad-UTM / other / blank).
③ This cycle per ad: spend · LPV · 报名 · CPL, grouped by how it got live this cycle.  ④ Placements (both accounts, Thursday full day 11/12 vs 11/19).
⑤ Day split this cycle: 11/19 vs 11/20 so far. No personal data printed."""
import datetime as dt
import json
from collections import Counter, defaultdict

from adbot import cpa
from adbot.clients.sheets import SheetsClient
from adbot.commands import graph_client
from adbot.monitor_cpl import extract_results
from adbot.settings import REPO_ROOT, load_settings

NOW = dt.datetime.utcnow() + dt.timedelta(hours=8)
H = NOW.hour
STARTS = [dt.date(2026, 10, 29), dt.date(2026, 11, 5), dt.date(2026, 11, 12), dt.date(2026, 11, 19)]
ACCTS = (("MY", "config.my5.yaml", "1048291251556714"), ("SG", "config.sg.yaml", "1614065190214320"))
f = lambda r, k: float(r.get(k) or 0)
print(f"现在 {NOW:%m-%d %H:%M} MYT · 只读 · 每期都取「周四 00:00 → 周五 {H:02d}:00」")

s0 = load_settings(REPO_ROOT / "config" / "config.sg.yaml")
sc = SheetsClient(s0.secrets.google_sa_json)
reg = sc.read_tab(s0.cpa.spreadsheet_id, s0.cpa.register_tab)
keys, rows = cpa._named_table(reg, "utmcampaign")
cell = lambda row, i: row[i] if 0 <= i < len(row) else ""
rd, rc = cpa._col(keys, "createddate", "date"), cpa._col(keys, "utmcampaign")
rn, rx = (keys.index("name") if "name" in keys else -1), cpa._col(keys, "experience")
print(f"报名表栏位：日期栏 = {keys[rd] if rd >= 0 else '无'} · 例子 = {cell(rows[-1], rd) if rows else ''}")
reg_day = defaultdict(Counter)       # date -> Counter(kind)
for row in rows:
    d = cpa.parse_date(cell(row, rd))
    if not d or d < dt.date(2026, 10, 29):
        continue
    camp = cpa.norm(cell(row, rc))
    bot = rn >= 0 and rx >= 0 and cpa.is_bot_registration(cell(row, rn), cell(row, rx))
    if bot:
        kind = "机器人"
    elif camp.startswith("(webinarkit)") and "[sg]" in camp:
        kind = "SG 广告"
    elif camp.startswith("(webinarkit)"):
        kind = "MY 广告"
    elif camp:
        kind = "旧 UTM"
    else:
        kind = "无 UTM"
    reg_day[d][kind] += 1


def window(start):
    return [(start, 24), (start + dt.timedelta(days=1), H)]   # (day, hours to include)


def bots_in(start, lab):
    tot = 0
    for d, hrs in window(start):
        if hrs:
            tot += reg_day[d]["机器人"] if lab == "MY" else 0   # bots can't be split by account here (see note)
    return tot


fun = {}
for lab, cfg, cc in ACCTS:
    s = load_settings(REPO_ROOT / "config" / cfg)
    g = graph_client(s)
    acct = s.meta.account_path
    tok = f"offsite_conversion.custom.{cc}"
    print(f"\n################ {lab} ① 漏斗（同样经过时间）")
    print("   期          花费    CPM   CTR   每点击  LPV  每LPV  LPV→报名  报名")
    for st in STARTS:
        t = defaultdict(float)
        for d, hrs in window(st):
            if hrs <= 0:
                continue
            for r in g._get_all(acct + "/insights", {"fields": "spend,impressions,inline_link_clicks,actions", "level": "account",
                                                    "breakdowns": "hourly_stats_aggregated_by_advertiser_time_zone", "limit": "100",
                                                    "time_range": json.dumps({"since": d.isoformat(), "until": d.isoformat()})}):
                if int(r["hourly_stats_aggregated_by_advertiser_time_zone"][:2]) >= hrs:
                    continue
                t["sp"] += f(r, "spend"); t["im"] += f(r, "impressions"); t["cl"] += f(r, "inline_link_clicks")
                t["lpv"] += extract_results(r.get("actions"), "landing_page_view"); t["rg"] += extract_results(r.get("actions"), tok)
        fun[(lab, st)] = t
        sp, im, cl, lpv, rg = t["sp"], t["im"], t["cl"], t["lpv"], t["rg"]
        print(f"   {st:%m/%d} 起  RM{sp:6.0f}  {sp / im * 1000 if im else 0:4.0f}  {cl / im * 100 if im else 0:4.2f}%  RM{sp / cl if cl else 0:4.2f}"
              f"  {lpv:4.0f}  RM{sp / lpv if lpv else 0:5.2f}  {rg / lpv * 100 if lpv else 0:5.1f}%  {rg:4.0f}")
    print(f"   ⑤ 这一期按天：")
    for d in (dt.date(2026, 11, 19), dt.date(2026, 11, 20)):
        r = (g._get_all(acct + "/insights", {"fields": "spend,impressions,inline_link_clicks,actions", "level": "account",
                                            "time_range": json.dumps({"since": d.isoformat(), "until": d.isoformat()})}) or [{}])[0]
        sp, im, cl = f(r, "spend"), f(r, "impressions"), f(r, "inline_link_clicks")
        lpv, rg = extract_results(r.get("actions"), "landing_page_view"), extract_results(r.get("actions"), tok)
        print(f"     {d:%m/%d}  RM{sp:5.0f} · CPM {sp / im * 1000 if im else 0:4.0f} · CTR {cl / im * 100 if im else 0:4.2f}% · LPV {lpv:3.0f}"
              f" · 每LPV RM{sp / lpv if lpv else 0:5.2f} · LPV→报名 {rg / lpv * 100 if lpv else 0:4.1f}% · 报名 {rg:2.0f}")
    print(f"   ③ 这一期每支 ad（11/19 起）")
    rows_ad = g._get_all(acct + "/insights", {"fields": "ad_id,ad_name,adset_name,campaign_name,spend,actions,inline_link_clicks,impressions",
                                              "level": "ad", "limit": "500",
                                              "time_range": json.dumps({"since": "2026-11-19", "until": NOW.date().isoformat()})})
    for r in sorted(rows_ad, key=lambda x: -f(x, "spend")):
        sp = f(r, "spend")
        if sp < 5:
            continue
        lpv, rg = extract_results(r.get("actions"), "landing_page_view"), extract_results(r.get("actions"), tok)
        print(f"     RM{sp:5.0f} · LPV {lpv:3.0f} · 报名 {rg:2.0f}" + (f" · CPL {sp / rg:4.0f}" if rg else "        ")
              + f" · LPV→报名 {rg / lpv * 100 if lpv else 0:4.1f}% | {r['campaign_name'].replace('(Webinarkit) ', '')} › {r['adset_name']} · {r['ad_name']} · ad {r['ad_id']}")
    print(f"   ④ 版位（周四整天 11/12 vs 11/19）")
    for d in (dt.date(2026, 11, 12), dt.date(2026, 11, 19)):
        pl = g._get_all(acct + "/insights", {"fields": "spend,impressions,inline_link_clicks,actions", "level": "account",
                                             "breakdowns": "publisher_platform,platform_position", "limit": "200",
                                             "time_range": json.dumps({"since": d.isoformat(), "until": d.isoformat()})})
        tot = sum(f(x, "spend") for x in pl) or 1
        print(f"     {d:%m/%d}:")
        for r in sorted(pl, key=lambda x: -f(x, "spend"))[:6]:
            sp, im = f(r, "spend"), f(r, "impressions")
            lpv, rg = extract_results(r.get("actions"), "landing_page_view"), extract_results(r.get("actions"), tok)
            print(f"       {r['publisher_platform']}/{r['platform_position']:<24} {sp / tot * 100:3.0f}% · CPM {sp / im * 1000 if im else 0:4.0f}"
                  f" · LPV {lpv:3.0f} · 报名 {rg:2.0f}" + (f" · CPL {sp / rg:4.0f}" if rg else ""))

print("\n################ ② 追踪核对：报名表每天笔数（按来源）vs Meta 报名")
print("   日期    MY广告 SG广告 旧UTM 无UTM 机器人 | 合计")
for d in sorted(reg_day):
    if d < dt.date(2026, 11, 5):
        continue
    c = reg_day[d]
    print(f"   {d:%m/%d %a} {c['MY 广告']:5d} {c['SG 广告']:6d} {c['旧 UTM']:5d} {c['无 UTM']:5d} {c['机器人']:5d} | {sum(c.values()):4d}")
for lab, cfg, cc in ACCTS:
    s = load_settings(REPO_ROOT / "config" / cfg)
    g = graph_client(s)
    r = g._get_all(s.meta.account_path + "/insights", {"fields": "actions", "level": "account", "time_increment": "1",
                                                      "time_range": json.dumps({"since": "2026-11-05", "until": NOW.date().isoformat()})})
    print(f"   Meta {lab} 每天报名: " + " · ".join(f"{x['date_start'][5:]} {extract_results(x.get('actions'), f'offsite_conversion.custom.{cc}'):.0f}" for x in r))

print("\n################ 合计（两账户，同样经过时间；机器人用报名表全部机器人）")
for st in STARTS:
    sp = sum(fun[(lab, st)]["sp"] for lab, _, _ in ACCTS)
    rg = sum(fun[(lab, st)]["rg"] for lab, _, _ in ACCTS)
    b = sum(reg_day[d]["机器人"] for d, hrs in window(st) if hrs)
    print(f"   {st:%m/%d} 起: RM{sp:,.0f} / {rg:.0f} 报名 − 机器人 ≤{b} → CPL {sp / rg if rg else 0:.0f}（扣机器人后 ≥{sp / (rg - b) if rg - b > 0 else 0:.0f}）")
print("\nCPL WHY 1120 DONE (read-only)")
