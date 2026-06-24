"""build: create (and optionally activate) the 1-1-10 structure + write the caption log."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

from . import docs_client, drive_client, graph_client, llm_client, notion_client
from .. import build_1_1_10, docwriter, media
from ..captions import generate_for_units
from ..drive_sync import download_assets, load_units, load_units_from_manifest
from ..logging import get_logger
from ..notion_captions import fetch_captions
from ..settings import REPO_ROOT

# Approved-caption snapshots (from Notion): content_id -> {name, headline, caption, ...}.
# Used in preference to LLM generation so ads keep their vetted copy + "Video N：标题" names.
CURATED_CAPTION_FILES = ("captions_june2026.json", "captions_campaign2.json",
                         "captions_singleimage.json")


def _load_curated_captions() -> Dict[str, Any]:
    """Merge the approved caption snapshots from config/ (later files win on overlap)."""
    merged: Dict[str, Any] = {}
    for fname in CURATED_CAPTION_FILES:
        path = Path(REPO_ROOT) / "config" / fname
        if path.exists():
            merged.update(json.loads(path.read_text(encoding="utf-8")))
    return merged


def _merge_caption(primary: Dict[str, Any], fallback: Dict[str, Any]) -> Dict[str, Any]:
    """Field-level merge: a non-empty ``primary`` (Notion) value wins; ``fallback`` (snapshot)
    fills any field the primary left blank/absent. Either argument may be None/empty."""
    merged: Dict[str, Any] = dict(fallback or {})
    for key, value in (primary or {}).items():
        if value not in (None, "", []):
            merged[key] = value
    return merged


def _pull_notion_captions(settings, units, log) -> Dict[str, Any]:
    """Approved copy pulled live from Notion for any unit it covers.

    Returns {} when Notion is disabled/unconfigured or unreachable — Notion is the preferred
    source but must never become a build blocker (snapshot/LLM still cover the build).
    """
    if not (settings.notion.enabled and settings.secrets.notion_token
            and settings.notion.database_id):
        return {}
    try:
        pulled = fetch_captions(notion_client(settings), settings.notion.database_id)
    except Exception as exc:  # noqa: BLE001
        log.warning("Notion caption pull skipped (%s) — falling back to snapshot/LLM", exc)
        return {}
    return {u.content_id: pulled[u.content_id] for u in units if u.content_id in pulled}


def run(settings, *, dry_run: bool = False, manifest: str = None,
        state_key: str = "entities", label: str = "1-1-10",
        start_time: str = None, daily_budget_myr: float = None) -> Dict[str, Any]:
    log = get_logger()
    graph = graph_client(settings)
    if daily_budget_myr is not None:  # override CBO budget for this build without editing config
        settings.meta.budget.daily_amount_myr = daily_budget_myr

    # Creatives come from an explicit manifest (curated file_ids + clean content_ids) or, by
    # default, the recursive Drive folder scan. Manifest mode needs no Drive client for a dry-run.
    drive = None
    if manifest:
        units = load_units_from_manifest(manifest)
        log.info("Loaded %d creative unit(s) from manifest %s.", len(units), manifest)
    else:
        drive = drive_client(settings)
        _, units = load_units(drive, settings)
        log.info("Loaded %d creative unit(s) from Drive.", len(units))

    if dry_run:
        # Preview structure without uploading media or calling the LLM (no spend/cost).
        stub = {u.content_id: {"caption": "<generated on live run>",
                              "headline": "<generated>"} for u in units}
        return build_1_1_10.build(graph, settings, units, stub, dry_run=True,
                                  state_key=state_key, label=label, start_time=start_time)

    if drive is None:
        drive = drive_client(settings)
    download_assets(drive, units)
    media.sync_media(graph, settings, units, dry_run=False)

    # Caption sources in order of trust: Notion (live source of truth — vetted copy + proper
    # "Video N：标题" names) -> the committed snapshot (config/captions_*.json) -> LLM. The merge
    # is FIELD-LEVEL: a Notion value wins per field, the snapshot fills any blank, and the LLM
    # only covers content_ids with no caption from either — so a partly-filled Notion row
    # (e.g. just an edited headline) never blanks the rest of an ad.
    notion_caps = _pull_notion_captions(settings, units, log)
    if notion_caps:
        log.info("Notion provided copy for: %s", ", ".join(sorted(notion_caps)))
    curated = _load_curated_captions()

    captions: Dict[str, Any] = {}
    for u in units:
        merged = _merge_caption(notion_caps.get(u.content_id), curated.get(u.content_id))
        if merged:
            captions[u.content_id] = merged

    missing = [u for u in units if not captions.get(u.content_id, {}).get("caption")]
    if missing:
        log.info("Generating captions for %d unit(s) with no Notion/snapshot copy: %s",
                 len(missing), ", ".join(u.content_id for u in missing))
        for cid, cap in generate_for_units(llm_client(settings), settings, missing).items():
            captions[cid] = _merge_caption(captions.get(cid), cap)  # keep any Notion name/headline
    else:
        log.info("All %d unit(s) covered by Notion/snapshot — skipping LLM generation.",
                 len(units))

    entities = build_1_1_10.build(graph, settings, units, captions, dry_run=False,
                                  state_key=state_key, label=label, start_time=start_time)

    # The caption-log Google Doc is an optional audit; never fail the build on it
    # (e.g. the service account's Drive storage quota being exhausted).
    try:
        docwriter.write_caption_log(docs_client(settings), settings, units, captions)
    except Exception as exc:  # noqa: BLE001
        log.warning("caption-log Doc write skipped (%s)", exc)
    return entities
