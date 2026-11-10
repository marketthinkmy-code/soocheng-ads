# -*- coding: utf-8 -*-
"""owner 2026-11-10「你试试看先做一个 ad set，我印象中是不能改了的」— try setting ONE NEW VIDEO ad set's start_time to
2026-11-11 00:00 (account time zone). Ad set: SG «Broad | SG 28+ · V1» 120250544534940521 under the PAUSED campaign
«(Webinarkit) [SG] STOCKBLOOM | NEW VIDEO · Broad | 1-5-1 | 1110». Reads back before/after. Nothing is activated. CONFIRM=true writes."""
from __future__ import annotations

import os

from adbot.commands import graph_client
from adbot.settings import REPO_ROOT, load_settings

CONFIRM = os.environ.get("CONFIRM", "").lower() in ("1", "true", "yes")
ADSET = "120250544534940521"
s = load_settings(REPO_ROOT / "config" / "config.sg.yaml")
g = graph_client(s)
acc = g.get_object(s.meta.account_path, "timezone_name,timezone_offset_hours_utc")
a = g.get_object(ADSET, "name,status,effective_status,start_time,end_time,campaign{name,status}")
assert a["name"] == "Broad | SG 28+ · V1" and "NEW VIDEO · Broad" in a["campaign"]["name"] and a["campaign"]["status"] == "PAUSED", a
off = acc.get("timezone_offset_hours_utc")
target = f"2026-11-11T00:00:00{'+' if off >= 0 else '-'}{abs(int(off)):02d}00"
print(f"  账户时区 {acc.get('timezone_name')} (UTC{off:+}) · «{a['campaign']['name']}» ({a['campaign']['status']}) › «{a['name']}» {ADSET}")
print(f"  现在 start_time {a.get('start_time')} · end_time {a.get('end_time')} · {a['status']}/{a['effective_status']} → 目标 {target}")
if CONFIRM:
    try:
        r = g._request("POST", ADSET, data={"start_time": target})
        print(f"  Meta 回应: {r}")
    except Exception as e:                                               # noqa: BLE001
        print(f"  ❌ Meta 拒绝: {str(e)[:400]}")
    b = g.get_object(ADSET, "start_time,status,effective_status")
    print(f"  回读 start_time {b.get('start_time')} · {b['status']}/{b['effective_status']}")
print("TRY START_TIME DONE" + ("" if CONFIRM else " (dry-run)"))
