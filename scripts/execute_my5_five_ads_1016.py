# -*- coding: utf-8 -*-
"""owner 2026-10-16「MY 也每条放 5 支」— add a 5th ad «Video：用我的方法» to each MY 5.0 Webinarkit campaign
(new video creative from the MY 3.0 dark post «拼接：Video 1：用我的方法», video 1426088792952086, validated on
MY 5.0; link → -wed). NOT 不选 forex: it was rejected on MY 5.0 on 10/8. Names → 1-1-5; budgets unchanged
(RM150 × 4). Ban gate. CONFIRM=true writes; otherwise dry-run."""
from __future__ import annotations

import os
import re
import time

from adbot import compliance
from adbot.commands import graph_client
from adbot.settings import REPO_ROOT, load_settings

CONFIRM = os.environ.get("CONFIRM", "").lower() in ("1", "true", "yes")
LINK = "https://soochenginvesting.com/webinarkit-register-wed"
OLD_MY = "act_759339046918885"
SRC_NAME, SRC_VID = "拼接：Video 1：用我的方法", "1426088792952086"
NEW = "Video：用我的方法"
PAGE, IG = "1001334883061622", "17841480427751602"
CAMPS = {  # campaign -> ad set
    "120251454680840329": "120251454695860329",   # LUXURY MY
    "120251454700150329": "120251454700740329",   # BUSINESS OWNER
    "120251454704570329": "120251454705570329",   # BROAD MY
    "120251454713670329": "120251454714430329",   # DAY TRADING
}


def main() -> None:
    s = load_settings(REPO_ROOT / "config" / "config.my5.yaml")
    g = graph_client(s)
    acct = s.meta.account_path
    assert not compliance.filter_banned([NEW, SRC_NAME], s.compliance.banned_creatives), "banned"
    old = g._get_all(OLD_MY + "/ads", {"fields": "name,creative{object_story_spec}", "limit": "500"})
    a = next(x for x in old if (x.get("name") or "").replace("🌟", "").strip() == SRC_NAME and
             (((x.get("creative") or {}).get("object_story_spec") or {}).get("video_data") or {}).get("video_id") == SRC_VID)
    vd0 = a["creative"]["object_story_spec"]["video_data"]
    ref = g.get_object("120251454697280329", "creative{url_tags}")        # a MY Webinarkit ad built today
    url_tags = ref["creative"]["url_tags"]
    print(f"source video {SRC_VID} · caption {len(vd0.get('message') or '')} chars «{(vd0.get('message') or '')[:24]}» · url_tags {url_tags}")
    have_cr = {c.get("name"): c["id"] for c in g._get_all(acct + "/adcreatives", {"fields": "id,name", "limit": "500"})}
    cr = have_cr.get(f"{NEW} · webinarkit-wed")
    if CONFIRM and not cr:
        vd = {"video_id": SRC_VID, "message": vd0["message"], "call_to_action": {"type": "LEARN_MORE", "value": {"link": LINK}}}
        if vd0.get("image_url"):
            vd["image_url"] = vd0["image_url"]
        elif vd0.get("image_hash"):
            vd["image_hash"] = vd0["image_hash"]
        cr = g.create_adcreative(acct, name=f"{NEW} · webinarkit-wed", url_tags=url_tags,
                                 object_story_spec={"page_id": PAGE, "instagram_user_id": IG, "video_data": vd})["id"]
        print(f"creative → {cr}"); time.sleep(2)
    for cid, sid in CAMPS.items():
        c = g.get_object(cid, "name,status,daily_budget")
        ads = [x for x in g._get_all(sid + "/ads", {"fields": "name,status", "limit": "50"}) if x.get("status") not in ("DELETED", "ARCHIVED")]
        names = [x["name"] for x in ads]
        new_name = re.sub(r"\| 1-1-\d+ \|", f"| 1-1-{len(ads) + (0 if NEW in names else 1)} |", c["name"])
        print(f"«{c['name']}» {c.get('status')} RM{int(c['daily_budget']) // 100} · ads {names} · add {NEW not in names} · → «{new_name}»")
        if not CONFIRM:
            continue
        if NEW not in names:
            r = g.create_ad(acct, name=NEW, adset_id=sid, creative={"creative_id": cr}, status="ACTIVE")
            print(f"   + ad {r['id']}"); time.sleep(2)
        if new_name != c["name"]:
            g._request("POST", cid, data={"name": new_name}); time.sleep(1)
        n = len([x for x in g._get_all(sid + "/ads", {"fields": "status", "limit": "50"}) if x.get("status") not in ("DELETED", "ARCHIVED")])
        print(f"   ✅ «{g.get_object(cid, 'name')['name']}» · {n} ads")
    print("MY FIVE DONE" + ("" if CONFIRM else " (dry-run)"))


if __name__ == "__main__":
    main()
