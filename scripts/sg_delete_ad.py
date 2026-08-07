"""Delete the one DISAPPROVED SG ad (GOLF · freestyle 2, 'Unacceptable business
practices'). GOLF keeps its other 2 ads. Dry-run unless CONFIRM=true.
"""
from __future__ import annotations

import os

from adbot.commands import graph_client
from adbot.settings import load_settings

CONFIRM = os.environ.get("CONFIRM", "").lower() in ("1", "true", "yes")
AD = "120248220645020521"   # [SG] GOLF · freestyle 2 · DISAPPROVED


def main() -> None:
    g = graph_client(load_settings())
    a = g.get_object(AD, "id,name,effective_status")
    print(f"AD {a.get('id')} '{a.get('name')}' [{a.get('effective_status')}]")
    if not CONFIRM:
        print("WOULD DELETE (dry-run)")
        return
    g._request("DELETE", AD)
    print("DELETED ✓")


if __name__ == "__main__":
    main()
