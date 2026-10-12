# -*- coding: utf-8 -*-
"""owner 2026-10-12「全部」— SG horizontal scale for the 14/10 live: the winner creative × proven audiences.

  A/B/C  existing 🌟 chains get one post-reuse «HOOK：Video 12：不选 forex 不选黄金» ad (created PAUSED = the gate),
         every other ad in that ad set is PAUSED at ad level, campaign + ad set switched ACTIVE, CBO set to RM65:
         🌟 PURCHASE LAL 5% · 🌟 GOLF PICKBLEBALL · 🌟 PRIORITY BANKING
  G      «PURCHASE LAL 1% | 1-1-1 | 1012»  new campaign CBO RM65 · ad set PAUSED gate · 1 ad —
         audience = 1 % lookalike built from the same purchase seed the LAL 5 % chain uses (reused if one exists)
  F      «RETARGET LP 14D | 1-1-1 | 1012»  new campaign CBO RM40 · ad set PAUSED gate · 1 ad —
         audience = pixel PageView last 14 d minus CompleteRegistration last 14 d (website custom audience)
New ad sets: SG, age 28-65 hard, Advantage+ audience OFF, locales from config. Post reuse only (no new copy);
ban gate on the ad name; idempotent by names. Dry-run unless CONFIRM=true. No PII."""
from __future__ import annotations

import json
import os
import time

from adbot import compliance
from adbot.clients.graph import _encode
from adbot.commands import graph_client
from adbot.settings import REPO_ROOT, load_settings

CONFIRM = os.environ.get("CONFIRM", "").lower() in ("1", "true", "yes")
PACE = 4.0
AD_NAME = "HOOK：Video 12：不选 forex 不选黄金"
WINNER_POST_FALLBACK = "1001334883061622_122123316747286543"
CHAINS = [  # (campaign-name key, CBO cents)
    ("🌟 [SG] STOCKBLOOM | PURCHASE LAL 5%", 6500),
    ("🌟 [SG] STOCKBLOOM | GOLF PICKBLEBALL", 6500),
    ("PRIORITY BANKING", 6500),                       # the 🌟-prefixed exact key matched nothing on 10/12
]
LAL1_AUD = "LAL 1% | Purchase seed (SG) | 1012"
LAL1_CAMP, LAL1_ASET, LAL1_BUDGET = "[SG] STOCKBLOOM | PURCHASE LAL 1% | 1-1-1 | 1012", "Purchase LAL 1% | SG 28+", 6500
RT_AUD = "LP 14d visitors not registered (SG) | 1012"
RT_CAMP, RT_ASET, RT_BUDGET = "[SG] STOCKBLOOM | RETARGET LP 14D | 1-1-1 | 1012", "Retarget LP 14d | SG 28+", 4000
log_done, log_skip = [], []


def rm(c) -> str:
    return f"RM{int(c or 0) / 100:.0f}"


def main() -> None:
    s = load_settings(REPO_ROOT / "config" / "config.sg.yaml")
    g = graph_client(s)
    acct = s.meta.account_path
    conv = s.meta.conversion_domain_bare or None
    pixel = s.meta.pixel_id
    cats = list(s.meta.special_ad_categories)
    print(f"SG build-more on {acct} — {'APPLY' if CONFIRM else 'DRY-RUN'}\n")
    assert not compliance.banned_reason(AD_NAME, s.compliance.banned_creatives), "winner banned?!"

    camps = g._get_all(acct + "/campaigns", {"fields": "id,name,status,effective_status,daily_budget", "limit": "300"})
    time.sleep(0.8)

    def find(key: str):
        hits = [c for c in camps if key in (c.get("name") or "")]
        return hits

    # winner post (from the live 0911 ad) ------------------------------------------------
    post = WINNER_POST_FALLBACK
    c0911 = [c for c in find("0911 HOOK") if c.get("status") == "ACTIVE"]
    if c0911:
        for a in g._get_all(c0911[0]["id"] + "/ads", {"fields": "name,status,creative{effective_object_story_id}", "limit": "50"}):
            if (a.get("name") or "") == AD_NAME and a.get("status") == "ACTIVE":
                post = (a.get("creative") or {}).get("effective_object_story_id") or post
        time.sleep(0.6)
    print(f"winner post: {post}\n")

    def make_ad(aset_id: str, tag: str, status: str):
        spec = {"name": f"SG | {AD_NAME} @ {tag}", "object_story_id": post}
        if s.meta.url_tags:
            spec["url_tags"] = s.meta.url_tags
        cr = g.create_adcreative(acct, **spec)
        ad = g.create_ad(acct, name=AD_NAME, adset_id=aset_id, creative={"creative_id": cr["id"]},
                         status=status, conversion_domain=conv)
        time.sleep(PACE)
        return ad["id"]

    # ── A/B/C ───────────────────────────────────────────────────────────────────────────
    for key, budget in CHAINS:
        hits = find(key)
        if len(hits) != 1:
            log_skip.append(f"{key}: {len(hits)} campaigns matched"); print(f"✗ {key}: matched {[c.get('name') for c in hits]}\n"); continue
        c = hits[0]
        sets = g._get_all(c["id"] + "/adsets", {"fields": "id,name,status,effective_status,daily_budget", "limit": "20"})
        time.sleep(0.6)
        if not sets:
            log_skip.append(f"{key}: no ad set"); print(f"✗ {key}: no ad set\n"); continue
        aset = sets[0]
        ads = g._get_all(aset["id"] + "/ads", {"fields": "id,name,status,effective_status", "limit": "100"})
        time.sleep(0.6)
        print(f"▶ {key}  campaign {c.get('status')} CBO {rm(c.get('daily_budget'))} · adset «{(aset.get('name') or '')[:30]}» {aset.get('status')} · {len(sets)} adset(s)")
        have = [a for a in ads if (a.get("name") or "") == AD_NAME]
        to_pause = [a for a in ads if a["id"] not in {h["id"] for h in have} and a.get("status") == "ACTIVE"]
        for a in ads:
            flag = "⛔" if compliance.banned_reason(a.get("name") or "", s.compliance.banned_creatives) else "  "
            print(f"   {flag} ad «{(a.get('name') or '')[:40]}» {a.get('status')} / eff {a.get('effective_status')}" + ("  → will PAUSE" if a in to_pause else ""))
        print(f"   plan: {'ad exists' if have else 'create ' + AD_NAME + ' PAUSED'} · pause {len(to_pause)} other ad(s) · CBO → RM65 · adset+campaign → ACTIVE")
        if CONFIRM:
            try:
                for a in to_pause:
                    g.update_status(a["id"], "PAUSED"); time.sleep(0.8)
                if not have:
                    ad_id = make_ad(aset["id"], key.split("| ")[-1], "PAUSED")
                    print(f"   ✓ ad {ad_id} created PAUSED")
                if int(c.get("daily_budget") or 0) != budget:
                    g.update_daily_budget(c["id"], budget); time.sleep(0.8)
                if aset.get("status") != "ACTIVE":
                    g.update_status(aset["id"], "ACTIVE"); time.sleep(0.8)
                if c.get("status") != "ACTIVE":
                    g.update_status(c["id"], "ACTIVE"); time.sleep(0.8)
                log_done.append(f"{key.split('| ')[-1]}: ad ready (PAUSED), RM65, carriers ACTIVE, paused {len(to_pause)} other")
            except Exception as exc:                                   # noqa: BLE001
                log_skip.append(f"{key}: {str(exc)[:160]}"); print(f"   ❌ {str(exc)[:200]}")
        print()

    # ── audiences ───────────────────────────────────────────────────────────────────────
    auds = g._get_all(acct + "/customaudiences", {"fields": "id,name,subtype,approximate_count_lower_bound,lookalike_spec", "limit": "300"})
    time.sleep(0.8)
    by_name = {a.get("name"): a for a in auds}
    lal_auds = [a for a in auds if a.get("subtype") == "LOOKALIKE"]
    print(f"custom audiences on account: {len(auds)} · lookalikes: {len(lal_auds)}")
    for a in lal_auds[:12]:
        spec = a.get("lookalike_spec") or {}
        print(f"   LAL «{(a.get('name') or '')[:44]}» ratio={spec.get('ratio')} origin={[o.get('id') for o in (spec.get('origin') or [])]} ~{a.get('approximate_count_lower_bound')}")

    # G — 1 % purchase lookalike ----------------------------------------------------------
    lal1 = by_name.get(LAL1_AUD)
    if not lal1:                                        # reuse an existing 1 % purchase lookalike before building one
        ready = [a for a in lal_auds if str((a.get("lookalike_spec") or {}).get("ratio")) in ("0.01", "0.010")
                 and "purchase" in (a.get("name") or "").lower()]
        if ready:
            lal1 = ready[0]; print(f"   reuse existing 1% purchase LAL «{lal1.get('name')}» (~{lal1.get('approximate_count_lower_bound')})")
    seed = None
    if not lal1:
        # seed = origin of the lookalike the 🌟 LAL 5% ad set targets
        lal5 = find("🌟 [SG] STOCKBLOOM | PURCHASE LAL 5%")
        if lal5:
            sets5 = g._get_all(lal5[0]["id"] + "/adsets", {"fields": "id,name,targeting", "limit": "5"})
            time.sleep(0.6)
            cas = ((sets5[0].get("targeting") or {}).get("custom_audiences") or []) if sets5 else []
            for ca in cas:
                full = next((a for a in auds if a.get("id") == ca.get("id")), None)
                origin = ((full or {}).get("lookalike_spec") or {}).get("origin") or []
                if origin:
                    seed = origin[0].get("id"); print(f"   LAL 5% adset uses «{(full or {}).get('name')}» → seed {seed} «{origin[0].get('name')}»")
                    break
        if not seed:
            existing = [a for a in lal_auds if (a.get("lookalike_spec") or {}).get("ratio") in (0.01, "0.01") and "purchase" in (a.get("name") or "").lower()]
            if existing:
                lal1 = existing[0]; print(f"   reuse existing 1% purchase LAL «{lal1.get('name')}»")
    print(f"G plan: {'reuse «' + lal1.get('name') + '»' if lal1 else ('create ' + LAL1_AUD + ' from seed ' + str(seed) if seed else 'NO seed found — skip')}")
    if CONFIRM and not lal1 and seed:
        try:
            r = g._request("POST", acct + "/customaudiences", data=_encode({
                "name": LAL1_AUD, "subtype": "LOOKALIKE", "origin_audience_id": seed,
                "lookalike_spec": {"type": "custom_ratio", "ratio": 0.01, "country": "SG"}}))
            lal1 = {"id": r["id"], "name": LAL1_AUD}; print(f"   ✓ audience {r['id']} «{LAL1_AUD}»"); time.sleep(PACE)
        except Exception as exc:                                   # noqa: BLE001
            log_skip.append(f"LAL1 audience: {str(exc)[:160]}"); print(f"   ❌ {str(exc)[:200]}")

    # F — LP visitors 14 d minus registrants 14 d ---------------------------------------------
    rt = by_name.get(RT_AUD)
    rule = {"inclusions": {"operator": "or", "rules": [{"event_sources": [{"id": pixel, "type": "pixel"}], "retention_seconds": 14 * 86400,
                                                       "filter": {"operator": "and", "filters": [{"field": "event", "operator": "eq", "value": "PageView"}]}}]},
            "exclusions": {"operator": "or", "rules": [{"event_sources": [{"id": pixel, "type": "pixel"}], "retention_seconds": 14 * 86400,
                                                       "filter": {"operator": "and", "filters": [{"field": "event", "operator": "eq", "value": "CompleteRegistration"}]}}]}}
    print(f"F plan: {'reuse «' + rt.get('name') + '»' if rt else 'create ' + RT_AUD + ' (pixel ' + pixel + ')'}")
    if CONFIRM and not rt:
        try:
            r = g._request("POST", acct + "/customaudiences", data=_encode({
                "name": RT_AUD, "prefill": "1", "rule": rule,
                "description": "PageView 14d minus CompleteRegistration 14d — last-call pool for the 14/10 live"}))
            rt = {"id": r["id"], "name": RT_AUD}; print(f"   ✓ audience {r['id']} «{RT_AUD}»"); time.sleep(PACE)
        except Exception as exc:                                   # noqa: BLE001
            log_skip.append(f"retarget audience: {str(exc)[:160]}"); print(f"   ❌ {str(exc)[:200]}")

    # new campaigns G / F --------------------------------------------------------------------
    # Singapore delivery needs the ad-set field regional_regulated_categories (Meta: SINGAPORE_UNIVERSAL);
    # copy whatever a running SG ad set carries, fall back to the documented value.
    rrc = ["SINGAPORE_UNIVERSAL"]
    rri = {"singapore_universal_beneficiary": "1466824068581066", "singapore_universal_payer": "1466824068581066"}
    try:
        src_sets = g._get_all(find("0911 HOOK")[0]["id"] + "/adsets",
                              {"fields": "id,name,status,regional_regulated_categories,regional_regulation_identities", "limit": "5"})
        live = [x for x in src_sets if x.get("status") == "ACTIVE"] or src_sets
        got_c = next((x.get("regional_regulated_categories") for x in live if x.get("regional_regulated_categories")), None)
        got_i = next((x.get("regional_regulation_identities") for x in live if x.get("regional_regulation_identities")), None)
        rrc, rri = got_c or rrc, got_i or rri
        print(f"Singapore regulated fields copied from the 0911 adset: {rrc} · {json.dumps(rri)}")
    except Exception as exc:                                   # noqa: BLE001
        print(f"regulated fields: could not read ({str(exc)[:80]}) → using {rrc} · {json.dumps(rri)}")
    time.sleep(0.6)

    def build_chain(camp_name: str, aset_name: str, budget: int, aud: dict | None, label: str):
        if not aud:
            log_skip.append(f"{label}: no audience — campaign not built"); print(f"✗ {label}: no audience, skip\n"); return
        t = {"geo_locations": {"countries": s.meta.targeting.countries}, "age_min": 28, "age_max": 65,
             "custom_audiences": [{"id": aud["id"]}], "targeting_automation": {"advantage_audience": 0}}
        if s.meta.targeting.locales:
            t["locales"] = s.meta.targeting.locales
        print(f"▶ «{camp_name}» CBO {rm(budget)} · «{aset_name}» PAUSED · audience «{aud.get('name')}» · 1 ad\n   " + json.dumps(t, ensure_ascii=False)[:300])
        if not CONFIRM:
            print(); return
        try:
            cid = next((c["id"] for c in camps if (c.get("name") or "") == camp_name), None)
            if cid:
                info = g.get_object(cid, "id,name,special_ad_categories")
                has_sets = bool(g._get_all(cid + "/adsets", {"fields": "id", "limit": "5"}))
                if info.get("special_ad_categories") and not has_sets:
                    # tonight's empty scaffold carried FINANCIAL_PRODUCTS_SERVICES; the running SG chains have none ->
                    # drop it and rebuild clean (no ad set, no ad, no spend ever)
                    g._request("DELETE", cid); print(f"   · deleted empty scaffold campaign {cid} (special category mismatch)")
                    cid = None; time.sleep(1.0)
            if not cid:
                cid = g.create_campaign(acct, name=camp_name, objective="OUTCOME_SALES", buying_type="AUCTION",
                                        daily_budget=budget, bid_strategy="LOWEST_COST_WITHOUT_CAP",
                                        special_ad_categories=[], status="ACTIVE")["id"]
                print(f"   ✓ campaign {cid}"); time.sleep(PACE)
            sets = g._get_all(cid + "/adsets", {"fields": "id,name", "limit": "10"}); time.sleep(0.6)
            aid = next((x["id"] for x in sets if (x.get("name") or "") == aset_name), None)
            if not aid:
                aid = g.create_adset(acct, name=aset_name, campaign_id=cid, optimization_goal="OFFSITE_CONVERSIONS",
                                     billing_event="IMPRESSIONS", promoted_object=s.meta.promoted_object,
                                     targeting=t, regional_regulated_categories=rrc,
                                     regional_regulation_identities=rri, status="PAUSED")["id"]
                print(f"   ✓ adset {aid} (PAUSED gate)"); time.sleep(PACE)
            have = [a for a in g._get_all(cid + "/ads", {"fields": "name", "limit": "20"}) if (a.get("name") or "") == AD_NAME]
            time.sleep(0.6)
            if not have:
                ad_id = make_ad(aid, label, "ACTIVE"); print(f"   ✓ ad {ad_id} (ACTIVE inside the PAUSED adset)")
            log_done.append(f"{label}: campaign {rm(budget)}, adset PAUSED gate, 1 ad")
        except Exception as exc:                                   # noqa: BLE001
            log_skip.append(f"{label}: {str(exc)[:160]}"); print(f"   ❌ {str(exc)[:200]}")
        print()

    build_chain(LAL1_CAMP, LAL1_ASET, LAL1_BUDGET, lal1, "LAL 1%")
    build_chain(RT_CAMP, RT_ASET, RT_BUDGET, rt, "RETARGET LP 14D")

    if not CONFIRM:
        print("DRY RUN — CONFIRM=true 才动手。"); print("SG BUILD-MORE DONE (dry-run)"); return
    print("完成: " + (" · ".join(log_done) or "无"))
    if log_skip:
        print("跳过/失败: " + " · ".join(log_skip))
    print("SG BUILD-MORE DONE")


if __name__ == "__main__":
    main()
