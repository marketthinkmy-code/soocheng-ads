# -*- coding: utf-8 -*-
"""owner 2026-11-10「approve，照改好的版本建」— NEW VIDEO test build, MY 5.0 + SG, everything created under a PAUSED campaign.
Per account 3 campaigns (one per audience = top-3 by Paid Student List sales), each ABO with 5 ad sets × 1 video × RM50/day:
  MY : News · Luxury Goods · Broad          SG : Broad · Travel · Golf Pickleball
Copy + headline are read LIVE from Notion (Video 57–61) and must equal scripts/specs_newvideo_1110.json; videos come from the
SA-readable Drive copies whose pairing was verified frame-by-frame (11/10). Interest ad sets: hard age 28–65, Advantage+ off
(interests cloned from the account's own past ad set of that audience); Broad: Advantage+ on, age_range [28,65].
Link https://soochenginvesting.com/webinarkit-register-wed, Webinarkit conversion (promoted_object copied from the live Broad ad
set of that account, asserted to be the Webinarkit custom conversion). Ban gate. Idempotent by name. CONFIRM=true writes."""
from __future__ import annotations

import json
import os
import time
from pathlib import Path

from adbot import compliance
from adbot.clients.drive import DriveClient
from adbot.clients.notion import NotionClient
from adbot.commands import graph_client
from adbot.notion_captions import fetch_captions
from adbot.settings import REPO_ROOT, load_settings

CONFIRM = os.environ.get("CONFIRM", "").lower() in ("1", "true", "yes")
LINK = "https://soochenginvesting.com/webinarkit-register-wed"
SPECS = json.load(open(REPO_ROOT / "scripts" / "specs_newvideo_1110.json", encoding="utf-8"))
ACCTS = {
    "MY": {"cfg": "config.my5.yaml", "prefix": "(Webinarkit) STOCKBLOOM | NEW VIDEO · {aud} | 1-5-1 | 1110",
           "broad_set": "120251454705570329", "ref_ad": "120251456191090329",
           "auds": [("News", "News | MY 28+", "interest", ("news",), ("act_759339046918885", "act_2282909119125229")),
                    ("Luxury Goods", "Luxury Goods | MY 28+", "interest", ("luxury",), ("act_2285351942292267", "act_759339046918885")),
                    ("Broad", "Broad | MY 28+", "broad", (), ())]},
    "SG": {"cfg": "config.sg.yaml", "prefix": "(Webinarkit) [SG] STOCKBLOOM | NEW VIDEO · {aud} | 1-5-1 | 1110",
           "broad_set": "120250144811110521", "ref_ad": "120250144813480521",
           "auds": [("Broad", "Broad | SG 28+", "broad", (), ()),
                    ("Travel", "Travel | SG 28+", "interest", ("travel",), ("act_893025326577600",)),
                    ("Golf Pickleball", "Golf Pickleball | SG 28+", "interest", ("golf",), ("act_893025326577600",))]},
}
BUDGET = 5000          # RM50 / ad set / day (ABO)


def T(fn, *a, **k):
    """Retry a Graph call through Meta's per-account throttle (run 42795285614 hit «too many calls» mid-build)."""
    for i in range(10):
        try:
            return fn(*a, **k)
        except Exception as e:                                           # noqa: BLE001
            if "throttled" not in str(e) and "too many calls" not in str(e).lower() and "request limit" not in str(e).lower():
                raise
            print(f"      … Meta 限流，等 120s 再试（{i + 1}/10）"); time.sleep(120)
    raise RuntimeError("still throttled after 10 tries")


def link_of(cr: dict) -> str:
    vd = (cr.get("object_story_spec") or {}).get("video_data") or {}
    return ((vd.get("call_to_action") or {}).get("value") or {}).get("link") or ""


def find_interest_set(g, accts, keys):
    """Newest ad set (any status) in the given accounts whose name contains one of `keys` and that has interests."""
    best = None
    for acct in accts:
        try:
            sets = g._get_all(acct + "/adsets", {"fields": "name,created_time,targeting,campaign{name}", "limit": "500"})
        except Exception as e:                                           # noqa: BLE001
            print(f"      (读不到 {acct}: {str(e)[:80]})"); continue
        for s in sets:
            if any(k in s["name"].lower() for k in keys) and (s.get("targeting") or {}).get("flexible_spec"):
                if best is None or s["created_time"] > best[1]["created_time"]:
                    best = (acct, s)
    return best


def main() -> None:
    # ── copy: Notion live == spec ──
    s0 = load_settings(REPO_ROOT / "config" / "config.my5.yaml")
    caps = fetch_captions(NotionClient(s0.secrets.notion_token), s0.notion.database_id)
    for sp in SPECS:
        c = caps.get(f"video_{sp['n']}")
        assert c and c["caption"] == sp["caption"] and c["headline"] == sp["headline"], f"Notion video_{sp['n']} ≠ spec"
    print(f"NEW VIDEO build — {'APPLY' if CONFIRM else 'DRY-RUN'} · Notion Video 57–61 文案/标题 = 审批版 ✅")
    for sp in SPECS:
        print(f"  V{sp['video']} «{sp['ad_name']}» ← {sp['file']} (build copy {sp['drive_build']}) · {sp['headline']} · {len(sp['caption'])} 字")
    local = {}
    if CONFIRM:
        d = DriveClient(s0.secrets.google_sa_json)
        for sp in SPECS:
            local[sp["n"]] = str(d.download_file(sp["drive_build"], Path(f"/tmp/nv_{sp['n']}.mp4")))

    for key, A in ACCTS.items():
        s = load_settings(REPO_ROOT / "config" / A["cfg"])
        g = graph_client(s)
        acct = s.meta.account_path
        names = [sp["ad_name"] for sp in SPECS]
        hits = compliance.filter_banned(names, s.compliance.banned_creatives)
        assert not hits, f"⛔ 禁跑命中: {hits}"
        print(f"\n################ {key} {acct} · 禁跑闸 ✅")
        ref_ad = g.get_object(A["ref_ad"], "name,creative{id,url_tags,object_story_spec}")
        rc = ref_ad["creative"]
        assert link_of(rc) == LINK, f"ref creative links to {link_of(rc)}"
        url_tags, page, ig = rc.get("url_tags"), rc["object_story_spec"]["page_id"], rc["object_story_spec"].get("instagram_user_id")
        print(f"  参考素材 ad {A['ref_ad']} «{ref_ad['name']}» → {LINK} · page {page} · ig {ig} · url_tags {url_tags}")
        bs = g.get_object(A["broad_set"], "name,targeting,promoted_object,optimization_goal,billing_event,attribution_spec,"
                                           "regional_regulated_categories,regional_regulation_identities")
        po = bs["promoted_object"]
        cc = g.get_object(po["custom_conversion_id"], "name,rule,is_archived")
        assert "webinarkit" in (cc.get("name") or "").lower() and "webinarkit-thankyou" in (cc.get("rule") or "") and not cc.get("is_archived")
        print(f"  转化: «{bs['name']}» {A['broad_set']} → pixel {po.get('pixel_id')} · custom conversion {po['custom_conversion_id']} «{cc['name']}» ✅ · "
              f"opt {bs['optimization_goal']} · regional {bs.get('regional_regulated_categories')}")
        bt = bs["targeting"]
        base = {k: bt[k] for k in ("geo_locations", "locales") if k in bt}
        targets = {}
        for aud, sname, mode, keys, srcs in A["auds"]:
            if mode == "broad":
                t = dict(base, age_min=bt.get("age_min", 25), age_max=65, age_range=[28, 65], targeting_automation={"advantage_audience": 1})
                print(f"  受众 {aud}: Broad · geo {base['geo_locations'].get('countries')} · locales {base.get('locales')} · Advantage+ 开 · 建议 28–65")
            else:
                hit = find_interest_set(g, srcs, keys)
                assert hit, f"{aud}: 找不到来源 ad set"
                sacct, src = hit
                st = src["targeting"]
                t = dict(base, flexible_spec=st["flexible_spec"], age_min=28, age_max=65, targeting_automation={"advantage_audience": 0})
                if st.get("exclusions"):
                    t["exclusions"] = st["exclusions"]
                ints = [i.get("name") for sp_ in st["flexible_spec"] for i in (sp_.get("interests") or [])]
                beh = [i.get("name") for sp_ in st["flexible_spec"] for i in (sp_.get("behaviors") or [])]
                print(f"  受众 {aud}: 复制自 {sacct} «{src['campaign']['name']}» › «{src['name']}» ({src['id']}, {src['created_time'][:10]}) · "
                      f"硬锁 28–65 · Advantage+ 关 · geo {base['geo_locations'].get('countries')}\n      兴趣 {ints}" + (f" · 行为 {beh}" if beh else ""))
            targets[aud] = t
        camps = {c["name"]: c for c in T(g._get_all, acct + "/campaigns", {"fields": "name,effective_status", "limit": "500"})}
        for aud, sname, *_ in A["auds"]:
            cname = A["prefix"].format(aud=aud)
            print(f"  ▶ «{cname}» ABO · PAUSED · 已存在 {cname in camps}")
            for sp in SPECS:
                print(f"      › «{sname} · V{sp['video']}» RM{BUDGET // 100} · ad «{sp['ad_name']}»")
        if not CONFIRM:
            continue

        # ── videos + creatives (one per video per account; reused across the 3 audiences) ──
        all_cr = {c.get("name"): c for c in T(g._get_all, acct + "/adcreatives", {"fields": "id,name,object_story_spec", "limit": "3000"})}
        cr = {}
        for sp in SPECS:
            ex = all_cr.get(sp["ad_name"])
            vd0 = ((ex or {}).get("object_story_spec") or {}).get("video_data") or {}
            if ex and link_of(ex) == LINK and vd0.get("message") == sp["caption"] and vd0.get("title") == sp["headline"]:
                cr[sp["n"]] = ex["id"]; print(f"  = V{sp['video']} 已有素材 {ex['id']}"); continue
            vid = T(g.upload_video, acct, local[sp["n"]], sp["ad_name"])
            thumb = g.get_video_thumbnail(vid)
            vd = {"video_id": vid, "message": sp["caption"], "title": sp["headline"],
                  "call_to_action": {"type": "LEARN_MORE", "value": {"link": LINK}}}
            if thumb:
                vd["image_url"] = thumb
            oss = {"page_id": page, "video_data": vd}
            if ig:
                oss["instagram_user_id"] = ig
            cr[sp["n"]] = T(g.create_adcreative, acct, name=sp["ad_name"], url_tags=url_tags, object_story_spec=oss)["id"]
            print(f"  ✅ V{sp['video']} video {vid} · creative {cr[sp['n']]}"); time.sleep(5)

        # ── campaigns / ad sets / ads ──
        for aud, sname, *_ in A["auds"]:
            cname = A["prefix"].format(aud=aud)
            if cname in camps:
                cid = camps[cname]["id"]; print(f"  = «{cname}» 已存在 {cid}")
            else:
                cid = T(g.create_campaign, acct, name=cname, objective="OUTCOME_SALES", status="PAUSED", special_ad_categories=[],
                                        buying_type="AUCTION", is_adset_budget_sharing_enabled=False)["id"]
                time.sleep(5)
            have = {x["name"]: x["id"] for x in T(g._get_all, cid + "/adsets", {"fields": "name", "limit": "50"})}
            out = []
            for sp in SPECS:
                an = f"{sname} · V{sp['video']}"
                if an in have:
                    out.append(f"V{sp['video']}=adset {have[an]} (已存在)"); continue
                a = T(g.create_adset, acct, name=an, campaign_id=cid, status="ACTIVE", daily_budget=BUDGET,
                                   bid_strategy="LOWEST_COST_WITHOUT_CAP", optimization_goal=bs["optimization_goal"],
                                   billing_event=bs["billing_event"], targeting=targets[aud], promoted_object=po,
                                   attribution_spec=bs.get("attribution_spec"),
                                   regional_regulated_categories=bs.get("regional_regulated_categories") or [],
                                   regional_regulation_identities=bs.get("regional_regulation_identities") or {})["id"]
                time.sleep(5)
                ad = T(g.create_ad, acct, name=sp["ad_name"], adset_id=a, creative={"creative_id": cr[sp["n"]]}, status="ACTIVE")["id"]
                time.sleep(5)
                out.append(f"V{sp['video']}=adset {a}/ad {ad}")
            print(f"  ✅ «{cname}» campaign {cid} (PAUSED) · " + " · ".join(out))
    print("\nBUILD DONE" + ("" if CONFIRM else " (dry-run)"))


if __name__ == "__main__":
    main()
