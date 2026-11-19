# -*- coding: utf-8 -*-
"""READ-ONLY: print the raw placement-related targeting keys of a few MY ad sets (owner 11/19「MY 拿掉 AN」prep)."""
import json

from adbot.commands import graph_client
from adbot.settings import REPO_ROOT, load_settings

s = load_settings(REPO_ROOT / "config" / "config.my5.yaml")
g = graph_client(s)
for aid in ("120251993979530329", "120251995652710329", "120251840426800329", "120251454700740329"):
    a = g._request("GET", aid, params={"fields": "name,targeting,placement_soft_opt_out,dsa_beneficiary"})
    t = a.get("targeting") or {}
    print(a["name"], aid, "keys:", sorted(t))
    for k, v in t.items():
        if any(x in k for x in ("platform", "position", "exclu", "placement", "device", "os")):
            print("   ", k, "=", json.dumps(v, ensure_ascii=False)[:300])
    print("   placement_soft_opt_out =", a.get("placement_soft_opt_out"))
