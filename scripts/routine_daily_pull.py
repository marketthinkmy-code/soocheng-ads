# -*- coding: utf-8 -*-
"""Daily routine data pull (READ-ONLY — no writes, CONFIRM ignored).

What the scheduled daily-report routine needs that `daily_report.py` (campaign level)
does not give:

  1. **last_3d ad-level table** per account — effective_status / spend / registrations /
     CPL, plus the ACTIVE ads that spent nothing in the window.
  2. **Yesterday's sales** (MYT) from the Paid Student List sheet, grouped by ad + campaign,
     with each selling ad's live status — "昨天有没有新成交？哪几条广告出的单？"
  3. **Ad-level 60-day CPA hard-stop scan** — the pause candidates the hourly CPL/CPA
     monitor does not catch: CPA > hard_stop AND spend >= RM1,000 AND created >= 14 days
     ago AND still ACTIVE. Printed as candidates only; this script never writes.
  4. **Ad set budgets** for the reopened winners + MY TRAVEL (budget-change follow-up).

Rate-limit tolerant: every account section is wrapped, and a failure is reported as a
PARTIAL marker instead of killing the run.
"""
from __future__ import annotations

import datetime as dt
import time
import traceback

from adbot import cpa
from adbot.commands import graph_client
from adbot.monitor_cpl import extract_results, result_action_type
from adbot.settings import REPO_ROOT, load_settings

PACE = 1.0
ACCTS = (("MY", "config.yaml"), ("SG", "config.sg.yaml"))
CPA_HARD_STOP = 1200.0
MIN_SPEND = 1000.0
MIN_AGE_DAYS = 14

# the 8 winners reopened 8/4 (name fragments, matched case-insensitively after norm)
REOPENED = {
    "MY": ("你敢吗", "你没有本钱", "不选 forex"),
    "SG": ("freestyle 1", "盖电脑", "你没有本钱", "trading 早就不是这样了", "用我的方法"),
}
NEW_TESTS = ("beer", "day trading", "top3")
PARTIAL: list[str] = []


def fmt_cpl(spend: float, regs: float) -> str:
    if regs:
        return f"RM{spend / regs:.1f}"
    return "∞" if spend else "-"


def fmt_cpa(spend: float, n: int) -> str:
    return f"RM{spend / n:.0f}" if n else ("∞" if spend else "-")


def ad_rows(g, acct: str, token: str, *, date_preset=None, time_range=None) -> dict:
    rows = g.account_insights(
        acct, level="ad", date_preset=date_preset, time_range=time_range,
        fields="ad_id,ad_name,campaign_name,adset_name,spend,actions,impressions")
    out = {}
    for r in rows:
        out[r.get("ad_id")] = {
            "name": r.get("ad_name") or "?",
            "camp": r.get("campaign_name") or "?",
            "adset": r.get("adset_name") or "?",
            "spend": float(r.get("spend") or 0),
            "regs": extract_results(r.get("actions"), token),
            "impr": int(r.get("impressions") or 0),
        }
    return out


def live_ads(g, acct: str) -> dict:
    """ad_id -> {name, status, created, campaign, adset, adset_id}."""
    ads = g._get_all(f"{acct}/ads", {
        "fields": "id,name,effective_status,created_time,campaign{name},adset{id,name}",
        "limit": "300"})
    out = {}
    for a in ads:
        out[a["id"]] = {
            "name": a.get("name") or "?",
            "status": a.get("effective_status") or "?",
            "created": (a.get("created_time") or "")[:10],
            "camp": (a.get("campaign") or {}).get("name", "?"),
            "adset": (a.get("adset") or {}).get("name", "?"),
            "adset_id": (a.get("adset") or {}).get("id", ""),
        }
    return out


def main() -> None:
    today = (dt.datetime.utcnow() + dt.timedelta(hours=8)).date()  # MYT
    yday = today - dt.timedelta(days=1)
    print(f"ROUTINE PULL · today(MYT)={today} · yesterday={yday}\n")

    base = load_settings(REPO_ROOT / "config" / "config.yaml")
    from adbot.clients.sheets import SheetsClient

    sales = []
    try:
        values = SheetsClient(base.secrets.google_sa_json).read_tab(
            base.cpa.spreadsheet_id, base.cpa.sales_tab)
        sales, _c, _h = cpa.parse_sales(values, base.cpa.price_myr)
    except Exception as exc:  # noqa: BLE001
        PARTIAL.append(f"sheet read failed: {exc}")
        print(f"!! sheet read failed: {exc}")

    # ── sales windows ────────────────────────────────────────────────────────
    def since(d: dt.date):
        strict, by_name, amt = {}, {}, {}
        for s in sales:
            if not s.date or s.date < d:
                continue
            strict[(s.campaign, s.ad)] = strict.get((s.campaign, s.ad), 0) + 1
            by_name[s.ad] = by_name.get(s.ad, 0) + 1
            amt[s.ad] = amt.get(s.ad, 0.0) + s.amount
        return strict, by_name, amt

    s60_strict, s60_name, _s60_amt = since(today - dt.timedelta(days=60))
    _s3_strict, s3_name, _a = since(today - dt.timedelta(days=3))

    print("══════════ 昨天 (MYT %s) 的成交 ══════════" % yday)
    yday_sales = [s for s in sales if s.date == yday]
    if not yday_sales:
        print("  (sheet 上昨天 0 单)")
    grouped: dict = {}
    for s in yday_sales:
        grouped.setdefault((s.campaign, s.ad), []).append(s)
    for (camp, ad), rows in sorted(grouped.items(), key=lambda kv: -len(kv[1])):
        amt = sum(r.amount for r in rows)
        print(f"  {len(rows)} 单 · RM{amt:.0f} · [{camp[:52]}] «{ad[:48]}»")
    print(f"  昨天合计: {len(yday_sales)} 单 · RM{sum(s.amount for s in yday_sales):.0f}")
    d2 = today - dt.timedelta(days=2)
    print(f"  (前天 {d2}: {sum(1 for s in sales if s.date == d2)} 单 · "
          f"近 3 天合计 {sum(v for v in s3_name.values())} 单)\n")

    for label, cfg in ACCTS:
        print(f"\n════════════════ [{label}] ════════════════")
        try:
            s = load_settings(REPO_ROOT / "config" / cfg)
            g = graph_client(s)
            acct = s.meta.account_path
            token = result_action_type(s.meta.conversion_event)
            print(f"  account={acct} · cpl_ceiling={s.kpi.cpl_threshold_myr} · "
                  f"cpa_hard_stop={s.cpa.hard_stop_myr} · cpl_hold={s.kpi.cpl_hold}")

            live = live_ads(g, acct); time.sleep(PACE)
            r3 = ad_rows(g, acct, token, date_preset="last_3d"); time.sleep(PACE)
            r60 = ad_rows(g, acct, token, time_range={
                "since": str(today - dt.timedelta(days=60)), "until": str(today)})
            time.sleep(PACE)

            # ── 1) last_3d ad table ──────────────────────────────────────────
            print(f"\n  ── last_3d · ad level (spend desc) ──")
            tot_s = tot_r = 0.0
            for aid, r in sorted(r3.items(), key=lambda kv: -kv[1]["spend"]):
                tot_s += r["spend"]; tot_r += r["regs"]
                st = live.get(aid, {}).get("status", "?")
                print(f"    [{st:<8}] RM{r['spend']:>7.0f} · {int(r['regs']):>3} reg · "
                      f"CPL {fmt_cpl(r['spend'], r['regs']):>8} · "
                      f"{r['camp'][:40]:40} | {r['adset'][:22]:22} | «{r['name'][:44]}»")
            print(f"    TOTAL RM{tot_s:.0f} · {int(tot_r)} reg · CPL {fmt_cpl(tot_s, tot_r)}")

            spent = set(r3)
            zero = [(aid, v) for aid, v in live.items()
                    if v["status"] == "ACTIVE" and aid not in spent]
            print(f"\n  ── ACTIVE 但 last_3d 0 花费 ({len(zero)}) ──")
            for aid, v in sorted(zero, key=lambda kv: kv[1]["camp"]):
                print(f"    {v['camp'][:40]:40} | {v['adset'][:22]:22} | «{v['name'][:40]}» "
                      f"(建于 {v['created']})")

            # ── 2) 60d ad-level CPA hard-stop scan ───────────────────────────
            print(f"\n  ── 60d ad-level CPA 扫描 (hard-stop RM{CPA_HARD_STOP:.0f}, "
                  f"spend≥RM{MIN_SPEND:.0f}, 建立≥{MIN_AGE_DAYS}天, 仍在跑) ──")
            cands = 0
            for aid, r in sorted(r60.items(), key=lambda kv: -kv[1]["spend"]):
                v = live.get(aid)
                if not v or v["status"] != "ACTIVE":
                    continue
                if r["spend"] < MIN_SPEND:
                    continue
                nk = cpa.norm(r["name"])
                n_strict = s60_strict.get((cpa.norm(r["camp"]), nk), 0)
                n_name = s60_name.get(nk, 0)
                n = max(n_strict, n_name)   # rename-proof: name fallback
                val = (r["spend"] / n) if n else None
                age = "?"
                if v["created"]:
                    try:
                        age = (today - dt.date.fromisoformat(v["created"])).days
                    except ValueError:
                        pass
                over = (val is None) or (val > CPA_HARD_STOP)
                old = isinstance(age, int) and age >= MIN_AGE_DAYS
                flag = "  ⛔ CANDIDATE" if (over and old) else ""
                if flag:
                    cands += 1
                print(f"    RM{r['spend']:>7.0f} · sales {n} (strict {n_strict}/name {n_name})"
                      f" · CPA {fmt_cpa(r['spend'], n):>8} · age {age}d · "
                      f"«{r['name'][:40]}» [{r['camp'][:34]}]{flag}")
            print(f"    → {cands} 个 pause candidate")

            # ── 3) reopened winners ──────────────────────────────────────────
            print(f"\n  ── 8/4 重开的赢家 ──")
            for frag in REOPENED[label]:
                hits = [(aid, v) for aid, v in live.items()
                        if cpa.norm(frag) in cpa.norm(v["name"])]
                if not hits:
                    print(f"    «{frag}»: 账户里找不到")
                    continue
                for aid, v in hits:
                    r = r3.get(aid, {"spend": 0.0, "regs": 0.0})
                    r6 = r60.get(aid, {"spend": 0.0})
                    nk = cpa.norm(v["name"])
                    n = max(s60_strict.get((cpa.norm(v["camp"]), nk), 0), s60_name.get(nk, 0))
                    bud = ""
                    try:
                        if v["adset_id"]:
                            a = g.get_object(v["adset_id"], "daily_budget,name")
                            time.sleep(0.4)
                            if a.get("daily_budget"):
                                bud = f" · adset预算 RM{float(a['daily_budget']) / 100:.0f}/day"
                    except Exception:  # noqa: BLE001
                        pass
                    print(f"    [{v['status']:<8}] «{v['name'][:42]}» [{v['camp'][:34]}]")
                    print(f"        3d: RM{r['spend']:.0f} · {int(r['regs'])} reg · "
                          f"CPL {fmt_cpl(r['spend'], r['regs'])} | 60d: RM{r6['spend']:.0f} · "
                          f"{n} 单 · CPA {fmt_cpa(r6['spend'], n)}{bud}")

            # ── 4) new tests (BEER / DAY TRADING / TOP3) ─────────────────────
            print(f"\n  ── 新测试 campaign (BEER / DAY TRADING / TOP3) ──")
            camps = g.list_campaigns(acct); time.sleep(PACE)
            for c in camps:
                cn = cpa.norm(c.get("name", ""))
                if not any(t in cn for t in NEW_TESTS):
                    continue
                rows3 = [r for r in r3.values() if cpa.norm(r["camp"]) == cn]
                rows60 = [r for r in r60.values() if cpa.norm(r["camp"]) == cn]
                sp3 = sum(r["spend"] for r in rows3); rg3 = sum(r["regs"] for r in rows3)
                sp60 = sum(r["spend"] for r in rows60)
                n60 = sum(v for (ck, _ak), v in s60_strict.items() if ck == cn)
                print(f"    [{c.get('effective_status'):<8}] {c.get('name')[:52]}")
                print(f"        3d: RM{sp3:.0f} · {int(rg3)} reg · CPL {fmt_cpl(sp3, rg3)} | "
                      f"60d: RM{sp60:.0f} · {n60} 单 · CPA {fmt_cpa(sp60, n60)}")

            # ── 5) ad set budgets (all active adsets) ────────────────────────
            print(f"\n  ── 在跑 ad set 日预算 ──")
            try:
                adsets = g._get_all(f"{acct}/adsets", {
                    "fields": "name,daily_budget,effective_status,campaign{name}",
                    "limit": "200"})
                for a in sorted(adsets, key=lambda x: x.get("name", "")):
                    if a.get("effective_status") != "ACTIVE":
                        continue
                    db = a.get("daily_budget")
                    print(f"    {(a.get('campaign') or {}).get('name','?')[:40]:40} | "
                          f"{a.get('name','?')[:26]:26} | "
                          f"{('RM%.0f/day' % (float(db) / 100)) if db else 'CBO/campaign级'}")
            except Exception as exc:  # noqa: BLE001
                PARTIAL.append(f"{label} adsets: {exc}")
                print(f"    !! adset 读取失败: {exc}")

        except Exception as exc:  # noqa: BLE001
            PARTIAL.append(f"{label} account section failed: {exc}")
            print(f"  !! [{label}] 拉取失败: {exc}")
            traceback.print_exc()

    print("\n══════════ PARTIAL MARKERS ══════════")
    if PARTIAL:
        for p in PARTIAL:
            print(f"  ⚠️ {p}")
    else:
        print("  none — 数据完整")
    print("\nROUTINE PULL DONE (read-only)")


if __name__ == "__main__":
    main()
