# -*- coding: utf-8 -*-
"""Owner 2026-09-20「关」— close the one CONFLICT from the guarantee sweep:
SG «video 1：用我的方法» @ 🌟INVESTMENT (67 天老位、30 天无单、素材无 7 天内成交).
Ad-level pause only; idempotent; CONFIRM gate; verified after."""
from __future__ import annotations

import os
import time

from adbot.commands import graph_client
from adbot.settings import REPO_ROOT, load_settings

CONFIRM = os.environ.get("CONFIRM", "").lower() in ("1", "true", "yes")


def main() -> None:
    s = load_settings(REPO_ROOT / "config" / "config.sg.yaml")
    g = graph_client(s)
    ads = g._get_all(
        f"{s.meta.account_path}/ads",
        {"fields": "id,name,status,effective_status,campaign{name}", "limit": "500"})
    time.sleep(1.2)
    hits = [a for a in ads
            if (a.get("name") or "").strip() == "video 1：用我的方法"
            and "INVESTMENT" in ((a.get("campaign") or {}).get("name") or "")
            and ((a.get("campaign") or {}).get("name") or "").startswith("🌟")]
    if len(hits) != 1:
        print(f"⚠️ SKIP: {len(hits)} 个匹配，不猜。")
        return
    a = hits[0]
    if a.get("status") == "PAUSED":
        print("＝ 已是关的。")
        return
    if CONFIRM:
        g.update_status(a["id"], "PAUSED")
        time.sleep(2.0)
        o = g.get_object(a["id"], fields="effective_status")
        print(f"✔ 关 «video 1：用我的方法» @ «{(a['campaign'].get('name') or '')[:40]}» "
              f"→ {o.get('effective_status')}")
    else:
        print("[dry] 关 «video 1：用我的方法» @ 🌟INVESTMENT")
    print("CLOSE INVESTMENT DONE")


if __name__ == "__main__":
    main()
