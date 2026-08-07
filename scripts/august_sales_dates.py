# -*- coding: utf-8 -*-
"""List every August sale row (date · ad · campaign) from the Paid Student List.

Owner ask 2026-08-07: verify by date which August sales landed on/after the 8/4
reopen, so 'the reopen is already paying back' is a checked fact, not a guess.
Read-only.
"""
from __future__ import annotations

import datetime as dt

from adbot import cpa as C
from adbot.clients.sheets import SheetsClient
from adbot.settings import load_settings

REOPEN_DAY = dt.date(2026, 8, 4)
REOPENED = ("你敢吗", "你没有本钱", "不选 forex", "freestyle 1", "盖电脑",
            "早就不是这样了", "用我的方法")


def main() -> None:
    s = load_settings()
    values = SheetsClient(s.secrets.google_sa_json).read_tab(s.cpa.spreadsheet_id, s.cpa.sales_tab)
    sales, _cols, _hdr = C.parse_sales(values, s.cpa.price_myr)
    aug = sorted((x for x in sales if x.date and x.date >= dt.date(2026, 8, 1)),
                 key=lambda x: x.date)
    print(f"August sales (attributed rows): {len(aug)}\n")
    for x in aug:
        mark = " ◀ 重开日当天或之后" if x.date >= REOPEN_DAY else ""
        hit = " ★重开创意" if any(k in x.ad for k in REOPENED) and x.date >= REOPEN_DAY else ""
        print(f"  {x.date}  {x.ad[:38]:38} ← {x.campaign[:44]}{mark}{hit}")
    post = [x for x in aug if x.date >= REOPEN_DAY]
    print(f"\n≥{REOPEN_DAY} (重开后): {len(post)} 单 / 8月共 {len(aug)} 单")


if __name__ == "__main__":
    main()
