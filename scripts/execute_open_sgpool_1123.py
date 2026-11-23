# -*- coding: utf-8 -*-
"""owner 2026-11-23 选「建好后今天就开」→ open (campaign layer only) the SG pool built by execute_build_sgpool_1123.py:
(Webinarkit) [SG] STOCKBLOOM | BROAD POOL | 1-1-4 | 1123. Run with confirm=true only after WK removed Audience Network on its ad set in
Ads Manager and the placements were read back via META MCP. Reuses open_tests_lib_1121.open_campaigns: refuses when the RM5,950 cycle
cap is reached, any ad is banned / 🚫 / DISAPPROVED / WITH_ISSUES, or the (Webinarkit) prefix is missing; reads back every ad's
effective_status. CONFIRM=true writes + reads back; otherwise dry-run."""
import datetime as dt

from adbot.commands import graph_client
from adbot.settings import REPO_ROOT, load_settings
from open_tests_lib_1121 import open_campaigns

CNAME = "(Webinarkit) [SG] STOCKBLOOM | BROAD POOL | 1-1-4 | 1123"
s = load_settings(REPO_ROOT / "config" / "config.sg.yaml")
hits = [c for c in graph_client(s)._get_all(s.meta.account_path + "/campaigns", {"fields": "name", "limit": "500"}) if c["name"] == CNAME]
assert len(hits) == 1, f"expected exactly one «{CNAME}», found {len(hits)}"
open_campaigns([("config.sg.yaml", hits[0]["id"], "BROAD POOL | 1-1-4 | 1123")], dt.datetime(2026, 11, 23, 0, 0), "SG BROAD POOL 1123")
