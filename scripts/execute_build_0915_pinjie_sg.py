# -*- coding: utf-8 -*-
"""Owner 2026-09-15「也建在 SG 的这三个」— the two 拼接 videos into:

  [SG] STOCKBLOOM | GOLF PICKLEBALL 30-55 | 0914 HOOK 重拍
  [SG] STOCKBLOOM | BROAD SG 25+ | 0911 HOOK 重拍
  [SG] STOCKBLOOM | PURCHASE LAL 1-5% | 0910 重拍

  One NEW ad set (RM50/day PAUSED, SG regulated fields) per video per campaign.
  Targeting cloned VERBATIM from each campaign's own existing ad set — no
  stripping, because the LAL 0910 campaign's audience lives in custom_audiences
  (stripping would silently turn it broad). Captions/names imported from the MY
  script (pairing verified by Drive file names). Videos uploaded once to the SG
  account (advideos reuse on rerun). Idempotent. Dry-run unless CONFIRM=true."""
from __future__ import annotations

import copy as _copy
import os
import time
from pathlib import Path

from adbot import cpa
from adbot.clients.drive import DriveClient
from adbot.commands import graph_client
from adbot.settings import REPO_ROOT, load_settings

from execute_build_0915_pinjie import VIDEOS  # noqa: E402  names/files/captions

CONFIRM = os.environ.get("CONFIRM", "").lower() in ("1", "true", "yes")
PACE = 6.0
DAILY = 5000
N = cpa.norm

CAMPAIGNS = [
    "GOLF PICKLEBALL 30-55 | 0914",
    "BROAD SG 25+ | 0911 HOOK",
    "PURCHASE LAL 1-5% | 0910 重拍",
]
REG_IDENTITIES = {
    "singapore_universal_beneficiary": "1466824068581066",
    "singapore_universal_payer": "1466824068581066",
}
REGIONAL = ["SINGAPORE_UNIVERSAL"]


def main() -> None:
    mode = "APPLY (CONFIRM=true)" if CONFIRM else "DRY-RUN (set confirm=true to build)"
    print(f"拼接 ×2 → 3 个 SG campaign（各 +2 ad set RM50 PAUSED）— {mode}\n")
    s = load_settings(REPO_ROOT / "config" / "config.sg.yaml")
    g = graph_client(s)
    acct = s.meta.account_path
    conv = s.meta.conversion_domain_bare or None
    link = s.meta.lead_destination.link_url

    camps = g._get_all(f"{acct}/campaigns", {"fields": "id,name", "limit": "500"})
    time.sleep(1)
    targets = []
    for frag in CAMPAIGNS:
        hits = [c for c in camps if frag in (c.get("name") or "")]
        if len(hits) != 1:
            print(f"⛔ «{frag}» 匹配 {len(hits)} 个 campaign — 停")
            return
        c = hits[0]
        sc = (g._get_all(f"{c['id']}/adsets",
                         {"fields": "id,name,targeting,promoted_object", "limit": "5"})
              or [None])[0]
        time.sleep(1)
        if not sc:
            print(f"⛔ «{frag}» 没有现成 ad set 可 clone — 停")
            return
        tgt = _copy.deepcopy(sc.get("targeting") or {})   # 原封 clone（LAL 受众保留）
        age = tgt.get("age_range") or [tgt.get("age_min"), tgt.get("age_max")]
        n_ca = len(tgt.get("custom_audiences") or [])
        targets.append({"camp": c, "aset_name": sc.get("name") or "AdSet",
                        "tgt": tgt, "promo": sc.get("promoted_object") or {}})
        print(f"clone ✓ «{(c.get('name') or '')[:46]}» ← «{(sc.get('name') or '')[:26]}» "
              f"age {age} · custom_audiences×{n_ca}")

    for v in VIDEOS:
        print(f"video: «{v['name']}»  drive={v['file'][:8]}…")

    if not CONFIRM:
        print("\n▶ would: upload 2 videos once (advideos reuse) + 每 campaign 2 × "
              "[adset RM50 PAUSED (SG regulated) + ad ACTIVE]")
        return

    uploaded = {}
    try:
        acct_vids = g._get_all(f"{acct}/advideos", {"fields": "id,title", "limit": "200"})
        time.sleep(1)
        for v in VIDEOS:
            hit = next((x for x in acct_vids if (x.get("title") or "") == v["name"]), None)
            if hit:
                uploaded[v["file"]] = (hit["id"], g.get_video_thumbnail(hit["id"]))
                print(f"   ↺ reuse video {hit['id']}  «{v['name'][:30]}»")
                time.sleep(1)
    except Exception as e:  # noqa: BLE001
        print(f"   （advideos 查询失败，将直接上传：{str(e)[:80]}）")
    drive = None
    for t in targets:
        camp_id = t["camp"]["id"]
        have = {N(a.get("name") or "") for a in g._get_all(
            f"{camp_id}/ads", {"fields": "name", "limit": "50"})}
        for i, v in enumerate(VIDEOS):
            if N(v["name"]) in have:
                print(f"  · «{v['name'][:30]}» 已在 «{(t['camp'].get('name') or '')[:34]}» — skip")
                continue
            if v["file"] not in uploaded:
                if drive is None:
                    drive = DriveClient(s.secrets.google_sa_json)
                p = drive.download_file(v["file"], Path(f"/tmp/pjsg_{i}.mp4"))
                vid = g.upload_video(acct, str(p), v["name"])
                time.sleep(PACE)
                uploaded[v["file"]] = (vid, g.get_video_thumbnail(vid))
                print(f"   ⬆ video {vid}  thumb={'✓' if uploaded[v['file']][1] else '—'}")
            vid, thumb = uploaded[v["file"]]
            aset = g.create_adset(
                acct, name=t["aset_name"], campaign_id=camp_id, daily_budget=DAILY,
                optimization_goal="OFFSITE_CONVERSIONS", billing_event="IMPRESSIONS",
                bid_strategy="LOWEST_COST_WITHOUT_CAP", promoted_object=t["promo"],
                targeting=_copy.deepcopy(t["tgt"]), status="PAUSED",
                regional_regulated_categories=REGIONAL,
                regional_regulation_identities=REG_IDENTITIES)
            time.sleep(PACE)
            video_data = {"video_id": vid, "title": "🚨 教你如何在 1️⃣ 分钟内，判读市场节奏",
                          "message": v["cap"],
                          "call_to_action": {"type": s.meta.call_to_action or "LEARN_MORE",
                                             "value": {"link": link}}}
            if thumb:
                video_data["image_url"] = thumb
            spec = {"name": f"SG | 0915 拼接 | {v['name']}",
                    "object_story_spec": {"page_id": s.meta.page_id,
                                          "video_data": video_data}}
            if s.meta.url_tags:
                spec["url_tags"] = s.meta.url_tags
            cr = g.create_adcreative(acct, **spec)
            ad = g.create_ad(acct, name=v["name"], adset_id=aset["id"],
                             creative={"creative_id": cr["id"]},
                             status="ACTIVE", conversion_domain=conv)
            print(f"  ✓ «{(t['camp'].get('name') or '')[:34]}» + adset {aset['id']}(PAUSED) "
                  f"+ ad {ad['id']}  «{v['name'][:28]}»")
            time.sleep(PACE)

    print("\nBUILD 0915 拼接 SG DONE — 新 ad set 全 PAUSED，owner 审后自行开启。")


if __name__ == "__main__":
    main()
