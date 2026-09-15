# -*- coding: utf-8 -*-
"""Owner 2026-09-15: two new 拼接 videos into the 3 checked MY campaigns.

  Videos (pairing VERIFIED by Drive file names — Video 5.mp4 / Video 1.mp4):
    «拼接：Video 5：Trading 早就不是这样了！»  1SVB-kRxCw-rEl92aOhrZ9XblhKNc6PcZ
    «拼接：Video 1：用我的方法»                1mYbcI74Sb_jzR-0GVftELb1nymo2bwm3

  Into each of: BROAD MY 25+ | 0911 HOOK 重拍 · DAY TRADING 30-55 | 0914 ·
  BEER ALCOHOL 30-55 | 0914 — one NEW ad set (RM50/day PAUSED) per video per
  campaign, targeting + promoted_object + ad-set name cloned from that
  campaign's own existing ad set (Broad keeps broad, DT/BEER keep their hard
  interests + 30-55). Videos uploaded once, reused across campaigns.
  All-new clean captions (马丁 two-part; zero income wording). No special ad
  category on these campaigns already. Idempotent at (campaign, ad-name).
  Dry-run unless CONFIRM=true."""
from __future__ import annotations

import copy as _copy
import os
import time
from pathlib import Path

from adbot import cpa
from adbot.clients.drive import DriveClient
from adbot.commands import graph_client
from adbot.settings import REPO_ROOT, load_settings

from execute_build_0911_hook_144 import FIXED_TAIL, HEADLINE, SEP  # noqa: E402

CONFIRM = os.environ.get("CONFIRM", "").lower() in ("1", "true", "yes")
PACE = 6.0
DAILY = 5000
N = cpa.norm

CAMPAIGNS = [
    "BROAD MY 25+ | 0911 HOOK",
    "DAY TRADING 30-55 | 0914 HOOK",
    "BEER ALCOHOL 30-55 | 0914 HOOK",
]

P1_PJ5 = """还在用 15 分钟、一个小时，
盯着一堆图表做一单？

Trading 早就不是这样了。

不是你不够努力——
是你还在用旧的方法，
做现在的市场。

💬 Soo Cheng 老师常说：
「市场很快，
你要的是效率：快、狠、准。
一分钟内进场、出场，完成你的单子。」

做完该做的，就关电脑，
不用把一整晚交给屏幕。

📍 这套一分钟的做法怎么运作，
免费线上分享会里完整示范给你看。"""

P1_PJ1 = """学了很多课、看了很多视频，
结果呢？

现在该不该进，你不知道；
进了怕错，不进又怕错过——
最后变成：看很多，做很少。

不是 market 不好，
是你学的东西，
没有帮你做决定。

💬 Soo Cheng 老师常说：
「长期做交易，只需要搞懂三件事：
什么时候该出手，
做错了下一步怎么办，
什么时候该停。」

这三件事搞懂，
你基本上就可以自己走了。

📍 免费线上分享会，
就只专注讲这三个重点。"""

VIDEOS = [
    {"name": "拼接：Video 5：Trading 早就不是这样了！",
     "file": "1SVB-kRxCw-rEl92aOhrZ9XblhKNc6PcZ",          # Video 5.mp4（文件名已验证）
     "cap": P1_PJ5 + SEP + FIXED_TAIL.format(
         bullet="📊 为什么现在做交易，不需要看一堆复杂图表")},
    {"name": "拼接：Video 1：用我的方法",
     "file": "1mYbcI74Sb_jzR-0GVftELb1nymo2bwm3",          # Video 1.mp4（文件名已验证）
     "cap": P1_PJ1 + SEP + FIXED_TAIL.format(
         bullet="🧭 三个重点：什么时候出手、错了怎么办、什么时候停")},
]


def main() -> None:
    mode = "APPLY (CONFIRM=true)" if CONFIRM else "DRY-RUN (set confirm=true to build)"
    print(f"拼接 ×2 → 3 个 MY campaign（各 +2 ad set RM50 PAUSED）— {mode}\n")
    s = load_settings(REPO_ROOT / "config" / "config.yaml")
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
        tgt = _copy.deepcopy(sc.get("targeting") or {})
        for k in ("custom_audiences", "excluded_custom_audiences"):
            tgt.pop(k, None)
        age = tgt.get("age_range") or [tgt.get("age_min"), tgt.get("age_max")]
        targets.append({"camp": c, "aset_name": sc.get("name") or "AdSet",
                        "tgt": tgt, "promo": sc.get("promoted_object") or {}})
        print(f"clone ✓ «{(c.get('name') or '')[:44]}» ← adset «{(sc.get('name') or '')[:26]}» "
              f"age {age}")

    for v in VIDEOS:
        print(f"video: «{v['name']}»  drive={v['file'][:8]}…  caption={len(v['cap'])} chars")

    if not CONFIRM:
        print("\n▶ would: upload 2 videos once + 每个 campaign 建 2 × [adset RM50 PAUSED + ad ACTIVE]")
        return

    # 重跑省 quota：账户里已存在的同名 video 直接复用，不重新下载/上传
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
                print(f"  · «{v['name'][:30]}» 已在 «{(t['camp'].get('name') or '')[:30]}» — skip")
                continue
            if v["file"] not in uploaded:
                if drive is None:
                    drive = DriveClient(s.secrets.google_sa_json)
                p = drive.download_file(v["file"], Path(f"/tmp/pj_{i}.mp4"))
                vid = g.upload_video(acct, str(p), v["name"])
                time.sleep(PACE)
                uploaded[v["file"]] = (vid, g.get_video_thumbnail(vid))
                print(f"   ⬆ video {vid}  thumb={'✓' if uploaded[v['file']][1] else '—'}")
            vid, thumb = uploaded[v["file"]]
            aset = g.create_adset(
                acct, name=t["aset_name"], campaign_id=camp_id, daily_budget=DAILY,
                optimization_goal="OFFSITE_CONVERSIONS", billing_event="IMPRESSIONS",
                bid_strategy="LOWEST_COST_WITHOUT_CAP", promoted_object=t["promo"],
                targeting=_copy.deepcopy(t["tgt"]), status="PAUSED")
            time.sleep(PACE)
            video_data = {"video_id": vid, "title": HEADLINE, "message": v["cap"],
                          "call_to_action": {"type": s.meta.call_to_action or "LEARN_MORE",
                                             "value": {"link": link}}}
            if thumb:
                video_data["image_url"] = thumb
            spec = {"name": f"MY | 0915 拼接 | {v['name']}",
                    "object_story_spec": {"page_id": s.meta.page_id,
                                          "video_data": video_data}}
            if s.meta.url_tags:
                spec["url_tags"] = s.meta.url_tags
            cr = g.create_adcreative(acct, **spec)
            ad = g.create_ad(acct, name=v["name"], adset_id=aset["id"],
                             creative={"creative_id": cr["id"]},
                             status="ACTIVE", conversion_domain=conv)
            print(f"  ✓ «{(t['camp'].get('name') or '')[:30]}» + adset {aset['id']}(PAUSED) "
                  f"+ ad {ad['id']}  «{v['name'][:28]}»")
            time.sleep(PACE)

    print("\nBUILD 0915 拼接 DONE — 新 ad set 全 PAUSED，owner 审后自行开启。")


if __name__ == "__main__":
    main()
