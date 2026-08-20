# -*- coding: utf-8 -*-
"""Owner 2026-08-20 «执行» — the lead-quality fix list from the 8/19 audit:

MY: pause trading早就 ads · TRAVEL TOP3 (炒过那么多) ×1.5 · RUNNING (你敢吗) ×1.3
    · TRAVEL (盖电脑) ×0.7 · reactivate 用我的方法 chain
SG: pause 不选forex ads · RUNNING (你敢吗) ×1.3 · GOLF (我只有一个目的) ×1.5
    · 街头突击采访 halve ONLY if its campaign shares no active seller (else report)

Campaign targets are resolved at runtime as "the campaign where that ad name spent
the most in the last 30d" — never hardcoded ids. Every action prints old→new and is
individually try/except'd. ⚠️ ONE-SHOT: budget scales are NOT idempotent — never
rerun this blind; on partial failure write a targeted follow-up for the missed
actions only. Dry-run unless CONFIRM=true.
"""
from __future__ import annotations

import datetime as dt
import os
import time

from adbot import cpa
from adbot.commands import graph_client
from adbot.settings import REPO_ROOT, load_settings

CONFIRM = os.environ.get("CONFIRM", "").lower() in ("1", "true", "yes")
PACE = 8.0
TODAY = dt.date(2026, 8, 20)
D30 = (TODAY - dt.timedelta(days=30)).isoformat()

N = cpa.norm
SG_SELLERS = {N(x) for x in (
    "freestyle: korea", "freestyle 1", "video 5：trading 早就不是这样了！",
    "video 1：用我的方法", "video 2：你敢吗？", "video 11：office 突访",
    "video 2: 我只有一个目的", "video 5：盖电脑，喂！",
    "video 12：炒过那么多，累而且不稳定")}

PLAN = {
    "MY": {
        "cfg": "config.yaml",
        "pause_ads": ["video 5：trading 早就不是这样了！"],
        "scales": [("video 12：炒过那么多，累而且不稳定", 1.5),
                   ("video 2：你敢吗？", 1.3),
                   ("video 5：盖电脑，喂！", 0.7)],
        "reactivate": "video 1: 用我的方法，你也可以有将多",
        "halve_if_alone": None,
    },
    "SG": {
        "cfg": "config.sg.yaml",
        "pause_ads": ["video 12：不选 forex 不选黄金"],
        "scales": [("video 2：你敢吗？", 1.3),
                   ("video 2: 我只有一个目的", 1.5)],
        "reactivate": None,
        "halve_if_alone": "video 6：街头突击采访！",
    },
}


def main() -> None:
    mode = "APPLY (CONFIRM=true)" if CONFIRM else "DRY-RUN (set confirm=true to apply)"
    print(f"Lead-quality fix 8/20 — {mode}\n")

    for label in ("MY", "SG"):
        p = PLAN[label]
        s = load_settings(REPO_ROOT / "config" / p["cfg"])
        g = graph_client(s)
        acct = s.meta.account_path
        print(f"═══ [{label}] {acct} ═══")
        try:
            spend30 = {}   # norm ad name -> {campaign_id: spend}
            for r in g.account_insights(
                    acct, level="ad", fields="ad_name,campaign_id,campaign_name,spend",
                    time_range={"since": D30, "until": TODAY.isoformat()}):
                name = N(r.get("ad_name") or "")
                cid = r.get("campaign_id")
                if name and cid:
                    spend30.setdefault(name, {})
                    spend30[name][cid] = spend30[name].get(cid, 0.0) + float(r.get("spend") or 0)
            time.sleep(2)
            camp_info = {c["id"]: c for c in g._get_all(
                f"{acct}/campaigns",
                {"fields": "id,name,effective_status,daily_budget", "limit": "500"})}
            time.sleep(2)
            ads = g._get_all(
                f"{acct}/ads",
                {"fields": "id,name,effective_status,adset_id,campaign{id,name}",
                 "limit": "300"})
            time.sleep(2)

            def top_campaign(ad_name: str):
                per = spend30.get(N(ad_name)) or {}
                if not per:
                    return None
                cid = max(per, key=per.get)
                return cid, per[cid]

            # ── 1) ad-level pauses ────────────────────────────────────────────
            for tgt in p["pause_ads"]:
                hits = [a for a in ads
                        if N(a.get("name") or "") == N(tgt)
                        and a.get("effective_status") == "ACTIVE"]
                if not hits:
                    print(f"  · pause «{tgt}»: no ACTIVE instance found — nothing to do")
                for a in hits:
                    camp = (a.get("campaign") or {}).get("name", "?")
                    if CONFIRM:
                        g.update_status(a["id"], "PAUSED")
                        print(f"  ⏸ paused ad {a['id']} «{a.get('name')}» in «{camp}»")
                        time.sleep(PACE)
                    else:
                        print(f"  ▶ would pause ad {a['id']} «{a.get('name')}» in «{camp}»")

            # ── 2) campaign budget scales (via the ad's top-spend campaign) ──
            for tgt, factor in p["scales"]:
                hit = top_campaign(tgt)
                if not hit:
                    print(f"  ⛔ scale «{tgt}»: no 30d spend found — skipping")
                    continue
                cid, sp = hit
                c = camp_info.get(cid) or {}
                cur = int(c.get("daily_budget") or 0)
                st_ok = c.get("effective_status") in ("ACTIVE", "IN_PROCESS")
                if not cur or not st_ok:
                    print(f"  ⛔ scale «{tgt}»: campaign «{c.get('name')}» "
                          f"[{c.get('effective_status')}] budget={cur} — skipping")
                    continue
                new = int(round(cur * factor / 100.0)) * 100
                line = (f"campaign «{c.get('name')}» ({cid})  "
                        f"RM{cur/100:.0f} → RM{new/100:.0f}/day  (×{factor}, "
                        f"driver «{tgt[:24]}» 30d spend {sp:.0f})")
                if CONFIRM:
                    g._request("POST", cid, data={"daily_budget": new})
                    print(f"  💰 scaled {line}")
                    time.sleep(PACE)
                else:
                    print(f"  ▶ would scale {line}")

            # ── 3) conditional halve (only if no other seller shares the CBO) ─
            if p["halve_if_alone"]:
                tgt = p["halve_if_alone"]
                hit = top_campaign(tgt)
                if not hit:
                    print(f"  ⛔ halve «{tgt}»: no 30d spend — skipping")
                else:
                    cid, sp = hit
                    c = camp_info.get(cid) or {}
                    mates = {N(a.get("name") or "") for a in ads
                             if (a.get("campaign") or {}).get("id") == cid
                             and a.get("effective_status") == "ACTIVE"
                             and N(a.get("name") or "") != N(tgt)}
                    shared = sorted(m for m in mates if m in SG_SELLERS)
                    if shared:
                        print(f"  ⚠️ halve «{tgt}» SKIPPED — campaign «{c.get('name')}» "
                              f"shares CBO with seller(s): {shared} (owner decides)")
                    else:
                        cur = int(c.get("daily_budget") or 0)
                        if not cur:
                            print(f"  ⛔ halve «{tgt}»: no campaign daily_budget — skipping")
                        else:
                            new = int(round(cur * 0.5 / 100.0)) * 100
                            if CONFIRM:
                                g._request("POST", cid, data={"daily_budget": new})
                                print(f"  💰 halved «{c.get('name')}» RM{cur/100:.0f}"
                                      f" → RM{new/100:.0f}/day")
                                time.sleep(PACE)
                            else:
                                print(f"  ▶ would halve «{c.get('name')}» "
                                      f"RM{cur/100:.0f} → RM{new/100:.0f}/day")

            # ── 4) reactivate chain (campaign → adsets → ads) ─────────────────
            if p["reactivate"]:
                tgt = p["reactivate"]
                hit = top_campaign(tgt)
                if not hit:
                    print(f"  ⛔ reactivate «{tgt}»: no 30d spend anywhere — report only")
                else:
                    cid, sp = hit
                    c = camp_info.get(cid) or {}
                    print(f"  reactivating chain of «{c.get('name')}» ({cid}) "
                          f"[{c.get('effective_status')}] — 30d spend {sp:.0f}")
                    if CONFIRM:
                        if c.get("effective_status") != "ACTIVE":
                            g.update_status(cid, "ACTIVE")
                            print(f"   ▶ campaign → ACTIVE")
                            time.sleep(PACE)
                        for aset in g._get_all(f"{cid}/adsets",
                                               {"fields": "id,name,status", "limit": "10"}):
                            if aset.get("status") != "ACTIVE":
                                g.update_status(aset["id"], "ACTIVE")
                                print(f"   ▶ adset «{aset.get('name')}» → ACTIVE")
                                time.sleep(PACE)
                        for a in g._get_all(f"{cid}/ads",
                                            {"fields": "id,name,status", "limit": "20"}):
                            if a.get("status") != "ACTIVE":
                                g.update_status(a["id"], "ACTIVE")
                                print(f"   ▶ ad «{a.get('name')}» → ACTIVE")
                                time.sleep(PACE)
                        print(f"   ✅ chain live")
                    else:
                        print(f"   ▶ would flip campaign/adsets/ads to ACTIVE as needed")
        except Exception as e:
            print(f"  ❌ [{label}] {str(e)[:140]} — continuing")
        print()

    print("EXECUTED — verify in Ads Manager; CPL monitor keeps watching."
          if CONFIRM else "DRY-RUN — review plan, then confirm=true (ONE-SHOT).")


if __name__ == "__main__":
    main()
