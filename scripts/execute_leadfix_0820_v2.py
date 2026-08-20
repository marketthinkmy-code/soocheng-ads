# -*- coding: utf-8 -*-
"""Lead-fix 8/20 v2 — split into what is safe to do now vs what needs the owner.

PART 1 (writes when CONFIRM=true) — unambiguous, validated by the v1 dry-run:
  MY: pin every «trading早就» ad PAUSED (stored status) ·
      TRAVEL campaign 120247524817830575 ×0.7
  SG: pin every «不选forex» ad PAUSED ·
      halve «[SG] STOCKBLOOM | BROAD | 1-1-3 B» (街头突击采访, no seller shares it)

PART 2 (read-only, always) — full carrier map for the five revive-dependent
targets (MY 炒过那么多 / MY 你敢吗 / MY 用我的方法 / SG 你敢吗 / SG 我只有一个目的):
every campaign carrying the name with status, budget, 30d/14d spend, and sibling
ads — because the v1 dry-run found their top carriers PAUSED, which contradicts
the 8/19 audit; the owner decides revive+scale vs skip.

⚠️ ONE-SHOT for the two scales — never rerun blind.
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
N = cpa.norm

MY_TRAVEL_ID = "120247524817830575"          # real TRAVEL (v1-validated ×0.7 target)
SG_BROAD_B = "[SG] STOCKBLOOM | BROAD | 1-1-3 B"

PIN_PAUSE = {"MY": ["video 5：trading 早就不是这样了！"],
             "SG": ["video 12：不选 forex 不选黄金"]}
DIAG = {"MY": ["video 12：炒过那么多，累而且不稳定", "video 2：你敢吗？",
               "video 1: 用我的方法，你也可以有将多"],
        "SG": ["video 2：你敢吗？", "video 2: 我只有一个目的"]}


def spend_map(g, acct, days):
    out = {}
    since = (TODAY - dt.timedelta(days=days)).isoformat()
    for r in g.account_insights(acct, level="ad", fields="ad_name,campaign_id,spend",
                                time_range={"since": since, "until": TODAY.isoformat()}):
        key = (N(r.get("ad_name") or ""), r.get("campaign_id"))
        out[key] = out.get(key, 0.0) + float(r.get("spend") or 0)
    return out


def main() -> None:
    mode = "APPLY (CONFIRM=true)" if CONFIRM else "DRY-RUN"
    print(f"Lead-fix v2 — part1 {mode} + part2 diagnostics\n")

    for label, cfg in (("MY", "config.yaml"), ("SG", "config.sg.yaml")):
        s = load_settings(REPO_ROOT / "config" / cfg)
        g = graph_client(s)
        acct = s.meta.account_path
        print(f"═══ [{label}] {acct} ═══")
        try:
            ads = g._get_all(
                f"{acct}/ads",
                {"fields": "id,name,status,effective_status,"
                           "campaign{id,name,effective_status,daily_budget}",
                 "limit": "300"})
            time.sleep(2)
            sp30 = spend_map(g, acct, 30)
            time.sleep(2)
            sp14 = spend_map(g, acct, 14)
            time.sleep(2)

            # ── PART 1a: pin pauses (stored status, catches dormant instances) ──
            for tgt in PIN_PAUSE[label]:
                hits = [a for a in ads if N(a.get("name") or "") == N(tgt)
                        and a.get("status") == "ACTIVE"]
                if not hits:
                    print(f"  · pin «{tgt[:30]}»: no stored-ACTIVE instance — done already")
                for a in hits:
                    c = a.get("campaign") or {}
                    line = (f"ad {a['id']} «{a.get('name')}» in «{c.get('name')}» "
                            f"[eff {a.get('effective_status')}]")
                    if CONFIRM:
                        g.update_status(a["id"], "PAUSED")
                        print(f"  ⏸ pinned PAUSED {line}")
                        time.sleep(PACE)
                    else:
                        print(f"  ▶ would pin PAUSED {line}")

            # ── PART 1b: the two v1-validated budget moves ──
            camp_by_id = {}
            for a in ads:
                c = a.get("campaign") or {}
                if c.get("id"):
                    camp_by_id[c["id"]] = c
            if label == "MY":
                c = camp_by_id.get(MY_TRAVEL_ID)
                cur = int((c or {}).get("daily_budget") or 0)
                if not c or c.get("effective_status") != "ACTIVE" or not cur:
                    print(f"  ⛔ TRAVEL ×0.7 skipped — {MY_TRAVEL_ID} state changed: "
                          f"{(c or {}).get('effective_status')} budget={cur}")
                else:
                    new = int(round(cur * 0.7 / 100.0)) * 100
                    if CONFIRM:
                        g._request("POST", MY_TRAVEL_ID, data={"daily_budget": new})
                        print(f"  💰 TRAVEL «{c.get('name')}» RM{cur/100:.0f} → RM{new/100:.0f}/day (×0.7)")
                        time.sleep(PACE)
                    else:
                        print(f"  ▶ would scale TRAVEL RM{cur/100:.0f} → RM{new/100:.0f}/day (×0.7)")
            else:
                c = next((c for c in camp_by_id.values() if c.get("name") == SG_BROAD_B), None)
                cur = int((c or {}).get("daily_budget") or 0)
                if not c or c.get("effective_status") != "ACTIVE" or not cur:
                    print(f"  ⛔ BROAD B halve skipped — state changed: "
                          f"{(c or {}).get('effective_status')} budget={cur}")
                else:
                    new = int(round(cur * 0.5 / 100.0)) * 100
                    if CONFIRM:
                        g._request("POST", c["id"], data={"daily_budget": new})
                        print(f"  💰 halved «{c.get('name')}» RM{cur/100:.0f} → RM{new/100:.0f}/day")
                        time.sleep(PACE)
                    else:
                        print(f"  ▶ would halve «{c.get('name')}» RM{cur/100:.0f} → RM{new/100:.0f}/day")

            # ── PART 2: carrier diagnostics for the revive-dependent targets ──
            print(f"\n  ▍诊断：加钱/重开目标的所有 carrier（campaign 状态 · 预算 · 30d/14d 花费）")
            for tgt in DIAG[label]:
                nt = N(tgt)
                print(f"  ● «{tgt}»")
                seen = set()
                for a in ads:
                    if N(a.get("name") or "") != nt:
                        continue
                    c = a.get("campaign") or {}
                    cid = c.get("id")
                    if not cid or cid in seen:
                        continue
                    seen.add(cid)
                    cur = int(c.get("daily_budget") or 0)
                    print(f"     [{c.get('effective_status'):>15}] «{c.get('name')}» ({cid})"
                          f"  RM{cur/100:.0f}/day  spend30={sp30.get((nt, cid), 0):7.0f}"
                          f"  spend14={sp14.get((nt, cid), 0):7.0f}"
                          f"  ad status={a.get('status')}/{a.get('effective_status')}")
                    sibs = [f"«{(x.get('name') or '')[:26]}»[{x.get('status')}]"
                            for x in ads
                            if (x.get('campaign') or {}).get('id') == cid
                            and N(x.get('name') or '') != nt]
                    if sibs:
                        print(f"        同 campaign 其他广告: {', '.join(sibs[:6])}")
                if not seen:
                    print(f"     (账上没有任何该名字的广告实例)")
        except Exception as e:
            print(f"  ❌ [{label}] {str(e)[:140]} — continuing")
        print()

    print("PART1 EXECUTED + diagnostics above — owner decides the revive set."
          if CONFIRM else "DRY-RUN — part1 pending confirm; diagnostics above.")


if __name__ == "__main__":
    main()
