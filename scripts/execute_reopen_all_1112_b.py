# -*- coding: utf-8 -*-
"""Option B of execute_reopen_all_1112.py: same run, but hold the 0-报名 ads (see HOLD there)."""
import os
import runpy
from pathlib import Path

os.environ["REOPEN_MODE"] = "B"
runpy.run_path(str(Path(__file__).with_name("execute_reopen_all_1112.py")), run_name="__main__")
