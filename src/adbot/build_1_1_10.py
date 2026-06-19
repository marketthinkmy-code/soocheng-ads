"""Build the 1-1-10 structure: 1 CBO campaign, 1 broad ad set (MY 25+), 10 ads.

Everything is created PAUSED. If ``meta.build.activate_after_build`` is true, the whole
hierarchy is then activated (campaign -> ad set -> ads) at the configured CBO budget.
"""

from __future__ import annotations

from typing import Any, Dict, List

from . import state
from .creative_groups import CAROUSEL, SINGLE_IMAGE, VIDEO, Unit
from .logging import final_summary, get_logger
from .settings import Settings


def _cta(settings: Settings) -> Dict[str, Any]:
    return {"type": settings.meta.call_to_action,
            "value": {"link": settings.meta.lead_destination.link_url}}


def creative_spec(settings: Settings, unit: Unit, caption: Dict[str, Any]) -> Dict[str, Any]:
    """Build the ad-creative payload for one unit (video / image / carousel)."""
    page_id = settings.meta.page_id
    link = settings.meta.lead_destination.link_url
    message = caption.get("caption", "")
    headline = caption.get("headline", "")
    cta = _cta(settings)

    if unit.kind == VIDEO:
        story = {"page_id": page_id, "video_data": {
            "video_id": unit.assets[0].meta_id, "title": headline,
            "message": message, "call_to_action": cta, "link_description": link}}
    elif unit.kind == SINGLE_IMAGE:
        story = {"page_id": page_id, "link_data": {
            "link": link, "image_hash": unit.assets[0].meta_id,
            "message": message, "name": headline, "call_to_action": cta}}
    elif unit.kind == CAROUSEL:
        cards = caption.get("carousel_card_texts") or []
        child = []
        for i, asset in enumerate(unit.assets):
            card = cards[i] if i < len(cards) else {}
            child.append({"link": link, "image_hash": asset.meta_id,
                          "name": card.get("name", headline),
                          "description": card.get("description", ""), "call_to_action": cta})
        story = {"page_id": page_id, "link_data": {
            "link": link, "message": message, "child_attachments": child,
            "multi_share_optimized": True, "multi_share_end_card": True}}
    else:  # pragma: no cover - guarded by grouping
        raise ValueError(f"unknown unit kind: {unit.kind}")

    spec = {"name": f"{settings.naming.prefix} | {unit.content_id}", "object_story_spec": story}
    if settings.meta.instagram_actor_id:
        spec["instagram_actor_id"] = settings.meta.instagram_actor_id
    return spec


def build(graph, settings: Settings, units: List[Unit],
          captions: Dict[str, Dict[str, Any]], *, dry_run: bool = False) -> Dict[str, Any]:
    log = get_logger()
    account = settings.meta.account_path
    m = settings.meta

    campaign_fields = {
        "name": settings.naming.campaign_name("1-1-10"),
        "objective": m.objective, "buying_type": "AUCTION", "status": "PAUSED",
        "special_ad_categories": m.special_ad_categories,
        "daily_budget": m.budget.daily_amount_cents,
        "bid_strategy": "LOWEST_COST_WITHOUT_CAP",
    }
    adset_fields = {
        "name": settings.naming.campaign_name("AdSet | Broad MY 25+"),
        "optimization_goal": m.optimization_goal, "billing_event": "IMPRESSIONS",
        "promoted_object": m.promoted_object, "targeting": m.targeting.to_spec(),
        "daily_min_spend_target": m.budget.adset_min_spend_cents, "status": "PAUSED",
    }

    if dry_run:
        log.info("[dry-run] CAMPAIGN: %s", campaign_fields)
        log.info("[dry-run] AD SET:   %s", adset_fields)
        for unit in units:
            log.info("[dry-run] CREATIVE %s (%s): %s", unit.content_id, unit.kind,
                     creative_spec(settings, unit, captions.get(unit.content_id, {})))
        final_summary(log, f"build (dry-run): would create 1 campaign, 1 ad set, {len(units)} ads "
                           f"at {m.budget.daily_amount_myr:.0f} MYR/day CBO (nothing created)")
        return {"dry_run": True, "ads": len(units)}

    campaign_id = graph.create_campaign(account, **campaign_fields)["id"]
    log.info("Created campaign %s", campaign_id)
    adset_id = graph.create_adset(account, campaign_id=campaign_id, **adset_fields)["id"]
    log.info("Created ad set %s (min daily spend %d MYR)", adset_id, m.budget.adset_min_spend_myr)

    ad_ids: List[str] = []
    for unit in units:
        spec = creative_spec(settings, unit, captions.get(unit.content_id, {}))
        creative_id = graph.create_adcreative(account, **spec)["id"]
        ad = graph.create_ad(
            account, name=f"{settings.naming.prefix} | {unit.content_id}",
            adset_id=adset_id, creative={"creative_id": creative_id}, status="PAUSED",
            conversion_domain=m.conversion_domain_bare or None,
        )
        ad_ids.append(ad["id"])
        log.info("  Created ad %s (%s, creative %s)", ad["id"], unit.kind, creative_id)

    entities = {"campaign_id": campaign_id, "adset_id": adset_id, "ad_ids": ad_ids,
                "created_at": state.now_iso()}
    state.save("entities", entities)

    activated = False
    if m.build.activate_after_build:
        graph.update_status(campaign_id, "ACTIVE")
        graph.update_status(adset_id, "ACTIVE")
        for ad_id in ad_ids:
            graph.update_status(ad_id, "ACTIVE")
        activated = True

    state_word = "ACTIVE" if activated else "PAUSED"
    final_summary(log, f"build: created 1 campaign + 1 ad set + {len(ad_ids)} ads "
                       f"at {m.budget.daily_amount_myr:.0f} MYR/day CBO — now {state_word}")
    entities["activated"] = activated
    return entities
