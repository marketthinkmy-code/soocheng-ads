# -*- coding: utf-8 -*-
"""owner 2026-10-16: headline「🚨 教你如何在 1️⃣ 分钟内，判读市场节奏」on every Webinarkit ad built today EXCEPT
the korea ads (owner: korea is his build, don't touch). Each distinct creative is cloned with video_data.title
added (same video / caption / link / url_tags) and the ads are switched to the clone. CONFIRM=true writes."""
from __future__ import annotations

import os
import time

from adbot import compliance
from adbot.commands import graph_client
from adbot.settings import REPO_ROOT, load_settings

CONFIRM = os.environ.get("CONFIRM", "").lower() in ("1", "true", "yes")
HEADLINE = "🚨 教你如何在 1️⃣ 分钟内，判读市场节奏"
PLAN = {
    "config.my5.yaml": ["120251454680840329", "120251454704570329", "120251454700150329", "120251454713670329"],
    "config.sg.yaml": ["120249918193090521", "120249918195380521", "120249918198320521", "120249918201630521"],
}


def main() -> None:
    for cfg, camps in PLAN.items():
        s = load_settings(REPO_ROOT / "config" / cfg)
        g = graph_client(s)
        acct = s.meta.account_path
        clones = {}
        print(f"\n## {cfg}")
        for cid in camps:
            ads = g._get_all(cid + "/ads", {"fields": "id,name,status,creative{id,name,url_tags,object_story_spec}", "limit": "50"})
            for a in ads:
                if a.get("status") in ("DELETED", "ARCHIVED"):
                    continue
                if "korea" in (a.get("name") or "").lower():
                    print(f"  skip korea «{a['name']}» {a['id']}"); continue
                assert not compliance.is_banned(a["name"], s.compliance.banned_creatives)
                cr = a["creative"]
                vd = ((cr.get("object_story_spec") or {}).get("video_data") or {})
                if vd.get("title") == HEADLINE:
                    print(f"  = «{a['name']}» already has the headline"); continue
                assert vd.get("video_id"), f"{a['name']}: creative {cr['id']} has no video_data"
                if cr["id"] not in clones:
                    print(f"  creative {cr['id']} «{cr.get('name')}» → clone with headline")
                    if CONFIRM:
                        spec = dict(cr["object_story_spec"])
                        nvd = dict(vd); nvd["title"] = HEADLINE
                        nvd.pop("image_hash", None) if nvd.get("image_url") else None
                        spec["video_data"] = nvd
                        clones[cr["id"]] = g.create_adcreative(acct, name=f"{cr.get('name')} · headline",
                                                               url_tags=cr.get("url_tags"), object_story_spec=spec)["id"]
                        print(f"    → {clones[cr['id']]}"); time.sleep(2)
                    else:
                        clones[cr["id"]] = "(dry)"
                print(f"  ad «{a['name']}» {a['id']} → {clones[cr['id']]}")
                if CONFIRM:
                    g._request("POST", a["id"], data={"creative": '{"creative_id": "%s"}' % clones[cr["id"]]}); time.sleep(1.5)
    print("\nHEADLINE DONE" + ("" if CONFIRM else " (dry-run)"))


if __name__ == "__main__":
    main()
