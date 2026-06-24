"""Read-only preflight: print the service-account email and verify it can READ every
file_id in a creatives manifest.

The single-image build downloads each manifest file via the service account, so a missing
Drive share would otherwise fail mid-build. Run this first to get a clear per-file report
plus the exact SA email to share the Drive files/folders with. No writes, no Meta calls.

    python scripts/check_manifest_access.py config/single_image_manifest.json
"""
from __future__ import annotations

import json
import sys

from adbot.clients.drive import build_credentials
from adbot.drive_sync import load_units_from_manifest
from adbot.settings import load_settings


def _sa_email(sa_json: str) -> str:
    try:
        return json.loads(sa_json).get("client_email", "(no client_email in key)")
    except Exception:  # noqa: BLE001
        return "(could not parse service-account JSON)"


def main(argv) -> int:
    manifest = argv[0] if argv else "config/single_image_manifest.json"
    settings = load_settings()
    sa_json = settings.secrets.google_sa_json
    if not sa_json:
        print("GOOGLE_SERVICE_ACCOUNT_JSON[_B64] is not set — cannot check Drive access.")
        return 1

    print(f"SERVICE ACCOUNT: {_sa_email(sa_json)}")
    print("Share each Drive file (or its parent folder) below with that email as Viewer "
          "if any line says FAIL.\n")

    from googleapiclient.discovery import build as gbuild  # lazy

    svc = gbuild("drive", "v3", credentials=build_credentials(sa_json), cache_discovery=False)
    units = load_units_from_manifest(manifest)
    ok = 0
    total = 0
    for u in units:
        for a in u.assets:
            total += 1
            try:
                meta = svc.files().get(fileId=a.file_id, fields="id,name,mimeType",
                                       supportsAllDrives=True).execute()
                print(f"  [OK]   {u.content_id:<10} {a.file_id}  {meta.get('name')}")
                ok += 1
            except Exception as exc:  # noqa: BLE001
                print(f"  [FAIL] {u.content_id:<10} {a.file_id}  {exc}")

    print(f"\n{ok}/{total} manifest file(s) readable by the service account.")
    return 0 if ok == total else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
