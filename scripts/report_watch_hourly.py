# -*- coding: utf-8 -*-
"""READ-ONLY hourly watch (owner 2026-11-20「你再帮我盯紧一点」). One run = the whole picture, both accounts:
A. Account funnel: Thursday window (from the cycle start) + today: spend · LPV · 报名 · CPL · LPV→报名 (Audience Network excluded) · last 3 hours.
B. Every delivering ad, judged by the monitor's own evaluate_account (same rules, same bot removal, same sales join), with its floor / line
   and how close it is → which ads the monitor will close at its next run.
C. Ads rejected / with issues / in review.  D. Ad sets whose learning was reset in the last 2 hours (human edits).
E. Register today: ad-UTM rows vs Meta 报名, bot (S1) rows.  F. Daily budget of what is delivering + spend cap projection.
Ends with an ALERTS block — empty means nothing needs the owner's attention. No personal data printed."""
import datetime as dt
import json
from collections import Counter, defaultdict

from adbot import compliance, cpa
from adbot.clients.sheets import SheetsClient
from adbot.commands import graph_client
from adbot.monitor_cpl import evaluate_account, extract_results, spend_cap_status
from adbot.settings import REPO_ROOT, load_settings

NOW = dt.datetime.utcnow() + dt.timedelta(hours=8)
TODAY = NOW.date()
ACCTS = (("MY", "config.my5.yaml", "1048291251556714"), ("SG", "config.sg.yaml", "1614065190214320"))
LIVE = '["ACTIVE","IN_PROCESS","PENDING_REVIEW"]'
f = lambda r, k: float(r.get(k) or 0)
tr = lambda a, b: json.dumps({"since": a.isoformat(), "until": b.isoformat()})
alerts = []

s_my = load_settings(REPO_ROOT / "config" / "config.my5.yaml")
START = cpa.parse_date(s_my.spend_cap.start) or TODAY
END = dt.datetime.strptime(s_my.spend_cap.end, "%Y-%m-%d %H:%M") if s_my.spend_cap.end else None
print(f"现在 {NOW:%m-%d %H:%M} MYT · 只读 · 周期 {START:%m/%d} 起")

# E. Register today
s0 = load_settings(REPO_ROOT / "config" / "config.sg.yaml")
reg = SheetsClient(s0.secrets.google_sa_json).read_tab(s0.cpa.spreadsheet_id, s0.cpa.register_tab)
keys, rows = cpa._named_table(reg, "utmcampaign")
cell = lambda row, i: row[i] if 0 <= i < len(row) else ""
rd, rc = cpa._col(keys, "createddate", "date"), cpa._col(keys, "utmcampaign")
rn, rx = (keys.index("name") if "name" in keys else -1), cpa._col(keys, "experience")
reg_today = Counter()
for row in rows:
    if cpa.parse_date(cell(row, rd)) != TODAY:
        continue
    camp = cpa.norm(cell(row, rc))
    if rn >= 0 and rx >= 0 and cpa.is_bot_registration(cell(row, rn), cell(row, rx)):
        reg_today["bots"] += 1
    elif camp.startswith("(webinarkit)"):
        reg_today["SG" if "[sg]" in camp else "MY"] += 1
    else:
        reg_today["other"] += 1
if reg_today["bots"]:
    alerts.append(f"报名表今天出现 {reg_today['bots']} 笔机器人报名（S1）")

day_budget = {}
for lab, cfg, cc in ACCTS:
    s = load_settings(REPO_ROOT / "config" / cfg)
    g = graph_client(s)
    acct = s.meta.account_path
    tok = f"offsite_conversion.custom.{cc}"
    print(f"\n################ {lab}")
    # A. funnel
    def plat(a, b):
        t = defaultdict(lambda: [0.0, 0.0, 0.0])
        for r in g._get_all(acct + "/insights", {"fields": "spend,actions", "level": "account", "breakdowns": "publisher_platform",
                                                "limit": "50", "time_range": tr(a, b)}):
            p = r["publisher_platform"]
            t[p][0] += f(r, "spend"); t[p][1] += extract_results(r.get("actions"), "landing_page_view"); t[p][2] += extract_results(r.get("actions"), tok)
        return t
    rate = {}
    for name, a in (("周四起", START), ("今天", TODAY)):
        t = plat(a, TODAY)
        sp = sum(v[0] for v in t.values()); rg = sum(v[2] for v in t.values())
        lpv_x = sum(v[1] for k, v in t.items() if k != "audience_network"); rg_x = sum(v[2] for k, v in t.items() if k != "audience_network")
        an = t.get("audience_network", [0, 0, 0])
        rate[name] = (lpv_x, rg_x)
        print(f"A {name}: RM{sp:,.0f} / {rg:.0f} 报名" + (f" · CPL {sp / rg:.0f}" if rg else "") +
              f" · 无 AN 落地页→报名 {rg_x / lpv_x * 100 if lpv_x else 0:.1f}%（{lpv_x:.0f} LPV）· AN RM{an[0]:.0f}")
        if name == "今天" and an[0] >= 5:
            alerts.append(f"{lab} 今天 Audience Network 还在花钱 RM{an[0]:.0f}（你已拿掉 AN 的 ad set 不该再花）")
    (lw, rw), (lt, rt) = rate["周四起"], rate["今天"]
    if lt >= 20 and lw and rw and (rt / lt) < 0.5 * (rw / lw):
        alerts.append(f"{lab} 今天落地页→报名 {rt / lt * 100:.1f}%（{lt:.0f} LPV→{rt:.0f}），不到周四起 {rw / lw * 100:.1f}% 的一半")
    hrs = defaultdict(lambda: [0.0, 0.0])
    for r in g._get_all(acct + "/insights", {"fields": "spend,actions", "level": "account", "limit": "100", "time_range": tr(TODAY, TODAY),
                                             "breakdowns": "hourly_stats_aggregated_by_advertiser_time_zone"}):
        h = int(r["hourly_stats_aggregated_by_advertiser_time_zone"][:2])
        hrs[h][0] += f(r, "spend"); hrs[h][1] += extract_results(r.get("actions"), tok)
    last3 = [hrs[h] for h in range(max(0, NOW.hour - 3), NOW.hour)]
    sp3, rg3 = sum(x[0] for x in last3), sum(x[1] for x in last3)
    print(f"A 最近 3 个整点小时：RM{sp3:.0f} / {rg3:.0f} 报名")
    if sp3 >= 100 and rg3 == 0:
        alerts.append(f"{lab} 最近 3 小时花 RM{sp3:.0f}、0 报名（只是提醒，判断仍看周四起）")
    meta_today = sum(x[1] for x in hrs.values())
    if abs(meta_today - reg_today[lab]) >= 3:
        alerts.append(f"{lab} 今天 Meta 报名 {meta_today:.0f} vs 报名表广告报名 {reg_today[lab]}（差 ≥3，追踪可能有问题）")
    # B. every delivering ad, monitor's own verdict
    live = g._get_all(acct + "/ads", {"fields": "name,effective_status,adset{id,name,daily_budget},campaign{id,name,daily_budget}",
                                      "limit": "500", "effective_status": LIVE})
    live_ids = {a["id"] for a in live}
    carriers = {}
    for a in live:
        cb = int(a["campaign"].get("daily_budget") or 0) // 100
        carriers[("c", a["campaign"]["id"]) if cb else ("s", a["adset"]["id"])] = cb or int(a["adset"].get("daily_budget") or 0) // 100
        if not a["campaign"]["name"].lower().startswith("(webinarkit)"):
            alerts.append(f"{lab} 在投放但不是 (Webinarkit)：{a['campaign']['name']} › {a['adset']['name']} · {a['name']} · ad {a['id']}")
    day_budget[lab] = sum(carriers.values())
    kpi = s.kpi
    decs = [d for d in evaluate_account(g, s) if d.ad_id in live_ids]
    print(f"B 在投放 {len(live)} 支 · 日预算 RM{day_budget[lab]}（monitor 视角，周四起，已扣机器人）")
    for d in sorted(decs, key=lambda d: -d.spend):
        camp = d.where.split(" › ")[0]
        ov = next((o for o in kpi.campaign_overrides if o.match and o.match in camp), None)
        line = (ov.cpl_threshold_myr if ov and ov.cpl_threshold_myr else kpi.cpl_threshold_myr)
        floor = (ov.zero_lead_spend_myr if ov and ov.zero_lead_spend_myr else (kpi.zero_lead_spend_myr or kpi.cpl_min_spend_myr))
        if d.reason == "veteran_wait":
            floor = max(floor, kpi.veteran_min_spend_myr)
        res = d.results
        cpl = f"CPL {d.spend / res:.0f}" if res else "0 报名"
        near = ""
        if not d.should_pause and res == 0 and d.spend >= 0.75 * floor:
            near = f" ⚠️ 离 0 报名门槛 RM{floor:.0f} 还差 RM{floor - d.spend:.0f}"
        verdict = "下一轮会关" if d.should_pause else "留"
        print(f"   RM{d.spend:5.0f} / {res:.0f} · {cpl} · 线 {line:.0f} / 门槛 {floor:.0f} · {verdict}（{d.reason}）{near}"
              f" | {d.where.replace('(Webinarkit) ', '')} · {d.name} · ad {d.ad_id}")
        if d.should_pause:
            alerts.append(f"{lab} monitor 下一轮会关：{d.where.replace('(Webinarkit) ', '')} · {d.name} · ad {d.ad_id}"
                          f"（RM{d.spend:.0f} / {res:.0f}，{d.reason}）")
    # C. review
    bad = g._get_all(acct + "/ads", {"fields": "name,status,effective_status,adset{name},campaign{name}", "limit": "500",
                                     "effective_status": '["DISAPPROVED","WITH_ISSUES","PENDING_REVIEW"]'})
    print(f"C 被拒 / 有问题 / 审核中：{len(bad)}")
    for r in bad:
        print(f"   {r['effective_status']} · ad {r['status']} | {r['campaign']['name']} › {r['adset']['name']} · {r['name']} · ad {r['id']}")
        if r["effective_status"] in ("DISAPPROVED", "WITH_ISSUES"):
            alerts.append(f"{lab} {r['effective_status']}：{r['campaign']['name']} › {r['adset']['name']} · {r['name']} · ad {r['id']}"
                          + ("（禁跑素材）" if compliance.is_banned(r["name"], s.compliance.banned_creatives) else ""))
    # D. learning resets in the last 2 hours
    sets = g._get_all(acct + "/adsets", {"fields": "name,learning_stage_info,campaign{name}", "limit": "300", "effective_status": '["ACTIVE"]'})
    st = Counter((x.get("learning_stage_info") or {}).get("status", "—") for x in sets)
    print("D 学习期：" + " · ".join(f"{k} {v}" for k, v in st.items()))
    for x in sets:
        ts = (x.get("learning_stage_info") or {}).get("last_sig_edit_ts")
        if ts and NOW - (dt.datetime.utcfromtimestamp(int(ts)) + dt.timedelta(hours=8)) < dt.timedelta(hours=2):
            t = (dt.datetime.utcfromtimestamp(int(ts)) + dt.timedelta(hours=8)).strftime("%H:%M")
            alerts.append(f"{lab} {t} 有重大修改、学习期重置：{x['campaign']['name'].replace('(Webinarkit) ', '')} › {x['name']} · adset {x['id']}")

# F. budget + cap
print(f"\nE 报名表今天：MY 广告 {reg_today['MY']} · SG 广告 {reg_today['SG']} · 其它 {reg_today['other']} · 机器人 {reg_today['bots']}")
day = sum(day_budget.values())
stc = spend_cap_status(graph_client(s_my), s_my, NOW)
if stc:
    total, line = stc
    hrs_left = max(0.0, (END - NOW).total_seconds() / 3600) if END else 0
    hit = NOW + dt.timedelta(hours=(line - total) / day * 24) if day and total < line else None
    print(f"F 日预算 RM{day:,}（MY {day_budget['MY']} / SG {day_budget['SG']}）· 周期花费 RM{total:,.0f} / 关停线 RM{line:,.0f} · 到周三 15:00 约 RM{total + day * hrs_left / 24:,.0f}"
          + (f" · 约 {hit:%m-%d %a %H:%M} 碰线" if hit and END and hit < END else ""))
    if total >= line:
        alerts.append(f"周期花费 RM{total:,.0f} 已到关停线 RM{line:,.0f}")
    elif total >= 5000:
        alerts.append(f"周期花费 RM{total:,.0f} 已过 RM5,000")
print("\nALERTS:" + ("" if alerts else " 无"))
for a in alerts:
    print(" - " + a)
print("\nWATCH HOURLY DONE (read-only)")
