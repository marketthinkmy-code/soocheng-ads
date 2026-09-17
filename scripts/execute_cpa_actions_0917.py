# -*- coding: utf-8 -*-
"""Owner 2026-09-18 approval of the 0917 per-ad CPA report:「全部照你建议做」+
「我刚开回 MY 13 个 campaign，你可以照你建议做了」.

Actions (exactly the report's recommendations, nothing more):
  SG  open:  🌟freestyle 1 @ 🌟BROAD (CPA510) · freestyle 1 @ 🌟PURCHASE LAL (558) ·
             freestyle: korea @ BROAD (880) · 🌟我只有一个目的 @ 🌟GOLF (563) ·
             用我的方法 @ LUXURY GOODS (665) · 用我的方法 @ 🌟INVESTMENT (731) ·
             盖电脑 @ TRAVEL (667, adset 级)
  SG  scale: 🌟GOLF campaign budget +30% (trading早就 CPA618, label-guarded)
  MY  open:  🌟你敢吗 @ 🌟PURCHASE LAL 1-5% (546 instance) · freestyle 1 @ BUSINESS OWNER (847)
  MY  ensure-delivering (owner's 13-campaign reopen should cover): korea @ BROAD MY 25+ ·
             🌟盖电脑 @ 🌟DAY TRADING

Mechanics: each target = "make this ad deliver" — open its ad/adset/campaign layers
only where the layer's OWN status is PAUSED. Any NON-target ad that would newly start
delivering because of a layer I open is ad-level paused first (唯一开回路径 = owner
点名 — un-named ads must not ride along; run-257 precedent). Ads the owner's own
reopen already made live are untouched. Targets resolved by exact raw ad name +
campaign substring/🌟 + 60d-spend proximity; ambiguity -> SKIP, never guess.
CONFIRM gate; idempotent (re-run opens nothing twice; budget bump label-guarded)."""
from __future__ import annotations

import datetime as dt
import os
import time

from adbot.commands import graph_client
from adbot.settings import REPO_ROOT, load_settings

CONFIRM = os.environ.get("CONFIRM", "").lower() in ("1", "true", "yes")
PACE = 2.5

# (ad raw name, campaign substring, campaign starts with 🌟, expected 60d spend RM)
TARGETS = {
    "config.sg.yaml": [
        ("🌟 freestyle 1", "| BROAD", True, 2549),
        ("freestyle 1", "PURCHASE L", True, 1674),
        ("freestyle: korea", "| BROAD", False, 7037),
        ("🌟 video 2: 我只有一个目的", "GOLF", True, 3380),
        ("video 1：用我的方法", "LUXURY GOODS", False, 1996),
        ("video 1：用我的方法", "INVESTMENT", True, 2925),
        ("video 5：盖电脑，喂！", "| TRAVEL |", False, 2668),
    ],
    "config.yaml": [
        ("🌟 video 2：你敢吗？", "PURCHASE LAL 1-5%", True, 1639),
        ("freestyle 1", "BUSINESS OWNER", False, 4234),
        ("freestyle: korea", "BROAD MY 25+", False, 1330),
        ("🌟 video 5：盖电脑，喂！", "DAY TRADING", True, 3030),
    ],
}
SCALE_AD = "video 5：trading 早就不是这样了！"   # its 🌟GOLF campaign gets +30%
SCALE_PCT = 0.30
SCALE_LABEL_PREFIX = "ADBOT_SCALE30_"


def act(g, entity_id: str, status: str, desc: str) -> None:
    if CONFIRM:
        g.update_status(entity_id, status)
        time.sleep(PACE)
        print(f"  ✔ {desc}")
    else:
        print(f"  [dry] {desc}")


def main() -> None:
    mode = "APPLY" if CONFIRM else "DRY-RUN"
    today = (dt.datetime.utcnow() + dt.timedelta(hours=8)).date()
    d60 = today - dt.timedelta(days=60)
    print(f"CPA actions 0917（owner「全部照你建议做」）— {mode}\n")

    for cfg, targets in TARGETS.items():
        label = "SG" if "sg" in cfg else "MY"
        s = load_settings(REPO_ROOT / "config" / cfg)
        g = graph_client(s)
        ads = g._get_all(
            f"{s.meta.account_path}/ads",
            {"fields": "id,name,status,effective_status,"
                       "campaign{id,name,status,daily_budget},"
                       "adset{id,name,status,daily_budget}",
             "limit": "500"})
        time.sleep(1.2)
        sp60 = {r.get("ad_id"): float(r.get("spend") or 0)
                for r in g.account_insights(
                    s.meta.account_path, level="ad", fields="ad_id,spend",
                    time_range={"since": d60.isoformat(), "until": today.isoformat()})}
        time.sleep(1.2)

        print(f"═══ [{label}] ═══")
        resolved = []
        for ad_raw, csub, cstar, sp_exp in targets:
            tol = max(60.0, 0.15 * sp_exp)
            hits = []
            for a in ads:
                camp = a.get("campaign") or {}
                if (a.get("name") or "").strip() != ad_raw:
                    continue
                cname = camp.get("name") or ""
                if csub not in cname or cname.startswith("🌟") != cstar:
                    continue
                if abs(sp60.get(a["id"], 0.0) - sp_exp) > tol:
                    continue
                hits.append(a)
            if len(hits) != 1:
                print(f"  ⚠️ SKIP «{ad_raw}» ({csub}): {len(hits)} 个匹配，不猜。")
                continue
            resolved.append(hits[0])
            print(f"  目标 «{ad_raw}» @ «{(hits[0]['campaign'].get('name') or '')[:40]}» "
                  f"(effective {hits[0].get('effective_status')})")

        target_ids = {a["id"] for a in resolved}
        open_ads = [a for a in resolved if a.get("status") != "ACTIVE"]
        open_adsets, open_camps = {}, {}
        for a in resolved:
            aset, camp = a.get("adset") or {}, a.get("campaign") or {}
            if aset.get("status") == "PAUSED":
                open_adsets[aset["id"]] = aset
            if camp.get("status") == "PAUSED":
                open_camps[camp["id"]] = camp

        # non-target ads that would NEWLY deliver because of the layers we open
        neutralize = []
        for a in ads:
            if a["id"] in target_ids or a.get("status") != "ACTIVE":
                continue
            aset, camp = a.get("adset") or {}, a.get("campaign") or {}
            set_live = aset.get("status") == "ACTIVE" or aset.get("id") in open_adsets
            camp_live = camp.get("status") == "ACTIVE" or camp.get("id") in open_camps
            was_live = aset.get("status") == "ACTIVE" and camp.get("status") == "ACTIVE"
            if set_live and camp_live and not was_live:
                neutralize.append(a)

        for a in neutralize:
            act(g, a["id"], "PAUSED",
                f"NEUTRALIZE ad «{(a.get('name') or '')[:34]}» @ "
                f"«{(a['campaign'].get('name') or '')[:34]}»（未点名，不跟车）")
        for a in open_ads:
            act(g, a["id"], "ACTIVE", f"OPEN ad «{(a.get('name') or '')[:40]}»")
        for aset in open_adsets.values():
            act(g, aset["id"], "ACTIVE", f"OPEN adset «{(aset.get('name') or '')[:40]}»")
        for camp in open_camps.values():
            act(g, camp["id"], "ACTIVE", f"OPEN campaign «{(camp.get('name') or '')[:40]}»")
        already = [a for a in resolved
                   if a.get("status") == "ACTIVE" and not (
                       (a.get("adset") or {}).get("id") in open_adsets
                       or (a.get("campaign") or {}).get("id") in open_camps)
                   and a.get("effective_status") == "ACTIVE"]
        for a in already:
            print(f"  ＝ 已在跑（owner 已开）«{(a.get('name') or '')[:40]}»")

        if label == "SG":
            hosts = [a for a in ads
                     if (a.get("name") or "").strip() == SCALE_AD
                     and (a.get("campaign") or {}).get("name", "").startswith("🌟")
                     and "GOLF" in (a.get("campaign") or {}).get("name", "")]
            if len(hosts) != 1:
                print(f"  ⚠️ SCALE SKIP: trading早就 @ 🌟GOLF 匹配 {len(hosts)} 个")
            else:
                camp = hosts[0]["campaign"]
                carrier = (camp if camp.get("daily_budget")
                           else hosts[0].get("adset") or {})
                kind = "campaign" if camp.get("daily_budget") else "adset"
                cur = int(carrier.get("daily_budget") or 0)
                info = g.get_object(carrier["id"], fields="adlabels{id,name}")
                labels = (info.get("adlabels") or {}).get("data", []) \
                    if isinstance(info.get("adlabels"), dict) else (info.get("adlabels") or [])
                if any((l.get("name") or "").startswith(SCALE_LABEL_PREFIX) for l in labels):
                    print(f"  ＝ SCALE 已做过（label 在），跳过")
                elif cur <= 0:
                    print(f"  ⚠️ SCALE SKIP: {kind} 无 daily_budget")
                else:
                    new = int(round(cur * (1 + SCALE_PCT) / 100.0) * 100)
                    if CONFIRM:
                        lid = g.get_or_create_label(
                            s.meta.account_path, f"{SCALE_LABEL_PREFIX}{today}")
                        g.set_ad_labels(carrier["id"],
                                        [l["id"] for l in labels] + [lid])
                        time.sleep(PACE)
                        g.update_daily_budget(carrier["id"], new)
                        time.sleep(PACE)
                        print(f"  ✔ SCALE 🌟GOLF {kind} 预算 RM{cur/100:.0f} → RM{new/100:.0f} (+30%)")
                    else:
                        print(f"  [dry] SCALE 🌟GOLF {kind} 预算 RM{cur/100:.0f} → RM{new/100:.0f} (+30%)")
        print()

    if CONFIRM:
        print("── 复核（重读每个目标 effective_status）──")
        for cfg, targets in TARGETS.items():
            s = load_settings(REPO_ROOT / "config" / cfg)
            g = graph_client(s)
            label = "SG" if "sg" in cfg else "MY"
            ads = g._get_all(
                f"{s.meta.account_path}/ads",
                {"fields": "id,name,effective_status,campaign{name}", "limit": "500"})
            time.sleep(1.2)
            for ad_raw, csub, cstar, _sp in targets:
                for a in ads:
                    cname = (a.get("campaign") or {}).get("name") or ""
                    if ((a.get("name") or "").strip() == ad_raw and csub in cname
                            and cname.startswith("🌟") == cstar):
                        print(f"  [{label}] «{ad_raw[:34]}» → {a.get('effective_status')}")
    print("\nCPA ACTIONS DONE")


if __name__ == "__main__":
    main()
