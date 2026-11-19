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
    sub = "publisher_platforms,facebook_positions,instagram_positions,messenger_positions,audience_network_positions,threads_positions,whatsapp_positions,device_platforms,excluded_publisher_categories"
    try:
        b = g._request("GET", aid, params={"fields": "targeting{" + sub + "}"})
        print("   explicit subfields:", json.dumps(b.get("targeting"), ensure_ascii=False)[:400])
    except Exception as exc:  # noqa: BLE001
        print("   explicit subfields error:", str(exc)[:300])
    try:
        ads = g._get_all(aid + "/ads", {"fields": "name,effective_status,creative{id,asset_feed_spec,object_story_id}", "limit": "5"})
        for ad in ads[:1]:
            print("   ad", ad["id"], ad["effective_status"], "creative", json.dumps(ad.get("creative"), ensure_ascii=False)[:300])
    except Exception as exc:  # noqa: BLE001
        print("   ads error:", str(exc)[:200])
    print("   graph version:", getattr(g, "version", None) or getattr(g, "base_url", None))
