# -*- coding: utf-8 -*-
"""READ-ONLY: Source values (webinar cycle labels) on Register rows created since 11/25, counted. Prints only the
Source label, created day and whether UTM Campaign is Webinarkit / old / blank. No names, emails or phones."""
from __future__ import annotations

from collections import Counter

from adbot.clients.sheets import SheetsClient
from adbot.settings import REPO_ROOT, load_settings

s = load_settings(REPO_ROOT / "config" / "config.sg.yaml")
reg = SheetsClient(s.secrets.google_sa_json).read_tab(s.cpa.spreadsheet_id, "Register")
hi = next(i for i, r in enumerate(reg[:8]) if "UTM Campaign" in r)
h = reg[hi]
print("Register 栏位:", [c for c in h if c and not any(x in c.lower() for x in ("name", "email", "phone", "remark", "experience"))])
c = Counter()
for r in reg[hi + 1:]:
    d = dict(zip(h, r))
    day = (d.get("Created date") or "")[:10]
    if day < "2026-11-25":
        continue
    u = (d.get("UTM Campaign") or "").strip().lower()
    k = "空白" if not u else ("Webinarkit" if "webinarkit" in u else "旧 campaign")
    c[(day, (d.get("Source") or "").strip(), k)] += 1
for (day, src, k), n in sorted(c.items()):
    print(f"  {day} · Source={src!r} · UTM {k}: {n}")
print("REGISTER SOURCES DONE (read-only)")
