# -*- coding: utf-8 -*-
"""owner 2026-11-19「方案 B，我排程自动开」— Saturday 11/21 00:00 MYT:
  · (Webinarkit) [SG] STOCKBLOOM | BEST · Broad | 1-1-3 | 1120 · campaign 120250705800700521 (CBO RM100)
  · (Webinarkit) STOCKBLOOM | CBO · LUX BEER OMAKASE | 1-3-3 | 1120 · campaign 120251995650640329 (CBO RM100)
Campaign layer only; reads back every ad. Logic + safety gates: open_tests_lib_1121.py."""
import datetime as dt

from open_tests_lib_1121 import open_campaigns

open_campaigns([("config.sg.yaml", "120250705800700521", "BEST · Broad | 1-1-3 | 1120"),
                ("config.my5.yaml", "120251995650640329", "CBO · LUX BEER OMAKASE | 1-3-3 | 1120")],
               dt.datetime(2026, 11, 21, 0, 0), "SAT 1121")
