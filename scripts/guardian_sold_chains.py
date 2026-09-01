# -*- coding: utf-8 -*-
"""Guardian · sold chains (owner 2026-09-01 «保护成交链»).

Every hour: for each Paid-Student-List sale in the rolling last 14 days,
make sure the attributed campaign → ad set → ad chain is deliverable. If any
layer of a sold chain is paused, flip exactly that chain back ACTIVE —
nothing else (solo principle: sibling ads/ad sets keep their stored status,
so the CPL monitor's pauses on non-sellers stay in force).

Matching: exact cpa.norm equality on (campaign, adset, ad) from the row's
UTMs; if the adset name drifted, a UNIQUE campaign+ad match is accepted.
Unresolvable chains are skipped, never guessed.

Guards:
  · MY is skipped entirely during the Wednesday weekly-off window
    (Wed 15:00 MYT → Thu 00:00 MYT — that cycle owns those pauses)
  · a campaign carrying the ADBOT_WEEKLY_OFF label is skipped
  · chains listed in EXCLUDE are never revived (owner's escape hatch for
    deliberately retiring a seller: add the exact ad name per account)
  · at most MAX_FLIPS status writes per run (safety fuse)

Runs headless from adbot-guardian.yml (hourly cron on main) with
CONFIRM=true; without it this prints what it would do. The run log is the
incident timeline."""
from __future__ import annotations

import collections
import datetime as dt
import os
import time

from adbot import cpa
from adbot.clients.sheets import SheetsClient
from adbot.commands import graph_client
from adbot.settings import REPO_ROOT, load_settings

CONFIRM = os.environ.get("CONFIRM", "").lower() in ("1", "true", "yes")
PACE = 3.0
MAX_FLIPS = 30
WEEKLY_LABEL = "ADBOT_WEEKLY_OFF"
WINDOW_DAYS = 14
N = cpa.norm

# Owner escape hatch: ad names (per account label) whose sold chains must NOT
# be auto-revived — for deliberately retiring a seller. Example: {"MY": {N("freestyle 1")}}
EXCLUDE: dict[str, set[str]] = {"MY": set(), "SG": set()}


def main() -> None:
    now_myt = dt.datetime.utcnow() + dt.timedelta(hours=8)
    today = now_myt.date()
    since = today - dt.timedelta(days=WINDOW_DAYS)
    stamp = now_myt.strftime("%Y-%m-%d %H:%M MYT")
    print(f"guardian·sold-chains — 成交窗口 {since} → {today} — "
          f"{'LIVE' if CONFIRM else 'DRY-RUN'} @ {stamp}")

    my_weekly_window = now_myt.weekday() == 2 and now_myt.hour >= 15
    if my_weekly_window:
        print("  💤 MY 周三全停窗口内 — 本轮跳过 MY（周四 00:09 weekly-on 恢复）")

    try:
        base = load_settings(REPO_ROOT / "config" / "config.yaml")
        values = SheetsClient(base.secrets.google_sa_json).read_tab(
            base.cpa.spreadsheet_id, base.cpa.sales_tab)
        sales, _c, _h = cpa.parse_sales(values, base.cpa.price_myr)
    except Exception as e:
        print(f"  ❌ sheet 读取失败，不动任何东西: {str(e)[:120]}")
        return

    triples: dict[str, collections.Counter] = {
        "MY": collections.Counter(), "SG": collections.Counter()}
    for s in sales:
        if not (s.date and s.date >= since and s.ad and s.adset and s.campaign):
            continue
        acct = "SG" if s.campaign.startswith("[sg]") else "MY"
        if s.ad in EXCLUDE.get(acct, set()):
            continue
        triples[acct][(s.campaign, s.adset, s.ad)] += 1

    flips = revived = 0
    for label, cfg in (("MY", "config.yaml"), ("SG", "config.sg.yaml")):
        if label == "MY" and my_weekly_window:
            continue
        if not triples[label]:
            continue
        try:
            s2 = load_settings(REPO_ROOT / "config" / cfg)
            g = graph_client(s2)
            acct = s2.meta.account_path
            ads = g._get_all(
                f"{acct}/ads",
                {"fields": "id,name,status,"
                           "campaign{id,name,status,adlabels},"
                           "adset{id,name,status}", "limit": "500"})
        except Exception as e:
            print(f"  ❌ [{label}] 拉取失败: {str(e)[:120]} — continuing")
            continue
        time.sleep(1)

        idx = collections.defaultdict(list)
        for a in ads:
            c = a.get("campaign") or {}
            aset = a.get("adset") or {}
            idx[(N(c.get("name") or ""), N(aset.get("name") or ""),
                 N(a.get("name") or ""))].append(a)

        flipped_c: set[str] = set()
        flipped_as: set[str] = set()
        for (camp_n, aset_n, ad_n), n_sales in triples[label].most_common():
            hits = idx.get((camp_n, aset_n, ad_n))
            if not hits:
                cand = [a for a in ads
                        if N((a.get("campaign") or {}).get("name") or "") == camp_n
                        and N(a.get("name") or "") == ad_n]
                if len(cand) != 1:
                    continue  # unresolvable — never guess
                hits = cand
            for a in hits:
                c = a.get("campaign") or {}
                aset = a.get("adset") or {}
                labels = {(l.get("name") or "") for l in (c.get("adlabels") or [])}
                if WEEKLY_LABEL in labels:
                    continue  # weekly-off owns this pause
                todo = []
                if c.get("status") != "ACTIVE" and c.get("id") not in flipped_c:
                    todo.append(("campaign", c["id"]))
                if aset.get("status") != "ACTIVE" and aset.get("id") not in flipped_as:
                    todo.append(("adset", aset["id"]))
                if a.get("status") != "ACTIVE":
                    todo.append(("ad", a["id"]))
                if not todo:
                    continue
                tag = (f"«{(c.get('name') or '')[:34]}» › "
                       f"«{(a.get('name') or '')[:28]}» ({n_sales}单)")
                if flips + len(todo) > MAX_FLIPS:
                    print(f"  ⚠️ 达到 {MAX_FLIPS} 次写入上限，剩余留给下一小时 — 停在 {tag}")
                    print(f"GUARDIAN·SOLD-CHAINS DONE — revived {revived} chains"
                          f" ({flips} flips) @ {stamp}")
                    return
                print(f"  🚨 {stamp} 发现被关 [{'+'.join(t for t, _ in todo)}] {tag}")
                if not CONFIRM:
                    continue
                try:
                    for level, oid in todo:
                        g.update_status(oid, "ACTIVE")
                        flips += 1
                        if level == "campaign":
                            flipped_c.add(oid)
                        if level == "adset":
                            flipped_as.add(oid)
                        time.sleep(PACE)
                    revived += 1
                    print(f"  ⛑ 已开回 {tag}")
                except Exception as e:
                    print(f"  ❌ {tag}: {str(e)[:110]} — continuing")
    print(f"GUARDIAN·SOLD-CHAINS DONE — revived {revived} chains ({flips} flips) @ {stamp}"
          if CONFIRM else "GUARDIAN·SOLD-CHAINS DRY-RUN DONE")


if __name__ == "__main__":
    main()
