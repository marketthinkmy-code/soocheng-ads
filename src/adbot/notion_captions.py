"""Pull approved ad copy from the Notion Content Pipeline database.

Mapping (the operator's spec):
  - Title   "Video N：标题"  -> content_id ``video_N`` + the ad name (verbatim Title)
  - Hook    (rich_text prop) -> the ad headline
  - Caption (rich_text prop) -> the caption (message); empty -> the build fills it from the
                                committed snapshot (config/captions_*.json), which holds the
                                byte-exact vetted copy

The caption is read from a rich_text PROPERTY, not the page body: a property round-trips
multi-paragraph copy faithfully (blank lines preserved), whereas the page body collapses
paragraph spacing on read. Write/edit captions in the Caption field, not the body.

Status is intentionally NOT filtered — whatever copy is in the row is what runs (the operator
reviews the PAUSED build before activating). Rows whose Title doesn't name a buildable
content id (e.g. a copy-collection page) are skipped, so a mixed database is fine.
"""

from __future__ import annotations

import re
from typing import Any, Dict, Optional

from .clients.notion import NotionClient, rich_text_to_plain
from .logging import get_logger

# "Video 1：…" -> video_1 ; "Image 3：…" -> image_3 ; "video2", "Image 11 - …" likewise.
# Both creative kinds share one Content Pipeline DB; the prefix word picks the content_id space.
_CONTENT_ID_RE = re.compile(r"^\s*(video|image)\s*0*(\d+)", re.IGNORECASE)


def content_id_from_title(title: str) -> Optional[str]:
    """'Video 11：你不敢下单…' -> 'video_11'; 'Image 3：…' -> 'image_3';
    None if the Title doesn't name a buildable video/image row."""
    m = _CONTENT_ID_RE.match(title or "")
    return f"{m.group(1).lower()}_{int(m.group(2))}" if m else None


def _title_text(props: Dict[str, Any]) -> str:
    # The title property may be named anything; find the one of type 'title'.
    for prop in props.values():
        if isinstance(prop, dict) and prop.get("type") == "title":
            return rich_text_to_plain(prop.get("title", []))
    return ""


def _rich_text_prop(props: Dict[str, Any], name: str) -> str:
    prop = props.get(name)
    if isinstance(prop, dict) and prop.get("type") == "rich_text":
        return rich_text_to_plain(prop.get("rich_text", []))
    return ""


def fetch_captions(notion: NotionClient, database_id: str) -> Dict[str, Dict[str, Any]]:
    """Return {content_id: {name, headline, caption}} for every video row in the database."""
    log = get_logger()
    out: Dict[str, Dict[str, Any]] = {}
    for page in notion.query_database(database_id):
        props = page.get("properties", {})
        title = _title_text(props)
        content_id = content_id_from_title(title)
        if not content_id:
            continue  # not a per-video row (e.g. a copy-collection or script page)
        out[content_id] = {
            "name": title.strip(),
            "headline": _rich_text_prop(props, "Hook").strip(),
            "caption": _rich_text_prop(props, "Caption").strip(),  # "" -> snapshot fills it
        }
    log.info("Notion: pulled %d caption(s): %s",
             len(out), ", ".join(sorted(out)) or "(none)")
    return out
