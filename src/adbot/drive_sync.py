"""Download creatives from the Drive folder and group them into 10 units."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Tuple

from .creative_groups import Asset, SINGLE_IMAGE, Unit, build_units, select_ten
from .logging import get_logger
from .settings import REPO_ROOT, Settings

DOWNLOAD_DIR = Path(REPO_ROOT) / "downloads"


def fetch_tree(drive, folder_id: str) -> Dict[str, Any]:
    """Recursively build a {id,name,mimeType,children:[...]} tree for the folder."""
    def walk(fid: str, name: str = "root") -> Dict[str, Any]:
        node = {"id": fid, "name": name,
                "mimeType": "application/vnd.google-apps.folder", "children": []}
        for child in drive.list_children(fid):
            if drive.is_folder(child):
                node["children"].append(walk(child["id"], child["name"]))
            else:
                node["children"].append(child)
        return node
    return walk(folder_id)


def load_units(drive, settings: Settings) -> Tuple[Dict[str, Any], List[Unit]]:
    tree = fetch_tree(drive, settings.drive.creatives_folder_id)
    units = select_ten(
        build_units(tree, settings.drive.carousel_subfolder_marker),
        settings.meta.build.creatives_per_adset,
    )
    return tree, units


def download_assets(drive, units: List[Unit], dest_dir: Path = DOWNLOAD_DIR) -> List[Unit]:
    log = get_logger()
    for unit in units:
        for asset in unit.assets:
            target = dest_dir / f"{asset.file_id}_{asset.name}"
            drive.download_file(asset.file_id, target)
            asset.local_path = str(target)
        if unit.script_file_id:
            script_path = dest_dir / f"{unit.script_file_id}.txt"
            drive.download_file(unit.script_file_id, script_path)
            unit.script_text = script_path.read_text(encoding="utf-8", errors="ignore").strip()
        log.info("  [downloaded] %s (%s, %d asset(s))", unit.content_id, unit.kind, len(unit.assets))
    return units


def load_units_from_manifest(manifest_path, *, default_kind: str = SINGLE_IMAGE) -> List[Unit]:
    """Build creative units from an explicit manifest, bypassing the Drive folder scan.

    The folder scan grabs *every* file in a folder and derives content_ids from messy
    filenames; a manifest instead names exactly which Drive files to use and pins clean,
    stable content_ids (e.g. ``image_1``) so the snapshot/Notion copy maps deterministically.
    The service account still needs read access to each ``file_id`` — ``download_assets``
    reads it like any other creative.

    Manifest JSON::

        {"creatives": [
            {"content_id": "image_1", "file_id": "<drive id>", "name": "Image 1：…"},
            {"content_id": "carousel_1", "kind": "carousel",
             "files": [{"file_id": "…", "name": "…", "mime": "image/png"}, …]}
        ]}

    ``kind`` defaults to ``single_image``; ``mime`` defaults to ``image/png``.
    """
    path = Path(manifest_path)
    if not path.is_absolute():
        path = Path(REPO_ROOT) / path
    data = json.loads(path.read_text(encoding="utf-8"))
    units: List[Unit] = []
    for item in data.get("creatives", []):
        kind = item.get("kind", default_kind)
        files = item.get("files") or [{"file_id": item["file_id"],
                                       "name": item.get("name", ""),
                                       "mime": item.get("mime", "image/png")}]
        assets = [Asset(f["file_id"], f.get("name", ""), f.get("mime", "image/png")) for f in files]
        units.append(Unit(content_id=item["content_id"], kind=kind, assets=assets))
    return select_ten(units, n=len(units))  # de-dup by content_id, keep curated order
