# -*- coding: utf-8 -*-
"""Owner 2026-09-19「全部听你的。Scale 的话，+20% budget 就好」— execute the
Fri→now CPL×CPA verdicts exactly as reported:

  关 (ad-level pause, 6):
    MY 🌟盖电脑 @ 🌟DAY TRADING (RM403/0reg wknd, CPA-rescue was shielding it)
    MY 盖电脑 @ 🌟PURCHASE LAL 5% (CPL 98, no sales; CBO untouched for 赚美金)
    MY HOOK V8 @ BEER ALCOHOL (CPL 197)
    SG 盖电脑 @ TRAVEL (RM166/0reg)
    SG freestyle 1 @ 🌟PRIORITY BANKING (CPL 193, position never sold)
    SG 拼接 V1 @ GOLF 0914 (CPL 194; the MY DT twin at CPL 36 stays)
  scale (+20% on the ad's budget carrier — adset else CBO campaign, 5):
    MY HOOK V8 @ BROAD 0911 (CPL 35) · MY 拼接 V1 @ DT 30-55 (CPL 36) ·
    MY 🌟你敢吗 @ 🌟LAL 1-5% (CPL 54/CPA 636) · SG HOOK 不选 @ GOLF 0914 (CPL 25) ·
    SG 用我的方法 @ LUXURY GOODS (CPL 76/CPA 705)

Kills run BEFORE scales so a bumped shared adset never feeds a just-killed ad.
Targets resolved by exact raw ad name + campaign substring/🌟 + Fri-window spend;
ambiguity -> SKIP, never guess. Scale is idempotent via a per-day
ADBOT_SCALE20_<date> label on the carrier. CONFIRM gate; verify pass at the end."""
from __future__ import annotations

import datetime as dt
import os
import time

from adbot.commands import graph_client
from adbot.settings import REPO_ROOT, load_settings

CONFIRM = os.environ.get("CONFIRM", "").lower() in ("1", "true", "yes")
PACE = 2.5
SINCE = "2026-09-18"
SCALE_PCT = 0.20
LABEL_PREFIX = "ADBOT_SCALE20_"

# (ad raw name, campaign substring, campaign starts with 🌟, expected Fri-window spend RM)
KILLS = {
    "config.yaml": [
        ("🌟 video 5：盖电脑，喂！", "DAY TRADING", True, 403),
        ("video 5：盖电脑，喂！", "PURCHASE LAL 5%", True, 294),
        ("HOOK：Video 8：做么你 Trading 不用看盘的？", "BEER ALCOHOL", False, 197),
    ],
    "config.sg.yaml": [
        ("video 5：盖电脑，喂！", "| TRAVEL |", False, 166),
        ("freestyle 1", "PRIORITY", True, 193),
        ("拼接：Video 1：用我的方法", "GOLF", False, 194),
    ],
}
SCALES = {
    "config.yaml": [
        ("HOOK：Video 8：做么你 Trading 不用看盘的？", "BROAD MY 25+ | 0911", False, 420),
        ("拼接：Video 1：用我的方法", "DAY TRADING 30-55", False, 181),
        ("🌟 video 2：你敢吗？", "PURCHASE LAL 1-5%", True, 268),
    ],
    "config.sg.yaml": [
        ("HOOK：Video 12：不选 forex 不选黄金", "GOLF", False, 198),
        ("video 1：用我的方法", "LUXURY GOO", False, 303),
    ],
}


def resolve(ads, win, ad_raw, csub, cstar, sp_exp):
    tol = max(40.0, 0.25 * sp_exp)
    hits = []
    for a in ads:
        cname = (a.get("campaign") or {}).get("name") or ""
        if ((a.get("name") or "").strip() == ad_raw and csub in cname
                and cname.startswith("🌟") == cstar
                and abs(float((win.get(a["id"]) or {}).get("spend") or 0) - sp_exp) <= tol):
            hits.append(a)
    return hits


def main() -> None:
    mode = "APPLY" if CONFIRM else "DRY-RUN"
    today = (dt.datetime.utcnow() + dt.timedelta(hours=8)).date()
    print(f"CPA/CPL actions 0919（owner「全部听你的，scale +20%」）— {mode}\n")

    touched = []
    for cfg in ("config.yaml", "config.sg.yaml"):
        label = "MY" if cfg == "config.yaml" else "SG"
        s = load_settings(REPO_ROOT / "config" / cfg)
        g = graph_client(s)
        ads = g._get_all(
            f"{s.meta.account_path}/ads",
            {"fields": "id,name,status,effective_status,"
                       "campaign{id,name,daily_budget},adset{id,name,daily_budget}",
             "limit": "500"})
        time.sleep(1.2)
        win = {r.get("ad_id"): r for r in g.account_insights(
            s.meta.account_path, level="ad", fields="ad_id,spend",
            time_range={"since": SINCE, "until": today.isoformat()})}
        time.sleep(1.2)
        print(f"═══ [{label}] ═══")

        for ad_raw, csub, cstar, sp_exp in KILLS.get(cfg, []):
            hits = resolve(ads, win, ad_raw, csub, cstar, sp_exp)
            if len(hits) != 1:
                print(f"  ⚠️ SKIP 关 «{ad_raw[:30]}» ({csub}): {len(hits)} 个匹配")
                continue
            a = hits[0]
            desc = f"关 ad «{ad_raw[:32]}» @ «{(a['campaign'].get('name') or '')[:36]}»"
            if a.get("status") == "PAUSED":
                print(f"  ＝ 已是关的 {desc}")
                continue
            if CONFIRM:
                g.update_status(a["id"], "PAUSED")
                time.sleep(PACE)
                print(f"  ✔ {desc}")
                touched.append((cfg, "ad", a["id"], ad_raw))
            else:
                print(f"  [dry] {desc}")

        done_carriers = set()
        for ad_raw, csub, cstar, sp_exp in SCALES.get(cfg, []):
            hits = resolve(ads, win, ad_raw, csub, cstar, sp_exp)
            if len(hits) != 1:
                print(f"  ⚠️ SKIP scale «{ad_raw[:30]}» ({csub}): {len(hits)} 个匹配")
                continue
            a = hits[0]
            aset, camp = a.get("adset") or {}, a.get("campaign") or {}
            carrier = aset if aset.get("daily_budget") else camp
            kind = "adset" if aset.get("daily_budget") else "campaign"
            if carrier.get("id") in done_carriers:
                print(f"  ＝ 载体已加过（同 {kind}）«{ad_raw[:30]}»")
                continue
            cur = int(carrier.get("daily_budget") or 0)
            if cur <= 0:
                print(f"  ⚠️ SKIP scale «{ad_raw[:30]}»: {kind} 无 daily_budget")
                continue
            info = g.get_object(carrier["id"], fields="adlabels{id,name}")
            raw_l = info.get("adlabels") or {}
            labels = raw_l.get("data", []) if isinstance(raw_l, dict) else raw_l
            if any((l.get("name") or "").startswith(f"{LABEL_PREFIX}{today}")
                   for l in labels):
                print(f"  ＝ 今天已加过 «{ad_raw[:30]}» 的 {kind}")
                done_carriers.add(carrier.get("id"))
                continue
            new = int(round(cur * (1 + SCALE_PCT) / 100.0) * 100)
            desc = (f"scale {kind} of «{ad_raw[:30]}» @ «{(camp.get('name') or '')[:32]}» "
                    f"RM{cur / 100:.0f} → RM{new / 100:.0f} (+20%)")
            if CONFIRM:
                lid = g.get_or_create_label(s.meta.account_path,
                                            f"{LABEL_PREFIX}{today}")
                g.set_ad_labels(carrier["id"], [l["id"] for l in labels] + [lid])
                time.sleep(PACE)
                g.update_daily_budget(carrier["id"], new)
                time.sleep(PACE)
                print(f"  ✔ {desc}")
                touched.append((cfg, kind, carrier["id"], ad_raw))
            else:
                print(f"  [dry] {desc}")
            done_carriers.add(carrier.get("id"))
        print()

    if CONFIRM and touched:
        print("── 复核 ──")
        for cfg, kind, eid, name in touched:
            s = load_settings(REPO_ROOT / "config" / cfg)
            g = graph_client(s)
            fields = "effective_status" if kind == "ad" else "daily_budget,status"
            o = g.get_object(eid, fields=fields)
            time.sleep(1.0)
            if kind == "ad":
                print(f"  «{name[:32]}» → {o.get('effective_status')}")
            else:
                print(f"  «{name[:32]}» 载体 → RM{int(o.get('daily_budget') or 0) / 100:.0f}/天 "
                      f"({o.get('status')})")
    print("\n0919 ACTIONS DONE")


if __name__ == "__main__":
    main()
