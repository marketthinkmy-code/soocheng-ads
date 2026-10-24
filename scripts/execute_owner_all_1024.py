# -*- coding: utf-8 -*-
"""owner 2026-10-24「全部照建议」:
① 赚美金，一定要接美国客户 → 禁跑 (rejected on MY 5.0): DELETE the rejected ad 120251533797560329; every other copy on
   MY 5.0 + SG: ad-level PAUSED and renamed «🚫 …». (「赚美金 = 求人？」/「马来西亚小白怎样赚美金」 are other masters.)
② SG back to ≈RM585: LAL 5% 90→75 · WINNERS Investment · 盖电脑 80→65 · pause WINNERS ad sets Travel · 盖电脑 and Golf · 盖电脑.
③ MY: pause PURCHASE LAL 5% MY (RM137, 0 reg) · LUXURY MY 50→80 (this week CPL 21).
CONFIRM=true writes."""
from __future__ import annotations

import os
import time

from adbot import compliance
from adbot.commands import graph_client
from adbot.settings import REPO_ROOT, load_settings

CONFIRM = os.environ.get("CONFIRM", "").lower() in ("1", "true", "yes")
REJECTED = "120251533797560329"
MASTER = ["赚美金，一定要接美国客户"]
SG_WIN = "120249964890710521"


def budget(g, oid, cents):
    o = g.get_object(oid, "name,daily_budget")
    print(f"   budget «{o['name']}» RM{int(o.get('daily_budget') or 0) // 100} → RM{cents // 100}")
    if CONFIRM and int(o.get("daily_budget") or 0) != cents:
        g.update_daily_budget(oid, cents); time.sleep(1)
        print(f"     ✅ RM{int(g.get_object(oid, 'daily_budget')['daily_budget']) // 100}")


def pause(g, oid):
    o = g.get_object(oid, "name,status")
    print(f"   pause «{o['name']}» {o['status']} → PAUSED")
    if CONFIRM and o["status"] != "PAUSED":
        g.update_status(oid, "PAUSED"); time.sleep(1)
        print(f"     ✅ {g.get_object(oid, 'status')['status']}")


def main() -> None:
    my_s = load_settings(REPO_ROOT / "config" / "config.my5.yaml")
    sg_s = load_settings(REPO_ROOT / "config" / "config.sg.yaml")
    assert compliance.is_banned("Video：赚美金，一定要接美国客户？", my_s.compliance.banned_creatives), "ban list not synced"
    print("① 赚美金 ban")
    for label, s in (("MY5", my_s), ("SG", sg_s)):
        g = graph_client(s)
        for a in g._get_all(s.meta.account_path + "/ads", {"fields": "name,status,effective_status", "limit": "500"}):
            if a["effective_status"] in ("DELETED", "ARCHIVED") or not compliance.is_banned(a["name"], MASTER):
                continue
            if a["id"] == REJECTED:
                print(f"   {label} DELETE {a['id']} «{a['name']}» {a['effective_status']}")
                if CONFIRM:
                    g._request("POST", a["id"], data={"status": "DELETED"}); time.sleep(1)
                    print(f"     ✅ {g.get_object(a['id'], 'effective_status')['effective_status']}")
                continue
            new = a["name"] if a["name"].startswith("🚫") else "🚫 " + a["name"]
            print(f"   {label} {a['id']} «{a['name']}» {a['status']}/{a['effective_status']} → PAUSED «{new}»")
            if CONFIRM:
                data = {"name": new}
                if a["status"] != "PAUSED":
                    data["status"] = "PAUSED"
                if data != {"name": a["name"]}:
                    g._request("POST", a["id"], data=data); time.sleep(0.8)
    print("② SG")
    g = graph_client(sg_s)
    budget(g, "120249918198320521", 7500)
    for st in g._get_all(SG_WIN + "/adsets", {"fields": "name,status,daily_budget,ads{name,status}", "limit": "20"}):
        live = [a["name"] for a in (st.get("ads") or {}).get("data", []) if a.get("status") == "ACTIVE"]
        if st["status"] != "ACTIVE" or live != ["Video：盖电脑，喂！"]:
            continue
        if st["name"].startswith("Investment"):
            budget(g, st["id"], 6500)
        elif st["name"].startswith("Travel") or st["name"].startswith("Golf"):
            pause(g, st["id"])
    print("③ MY")
    g = graph_client(my_s)
    pause(g, "120251533786300329")
    budget(g, "120251454680840329", 8000)
    print("OWNER ALL DONE" + ("" if CONFIRM else " (dry-run)"))


if __name__ == "__main__":
    main()
