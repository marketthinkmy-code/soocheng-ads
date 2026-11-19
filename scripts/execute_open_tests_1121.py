# -*- coding: utf-8 -*-
"""⚠️ owner 11/19 ~17:2x「周六你看看到时候的成绩和预算，建议和问我要不要开 MY CBO SG CBO」→ NOT scheduled any more:
run with confirm=true ONLY after WK says 开 (Saturday review). Time guard relaxed to 11/19 for that reason.
Originally: owner 2026-11-19「方案 B，我排程自动开」— Saturday 11/21 00:00 MYT:
  · (SG 1-1-3 BEST removed 11/19 ~17:1x — WK opened both SG 1-1-3 himself)
  · (Webinarkit) STOCKBLOOM | CBO · LUX BEER OMAKASE | 1-3-3 | 1120 · campaign 120251995650640329 (CBO RM100)
Campaign layer only; reads back every ad. Logic + safety gates: open_tests_lib_1121.py."""
import datetime as dt

from open_tests_lib_1121 import open_campaigns

# owner 11/19 ~17:1x「sg 我会先开 2 个 1-1-3」: WK switched on SG 1-1-3 BEST + LOW CPL himself → SG BEST removed from this run
# (if WK later closes it by hand, this script must not reopen it). Saturday now opens MY CBO only.
open_campaigns([("config.my5.yaml", "120251995650640329", "CBO · LUX BEER OMAKASE | 1-3-3 | 1120")],
               dt.datetime(2026, 11, 19, 0, 0), "SAT 1121")
