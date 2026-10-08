# -*- coding: utf-8 -*-
"""READ-ONLY: owner 2026-10-08 要在**新的 MY 账户** act_2285351942292267 重新开投：
「你去分析，抓回数据，告诉我要建什么 campaign-adset-ad，为什么」。

1. 新账户：token 读不读得到、status、币种、时区、所属 BM、有没有 pixel / campaign；
   并对照旧 MY（已封）和 SG 的 BM —— 同一个 BM 是封号风险的关键。
2. 旧 MY 账户（act_759339046918885，已封但数据还能读）的历史：按素材（creative_key）
   汇总 lifetime + 60d 花费 / 报名 / CPL / sheet 成交 / CPA / 最近成交，标禁跑，
   并给每支素材一个可复用的 page post id（effective_object_story_id）。
3. 旧 MY 按受众（campaign 名）汇总成交 —— 选 ad set 用。
只印日期 / UTM / RM，无 PII。"""
from __future__ import annotations

import collections
import datetime as dt
import time

from adbot import compliance, cpa
from adbot.clients.sheets import SheetsClient
from adbot.commands import graph_client
from adbot.monitor_cpl import _mkey, extract_results, result_action_type
from adbot.settings import REPO_ROOT, load_settings

NEW_ACCT = "act_2285351942292267"
OLD_MY = "act_759339046918885"
SG = "act_893025326577600"


def main() -> None:
    s = load_settings(REPO_ROOT / "config" / "config.yaml")
    g = graph_client(s)
    token = result_action_type(s.meta.conversion_event)
    today = (dt.datetime.utcnow() + dt.timedelta(hours=8)).date()
    d60 = today - dt.timedelta(days=60)
    banned = s.compliance.banned_creatives

    # ── 1. 三个账户的身份 ────────────────────────────────────────────────────
    print("═══ 1. 账户身份（新 MY / 旧 MY / SG）═══")
    for label, acct in (("新 MY", NEW_ACCT), ("旧 MY(已封)", OLD_MY), ("SG", SG)):
        try:
            info = g._request("GET", acct, params={
                "fields": "name,account_status,disable_reason,currency,timezone_name,"
                          "business{id,name},created_time,amount_spent,spend_cap"})
            print(f"  [{label}] «{info.get('name')}» status={info.get('account_status')}"
                  f" reason={info.get('disable_reason')} {info.get('currency')} tz={info.get('timezone_name')}"
                  f" BM={((info.get('business') or {}).get('name'))}({((info.get('business') or {}).get('id'))})"
                  f" 建 {(info.get('created_time') or '')[:10]} 累计花费 {float(info.get('amount_spent') or 0)/100:,.0f}")
        except Exception as exc:                                   # noqa: BLE001
            print(f"  [{label}] ❌ 读不到：{str(exc)[:160]}")
        time.sleep(0.8)
    print()

    print("═══ 新 MY 账户里有什么 ═══")
    for edge, fields in (("campaigns", "id,name,status,objective,created_time"),
                         ("adspixels", "id,name,last_fired_time"),
                         ("customaudiences", "id,name,approximate_count_lower_bound")):
        try:
            rows = g._get_all(f"{NEW_ACCT}/{edge}", {"fields": fields, "limit": "100"})
            print(f"  {edge}: {len(rows)}")
            for r in rows[:15]:
                print(f"      · {r}")
        except Exception as exc:                                   # noqa: BLE001
            print(f"  {edge}: ❌ {str(exc)[:140]}")
        time.sleep(0.8)
    print()

    # ── 2. 旧 MY 的素材战绩 ───────────────────────────────────────────────────
    values = SheetsClient(s.secrets.google_sa_json).read_tab(s.cpa.spreadsheet_id, s.cpa.sales_tab)
    sales, _c, _h = cpa.parse_sales(values, s.cpa.price_myr)
    my_sales = [x for x in sales if "[sg]" not in (x.campaign or "").casefold()]
    strict_all, strict60 = {}, {}
    pool_all, pool60, last_sale = {}, {}, {}
    by_camp_sales = collections.Counter()
    for x in my_sales:
        k = (_mkey(x.campaign), cpa.norm(x.ad))
        ck = cpa.creative_key(x.ad)
        strict_all[k] = strict_all.get(k, 0) + 1
        pool_all[ck] = pool_all.get(ck, 0) + 1
        by_camp_sales[_mkey(x.campaign)] += 1
        if x.date and x.date >= d60:
            strict60[k] = strict60.get(k, 0) + 1
            pool60[ck] = pool60.get(ck, 0) + 1
        if x.date and (ck not in last_sale or x.date > last_sale[ck]):
            last_sale[ck] = x.date
    print(f"sheet 里 MY 成交共 {len(my_sales)} 单（非 [sg] 的 campaign）\n")

    try:
        ads = g._get_all(OLD_MY + "/ads", {
            "fields": "id,name,status,effective_status,created_time,"
                      "campaign{id,name},adset{name},creative{id,effective_object_story_id,object_type,video_id}",
            "limit": "500"})
        time.sleep(1.2)
        life = {r.get("ad_id"): r for r in g.account_insights(
            OLD_MY, level="ad", fields="ad_id,spend,actions", date_preset="maximum")}
        time.sleep(1.2)
        i60 = {r.get("ad_id"): r for r in g.account_insights(
            OLD_MY, level="ad", fields="ad_id,spend,actions",
            time_range={"since": d60.isoformat(), "until": today.isoformat()})}
    except Exception as exc:                                       # noqa: BLE001
        print(f"❌ 旧 MY 读不到：{str(exc)[:160]}")
        return

    agg = {}
    camp_agg = {}
    for a in ads:
        nm = a.get("name") or ""
        ck = cpa.creative_key(nm)
        camp = (a.get("campaign") or {}).get("name") or ""
        r = life.get(a["id"]) or {}
        sp = float(r.get("spend") or 0); rg = extract_results(r.get("actions"), token)
        r6 = i60.get(a["id"]) or {}
        sp6 = float(r6.get("spend") or 0); rg6 = extract_results(r6.get("actions"), token)
        n = strict_all.get((_mkey(camp), cpa.norm(nm)), 0)
        n6 = strict60.get((_mkey(camp), cpa.norm(nm)), 0)
        e = agg.setdefault(ck, {"sp": 0.0, "rg": 0.0, "n": 0, "sp6": 0.0, "rg6": 0.0, "n6": 0,
                                "pos": 0, "names": set(), "post": None, "post_sales": -1,
                                "ban": compliance.banned_reason(nm, banned)})
        e["sp"] += sp; e["rg"] += rg; e["n"] += n; e["sp6"] += sp6; e["rg6"] += rg6; e["n6"] += n6
        e["pos"] += 1 if sp > 0 else 0
        e["names"].add(nm)
        post = (a.get("creative") or {}).get("effective_object_story_id")
        if post and (n > e["post_sales"] or (n == e["post_sales"] and sp > 0)):
            e["post"], e["post_sales"] = post, n
        c = camp_agg.setdefault(_mkey(camp), {"name": camp, "sp": 0.0, "rg": 0.0, "sp6": 0.0, "rg6": 0.0})
        c["sp"] += sp; c["rg"] += rg; c["sp6"] += sp6; c["rg6"] += rg6

    print("═══ 2. 旧 MY 素材战绩（lifetime，按成交排；⛔ = 禁跑，永远不建）═══")
    print(f"{'素材':<34} {'位':>2} {'花费':>8} {'报名':>5} {'CPL':>5} {'成交':>4} {'CPA':>6} | {'60d花费':>8} {'60d单':>5} {'CPA60':>6} | 最近成交   post")
    for ck, e in sorted(agg.items(), key=lambda kv: (-kv[1]["n"], kv[1]["sp"] / max(kv[1]["n"], 1))):
        if e["sp"] < 100 and e["n"] == 0:
            continue
        cpl = f"{e['sp']/e['rg']:.0f}" if e["rg"] else "—"
        c = f"{e['sp']/e['n']:.0f}" if e["n"] else "—"
        c6 = f"{e['sp6']/e['n6']:.0f}" if e["n6"] else "—"
        tag = "⛔" if e["ban"] else "  "
        print(f"{tag}{ck[:32]:<32} {e['pos']:>2} RM{e['sp']:>6.0f} {e['rg']:>5.0f} {cpl:>5} {e['n']:>4} {c:>6}"
              f" | RM{e['sp6']:>6.0f} {e['n6']:>5} {c6:>6} | {str(last_sale.get(ck) or '—'):<10} {e['post'] or '—'}")
    print()

    print("═══ 3. 旧 MY 按受众（campaign）— lifetime 花费 / 报名 / 成交 / CPA ═══")
    rows = []
    for key, c in camp_agg.items():
        n = by_camp_sales.get(key, 0)
        rows.append((n, c["sp"], c["rg"], c["name"], c["sp6"], c["rg6"]))
    for n, sp, rg, name, sp6, rg6 in sorted(rows, key=lambda r: (-r[0], r[1]))[:25]:
        if sp < 200:
            continue
        print(f"  {name[:48]:<50} RM{sp:>7.0f} 报名 {rg:>4.0f} CPL {sp/rg if rg else 0:>4.0f}"
              f" 成交 {n:>2} CPA {sp/n if n else 0:>5.0f} | 60d RM{sp6:>6.0f} 报名 {rg6:>3.0f}")
    print("\nNEW MY ACCOUNT REPORT DONE (read-only)")


if __name__ == "__main__":
    main()
