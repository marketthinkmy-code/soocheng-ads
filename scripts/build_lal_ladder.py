# -*- coding: utf-8 -*-
"""Owner 2026-08-19 «帮我建 Lookalike Cust Paid List 1-5%»: the banded lookalike ladder
from the Paid Student List seed, on BOTH accounts.

Per account (MY country MY, SG country SG), five audiences matching the old account's
banded convention:

  PURCHASE 1% LAL {C}    · PURCHASE 1-2% LAL {C} · PURCHASE 2-3% LAL {C}
  PURCHASE 3-4% LAL {C}  · PURCHASE 4-5% LAL {C}     (seed: Paid Student List)

Before creating, the existing seed custom audience (built 2026-08-10) is refreshed with
the sheet's latest buyers — emails/phones normalised and SHA256-hashed IN-PROCESS ONLY,
never printed or logged; Meta dedups re-uploads. The full 5% LAL from 2026-08-10 stays
as-is. Idempotent by audience name; dry-run unless CONFIRM=true.
"""
from __future__ import annotations

import importlib.util
import json
import os
import time

from adbot.clients.graph import GraphError
from adbot.clients.sheets import SheetsClient
from adbot.commands import graph_client
from adbot.settings import REPO_ROOT, load_settings

CONFIRM = (os.environ.get("CONFIRM") or "").strip().lower() in ("1", "true", "yes")
PACE = 3.0


def _load(name: str, fname: str):
    spec = importlib.util.spec_from_file_location(name, str(REPO_ROOT / "scripts" / fname))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


_bl = _load("_build_lal", "build_lal.py")   # find_col / norm_phone / sha / AUD_NAME

BANDS = [
    (None, 0.01, "1%"),
    (0.01, 0.02, "1-2%"),
    (0.02, 0.03, "2-3%"),
    (0.03, 0.04, "3-4%"),
    (0.04, 0.05, "4-5%"),
]
ACCOUNTS = (("MY", "config.yaml", "MY"), ("SG", "config.sg.yaml", "SG"))


def main() -> None:
    mode = "APPLY (CONFIRM=true)" if CONFIRM else "DRY-RUN (set confirm=true to apply)"
    print(f"Purchase LAL ladder 1-5% × MY + SG — {mode}\n")

    base = load_settings(REPO_ROOT / "config" / "config.yaml")
    values = SheetsClient(base.secrets.google_sa_json).read_tab(
        base.cpa.spreadsheet_id, base.cpa.sales_tab)
    header_idx = 0
    for i, row in enumerate(values[:8]):
        if _bl.find_col(row, "email") >= 0 or _bl.find_col(row, "phone", "contact") >= 0:
            header_idx = i
            break
    header = values[header_idx]
    e_col = _bl.find_col(header, "email", "邮箱")
    p_col = _bl.find_col(header, "phone", "contact", "whatsapp", "电话", "手机", "号码")
    emails, phones, rows = set(), set(), 0
    for row in values[header_idx + 1:]:
        got = False
        if 0 <= e_col < len(row):
            e = (row[e_col] or "").strip().lower()
            if "@" in e and "." in e:
                emails.add(_bl.sha(e))
                got = True
        if 0 <= p_col < len(row):
            p = _bl.norm_phone(row[p_col] if p_col < len(row) else "")
            if p:
                phones.add(_bl.sha(p))
                got = True
        rows += got
    print(f"seed refresh source: {rows} identifiable rows · "
          f"{len(emails)} unique emails · {len(phones)} unique phones\n")

    for label, cfg, country in ACCOUNTS:
        s = load_settings(REPO_ROOT / "config" / cfg)
        g = graph_client(s)
        acct = s.meta.account_path
        print(f"═══ [{label}] {acct} — country {country} ═══")
        try:
            existing = {a.get("name"): a.get("id") for a in g.list_custom_audiences(acct)}
            aud_id = existing.get(_bl.AUD_NAME)
            if not aud_id:
                print(f"  ⛔ seed audience «{_bl.AUD_NAME}» not found — skipping account")
                continue
            print(f"  seed audience id {aud_id}")

            if CONFIRM:
                for schema, hashes in (("EMAIL_SHA256", emails), ("PHONE_SHA256", phones)):
                    if not hashes:
                        continue
                    g._request("POST", f"{aud_id}/users", data={
                        "payload": json.dumps(
                            {"schema": schema, "data": [[h] for h in sorted(hashes)]})})
                    print(f"  ✅ refreshed {len(hashes)} {schema} hashes (Meta dedups)")
                    time.sleep(PACE)
            else:
                print(f"  ▶ would refresh seed with {len(emails)} email + {len(phones)} phone hashes")

            for start, ratio, band in BANDS:
                lal_name = f"PURCHASE {band} LAL {country} (seed: Paid Student List)"
                if lal_name in existing:
                    print(f"  ✓ exists: «{lal_name}» (id {existing[lal_name]})")
                    continue
                if not CONFIRM:
                    print(f"  ▶ would create «{lal_name}»"
                          f"  spec start={start if start is not None else 0} ratio={ratio}")
                    continue
                spec = {"ratio": ratio, "country": country}
                if start is not None:
                    spec["starting_ratio"] = start
                res = g._request("POST", f"{acct}/customaudiences", data={
                    "name": lal_name, "subtype": "LOOKALIKE",
                    "origin_audience_id": aud_id,
                    "lookalike_spec": json.dumps(spec)})
                print(f"  ✅ created «{lal_name}»  id {res.get('id')}")
                time.sleep(PACE)
        except GraphError as e:
            print(f"  ❌ [{label}] {e} — continuing")
        print()

    print("DONE — audiences populate over ~1-6h; attach to campaigns when ready."
          if CONFIRM else "DRY-RUN — set confirm=true to build.")


if __name__ == "__main__":
    main()
