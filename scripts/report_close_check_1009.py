# -*- coding: utf-8 -*-
"""READ-ONLY: owner 2026-10-09「看下 SG MY 有什么广告我需要关的吗」.

For SG and MY 5.0, every ACTIVE registration ad gets ONE verdict, in rule order:
  ⛔禁跑·必删   banned master (yaml list / 🚫 mark)           — hard rule, delete not pause
  ❗被拒·必删   DISAPPROVED / WITH_ISSUES / issues_info       — rejected ads must leave the account
  ⚠️WhatsApp   registration ad whose CTA leaves the LP       — 10/8 lesson (Thelyin's edit)
  🛑hard-stop  60d strict CPA > RM1,200 with real sales      — the monitor pauses these itself
  🆕新(例外)    position ≤14 days old                         — owner 9/20: new ads exempt
  ✅达标        30d strict CPA ≤ RM960
  ⚠️WATCH      30d strict CPA 960–1,200
  ❌超1200      30d strict CPA > RM1,200                      — per the 9/20 standard; 9/23: owner's call, never auto
  ✅素材7d有单   30d no sale on this position, but the creative sold within 7 days
  ❌30d无单     30d no sale, creative silent ≥7 days          — per the 9/20 standard; owner's call
plus week-to-date (Thursday→today) CPL flags against the account line — what the monitor will do
once kpi.cpl_paused_until expires. Then: rejected ads still sitting in the account (any status),
and banned ads that are ACTIVE at ad level but held only by a paused parent (armed). No PII."""
from __future__ import annotations

import datetime as dt
import time

from adbot import compliance, cpa
from adbot.clients.sheets import SheetsClient
from adbot.commands import graph_client
from adbot.monitor_cpl import _mkey, extract_results, result_action_type
from adbot.settings import REPO_ROOT, load_settings

NEW_DAYS, FRESH_DAYS = 14, 7
PASS_MAX, HARD = 960.0, 1200.0
BAD_EFF = {"DISAPPROVED", "WITH_ISSUES"}
REVIEW_EFF = {"PENDING_REVIEW", "PREAPPROVED", "IN_PROCESS"}


def cta_of(cr: dict) -> str:
    spec = cr.get("object_story_spec") or {}
    for key in ("link_data", "video_data", "photo_data"):
        d = spec.get(key) or {}
        cta = d.get("call_to_action") or {}
        if cta:
            v = cta.get("value") or {}
            return f"{cta.get('type')} {v.get('link') or ''} {v.get('app_destination') or ''}".strip()
        if d.get("link"):
            return f"link {d.get('link')}"
    if cr.get("effective_object_story_id"):
        return f"{cr.get('call_to_action_type') or '?'} (post reuse)"
    return cr.get("call_to_action_type") or "?"


def fmt(v, nd=0):
    return "—" if v is None else f"{v:,.{nd}f}"


def main() -> None:
    s_my = load_settings(REPO_ROOT / "config" / "config.yaml")
    today = (dt.datetime.utcnow() + dt.timedelta(hours=8)).date()
    thu = today - dt.timedelta(days=(today.weekday() - 3) % 7)      # most recent Thursday
    d7, d30, d60 = (today - dt.timedelta(days=n) for n in (7, 30, 60))
    print(f"今天 {today} ({'一二三四五六日'[today.weekday()]}) · 本周窗口 {thu} → {today}")

    values = SheetsClient(s_my.secrets.google_sa_json).read_tab(s_my.cpa.spreadsheet_id, s_my.cpa.sales_tab)
    sales, _c, _h = cpa.parse_sales(values, s_my.cpa.price_myr)
    strict30, strict60, pool7, pool30, last_sale = {}, {}, {}, {}, {}
    for x in sales:
        if not x.date:
            continue
        k = (_mkey(x.campaign), cpa.norm(x.ad))
        ck = cpa.creative_key(x.ad)
        if x.date >= d60:
            strict60[k] = strict60.get(k, 0) + 1
        if x.date >= d30:
            strict30[k] = strict30.get(k, 0) + 1
            pool30[ck] = pool30.get(ck, 0) + 1
        if x.date >= d7:
            pool7[ck] = pool7.get(ck, 0) + 1
        if ck not in last_sale or x.date > last_sale[ck]:
            last_sale[ck] = x.date

    for label, cfg in (("SG", "config.sg.yaml"), ("MY 5.0", "config.my5.yaml")):
        s = load_settings(REPO_ROOT / "config" / cfg)
        banned = s.compliance.banned_creatives
        line, min_spend = s.kpi.cpl_threshold_myr, s.kpi.cpl_min_spend_myr
        until = cpa.parse_date(s.kpi.cpl_paused_until or "")
        resume = (until + dt.timedelta(days=1)).isoformat() if until and today <= until else "已恢复"
        g = graph_client(s)
        acct = s.meta.account_path
        token = result_action_type(s.meta.conversion_event)
        try:
            ads = g._get_all(acct + "/ads", {
                "fields": "id,name,status,effective_status,created_time,issues_info,"
                          "campaign{id,name,status,daily_budget},"
                          "adset{id,name,status,daily_budget,promoted_object},"
                          "creative{id,effective_object_story_id,object_story_spec,call_to_action_type}",
                "limit": "500"})
            time.sleep(1.2)
            insw = {r.get("ad_id"): r for r in g.account_insights(
                acct, level="ad", fields="ad_id,spend,actions",
                time_range={"since": thu.isoformat(), "until": today.isoformat()})}
            time.sleep(1.2)
            ins30 = {r.get("ad_id"): r for r in g.account_insights(
                acct, level="ad", fields="ad_id,spend,actions",
                time_range={"since": d30.isoformat(), "until": today.isoformat()})}
            time.sleep(1.2)
            sp60 = {r.get("ad_id"): float(r.get("spend") or 0) for r in g.account_insights(
                acct, level="ad", fields="ad_id,spend",
                time_range={"since": d60.isoformat(), "until": today.isoformat()})}
            time.sleep(1.2)
        except Exception as exc:                                     # noqa: BLE001
            print(f"\n═══ [{label}] 读不到：{str(exc)[:200]}")
            continue

        def is_reg(a: dict) -> bool:
            return ((((a.get("adset") or {}).get("promoted_object") or {}).get("custom_event_type") or "")
                    .upper() == "COMPLETE_REGISTRATION")

        live = [a for a in ads if a.get("effective_status") == "ACTIVE" and is_reg(a)]
        print(f"\n═══ [{label}] 在跑 {len(live)} 支 · 线 RM{line:.0f} · 0-reg 门槛 RM{min_spend:.0f}"
              f" · CPL 判读{'停到 ' + until.isoformat() + '，' + resume + ' 恢复' if until and today <= until else '已恢复'} ═══")
        counts: dict = {}
        rows = []
        for a in live:
            nm = a.get("name") or ""
            camp = a.get("campaign") or {}
            aset = a.get("adset") or {}
            rw = insw.get(a["id"]) or {}
            spw, rgw = float(rw.get("spend") or 0), extract_results(rw.get("actions"), token)
            r30 = ins30.get(a["id"]) or {}
            sp30, rg30 = float(r30.get("spend") or 0), extract_results(r30.get("actions"), token)
            k = (_mkey(camp.get("name") or ""), cpa.norm(nm))
            ck = cpa.creative_key(nm)
            n30, n60 = strict30.get(k, 0), strict60.get(k, 0)
            cpa30 = (sp30 / n30) if n30 else None
            cpa60 = (sp60.get(a["id"], 0.0) / n60) if n60 else None
            try:
                age = (today - dt.date.fromisoformat((a.get("created_time") or "")[:10])).days
            except ValueError:
                age = 999
            cta = cta_of(a.get("creative") or {})
            p7 = pool7.get(ck, 0)
            ban = compliance.banned_reason(nm, banned)
            eff = a.get("effective_status")
            if ban:
                v = "⛔禁跑·必删"
            elif a.get("issues_info") or eff in BAD_EFF:
                v = "❗被拒·必删"
            elif "WHATSAPP" in cta.upper() or "wa.me" in cta:
                v = "⚠️WhatsApp"
            elif n60 and cpa60 is not None and cpa60 > HARD:
                v = "🛑hard-stop"
            elif age <= NEW_DAYS:
                v = "🆕新(例外)"
            elif n30 and cpa30 <= PASS_MAX:
                v = "✅达标"
            elif n30 and cpa30 <= HARD:
                v = "⚠️WATCH"
            elif n30:
                v = "❌超1200"
            elif p7:
                v = "✅素材7d有单"
            else:
                v = "❌30d无单"
            flags = []
            if rgw == 0 and spw >= min_spend:
                flags.append(f"本周0报名花满RM{spw:.0f}→{resume} monitor会关")
            elif rgw and spw >= min_spend and spw / rgw > line:
                flags.append(f"本周CPL {spw / rgw:.0f}>{line:.0f}→{resume} monitor先降载体30%")
            elif rgw == 0 and spw >= 0.6 * min_spend:
                flags.append(f"本周0报名RM{spw:.0f}（门槛{min_spend:.0f}）")
            if v != "🛑hard-stop" and n60 and cpa60 is not None and cpa60 > 1000:
                flags.append(f"CPA60 {cpa60:,.0f} 接近hard-stop")
            counts[v] = counts.get(v, 0) + 1
            rows.append((v, nm, camp.get("name") or "", aset, age, spw, rgw, sp30, rg30, n30, cpa30, n60, cpa60,
                         p7, pool30.get(ck, 0), last_sale.get(ck), cta, flags))

        order = ["⛔禁跑·必删", "❗被拒·必删", "⚠️WhatsApp", "🛑hard-stop", "❌超1200", "❌30d无单",
                 "⚠️WATCH", "🆕新(例外)", "✅素材7d有单", "✅达标"]
        rows.sort(key=lambda r: (order.index(r[0]) if r[0] in order else 99, -r[5]))
        for (v, nm, cn, aset, age, spw, rgw, sp30, rg30, n30, cpa30, n60, cpa60, p7, p30, last, cta, flags) in rows:
            cplw = (spw / rgw) if rgw else None
            cpl30 = (sp30 / rg30) if rg30 else None
            print(f"  {v:<11} «{nm[:30]}» @ «{cn[:34]}» {age}天")
            print(f"      本周 RM{spw:>5.0f} / {rgw:>2.0f} 报名 / CPL {fmt(cplw):>5} | 30d RM{sp30:>6,.0f} / {rg30:.0f} 报名 / "
                  f"CPL {fmt(cpl30)} · CPA30 {fmt(cpa30)}({n30}单) · CPA60 {fmt(cpa60)}({n60}单) | "
                  f"素材池 7d:{p7} 30d:{p30} 最近成交 {last or '无'}")
            print(f"      目的地 {cta[:80]}" + ("" if not flags else "  ‖ " + " · ".join(flags)))
        print("  合计：" + " · ".join(f"{k} {n}" for k, n in sorted(counts.items(), key=lambda kv: order.index(kv[0]) if kv[0] in order else 99)))

        # ── rejected ads still in the account (any status) ────────────────────────────
        rej = [a for a in ads if a.get("effective_status") in BAD_EFF or a.get("issues_info")]
        pend = [a for a in ads if a.get("effective_status") in REVIEW_EFF]
        print(f"\n  被拒 / 有 issue 还躺在账户里（规则：删，不只是停）：{len(rej)} 支")
        for a in rej:
            iss = a.get("issues_info") or []
            why = "; ".join((i.get("error_summary") or i.get("error_message") or "")[:60] for i in iss) if iss else ""
            print(f"    {a.get('effective_status'):<14} «{(a.get('name') or '')[:34]}» @ «{((a.get('campaign') or {}).get('name') or '')[:34]}» "
                  f"ad层 {a.get('status')}  {why}")
        if pend:
            print(f"  审核中：{len(pend)} 支 — " + " · ".join(f"«{(a.get('name') or '')[:24]}»" for a in pend[:8]))

        # ── banned masters armed at ad level ─────────────────────────────────────────
        armed, disarmed = [], 0
        for a in ads:
            if not compliance.banned_reason(a.get("name") or "", banned):
                continue
            if a.get("effective_status") == "ACTIVE":
                continue                                   # already counted above as ⛔ live
            if a.get("status") == "ACTIVE":
                armed.append(a)
            else:
                disarmed += 1
        print(f"  禁跑素材：在跑 {counts.get('⛔禁跑·必删', 0)} 支 · ad 层已 PAUSED {disarmed} 支 · "
              f"ad 层还 ACTIVE 只靠上层压住（上膛）{len(armed)} 支")
        for a in armed:
            print(f"    🚫上膛 «{(a.get('name') or '')[:34]}» @ «{((a.get('campaign') or {}).get('name') or '')[:34]}» eff={a.get('effective_status')}")
        time.sleep(1.0)

    print("\nCLOSE CHECK DONE (read-only)")


if __name__ == "__main__":
    main()
