# -*- coding: utf-8 -*-
"""owner 2026-10-22「做」— restore MY 5.0 BUSINESS OWNER (Webinarkit) RM70 → RM100: undo the monitor's 10/21 −30%
(triggered by one ad's CPL while the campaign ran CPL 24). Only this campaign. CONFIRM=true writes."""
from __future__ import annotations

import os

from adbot.commands import graph_client
from adbot.settings import REPO_ROOT, load_settings

CONFIRM = os.environ.get("CONFIRM", "").lower() in ("1", "true", "yes")
CID, CENTS = "120251454700150329", 10000


def main() -> None:
    g = graph_client(load_settings(REPO_ROOT / "config" / "config.my5.yaml"))
    c = g.get_object(CID, "name,daily_budget,effective_status")
    print(f"  «{c['name']}» {c['effective_status']} RM{int(c['daily_budget']) // 100} → RM{CENTS // 100}")
    if CONFIRM and int(c["daily_budget"]) != CENTS:
        g.update_daily_budget(CID, CENTS)
        print(f"    ✅ now RM{int(g.get_object(CID, 'daily_budget')['daily_budget']) // 100}")
    print("BO RESTORE DONE" + ("" if CONFIRM else " (dry-run)"))


if __name__ == "__main__":
    main()
