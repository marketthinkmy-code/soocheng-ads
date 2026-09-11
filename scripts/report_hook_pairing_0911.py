# -*- coding: utf-8 -*-
"""READ-ONLY: owner fixed the HOOK 1-4-4 pairing himself in Ads Manager
(「我改完了，你自己看，都是對的」). Read back every ad in the campaign and print
the final (ad name ↔ video file ↔ caption) mapping so the record matches reality."""
from __future__ import annotations

from adbot.commands import graph_client
from adbot.settings import REPO_ROOT, load_settings

CAMP = "120248807549960575"     # STOCKBLOOM | BROAD MY 25+ | 0911 HOOK 重拍
VIDEO_FILE = {                  # video_id uploaded in run 252 -> Drive 文件名
    "1389280419352027": "HOOK 3 (drive 1RNE…)",
    "2255229208351500": "HOOK 4 (drive 1miH…)",
    "1777022643249778": "HOOK 2 (drive 1EHk…)",
    "1687663009590997": "HOOK 1 (drive 1XCT…)",
}
CAPS = {"一单，你用了": "盖电脑 文案", "外汇做过，黄金": "不选forex 文案",
        "「诶，做么你": "不用看盘 文案", "黄金炒过，外汇": "炒过那么多 文案"}


def main() -> None:
    s = load_settings(REPO_ROOT / "config" / "config.yaml")
    g = graph_client(s)
    ads = g._get_all(
        f"{CAMP}/ads",
        {"fields": "id,name,status,effective_status,"
                   "adset{id,name,status,targeting},"
                   "creative{id,body,object_story_spec}",
         "limit": "25"})
    print(f"campaign {CAMP} — {len(ads)} ads\n")
    for a in ads:
        cr = a.get("creative") or {}
        oss = cr.get("object_story_spec") or {}
        vid = str((oss.get("video_data") or {}).get("video_id") or "?")
        body = (cr.get("body") or "").strip()[:12]
        cap = next((v for k, v in CAPS.items() if body.startswith(k[:6])), f"未知文案「{body}…」")
        aset = a.get("adset") or {}
        tgt = aset.get("targeting") or {}
        age = tgt.get("age_range") or [tgt.get("age_min"), tgt.get("age_max")]
        print(f"◆ «{a.get('name')}»  [{a.get('effective_status')}]")
        print(f"   video: {VIDEO_FILE.get(vid, '新上传/未知 id=' + vid)}")
        print(f"   caption: {cap} · adset age {age}")
    print("\nPAIRING READ DONE (read-only)")


if __name__ == "__main__":
    main()
