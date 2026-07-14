"""Read-only: why did the SG 'freestyle 2' ad (GOLF) get DISAPPROVED? Dump its
issues_info + ad_review_feedback so we know whether it's the creative (delete/replace)
or a fixable/appealable issue — and whether the same reason threatens the other SG ads
still in review. No writes.
"""
from __future__ import annotations

import json

from adbot.commands import graph_client
from adbot.settings import load_settings

AD = "120248220645020521"   # [SG] GOLF · freestyle 2 · DISAPPROVED


def main() -> None:
    g = graph_client(load_settings())
    a = g.get_object(AD, "id,name,effective_status,configured_status,"
                         "issues_info,ad_review_feedback,"
                         "creative{id,effective_object_story_id,object_story_id}")
    print(f"AD {a.get('id')} '{a.get('name')}'  effective={a.get('effective_status')} "
          f"configured={a.get('configured_status')}")
    cr = a.get("creative") or {}
    print(f"post = {cr.get('effective_object_story_id') or cr.get('object_story_id')}\n")

    print("ISSUES_INFO >>>")
    print(json.dumps(a.get("issues_info"), ensure_ascii=False, indent=2))
    print("\nAD_REVIEW_FEEDBACK >>>")
    print(json.dumps(a.get("ad_review_feedback"), ensure_ascii=False, indent=2))
    print("\nDONE.")


if __name__ == "__main__":
    main()
