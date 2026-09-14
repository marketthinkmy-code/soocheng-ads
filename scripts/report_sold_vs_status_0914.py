# -*- coding: utf-8 -*-
"""READ-ONLY: owner 2026-09-14「有哪些是近期成交但被我关掉的吗？」

  Join the Paid Student List's last-14-day sales (UTM campaign/ad) against the
  LIVE 3-level status of every matching ad on BOTH accounts. Report:
    ⚠️ chains with a recent sale where NO instance is delivering (the answer)
    ✓ chains with a recent sale still delivering
    ❓ sales whose UTM matches nothing (renamed / blank UTM)
  Prints only dates + UTM/entity names — no student PII."""
from __future__ import annotations

import datetime as dt
import time

from adbot import cpa
from adbot.clients.sheets import SheetsClient
from adbot.monitor_cpl import _mkey
from adbot.settings import REPO_ROOT, load_settings
from adbot.commands import graph_client

DAYS = 14
RUNNING = {"ACTIVE", "PENDING_REVIEW", "IN_PROCESS", "PREAPPROVED", "LIMITED"}


def main() -> None:
    s_my = load_settings(REPO_ROOT / "config" / "config.yaml")
    s_sg = load_settings(REPO_ROOT / "config" / "config.sg.yaml")
    today = (dt.datetime.utcnow() + dt.timedelta(hours=8)).date()
    cutoff = today - dt.timedelta(days=DAYS)

    values = SheetsClient(s_my.secrets.google_sa_json).read_tab(
        s_my.cpa.spreadsheet_id, s_my.cpa.sales_tab)
    sales, _cols, _hdr = cpa.parse_sales(values, s_my.cpa.price_myr)
    recent = [x for x in sales if x.date and x.date >= cutoff]
    print(f"近 {DAYS} 天（{cutoff} 起）成交 {len(recent)} 单\n")

    pool = []          # (acct_label, ad row)
    for label, st in (("MY", s_my), ("SG", s_sg)):
        g = graph_client(st)
        rows = g._get_all(
            f"{st.meta.account_path}/ads",
            {"fields": "name,effective_status,"
                       "adset{name,effective_status},campaign{name,effective_status}",
             "limit": "500"})
        pool.extend((label, r) for r in rows)
        time.sleep(1.2)

    # group sales per (campaign, ad) chain
    chains = {}
    for x in recent:
        key = (_mkey(x.campaign), cpa.norm(x.ad))
        c = chains.setdefault(key, {"dates": [], "campaign": x.campaign, "ad": x.ad})
        c["dates"].append(x.date)

    def instances(key):
        strict = [(lb, r) for lb, r in pool
                  if _mkey((r.get("campaign") or {}).get("name") or "") == key[0]
                  and cpa.norm(r.get("name") or "") == key[1]]
        if strict:
            return strict, "strict"
        return [(lb, r) for lb, r in pool
                if cpa.norm(r.get("name") or "") == key[1]], "ad-name"

    dead, alive, lost = [], [], []
    for key, c in sorted(chains.items(), key=lambda kv: max(kv[1]["dates"]), reverse=True):
        inst, how = instances(key)
        if not inst:
            lost.append(c)
            continue
        run = [(lb, r) for lb, r in inst if r.get("effective_status") in RUNNING]
        dates = "、".join(d.strftime("%-m/%-d") for d in sorted(c["dates"]))
        if run:
            wheres = {f"[{lb}] {((r.get('campaign') or {}).get('name') or '')[:38]}"
                      for lb, r in run}
            alive.append(f"  ✓ «{c['ad'][:30]}» 成交 {dates}（{len(c['dates'])} 单）— "
                         f"在跑 {len(run)} 位：{' · '.join(sorted(wheres))}")
        else:
            lines = [f"  ⚠️ «{c['ad'][:30]}» 成交 {dates}（{len(c['dates'])} 单）"
                     f"  UTM campaign «{c['campaign'][:40]}» — 全部位置没在跑（match={how}）:"]
            for lb, r in inst[:4]:
                camp = (r.get("campaign") or {})
                aset = (r.get("adset") or {})
                lines.append(f"       [{lb}] {r.get('effective_status')} @ "
                             f"«{(camp.get('name') or '')[:36]}» "
                             f"(camp {camp.get('effective_status')}, "
                             f"adset {aset.get('effective_status')})")
            dead.append("\n".join(lines))
    print("═══ ⚠️ 近期有成交、现在整链没在跑 ═══")
    print("\n".join(dead) if dead else "  （没有——所有近期成交链都还活着）")
    print("\n═══ ✓ 近期有成交、还在跑 ═══")
    print("\n".join(alive) if alive else "  （无）")
    if lost:
        print(f"\n═══ ❓ UTM 对不上任何现存广告（改名/空白 UTM）═══")
        for c in lost:
            dates = "、".join(d.strftime("%-m/%-d") for d in sorted(c["dates"]))
            print(f"  ? «{c['ad'][:36]}» / camp «{c['campaign'][:40]}»  成交 {dates}")
    print("\nSOLD-VS-STATUS DONE (read-only)")


if __name__ == "__main__":
    main()
