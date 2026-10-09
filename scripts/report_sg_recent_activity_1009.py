# -*- coding: utf-8 -*-
"""READ-ONLY: SG — who touched what in the last 3 hours (status / budget events), plus the live
state of the LUXURY GOODS chain (the 86-day «video 1：用我的方法» position dropped out of the
monitor's active list between 11:34 and 11:38 SGT on 2026-10-09). No PII."""
from __future__ import annotations

import datetime as dt
import json
import time

from adbot.commands import graph_client
from adbot.settings import REPO_ROOT, load_settings

LUXURY_GOODS_CAMPAIGN = "120248256443280521"


def main() -> None:
    s = load_settings(REPO_ROOT / "config" / "config.sg.yaml")
    g = graph_client(s)
    acct = s.meta.account_path
    since_ts = int(dt.datetime.utcnow().timestamp()) - 3 * 3600
    acts = g._get_all(acct + "/activities", {
        "fields": "event_time,event_type,actor_name,object_name,object_id,extra_data",
        "since": str(since_ts), "limit": "200"})
    keep = [x for x in acts if any(k in (x.get("event_type") or "")
                                   for k in ("run_status", "budget", "review", "delete", "create"))]
    print(f"═══ SG 近 3 小时 开/关/预算/审核 动作（{len(keep)} 条，最新在前；时间 UTC）═══")
    for x in keep[:80]:
        extra = x.get("extra_data") or ""
        try:
            ed = json.loads(extra) if isinstance(extra, str) else extra
            extra = " ".join(f"{k}={str(v)[:40]}" for k, v in ed.items() if k in ("old_value", "new_value", "status"))
        except Exception:                                            # noqa: BLE001
            extra = str(extra)[:80]
        print(f"  {(x.get('event_time') or '')[5:19]}  {(x.get('actor_name') or '?')[:18]:<18} "
              f"{(x.get('event_type') or '')[:32]:<32} «{(x.get('object_name') or '')[:40]}»  {extra[:90]}")
    time.sleep(1.0)
    camp = g.get_object(LUXURY_GOODS_CAMPAIGN, "name,status,effective_status,daily_budget,updated_time")
    print(f"\nLUXURY GOODS campaign: {camp.get('status')} / eff {camp.get('effective_status')} / CBO "
          f"RM{float(camp.get('daily_budget') or 0) / 100:.0f} / updated {camp.get('updated_time')}")
    ads = g._get_all(LUXURY_GOODS_CAMPAIGN + "/ads", {
        "fields": "name,status,effective_status,updated_time,adset{name,status,effective_status,daily_budget}",
        "limit": "50"})
    for a in ads:
        aset = a.get("adset") or {}
        print(f"  ad «{(a.get('name') or '')[:40]}» {a.get('status')} / eff {a.get('effective_status')} "
              f"/ adset «{(aset.get('name') or '')[:30]}» {aset.get('status')} / updated {a.get('updated_time')}")
    print("\nRECENT ACTIVITY DONE (read-only)")


if __name__ == "__main__":
    main()
