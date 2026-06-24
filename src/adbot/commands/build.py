"""build: create (and optionally activate) the 1-1-10 structure + write the caption log."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

from . import docs_client, drive_client, graph_client, llm_client
from .. import build_1_1_10, docwriter, media
from ..captions import generate_for_units
from ..drive_sync import download_assets, load_units
from ..logging import get_logger
from ..settings import REPO_ROOT

# Approved-caption snapshots (from Notion): content_id -> {name, headline, caption, ...}.
# Used in preference to LLM generation so ads keep their vetted copy + "Video N：标题" names.
CURATED_CAPTION_FILES = ("captions_june2026.json", "captions_campaign2.json")


def _load_curated_captions() -> Dict[str, Any]:
    """Merge the approved caption snapshots from config/ (later files win on overlap)."""
    merged: Dict[str, Any] = {}
    for fname in CURATED_CAPTION_FILES:
        path = Path(REPO_ROOT) / "config" / fname
        if path.exists():
            merged.update(json.loads(path.read_text(encoding="utf-8")))
    return merged


def run(settings, *, dry_run: bool = False) -> Dict[str, Any]:
    log = get_logger()
    graph = graph_client(settings)
    drive = drive_client(settings)
    _, units = load_units(drive, settings)
    log.info("Loaded %d creative unit(s) from Drive.", len(units))

    if dry_run:
        # Preview structure without uploading media or calling the LLM (no spend/cost).
        stub = {u.content_id: {"caption": "<generated on live run>",
                              "headline": "<generated>"} for u in units}
        return build_1_1_10.build(graph, settings, units, stub, dry_run=True)

    download_assets(drive, units)
    media.sync_media(graph, settings, units, dry_run=False)

    # Prefer approved captions (snapshotted from Notion — vetted copy + proper "Video N：标题"
    # names) for any unit they cover; only fall back to LLM generation for the rest.
    curated = _load_curated_captions()
    captions: Dict[str, Any] = {u.content_id: curated[u.content_id]
                                for u in units if u.content_id in curated}
    missing = [u for u in units if u.content_id not in captions]
    if missing:
        log.info("Generating captions for %d unit(s) not in the approved set: %s",
                 len(missing), ", ".join(u.content_id for u in missing))
        captions.update(generate_for_units(llm_client(settings), settings, missing))
    else:
        log.info("All %d unit(s) covered by approved captions — skipping LLM generation.",
                 len(units))

    entities = build_1_1_10.build(graph, settings, units, captions, dry_run=False)

    # The caption-log Google Doc is an optional audit; never fail the build on it
    # (e.g. the service account's Drive storage quota being exhausted).
    try:
        docwriter.write_caption_log(docs_client(settings), settings, units, captions)
    except Exception as exc:  # noqa: BLE001
        log.warning("caption-log Doc write skipped (%s)", exc)
    return entities
