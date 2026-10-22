# -*- coding: utf-8 -*-
"""owner 2026-10-23「开回去 SG」— undo exactly what was paused by hand on SG after 10/22 13:00 UTC (the owner's
「我关完了」): read the activity log, take every campaign / ad set / ad whose run status a human set Active → Inactive,
and set it ACTIVE again. Never reopens: the SG TRAVEL 1-1-5 campaign (paused on owner's word 10/22), anything the
bot (STOCKBLOOM-ADS) paused, or a banned creative (ban gate). CONFIRM=true writes."""
from __future__ import annotations

import datetime as dt
import json
import os
import time

from adbot import compliance
from adbot.commands import graph_client
from adbot.settings import REPO_ROOT, load_settings

CONFIRM = os.environ.get("CONFIRM", "").lower() in ("1", "true", "yes")
SINCE = int(dt.datetime(2026, 10, 22, 13, 0, tzinfo=dt.timezone.utc).timestamp())
KEEP_OFF = {"120249918201630521"}           # SG TRAVEL 1-1-5 — stays paused
BOT = "STOCKBLOOM-ADS"


def main() -> None:
    s = load_settings(REPO_ROOT / "config" / "config.sg.yaml")
    g = graph_client(s)
    acts = g._get_all(s.meta.account_path + "/activities", {
        "fields": "event_time,event_type,actor_name,object_id,object_name,object_type,extra_data", "since": str(SINCE), "limit": "500"})
    todo = {}
    for a in sorted(acts, key=lambda x: x["event_time"]):
        if "run_status" not in (a.get("event_type") or "") or (a.get("actor_name") or "") in (BOT, "Meta", ""):
            continue
        try:
            ed = json.loads(a.get("extra_data") or "{}")
        except Exception:                                              # noqa: BLE001
            ed = {}
        old, new = str(ed.get("old_value", "")), str(ed.get("new_value", ""))
        print(f"  {a['event_time'][5:16]} {a['actor_name'][:16]:<16} {a['event_type'][:30]:<30} «{(a.get('object_name') or '')[:40]}» {old} → {new}")
        if new == "Inactive" and old == "Active":
            todo[a["object_id"]] = a.get("object_name") or ""
        elif new == "Active":
            todo.pop(a["object_id"], None)
    print(f"\n  要开回 {len(todo)} 个：")
    for oid, name in todo.items():
        o = g.get_object(oid, "name,status,effective_status")
        skip = oid in KEEP_OFF or compliance.is_banned(o["name"], s.compliance.banned_creatives)
        print(f"   {oid} «{o['name'][:60]}» {o['status']}/{o['effective_status']}" + ("  ⛔ 不开（TRAVEL/禁跑）" if skip else ""))
        if CONFIRM and not skip and o["status"] != "ACTIVE":
            g.update_status(oid, "ACTIVE"); time.sleep(1)
            print(f"     ✅ now {g.get_object(oid, 'status')['status']}")
    print("SG REOPEN DONE" + ("" if CONFIRM else " (dry-run)"))


if __name__ == "__main__":
    main()
