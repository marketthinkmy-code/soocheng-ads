# -*- coding: utf-8 -*-
"""owner 2026-10-22「关掉吧」— pause SG (Webinarkit) TRAVEL 1-1-5 campaign again (reactivated after the 10/20 pause;
CPL 274; Travel × 盖电脑 already runs in WINNERS). Only this campaign. CONFIRM=true writes."""
from __future__ import annotations

import os

from adbot.commands import graph_client
from adbot.settings import REPO_ROOT, load_settings

CONFIRM = os.environ.get("CONFIRM", "").lower() in ("1", "true", "yes")
CID = "120249918201630521"


def main() -> None:
    g = graph_client(load_settings(REPO_ROOT / "config" / "config.sg.yaml"))
    c = g.get_object(CID, "name,status,effective_status")
    print(f"  «{c['name']}» {c['status']}/{c['effective_status']} → PAUSED")
    if CONFIRM and c["status"] != "PAUSED":
        g.update_status(CID, "PAUSED")
        print(f"    ✅ now {g.get_object(CID, 'status')['status']}")
    print("SG TRAVEL OFF DONE" + ("" if CONFIRM else " (dry-run)"))


if __name__ == "__main__":
    main()
