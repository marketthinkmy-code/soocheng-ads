# -*- coding: utf-8 -*-
"""owner 2026-10-16: the owner built «freestyle: korea» (ad 120251455974450329) in the MY Webinarkit DAY TRADING
ad set — reuse its post (link → webinarkit-register-wed) in every other Webinarkit ad set built today:
MY 5.0 LUXURY / BUSINESS OWNER / BROAD (same creative id) and SG BROAD / LUXURY GOODS / LAL 5% / TRAVEL
(new SG creative from the same post id). Checks the link first; ban gate; skips ad sets that already carry it.
CONFIRM=true writes; otherwise dry-run."""
from __future__ import annotations

import json
import os
import time

from adbot import compliance
from adbot.commands import graph_client
from adbot.settings import REPO_ROOT, load_settings

CONFIRM = os.environ.get("CONFIRM", "").lower() in ("1", "true", "yes")
SRC_AD = "120251455974450329"
WANT_LINK = "webinarkit-register-wed"
MY_SETS = ["120251454695860329", "120251454700740329", "120251454705570329"]
SG_SETS = ["120249918193310521", "120249918195680521", "120249918199040521", "120249918201950521"]


def main() -> None:
    my = load_settings(REPO_ROOT / "config" / "config.my5.yaml")
    sg = load_settings(REPO_ROOT / "config" / "config.sg.yaml")
    g = graph_client(my)
    ad = g.get_object(SRC_AD, "name,status,effective_status,adset{name},creative{id,url_tags,effective_object_story_id,object_story_spec,asset_feed_spec}")
    cr = ad["creative"]
    name = ad["name"]
    blob = json.dumps(cr, ensure_ascii=False)
    print(f"source «{name}» {ad.get('status')}/{ad.get('effective_status')} @ «{ad['adset']['name']}» · creative {cr['id']} · post {cr.get('effective_object_story_id')}")
    print(f"  url_tags {cr.get('url_tags')}")
    print(f"  link ok: {WANT_LINK in blob}")
    assert WANT_LINK in blob, "creative does not point to webinarkit-register-wed — stop"
    assert not compliance.is_banned(name, my.compliance.banned_creatives), "banned name"
    post = cr.get("effective_object_story_id")
    sg_cr = None
    for label, sets, acct in (("MY", MY_SETS, my.meta.account_path), ("SG", SG_SETS, sg.meta.account_path)):
        for sid in sets:
            time.sleep(1)
            aset = g.get_object(sid, "name,campaign{name}")
            have = [a.get("name") for a in g._get_all(sid + "/ads", {"fields": "name", "limit": "20"})]
            tag = f"{label} «{aset['campaign']['name'][:52]}»"
            if name in have:
                print(f"  = {tag}: already has «{name}»"); continue
            print(f"  → {tag}: add «{name}»")
            if not CONFIRM:
                continue
            if label == "MY":
                cid = cr["id"]
            else:
                if not sg_cr:
                    sg_cr = g.create_adcreative(acct, name=f"{name} · webinarkit-wed (post reuse)", object_story_id=post,
                                                url_tags=cr.get("url_tags"))["id"]
                    print(f"    SG creative {sg_cr}"); time.sleep(2)
                cid = sg_cr
            r = g.create_ad(acct, name=name, adset_id=sid, creative={"creative_id": cid}, status="ACTIVE")
            print(f"    ad {r['id']}"); time.sleep(2)
    print("KOREA DONE" + ("" if CONFIRM else " (dry-run)"))


if __name__ == "__main__":
    main()
