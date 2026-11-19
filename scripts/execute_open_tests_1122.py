# -*- coding: utf-8 -*-
"""owner 2026-11-19「方案 B，我排程自动开」— Sunday 11/22 00:00 MYT:
  · (Webinarkit) [SG] STOCKBLOOM | CBO · LAL INVEST LUX | 1-3-3 | 1120 · campaign 120250705919180521 (CBO RM100)
SG 1-1-3 LOW CPL (campaign 120250706566080521) is NOT opened — owner plan B keeps it PAUSED.
Campaign layer only; reads back every ad. Logic + safety gates: open_tests_lib_1121.py."""
import datetime as dt

from open_tests_lib_1121 import open_campaigns

open_campaigns([("config.sg.yaml", "120250705919180521", "CBO · LAL INVEST LUX | 1-3-3 | 1120")],
               dt.datetime(2026, 11, 22, 0, 0), "SUN 1122")
