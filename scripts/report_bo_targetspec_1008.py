# -*- coding: utf-8 -*-
"""READ-ONLY: full history of targeting edits on the MY 5.0 Business Owner ad set today, with the
complete extra_data (old/new spec as Ads Manager renders it), so the team's own interest set
can be restored exactly if the owner wants it back. Also resolves those interest names to ids
via the targeting search API so a restore is one write away."""
from __future__ import annotations

import datetime as dt
import json
import time

from adbot.commands import graph_client
from adbot.settings import REPO_ROOT, load_settings

BO_ADSET = "120251329164990329"


def main() -> None:
    s = load_settings(REPO_ROOT / "config" / "config.my5.yaml")
    g = graph_client(s)
    acct = s.meta.account_path
    since = int(dt.datetime.utcnow().timestamp()) - 6 * 3600
    acts = g._get_all(acct + "/activities", {
        "fields": "event_time,event_type,actor_name,object_id,object_name,extra_data",
        "since": str(since), "limit": "300"})
    specs = [x for x in acts if x.get("event_type") == "update_ad_set_target_spec"
             and str(x.get("object_id")) == BO_ADSET]
    print(f"Business Owner ad set 今天的 targeting 编辑：{len(specs)} 次（最新在前）\n")
    names_by_time = []
    for x in specs:
        print(f"── {(x.get('event_time') or '')[:19]}  {x.get('actor_name')}")
        try:
            ed = json.loads(x.get("extra_data") or "{}")
        except json.JSONDecodeError:
            ed = {"raw": x.get("extra_data")}
        for side in ("old_value", "new_value"):
            v = ed.get(side)
            print(f"   {side}:")
            interests = []
            for item in v or []:
                if isinstance(item, dict):
                    c, ch = item.get("content"), item.get("children")
                    print(f"      {c} {ch}")
                    if c and ("Interest" in c or "兴趣" in c or "Detailed" in c or "People who match" in c):
                        interests.extend(ch or [])
            if side == "new_value":
                names_by_time.append(((x.get("event_time") or ""), x.get("actor_name"), interests))
        print()
    # resolve the latest non-system edit's interest names to ids
    human = [n for n in names_by_time if n[1] and "STOCKBLOOM-ADS" not in n[1]]
    if human:
        t, who, names = human[0]
        print(f"═══ 最近一次人工设定（{t[:19]} {who}）的兴趣名称 → id ═══")
        for nm in names:
            try:
                rows = g._get_all("search", {"type": "adinterest", "q": nm, "limit": "5"})
                hit = next((r for r in rows if (r.get("name") or "").casefold() == nm.casefold()), rows[0] if rows else None)
                print(f"   «{nm}» → {hit.get('id') if hit else '?'} ({hit.get('name') if hit else 'no match'}, audience {hit.get('audience_size_upper_bound') if hit else '-'})")
            except Exception as exc:                               # noqa: BLE001
                print(f"   «{nm}» → ❌ {str(exc)[:100]}")
            time.sleep(0.5)
    print("\nBO TARGETSPEC DONE (read-only)")


if __name__ == "__main__":
    main()
