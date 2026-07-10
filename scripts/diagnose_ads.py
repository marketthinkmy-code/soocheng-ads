"""Read-only 3-in-1 diagnostic for STOCK BLOOM (no writes to Meta):

  TASK 1  which ad / market is getting more expensive — per-campaign (MY vs SG)
          and per-(campaign,ad) daily CPL trend, last 14d.
  TASK 2  rejected / with-issues ads — issues_info + ad_review_feedback (the exact
          policy reason) + creative, to judge COPY vs VIDEO.
  TASK 3  Singapore candidates — every creative's lifetime paid buyers, kind, the
          campaign it's in, plus an income-claim / MY-locality flag (the two things
          that get an ad rejected in SG or make it un-portable).
"""
from __future__ import annotations

from collections import defaultdict

from adbot import cpa
from adbot.clients.sheets import SheetsClient
from adbot.commands import graph_client
from adbot.monitor_cpl import extract_results, result_action_type
from adbot.settings import load_settings

MY_TOKENS = ["RM", "令吉", "马来西亚", "大马", "Malaysia", "MYR", "ringgit", "马股", "KLSE", "大马股"]
# phrases that read as an income / guaranteed-return claim → Meta financial-policy reject risk
INCOME_FLAGS = ["月薪", "稳定收益", "每日稳定", "每周就能多出", "每天多", "1分钟赚", "1 分钟赚",
                "赚 300", "赚300", "多出 2", "翻本", "翻转了收入", "翻转收入", "提款", "日入",
                "月入", "被动收入", "睡后收入", "稳赚", "保证", "包赚", "轻松赚", "盈利营"]


def _cpl(spend: float, regs: float) -> str:
    if spend <= 0:
        return "  ·  "
    if regs <= 0:
        return f"RM{spend:.0f}/0=∞"
    return f"RM{spend/regs:.0f}"


def _income_hits(text: str):
    return [p for p in INCOME_FLAGS if p in (text or "")]


def _my_hits(text: str):
    return [t for t in MY_TOKENS if t.lower() in (text or "").lower()]


def main() -> None:
    s = load_settings()
    g = graph_client(s)
    acct = s.meta.account_path
    token = result_action_type(s.meta.conversion_event)

    # ══════════════════════════════════════════════════════════════════════════
    # TASK 1 — cost trend: per-campaign (MY vs SG) + per-(campaign,ad) daily CPL
    # ══════════════════════════════════════════════════════════════════════════
    print("=" * 80)
    print("TASK 1 · WHAT IS GETTING MORE EXPENSIVE  (daily CPL, last 14d)")
    print("=" * 80)

    # -- 1a: per-campaign daily, bucketed MY vs SG ------------------------------
    crows = g._get_all(f"{acct}/insights", {
        "level": "campaign", "fields": "campaign_name,spend,actions",
        "time_increment": "1", "date_preset": "last_14d", "limit": "500"})
    camp_daily = defaultdict(lambda: defaultdict(lambda: [0.0, 0.0]))  # camp -> date -> [sp,rg]
    mkt_daily = defaultdict(lambda: defaultdict(lambda: [0.0, 0.0]))   # 'SG'/'MY' -> date -> [sp,rg]
    camp_tot = defaultdict(float)
    for r in crows:
        cn = r.get("campaign_name", "?")
        d = r.get("date_start")
        sp = float(r.get("spend") or 0)
        rg = extract_results(r.get("actions"), token)
        camp_daily[cn][d][0] += sp
        camp_daily[cn][d][1] += rg
        camp_tot[cn] += sp
        mkt = "SG" if "[SG]" in cn.upper() or cn.upper().startswith("SG") else "MY"
        mkt_daily[mkt][d][0] += sp
        mkt_daily[mkt][d][1] += rg

    dates = sorted({d for cn in camp_daily for d in camp_daily[cn]})
    print("\n--- MY vs SG blended daily CPL (the 'why is it expensive' split) ---")
    print(f"{'date':12} | {'MY spend':>9} {'reg':>4} {'CPL':>8} | {'SG spend':>9} {'reg':>4} {'CPL':>8}")
    print("-" * 66)
    for d in dates:
        my = mkt_daily["MY"].get(d, [0, 0])
        sg = mkt_daily["SG"].get(d, [0, 0])
        print(f"{d:12} | {my[0]:9.0f} {my[1]:4.0f} {_cpl(*my):>8} | "
              f"{sg[0]:9.0f} {sg[1]:4.0f} {_cpl(*sg):>8}")

    print("\n--- per-campaign: 14d spend + early-half vs late-half CPL ---")
    half = len(dates) // 2 or 1
    ed, ld = dates[:half], dates[half:]
    print(f"{'campaign':40} {'14dSpend':>9} {'earlyCPL':>9} {'lateCPL':>9}")
    print("-" * 70)
    for cn in sorted(camp_tot, key=lambda c: -camp_tot[c]):
        e_sp = sum(camp_daily[cn].get(d, [0, 0])[0] for d in ed)
        e_rg = sum(camp_daily[cn].get(d, [0, 0])[1] for d in ed)
        l_sp = sum(camp_daily[cn].get(d, [0, 0])[0] for d in ld)
        l_rg = sum(camp_daily[cn].get(d, [0, 0])[1] for d in ld)
        print(f"{cn[:40]:40} {camp_tot[cn]:9.0f} {_cpl(e_sp, e_rg):>9} {_cpl(l_sp, l_rg):>9}")

    # -- 1b: per-(campaign, ad) climbers ---------------------------------------
    arows = g._get_all(f"{acct}/insights", {
        "level": "ad", "fields": "ad_id,ad_name,campaign_name,spend,actions",
        "time_increment": "1", "date_preset": "last_14d", "limit": "600"})
    ad_daily = defaultdict(lambda: defaultdict(lambda: [0.0, 0.0]))   # (camp,name)->date->[sp,rg]
    ad_tot = defaultdict(float)
    for r in arows:
        key = (r.get("campaign_name", "?"), r.get("ad_name", "?"))
        d = r.get("date_start")
        sp = float(r.get("spend") or 0)
        ad_daily[key][d][0] += sp
        ad_daily[key][d][1] += extract_results(r.get("actions"), token)
        ad_tot[key] += sp

    def win(key, ds):
        sp = sum(ad_daily[key].get(d, [0, 0])[0] for d in ds)
        rg = sum(ad_daily[key].get(d, [0, 0])[1] for d in ds)
        return sp, rg, (sp / rg if rg else float("inf") if sp else 0.0)

    climbers = []
    for key in [k for k in ad_tot if ad_tot[k] >= 50]:
        e_sp, e_rg, e_cpl = win(key, ed)
        l_sp, l_rg, l_cpl = win(key, ld)
        if e_cpl not in (0.0, float("inf")) and l_cpl not in (0.0, float("inf")):
            delta = l_cpl - e_cpl
        elif l_cpl == float("inf") and l_sp > 5:
            delta = 9e9
        else:
            delta = -9e9
        climbers.append((delta, key, e_cpl, l_cpl, ad_tot[key], l_sp))
    climbers.sort(key=lambda x: -x[0])

    print("\n--- ads with >=RM50 spend, ranked by CPL climb (early->late half) ---")
    print(f"{'campaign':22} {'ad name':30} {'eCPL':>6} {'lCPL':>6} {'delta':>6} {'14d$':>6} {'late$':>6}")
    print("-" * 92)
    for delta, (cn, nm), e_cpl, l_cpl, tot, l_sp in climbers:
        ec = "inf" if e_cpl == float("inf") else (f"{e_cpl:.0f}" if e_cpl else "-")
        lc = "inf" if l_cpl == float("inf") else (f"{l_cpl:.0f}" if l_cpl else "-")
        dd = "UPBIG" if delta >= 9e8 else ("-" if delta <= -9e8 else f"{delta:+.0f}")
        print(f"{cn[:22]:22} {nm[:30]:30} {ec:>6} {lc:>6} {dd:>6} {tot:6.0f} {l_sp:6.0f}")

    # ══════════════════════════════════════════════════════════════════════════
    # TASK 2 — rejected / with-issues ads (with the exact policy reason)
    # ══════════════════════════════════════════════════════════════════════════
    print("\n\n" + "=" * 80)
    print("TASK 2 · REJECTED ADS  (copy vs video — exact policy reason)")
    print("=" * 80)
    ads = g._get_all(f"{acct}/ads", {
        "fields": "name,effective_status,issues_info,ad_review_feedback,"
                  "campaign{name},creative{id,body,title,video_id,image_hash}",
        "limit": "400"})
    bad = [a for a in ads if a.get("issues_info") or a.get("ad_review_feedback")
           or a.get("effective_status") in ("DISAPPROVED", "WITH_ISSUES", "PENDING_REVIEW")]
    print(f"\n{len(ads)} ads total · {len(bad)} rejected/with-issues\n")
    for a in bad:
        cr = a.get("creative") or {}
        kind = "VIDEO" if cr.get("video_id") else ("IMAGE" if cr.get("image_hash") else "post")
        camp = (a.get("campaign") or {}).get("name", "?")
        body = cr.get("body") or ""
        inc = _income_hits(body + " " + (cr.get("title") or ""))
        print(f"\n# {a.get('name')}   [{a.get('effective_status')}]  ({kind})  in {camp}")
        if a.get("ad_review_feedback"):
            print(f"    REVIEW_FEEDBACK: {a.get('ad_review_feedback')}")
        for iss in a.get("issues_info") or []:
            print(f"    issue: {iss.get('error_summary')} — {iss.get('error_message')}")
        print(f"    income-claim phrases in copy: {inc if inc else 'NONE FOUND'}")
        print(f"    COPY: {body[:700].replace(chr(10), ' / ')}")

    # ══════════════════════════════════════════════════════════════════════════
    # TASK 3 — Singapore candidates
    # ══════════════════════════════════════════════════════════════════════════
    print("\n\n" + "=" * 80)
    print("TASK 3 · SINGAPORE CANDIDATES  (buyers · kind · income/MY flag · campaign)")
    print("=" * 80)
    buyers = defaultdict(int)
    try:
        values = SheetsClient(s.secrets.google_sa_json).read_tab(
            s.cpa.spreadsheet_id, s.cpa.sales_tab)
        sales, _c, _h = cpa.parse_sales(values, s.cpa.price_myr)
        for sale in sales:
            if sale.ad:
                buyers[cpa.norm(sale.ad)] += 1
    except Exception as exc:  # noqa: BLE001
        print("  (Paid Student List unavailable:", exc, ")")

    # dedupe by creative name; ACTIVE status + richest body win
    seen = {}
    for a in ads:
        nm = a.get("name", "")
        key = cpa.norm(nm)
        cr = a.get("creative") or {}
        body = (cr.get("body") or "") + " " + (cr.get("title") or "")
        kind = "VIDEO" if cr.get("video_id") else ("IMAGE" if cr.get("image_hash") else "post")
        camp = (a.get("campaign") or {}).get("name", "?")
        cur = seen.get(key)
        if not cur or (a.get("effective_status") == "ACTIVE") or (len(body) > len(cur["body"])):
            seen[key] = {"name": nm, "buyers": buyers.get(key, 0), "kind": kind,
                         "body": body, "camp": camp, "status": a.get("effective_status")}

    print(f"\n{'creative name':40} {'buys':>4} {'kind':>6} {'income?':>18} {'MY?':>6}  in-SG-already?")
    print("-" * 100)
    for r in sorted(seen.values(), key=lambda r: -r["buyers"]):
        inc = _income_hits(r["body"])
        myh = _my_hits(r["body"])
        in_sg = "YES" if "[SG]" in r["camp"].upper() else ""
        inc_s = (",".join(inc))[:18] if inc else "clean"
        my_s = (",".join(myh))[:6] if myh else "-"
        print(f"{r['name'][:40]:40} {r['buyers']:>4} {r['kind']:>6} {inc_s:>18} {my_s:>6}  {in_sg}")

    print("\nDONE.")


if __name__ == "__main__":
    main()
