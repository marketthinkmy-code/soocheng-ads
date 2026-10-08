# -*- coding: utf-8 -*-
"""READ-ONLY follow-up to report_sg_reopen_1008: which ad sits in which ad set
(with the ad set's budget) inside every SG campaign that is ACTIVE or that the
14/10 reopen plan would touch, plus 30 days of account-level daily spend so we
know how long SG has been dark. No sheet, no PII."""
from __future__ import annotations

import datetime as dt
import json
import time

from adbot import compliance
from adbot.commands import graph_client
from adbot.monitor_cpl import extract_results, result_action_type
from adbot.settings import REPO_ROOT, load_settings

WATCH = ("0911 HOOK", "0910 重拍", "0905", "GOLF PICKLEBALL 30-55", "ANDRO POOL",
         "LUXURY WATCHES", "PURCHASE LAL 5%", "LUXURY GOODS | 1-1-3", "GOLF PICKBLEBALL",
         "PRIORITY BANKING", "BROAD | 1-1-3 A")


def main() -> None:
    s = load_settings(REPO_ROOT / "config" / "config.sg.yaml")
    g = graph_client(s)
    acct = s.meta.account_path
    today = (dt.datetime.utcnow() + dt.timedelta(hours=8)).date()
    token = result_action_type(s.meta.conversion_event)
    d30 = today - dt.timedelta(days=30)

    rows = g._get_all(acct + "/insights", {
        "level": "account", "fields": "spend,actions", "time_increment": "1",
        "time_range": json.dumps({"since": d30.isoformat(), "until": today.isoformat()}),
        "limit": "100"})
    print("═══ SG 近 30 天 每日花费 / 报名（Meta 只回传有数据的日子）═══")
    if not rows:
        print("  （30 天内没有任何一天有花费）")
    for r in rows:
        sp = float(r.get("spend") or 0)
        rg = extract_results(r.get("actions"), token)
        cpl = f"CPL {sp/rg:.0f}" if rg else ("0 reg" if sp else "—")
        print(f"  {r.get('date_start')}  RM{sp:>7.0f}  报名 {rg:>4.0f}  {cpl:<9} {'█' * int(min(sp, 800) / 25)}")
    print()
    time.sleep(1.2)

    camps = g._get_all(acct + "/campaigns", {
        "fields": "id,name,status,daily_budget", "limit": "500"})
    time.sleep(1.2)
    asets = g._get_all(acct + "/adsets", {
        "fields": "id,name,status,daily_budget,campaign_id", "limit": "500"})
    time.sleep(1.2)
    ads = g._get_all(acct + "/ads", {
        "fields": "id,name,status,effective_status,adset_id,campaign_id", "limit": "500"})
    by_aset = {}
    for a in ads:
        by_aset.setdefault(a.get("adset_id"), []).append(a)
    asets_by_camp = {}
    for x in asets:
        asets_by_camp.setdefault(x.get("campaign_id"), []).append(x)

    print("═══ 载体明细（ACTIVE 的 + 计划会碰的 campaign）═══")
    for c in sorted(camps, key=lambda c: (c.get("status") != "ACTIVE", c.get("name") or "")):
        nm = c.get("name") or ""
        if c.get("status") != "ACTIVE" and not any(w in nm for w in WATCH):
            continue
        cb = f"CBO RM{float(c['daily_budget'])/100:.0f}/d" if c.get("daily_budget") else "ABO"
        print(f"[{c.get('status')}] «{nm}» {cb}  id={c['id']}")
        for x in asets_by_camp.get(c["id"], []):
            ab = f"RM{float(x['daily_budget'])/100:.0f}/d" if x.get("daily_budget") else "—"
            kids = by_aset.get(x["id"], [])
            print(f"    [{x.get('status')}] adset «{(x.get('name') or '')[:30]}» {ab}  id={x['id']}")
            for a in kids:
                ban = compliance.banned_reason(a.get("name") or "", s.compliance.banned_creatives)
                tag = "⛔" if ban else "  "
                print(f"        {tag} [{a.get('status')}/{a.get('effective_status')}] «{(a.get('name') or '')[:42]}»  id={a['id']}")
        print()
    print("CARRIERS DONE (read-only)")


if __name__ == "__main__":
    main()
