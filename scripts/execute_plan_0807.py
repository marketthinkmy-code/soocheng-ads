# -*- coding: utf-8 -*-
"""Owner-approved (2026-08-07「解禁」+「全部执行」) Ads Manager adjustments:

  reopen  MY INVESTMENT 你敢吗   (sold 8/2 + 8/5, 3d CPL RM38 — mis-killed)
  reopen  SG RUNNING 你敢吗      (sold 8/5 + 8/6; renamed campaign hides its sales
                                  from the CPA rescue — cpl_hold added in config)
  reopen  SG DAY TRADING campaign + its 炒过那么多 ad (un-banned; sold 8/5, 8 days old)
  +30%    SG BROAD A · MY INVESTMENT · SG GOLF (second step, 3 days after the first)
  pause   MY TRAVEL TOP3 campaign (all 3 ads monitor-killed — empty shell)

Same discipline as reopen_apply/budget_tilt: verify id/name/campaign/status live,
dry-run unless CONFIRM=true, each write isolated so one failure never blocks the rest.
"""
from __future__ import annotations

import os

from adbot.clients.graph import GraphError
from adbot.commands import graph_client
from adbot.settings import REPO_ROOT, load_settings

CONFIRM = (os.environ.get("CONFIRM") or "").strip().lower() in ("1", "true", "yes")

REOPEN_ADS = [
    ("MY 你敢吗 (INVESTMENT)", "config.yaml", "120247585359790575", "你敢吗", "investment"),
    ("SG 你敢吗 (RUNNING)", "config.sg.yaml", "120248232504790521", "你敢吗", "running"),
]
DAYTRADING_SG = ("config.sg.yaml", "120248577991730521", "DAY TRADING",
                 {"120248578056590521"})          # allowed wake-set: 早就不是这样了 only
CHAO_AD = ("SG 炒过那么多 (DAY TRADING)", "config.sg.yaml", "120248577931520521",
           "炒过那么多", "day trading")
BUDGET_UP = [
    ("SG BROAD A", "config.sg.yaml", "120248220658080521", "BROAD | 1-1-3 A"),
    ("MY INVESTMENT", "config.yaml", "120247585357770575", "INVESTMENT | 1-1-3"),
    ("SG GOLF", "config.sg.yaml", "120248220643620521", "GOLF"),
]
PAUSE_CAMPAIGN = ("MY TRAVEL TOP3", "config.yaml", "120247919640660575", "TRAVEL TOP3")

_clients: dict = {}


def cli(cfg):
    return _clients.setdefault(cfg, graph_client(load_settings(REPO_ROOT / "config" / cfg)))


def reopen_ad(label, cfg, ad_id, name_sub, camp_sub):
    g = cli(cfg)
    ad = g.get_object(ad_id, "id,name,effective_status,campaign{name,effective_status}")
    name, st = ad.get("name", "?"), ad.get("effective_status", "?")
    camp = (ad.get("campaign") or {}).get("name", "?")
    if name_sub not in name or camp_sub not in camp.casefold():
        print(f"⛔ SKIP {label}: id {ad_id} is '{name}' / '{camp}' — expected '{name_sub}'/'{camp_sub}'")
        return
    if st == "ACTIVE":
        print(f"✓ {label}: already ACTIVE")
        return
    if st not in ("PAUSED", "CAMPAIGN_PAUSED"):
        print(f"⚠️ SKIP {label}: effective_status={st}")
        return
    if not CONFIRM:
        print(f"▶ would ACTIVATE {label}: {name} ({camp}) [{st}]")
        return
    try:
        g.update_status(ad_id, "ACTIVE")
        after = g.get_object(ad_id, "effective_status").get("effective_status")
        print(f"✅ ACTIVATED {label}: {st} -> {after}")
    except GraphError as e:
        print(f"❌ FAILED {label}: {e}")


def main() -> None:
    mode = "APPLY (CONFIRM=true)" if CONFIRM else "DRY-RUN (set confirm=true to apply)"
    print(f"Execute plan 2026-08-07 — {mode}\n")

    print("— 重开误关的出单广告 —")
    for t in REOPEN_ADS:
        reopen_ad(*t)

    print("\n— SG DAY TRADING campaign（解禁后重开）—")
    cfg, cid, name_sub, allowed = DAYTRADING_SG
    g = cli(cfg)
    c = g.get_object(cid, "id,name,effective_status,daily_budget")
    name, st = c.get("name", "?"), c.get("effective_status", "?")
    if name_sub not in name:
        print(f"⛔ SKIP: id {cid} is '{name}'")
    elif st == "ACTIVE":
        print(f"✓ campaign already ACTIVE: {name}")
        reopen_ad(*CHAO_AD)
    elif st != "PAUSED":
        print(f"⚠️ SKIP campaign: effective_status={st}")
    else:
        ads = g._get_all(f"{cid}/ads", {"fields": "id,name,effective_status", "limit": 200})
        wake = {a["id"]: a.get("name", "?") for a in ads
                if a.get("effective_status") == "CAMPAIGN_PAUSED"}
        extra = set(wake) - allowed
        print(f"'{name}' [{st}] RM{int(c.get('daily_budget') or 0)/100:,.0f}/day — "
              f"campaign-ACTIVE wakes: {list(wake.values())}")
        if extra:
            print(f"⛔ SKIP — unexpected wake-set: {sorted(extra)}")
        elif not CONFIRM:
            print("▶ would ACTIVATE campaign, then ACTIVATE 炒过那么多 ad")
            reopen_ad(*CHAO_AD)
        else:
            try:
                g.update_status(cid, "ACTIVE")
                after = g.get_object(cid, "effective_status").get("effective_status")
                print(f"✅ campaign ACTIVATED: {st} -> {after}")
                reopen_ad(*CHAO_AD)
            except GraphError as e:
                print(f"❌ FAILED campaign: {e}")

    print("\n— 预算 +30% —")
    for label, cfg, cid, name_sub in BUDGET_UP:
        g = cli(cfg)
        c = g.get_object(cid, "id,name,effective_status,daily_budget")
        name, st = c.get("name", "?"), c.get("effective_status", "?")
        cur = int(c.get("daily_budget") or 0)
        if name_sub not in name:
            print(f"⛔ SKIP {label}: id {cid} is '{name}'")
            continue
        if cur <= 0:
            print(f"⛔ SKIP {label}: no campaign daily_budget")
            continue
        new = cur + int(cur * 0.30)
        line = f"{label}: {name} [{st}] RM{cur/100:,.0f} -> RM{new/100:,.0f}/day"
        if not CONFIRM:
            print(f"▶ would set  {line}")
            continue
        try:
            g._request("POST", cid, data={"daily_budget": new})
            after = int(g.get_object(cid, "daily_budget").get("daily_budget") or 0)
            print(f"✅ set  {line}  (verified RM{after/100:,.0f})")
        except GraphError as e:
            print(f"❌ FAILED {label}: {e}")

    print("\n— 关空壳 campaign —")
    label, cfg, cid, name_sub = PAUSE_CAMPAIGN
    g = cli(cfg)
    c = g.get_object(cid, "id,name,effective_status")
    name, st = c.get("name", "?"), c.get("effective_status", "?")
    if name_sub not in name:
        print(f"⛔ SKIP {label}: id {cid} is '{name}'")
    elif st != "ACTIVE":
        print(f"✓ {label}: already {st}")
    else:
        ads = g._get_all(f"{cid}/ads", {"fields": "id,effective_status", "limit": 200})
        live = [a["id"] for a in ads if a.get("effective_status") == "ACTIVE"]
        if live:
            print(f"⛔ SKIP {label}: {len(live)} ads still ACTIVE inside — not an empty shell")
        elif not CONFIRM:
            print(f"▶ would PAUSE {label}: {name} (all {len(ads)} ads already non-delivering)")
        else:
            try:
                g.update_status(cid, "PAUSED")
                after = g.get_object(cid, "effective_status").get("effective_status")
                print(f"✅ PAUSED {label}: {name} — now {after}")
            except GraphError as e:
                print(f"❌ FAILED {label}: {e}")


if __name__ == "__main__":
    main()
