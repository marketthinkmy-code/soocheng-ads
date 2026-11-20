# -*- coding: utf-8 -*-
"""READ-ONLY (owner 2026-11-20 proposes SG + all test campaigns at floor RM60 / line RM60, was RM80 / RM80;
「我没办法接受 SOOCHENG CPL 整体超过 RM60…很快就可以测试出，哪些广告一出市场就不达标」— asks for my view).
Replays REAL hourly delivery (Meta hourly insights, per ad, per Thursday window) under both rule sets for every ad whose rule
would change: all SG ads + MY test campaigns (NEW VIDEO / 1-1-3 | 1120 / 1-3-3 | 1120). MY regular ads are 60/60 under both → not replayed.
Rule: 0 报名 and window spend ≥ floor → close; ≥1 报名 and spend ≥ floor and spend/报名 > line → close (checked at each hour end).
Register S1 bots are taken off the day they happened (spread over that day's registration hours). Not modelled: CPA rescue, veteran
RM150 floor, money moving to other ads after a close. Output: the slice of spend + 报名 that RM60 would have cut (closed earlier than RM80
would) — its CPL tells whether RM60 lowers the CPL; plus each account's de-botted CPL per window. No personal data printed."""
import datetime as dt
import json
from collections import defaultdict

from adbot import cpa
from adbot.clients.sheets import SheetsClient
from adbot.commands import graph_client
from adbot.monitor_cpl import _mkey, extract_results
from adbot.settings import REPO_ROOT, load_settings

NOW = dt.datetime.utcnow() + dt.timedelta(hours=8)
WINDOWS = [(dt.date(2026, 11, 5), dt.date(2026, 11, 11)), (dt.date(2026, 11, 12), dt.date(2026, 11, 18)),
           (dt.date(2026, 11, 19), NOW.date())]
ACCTS = (("MY", "config.my5.yaml", "1048291251556714"), ("SG", "config.sg.yaml", "1614065190214320"))
TESTS = ("NEW VIDEO", "1-1-3 | 1120", "1-3-3 | 1120")
RULES = {"现行 80/80": (80.0, 80.0), "提议 60/60": (60.0, 60.0)}

s0 = load_settings(REPO_ROOT / "config" / "config.sg.yaml")
sc = SheetsClient(s0.secrets.google_sa_json)
reg = sc.read_tab(s0.cpa.spreadsheet_id, s0.cpa.register_tab)
bots = cpa.bot_registrations(reg, since=WINDOWS[0][0], camp_key=_mkey, adset_key=_mkey)
print(f"现在 {NOW:%m-%d %H:%M} MYT · 只读 · 报名表机器人（11/05 起）{sum(len(v) for v in bots.values())} 笔")


def kill_index(path, floor, line):
    """index of the hour after which the rule closes the ad (None = never inside the observed path)."""
    for i, (sp, rg) in enumerate(path):
        if (rg <= 0.0001 and sp >= floor) or (rg > 0.0001 and sp >= floor and sp / rg > line):
            return i
    return None


cut_tot = defaultdict(lambda: [0.0, 0.0])
seen_tot = [0.0, 0.0]
examples = []
for lab, cfg, cc in ACCTS:
    s = load_settings(REPO_ROOT / "config" / cfg)
    g = graph_client(s)
    acct = s.meta.account_path
    tok = f"offsite_conversion.custom.{cc}"
    for w0, w1 in WINDOWS:
        rows = g._get_all(acct + "/insights", {
            "fields": "ad_id,ad_name,adset_name,campaign_name,spend,actions", "level": "ad", "time_increment": "1",
            "breakdowns": "hourly_stats_aggregated_by_advertiser_time_zone", "limit": "500",
            "time_range": json.dumps({"since": w0.isoformat(), "until": w1.isoformat()})})
        acc = g._get_all(acct + "/insights", {"fields": "spend,actions", "level": "account",
                                              "time_range": json.dumps({"since": w0.isoformat(), "until": w1.isoformat()})})
        a_sp = sum(float(r.get("spend") or 0) for r in acc)
        a_rg = sum(extract_results(r.get("actions"), tok) for r in acc)
        hours = defaultdict(list)
        meta = {}
        for r in rows:
            hours[r["ad_id"]].append((r["date_start"], r["hourly_stats_aggregated_by_advertiser_time_zone"][:2],
                                      float(r.get("spend") or 0), extract_results(r.get("actions"), tok)))
            meta[r["ad_id"]] = (r["campaign_name"], r["adset_name"], r["ad_name"])
        a_bots = 0
        for aid, (cn, an, nm) in meta.items():
            k = (_mkey(cn), _mkey(an), cpa.norm(nm))
            a_bots += sum(1 for d in bots.get(k, []) if w0 <= d <= w1)
        print(f"\n### {lab} {w0:%m/%d}–{w1:%m/%d} · 账户 RM{a_sp:,.0f} / {a_rg:.0f} 报名 − 机器人 {a_bots} = {a_rg - a_bots:.0f} 真报名"
              + (f" · 真 CPL {a_sp / (a_rg - a_bots):.0f}" if a_rg - a_bots > 0 else ""))
        for aid, hs in hours.items():
            cn, an, nm = meta[aid]
            if lab == "MY" and not any(t in cn for t in TESTS):
                continue                                    # MY regular ads: 60/60 under both rule sets
            k = (_mkey(cn), _mkey(an), cpa.norm(nm))
            bot_days = defaultdict(int)
            for d in bots.get(k, []):
                if w0 <= d <= w1:
                    bot_days[d.isoformat()] += 1
            hs.sort()
            day_regs = defaultdict(float)
            for d, h, sp, rg in hs:
                day_regs[d] += rg
            path, csp, crg = [], 0.0, 0.0
            for d, h, sp, rg in hs:
                b = bot_days.get(d, 0)
                if b and day_regs[d] > 0:
                    rg = max(0.0, rg - b * rg / day_regs[d])
                csp += sp
                crg += rg
                path.append((csp, crg))
            if not path or csp <= 0:
                continue
            seen_tot[0] += csp
            seen_tot[1] += crg
            i80 = kill_index(path, *RULES["现行 80/80"])
            i60 = kill_index(path, *RULES["提议 60/60"])
            end = len(path) - 1 if i80 is None else i80
            if i60 is None or i60 >= end:
                continue
            sp_cut = path[end][0] - path[i60][0]
            rg_cut = path[end][1] - path[i60][1]
            cut_tot[lab][0] += sp_cut
            cut_tot[lab][1] += rg_cut
            examples.append((lab, f"{w0:%m/%d}", cn.replace("(Webinarkit) ", ""), an, nm, aid, path[i60], sp_cut, rg_cut, path[-1]))
print("\n================ RM60 会提早关掉的那一段（RM60 关的那一刻 → RM80 才会关 / 实际停下）")
for lab in ("MY", "SG"):
    sp, rg = cut_tot[lab]
    print(f"{lab}{'（只算测试 campaign）' if lab == 'MY' else ''}: 少花 RM{sp:,.0f} · 少 {rg:.1f} 个真报名" + (f" · 这一段 CPL {sp / rg:.0f}" if rg else " · 这一段 0 报名"))
sp = sum(v[0] for v in cut_tot.values()); rg = sum(v[1] for v in cut_tot.values())
print(f"合计: 少花 RM{sp:,.0f} · 少 {rg:.1f} 个真报名" + (f" · 这一段 CPL {sp / rg:.0f}" if rg else ""))
print(f"（回放范围合计 RM{seen_tot[0]:,.0f} / {seen_tot[1]:.1f} 真报名 · CPL {seen_tot[0] / seen_tot[1]:.0f} → 拿掉这一段后 "
      + (f"RM{seen_tot[0] - sp:,.0f} / {seen_tot[1] - rg:.1f} · CPL {(seen_tot[0] - sp) / (seen_tot[1] - rg):.0f}）" if seen_tot[1] - rg > 0 else "—）"))
print("\n逐支（RM60 关的那一刻 累计 花费/报名 → 被砍掉那一段 花费/报名 · 整个窗口实际）:")
for lab, w, cn, an, nm, aid, at60, spc, rgc, last in sorted(examples, key=lambda x: -x[8]):
    print(f"  {lab} {w} {cn} › {an} · {nm} · ad {aid}")
    print(f"       RM60 关在 RM{at60[0]:.0f}/{at60[1]:.1f} → 砍掉 RM{spc:.0f}/{rgc:.1f}" + (f"（CPL {spc / rgc:.0f}）" if rgc > 0.05 else "（0 报名）")
          + f" · 窗口实际 RM{last[0]:.0f}/{last[1]:.1f}")
print("\nLINE BACKTEST DONE (read-only)")
