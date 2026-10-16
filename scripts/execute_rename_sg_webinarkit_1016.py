# -*- coding: utf-8 -*-
"""owner 2026-10-16「改成正确的数字」— rename the 4 SG Webinarkit campaigns so 1-1-N matches their live ad
count after «freestyle: korea» was added. N is counted from the API (non-deleted ads). CONFIRM=true writes."""
from __future__ import annotations

import os
import re
import time

from adbot.commands import graph_client
from adbot.settings import REPO_ROOT, load_settings

CONFIRM = os.environ.get("CONFIRM", "").lower() in ("1", "true", "yes")
CAMPS = ["120249918193090521", "120249918195380521", "120249918198320521", "120249918201630521"]


def main() -> None:
    g = graph_client(load_settings(REPO_ROOT / "config" / "config.sg.yaml"))
    for cid in CAMPS:
        c = g.get_object(cid, "name")
        ads = [a for a in g._get_all(cid + "/ads", {"fields": "name,status", "limit": "50"})
               if a.get("status") not in ("DELETED", "ARCHIVED")]
        new = re.sub(r"\| 1-1-\d+ \|", f"| 1-1-{len(ads)} |", c["name"])
        print(f"  «{c['name']}» → «{new}» ({len(ads)} ads: {', '.join(a['name'] for a in ads)})")
        if CONFIRM and new != c["name"]:
            g._request("POST", cid, data={"name": new}); time.sleep(1)
            print(f"    ✅ {g.get_object(cid, 'name')['name']}")
    print("RENAME DONE" + ("" if CONFIRM else " (dry-run)"))


if __name__ == "__main__":
    main()
