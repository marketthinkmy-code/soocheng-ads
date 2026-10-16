# -*- coding: utf-8 -*-
"""owner 2026-10-16「要每条 campaign 都放同样 5 支，补上。budget 也要调整」— SG Webinarkit campaigns:
every campaign carries the same 5 ads (盖电脑 · 用我的方法 · 不选 forex · 我跟你讲 · freestyle: korea), reusing
the creatives built today; CBO budgets 150 / 125 / 125 / 100 (RM500/day, ≥ RM20 per ad); names → 1-1-5.
CONFIRM=true writes; otherwise dry-run."""
from __future__ import annotations

import os
import re
import time

from adbot.commands import graph_client
from adbot.settings import REPO_ROOT, load_settings

CONFIRM = os.environ.get("CONFIRM", "").lower() in ("1", "true", "yes")
# campaign id -> (ad set id, new daily budget cents)
CAMPS = {
    "120249918193090521": ("120249918193310521", 15000),   # BROAD SG
    "120249918195380521": ("120249918195680521", 12500),   # LUXURY GOODS
    "120249918198320521": ("120249918199040521", 12500),   # PURCHASE LAL 5%
    "120249918201630521": ("120249918201950521", 10000),   # TRAVEL
}
CREATIVES = {
    "Video：盖电脑，喂！": "996800046775417",
    "Video：用我的方法": "1578147406859568",
    "Video：不选 forex 不选黄金": "1589609515721902",
    "Video：我跟你讲！": "1414281500773499",
    "freestyle: korea": "1833392087837365",
}


def main() -> None:
    s = load_settings(REPO_ROOT / "config" / "config.sg.yaml")
    g = graph_client(s)
    acct = s.meta.account_path
    total = 0
    for cid, (sid, budget) in CAMPS.items():
        c = g.get_object(cid, "name,status,daily_budget")
        have = {a["name"] for a in g._get_all(sid + "/ads", {"fields": "name,status", "limit": "50"})
                if a.get("status") not in ("DELETED", "ARCHIVED")}
        missing = [n for n in CREATIVES if n not in have]
        new_name = re.sub(r"\| 1-1-\d+ \|", "| 1-1-5 |", c["name"])
        total += budget
        print(f"«{c['name']}» {c.get('status')} RM{int(c.get('daily_budget') or 0) // 100}→RM{budget // 100} · 补 {missing or '无'} · 名 → «{new_name}»")
        if not CONFIRM:
            continue
        for n in missing:
            r = g.create_ad(acct, name=n, adset_id=sid, creative={"creative_id": CREATIVES[n]}, status="ACTIVE")
            print(f"   + {n} → ad {r['id']}"); time.sleep(2)
        if int(c.get("daily_budget") or 0) != budget:
            g.update_daily_budget(cid, budget); time.sleep(1)
        if new_name != c["name"]:
            g._request("POST", cid, data={"name": new_name}); time.sleep(1)
        v = g.get_object(cid, "name,daily_budget")
        n_ads = len([a for a in g._get_all(sid + "/ads", {"fields": "status", "limit": "50"}) if a.get("status") not in ("DELETED", "ARCHIVED")])
        print(f"   ✅ «{v['name']}» RM{int(v['daily_budget']) // 100} · {n_ads} ads")
    print(f"SG 合计 RM{total // 100}/天")
    print("FIVE ADS DONE" + ("" if CONFIRM else " (dry-run)"))


if __name__ == "__main__":
    main()
