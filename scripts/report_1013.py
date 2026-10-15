# -*- coding: utf-8 -*-
"""READ-ONLY: owner 2026-10-13 morning「匯報」— the morning after the 14/10 scale-up (Mon 10/12 evening:
MY 5.0 every campaign RM200, SG step 1 RM445 + 6 new SG positions + LUXURY MY built and opened).

Both accounts: yesterday (account-tz day) + today-so-far + Thu-week-to-date per carrier and per live
registration ad; yesterday split before/after 20:00 (the raises landed 20:00-21:30 local) to see whether
CPL spiked; review state of every ad built last night; pending/rejected ads anywhere; who toggled what
in the last 16 h; banned creatives live. Prints RM / counts / dates only — no PII."""
from __future__ import annotations

import datetime as dt
import json
import time

from adbot import compliance
from adbot.commands import graph_client
from adbot.monitor_cpl import extract_results, result_action_type
from adbot.settings import REPO_ROOT, load_settings

PURCHASE = "offsite_conversion.fb_pixel_purchase"
NEW_SG_ADS = {
    "120249852158430521": "LUXURY GOODS · HOOK：V12 不选 forex (new ad)",
    "120249853085330521": "🌟 PURCHASE LAL 5% · 不选 forex",
    "120249853088580521": "🌟 GOLF PICKBLEBALL · 不选 forex",
    "120249853091340521": "PRIORITY BANKING · 不选 forex",
    "120249853227870521": "PURCHASE LAL 1% | 1012 · 不选 forex",
    "120249853230620521": "RETARGET LP 14D | 1012 · 不选 forex",
}
NEW_MY_ADS = {
    "120251390711070329": "LUXURY MY · 盖电脑",
    "120251390712180329": "LUXURY MY · korea",
    "120251390713510329": "LUXURY MY · 年纪大",
    "120251390715930329": "LUXURY MY · 赚美金",
}
RT_AUDIENCE = "120249853134410521"
LOCAL = dt.timezone(dt.timedelta(hours=8))


def main() -> None:
    for label, cfg, new_ads, line, floor in (("SG", "config.sg.yaml", NEW_SG_ADS, 95.0, 142.0),
                                             ("MY 5.0", "config.my5.yaml", NEW_MY_ADS, 60.0, 60.0)):
        print(f"\n################ {label} ################")
        try:
            one(label, cfg, new_ads, line, floor)
        except Exception as exc:                                   # noqa: BLE001
            print(f"  ❌ {label} 读不到：{str(exc)[:200]}")
        time.sleep(2.0)
    print("\nREPORT 1013 DONE (read-only)")


def rm(cents) -> float:
    try:
        return float(cents or 0) / 100.0
    except (TypeError, ValueError):
        return 0.0


def one(label: str, cfg: str, new_ads: dict, line: float, floor: float) -> None:
    s = load_settings(REPO_ROOT / "config" / cfg)
    g = graph_client(s)
    acct = s.meta.account_path
    token = result_action_type(s.meta.conversion_event)
    banned = s.compliance.banned_creatives

    now_local = dt.datetime.now(LOCAL)
    today = now_local.date()
    yday = today - dt.timedelta(days=1)
    thu = today - dt.timedelta(days=(today.weekday() - 3) % 7)
    if thu >= today:                      # on Thursday, show the week that just ended
        thu -= dt.timedelta(days=7)
    wk = {"since": thu.isoformat(), "until": yday.isoformat()}

    def ins(level, fields, **kw):
        time.sleep(1.3)
        return g.account_insights(acct, level=level, fields=fields, **kw)

    def metr(r):
        sp = float((r or {}).get("spend") or 0)
        rg = extract_results((r or {}).get("actions"), token)
        pu = extract_results((r or {}).get("actions"), PURCHASE)
        return sp, rg, pu

    def cpl(sp, rg):
        return f"{sp / rg:.0f}" if rg else ("∞" if sp >= 1 else "—")

    # ── campaigns / carriers ──────────────────────────────────────────────────
    camps = g._get_all(acct + "/campaigns", {
        "fields": "id,name,status,effective_status,daily_budget,updated_time", "limit": "200"})
    cy = {r["campaign_id"]: r for r in ins("campaign", "campaign_id,spend,actions", date_preset="yesterday")}
    ct = {r["campaign_id"]: r for r in ins("campaign", "campaign_id,spend,actions", date_preset="today")}
    cw = {r["campaign_id"]: r for r in ins("campaign", "campaign_id,spend,actions", time_range=wk)}

    time.sleep(1.3)
    adsets = g._get_all(acct + "/adsets", {
        "fields": "id,name,status,effective_status,daily_budget,campaign_id,updated_time", "limit": "500"})
    live_sets = {}
    for a in adsets:
        if a.get("effective_status") == "ACTIVE":
            live_sets.setdefault(a["campaign_id"], []).append(a)

    print(f"═══ {label} 载体 — 昨天 {yday}（账户时区整天）· 本周四起 {thu}→{yday} · 今天到 {now_local:%H:%M} ═══")
    print(f"{'campaign':<44} {'日预算':<16} {'昨花费':>7} {'报名':>4} {'CPL':>5} | {'周花费':>8} {'报名':>4} {'CPL':>5} 成交 | {'今花费':>7} {'报名':>4}")
    tot_y = [0.0, 0.0]; tot_t = [0.0, 0.0]; tot_w = [0.0, 0.0, 0.0]
    rows = []
    for c in camps:
        sy, ry, _ = metr(cy.get(c["id"]))
        st, rt, _ = metr(ct.get(c["id"]))
        sw, rw, pw = metr(cw.get(c["id"]))
        if c.get("effective_status") != "ACTIVE" and sy < 1 and st < 1 and sw < 1:
            continue
        rows.append((c, sy, ry, st, rt, sw, rw, pw))
    rows.sort(key=lambda r: (-(r[1] + r[3]), r[0]["name"]))
    for c, sy, ry, st, rt, sw, rw, pw in rows:
        sets = live_sets.get(c["id"], [])
        if c.get("daily_budget"):
            bud = f"CBO RM{rm(c['daily_budget']):.0f}"
        else:
            bud = "ABO " + "+".join(f"RM{rm(x.get('daily_budget')):.0f}" for x in sets) if sets else "ABO —"
        st_flag = "" if c.get("effective_status") == "ACTIVE" else f" [{c.get('effective_status')}]"
        name = (c.get("name") or "")[:42] + st_flag
        print(f"{name:<44} {bud:<16} RM{sy:>5.0f} {ry:>4.0f} {cpl(sy, ry):>5} | RM{sw:>6.0f} {rw:>4.0f} {cpl(sw, rw):>5} {pw:>3.0f}  | RM{st:>5.0f} {rt:>4.0f}")
        tot_y[0] += sy; tot_y[1] += ry; tot_t[0] += st; tot_t[1] += rt
        tot_w[0] += sw; tot_w[1] += rw; tot_w[2] += pw
    live_budget = sum(rm(c.get("daily_budget")) for c in camps if c.get("effective_status") == "ACTIVE" and c.get("daily_budget"))
    live_budget += sum(rm(a.get("daily_budget")) for a in adsets if a.get("effective_status") == "ACTIVE"
                       and a.get("daily_budget") and not next((c for c in camps if c["id"] == a["campaign_id"] and c.get("daily_budget")), None))
    print(f"\n  合计 昨天 RM{tot_y[0]:,.0f} · 报名 {tot_y[1]:.0f} · CPL {cpl(*tot_y)}   |   本周 RM{tot_w[0]:,.0f} · 报名 {tot_w[1]:.0f} · CPL {cpl(tot_w[0], tot_w[1])} · pixel 成交 {tot_w[2]:.0f}   |   今天 RM{tot_t[0]:,.0f} · 报名 {tot_t[1]:.0f} · CPL {cpl(*tot_t)}")
    print(f"  现在开着的日预算合计：RM{live_budget:,.0f}/天（线 RM{line:.0f}）")

    # ── yesterday before / after 20:00 local (raises landed 20:00-21:30) ────
    time.sleep(1.3)
    hourly = g._get_all(acct + "/insights", {
        "level": "account", "fields": "spend,actions", "date_preset": "yesterday",
        "breakdowns": "hourly_stats_aggregated_by_advertiser_time_zone", "limit": "50"})
    before = [0.0, 0.0]; after = [0.0, 0.0]
    for r in hourly:
        h = int((r.get("hourly_stats_aggregated_by_advertiser_time_zone") or "00")[:2])
        sp, rg, _ = metr(r)
        tgt = after if h >= 20 else before
        tgt[0] += sp; tgt[1] += rg
    print(f"  昨天 00-20h：RM{before[0]:.0f} · 报名 {before[1]:.0f} · CPL {cpl(*before)}   →   20-24h（加预算后）：RM{after[0]:.0f} · 报名 {after[1]:.0f} · CPL {cpl(*after)}")
    time.sleep(1.3)
    hourly_t = g._get_all(acct + "/insights", {
        "level": "account", "fields": "spend,actions", "date_preset": "today",
        "breakdowns": "hourly_stats_aggregated_by_advertiser_time_zone", "limit": "50"})
    seq = []
    for r in sorted(hourly_t, key=lambda r: r.get("hourly_stats_aggregated_by_advertiser_time_zone") or ""):
        sp, rg, _ = metr(r)
        if sp >= 1:
            seq.append(f"{(r.get('hourly_stats_aggregated_by_advertiser_time_zone') or '')[:2]}h RM{sp:.0f}/{rg:.0f}")
    print("  今天逐小时（花费/报名）：" + (" · ".join(seq) if seq else "—"))

    # ── live registration ads ────────────────────────────────────────────────
    time.sleep(1.3)
    ads = g._get_all(acct + "/ads", {
        "fields": "id,name,status,effective_status,ad_review_feedback,created_time,updated_time,"
                  "campaign{id,name,daily_budget},adset{id,name,daily_budget,promoted_object}", "limit": "500"})
    ay = {r.get("ad_id"): r for r in ins("ad", "ad_id,spend,actions", date_preset="yesterday")}
    at = {r.get("ad_id"): r for r in ins("ad", "ad_id,spend,actions", date_preset="today")}
    aw = {r.get("ad_id"): r for r in ins("ad", "ad_id,spend,actions", time_range=wk)}

    live = [a for a in ads if a.get("effective_status") == "ACTIVE"
            and (((a.get("adset") or {}).get("promoted_object") or {}).get("custom_event_type") or "").upper()
            == "COMPLETE_REGISTRATION"]
    print(f"\n═══ {label} 在跑 registration ad {len(live)} 支 ═══")
    print(f"{'素材 @ campaign':<60} {'昨花费':>7} {'报名':>4} {'CPL':>5} | {'周花费':>7} {'报名':>4} {'CPL':>5} | {'今花费':>6} {'报名':>4}")
    arows = []
    for a in live:
        sy, ry, _ = metr(ay.get(a["id"])); st, rt, _ = metr(at.get(a["id"])); sw, rw, _ = metr(aw.get(a["id"]))
        arows.append((a, sy, ry, st, rt, sw, rw))
    arows.sort(key=lambda r: -(r[1] + r[3]))
    for a, sy, ry, st, rt, sw, rw in arows:
        nm = f"{(a.get('name') or '')[:28]} @ {((a.get('campaign') or {}).get('name') or '')[16:46]}"
        flag = ""
        if ry and sy / ry > line:
            flag = " ⚠️超线"
        elif not ry and sy >= floor:
            flag = " ❌0reg花满"
        elif ry and sy / ry <= line and sy >= 30:
            flag = " ✅"
        if a["id"] in new_ads:
            flag += " 🆕"
        print(f"{nm:<60} RM{sy:>5.0f} {ry:>4.0f} {cpl(sy, ry):>5} | RM{sw:>5.0f} {rw:>4.0f} {cpl(sw, rw):>5} | RM{st:>4.0f} {rt:>4.0f}{flag}")

    bad = [a for a in live if compliance.is_banned(a.get("name") or "", banned)]
    print(f"\n🚫 在跑的禁跑素材：{len(bad)} 支" + ("" if not bad else " ← 立刻停！ " + " / ".join((a.get('name') or '')[:30] for a in bad)))

    # ── review state: last night's builds + anything pending / rejected ─────
    print(f"\n═══ {label} 昨晚建的位 — 审核状态 ═══")
    by_id = {a["id"]: a for a in ads}
    for aid, desc in new_ads.items():
        a = by_id.get(aid)
        if not a:
            print(f"  {desc:<46} ❓ 账户里找不到 {aid}")
            continue
        fb = a.get("ad_review_feedback") or {}
        fb_s = json.dumps(fb, ensure_ascii=False)[:160] if fb else ""
        sy, ry, _ = metr(ay.get(aid)); st, rt, _ = metr(at.get(aid))
        aset = a.get("adset") or {}
        print(f"  {desc:<46} ad {a.get('status')} / eff {a.get('effective_status'):<16} adset «{(aset.get('name') or '')[:24]}»  "
              f"昨 RM{sy:.0f}/{ry:.0f} 今 RM{st:.0f}/{rt:.0f} {fb_s}")
    odd = [a for a in ads if a.get("effective_status") not in ("ACTIVE", "PAUSED", "CAMPAIGN_PAUSED", "ADSET_PAUSED", "ARCHIVED", "DELETED")]
    print(f"\n  账户内非 ACTIVE/PAUSED 的 ad（审核中 / 被拒 / 有问题）：{len(odd)} 支")
    for a in odd[:40]:
        fb = a.get("ad_review_feedback") or {}
        fb_s = json.dumps(fb, ensure_ascii=False)[:140] if fb else ""
        print(f"    {a.get('effective_status'):<16} «{(a.get('name') or '')[:36]}» @ {((a.get('campaign') or {}).get('name') or '')[:34]}  {fb_s}")
    rej = [a for a in ads if a.get("effective_status") in ("DISAPPROVED", "WITH_ISSUES")]
    print(f"  被拒 / WITH_ISSUES：{len(rej)} 支" + ("" if not rej else " ← 不 resubmit、不申诉；告诉 owner"))

    if label == "SG":
        time.sleep(1.3)
        try:
            aud = g.get_object(RT_AUDIENCE, "name,approximate_count_lower_bound,approximate_count_upper_bound,delivery_status,operation_status")
            print(f"\n  RETARGET 受众 «{aud.get('name')}»: 约 {aud.get('approximate_count_lower_bound')}–{aud.get('approximate_count_upper_bound')} 人 · "
                  f"delivery {json.dumps(aud.get('delivery_status'), ensure_ascii=False)[:80]} · op {json.dumps(aud.get('operation_status'), ensure_ascii=False)[:80]}")
        except Exception as exc:                                   # noqa: BLE001
            print(f"\n  RETARGET 受众读不到：{str(exc)[:120]}")

    # ── who toggled what in the last 16 h ───────────────────────────────────
    time.sleep(1.3)
    since_ts = int(dt.datetime.utcnow().timestamp()) - 16 * 3600
    acts = g._get_all(acct + "/activities", {
        "fields": "event_time,event_type,actor_name,object_name,extra_data",
        "since": str(since_ts), "limit": "300"})
    keep = [x for x in acts if any(k in (x.get("event_type") or "")
                                   for k in ("run_status", "budget", "review", "delete", "create", "bid"))]
    print(f"\n═══ {label} 近 16 小时 开/关/预算/审核 动作（{len(keep)} 条，最新在前；时间 UTC，+8 = 本地）═══")
    for x in keep[:60]:
        extra = x.get("extra_data") or ""
        try:
            ed = json.loads(extra) if isinstance(extra, str) else extra
            extra = " ".join(f"{k}={str(v)[:36]}" for k, v in ed.items() if k in ("old_value", "new_value", "status"))
        except Exception:                                            # noqa: BLE001
            extra = str(extra)[:80]
        print(f"  {(x.get('event_time') or '')[5:16]}  {(x.get('actor_name') or '?')[:18]:<18} "
              f"{(x.get('event_type') or '')[:30]:<30} «{(x.get('object_name') or '')[:38]}»  {extra[:80]}")


if __name__ == "__main__":
    main()
