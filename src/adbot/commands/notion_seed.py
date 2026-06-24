"""notion_seed: push the byte-exact snapshot copy into the Notion Content Pipeline rows.

For each ``video_N`` in the committed snapshot (config/captions_*.json), find the matching
Notion row (Title "Video N：…") and write Title + Hook + Caption verbatim from the snapshot —
no hand-transcription, so the copy in Notion is character-identical to the vetted source.
Idempotent: re-running just rewrites the same values. Rows with no matching snapshot entry,
and snapshot entries with no matching row, are left untouched (logged).

Needs the Notion integration's "Update content" capability (in addition to read). If the
token is read-only the PATCH fails with a clear permission error.
"""

from __future__ import annotations

from typing import Any, Dict

from . import notion_client
from .build import _load_curated_captions
from ..clients.notion import rich_text_property, title_property
from ..logging import final_summary, get_logger
from ..notion_captions import content_id_from_title, _title_text


def run(settings, *, dry_run: bool = False) -> Dict[str, Any]:
    log = get_logger()
    snapshot = _load_curated_captions()
    notion = notion_client(settings)
    db_id = settings.notion.database_id

    # Map content_id -> Notion page id from the current rows.
    pages: Dict[str, str] = {}
    for page in notion.query_database(db_id):
        cid = content_id_from_title(_title_text(page.get("properties", {})))
        if cid:
            pages[cid] = page["id"]

    seeded, missing_row = [], []
    for cid, copy in sorted(snapshot.items()):
        if not cid.startswith("video_"):
            continue  # only the per-video rows live in this database
        if cid not in pages:
            missing_row.append(cid)
            continue
        props = {
            "Title": title_property(copy.get("name") or cid),
            "Hook": rich_text_property(copy.get("headline", "")),
            "Caption": rich_text_property(copy.get("caption", "")),
        }
        if dry_run:
            log.info("[dry-run] would seed %s (caption %d chars)", cid, len(copy.get("caption", "")))
        else:
            notion.update_page_properties(pages[cid], props)
            log.info("Seeded %s -> %s (caption %d chars)", cid, pages[cid], len(copy.get("caption", "")))
        seeded.append(cid)

    if missing_row:
        log.warning("No Notion row for: %s (create the row first)", ", ".join(missing_row))
    verb = "would seed" if dry_run else "seeded"
    final_summary(log, f"notion_seed: {verb} {len(seeded)} row(s) from the snapshot"
                       + (f"; {len(missing_row)} snapshot id(s) had no row" if missing_row else ""))
    return {"seeded": seeded, "missing_row": missing_row, "dry_run": dry_run}
