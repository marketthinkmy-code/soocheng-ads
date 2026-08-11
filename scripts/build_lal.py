# -*- coding: utf-8 -*-
"""Build the PURCHASE customer audience + 5% Lookalike on BOTH accounts.

Owner-approved 2026-08-10 (「同时间…今天把 546 买家的 customer audience + 5% LAL
(MY+SG) 建起来」). Reads the Paid Student List, normalises + SHA256-hashes emails and
phones IN THIS PROCESS ONLY (no raw identifiers are ever printed or logged), then per
account: reuse-or-create the CUSTOM audience, upload the hashed users, and create the
5% lookalike (country MY on the MY account, SG on the SG account).

FPS note: the accounts declare FINANCIAL_PRODUCTS_SERVICES — if Meta blocks lookalikes
for this vertical it surfaces at ad-set attach time, not here; creation should succeed.
Dry-run unless CONFIRM=true.
"""
from __future__ import annotations

import hashlib
import json
import os
import re

from adbot.clients.graph import GraphError
from adbot.clients.sheets import SheetsClient
from adbot.commands import graph_client
from adbot.settings import REPO_ROOT, load_settings

CONFIRM = (os.environ.get("CONFIRM") or "").strip().lower() in ("1", "true", "yes")
AUD_NAME = "PURCHASE LIST — Paid Student List (2026-08-10)"
LAL_RATIO = 0.05
ACCOUNTS = (("MY", "config.yaml", "MY"), ("SG", "config.sg.yaml", "SG"))


def _hkey(s: str) -> str:
    return re.sub(r"[^a-z0-9一-鿿]", "", (s or "").casefold())


def find_col(header, *needles):
    keys = [_hkey(h) for h in header]
    for n in needles:
        for i, k in enumerate(keys):
            if n in k:
                return i
    return -1


def norm_phone(s: str) -> str:
    d = re.sub(r"\D", "", s or "")
    if len(d) < 8:
        return ""
    if d.startswith("60") or d.startswith("65"):
        return d
    if d.startswith("0"):
        return "6" + d
    if len(d) == 8 and d[0] in "89":
        return "65" + d
    return d


def sha(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def main() -> None:
    mode = "APPLY (CONFIRM=true)" if CONFIRM else "DRY-RUN (set confirm=true to apply)"
    print(f"Build purchase LAL — {mode}\n")
    base = load_settings(REPO_ROOT / "config" / "config.yaml")
    values = SheetsClient(base.secrets.google_sa_json).read_tab(
        base.cpa.spreadsheet_id, base.cpa.sales_tab)
    header_idx = 0
    for i, row in enumerate(values[:8]):
        if find_col(row, "email") >= 0 or find_col(row, "phone", "contact", "电话", "手机") >= 0:
            header_idx = i
            break
    header = values[header_idx]
    e_col = find_col(header, "email", "邮箱")
    p_col = find_col(header, "phone", "contact", "whatsapp", "电话", "手机", "号码")
    print(f"header row {header_idx + 1}: email col={e_col} «{header[e_col] if e_col >= 0 else '-'}» · "
          f"phone col={p_col} «{header[p_col] if p_col >= 0 else '-'}»")
    if e_col < 0 and p_col < 0:
        raise SystemExit("⛔ no email/phone column found — check the sheet headers")

    emails, phones, rows = set(), set(), 0
    for row in values[header_idx + 1:]:
        got = False
        if 0 <= e_col < len(row):
            e = (row[e_col] or "").strip().lower()
            if "@" in e and "." in e:
                emails.add(sha(e))
                got = True
        if 0 <= p_col < len(row):
            p = norm_phone(row[p_col] if p_col < len(row) else "")
            if p:
                phones.add(sha(p))
                got = True
        rows += got
    print(f"identifiable rows={rows} · unique emails={len(emails)} · unique phones={len(phones)}")
    if rows < 100:
        print("⚠️ fewer than 100 identifiable rows — lookalike creation may be refused")

    for label, cfg, country in ACCOUNTS:
        s = load_settings(REPO_ROOT / "config" / cfg)
        g = graph_client(s)
        acct = s.meta.account_path
        print(f"\n═══ [{label}] {acct} — LAL country {country} ═══")
        existing = {a.get("name"): a.get("id") for a in g.list_custom_audiences(acct)}
        aud_id = existing.get(AUD_NAME)
        lal_name = f"PURCHASE 5% LAL {country} (seed: Paid Student List)"
        if not CONFIRM:
            print(f"▶ would {'reuse' if aud_id else 'create'} custom audience «{AUD_NAME}»"
                  + (f" (id {aud_id})" if aud_id else ""))
            print(f"▶ would upload {len(emails)} email + {len(phones)} phone hashes")
            if lal_name in existing:
                print(f"✓ LAL already exists: «{lal_name}» (id {existing[lal_name]})")
            else:
                print(f"▶ would create «{lal_name}» ratio {LAL_RATIO}")
            continue
        try:
            if not aud_id:
                res = g._request("POST", f"{acct}/customaudiences", data={
                    "name": AUD_NAME, "subtype": "CUSTOM",
                    "customer_file_source": "USER_PROVIDED_ONLY",
                    "description": "Course buyers from the Paid Student List (hashed upload)"})
                aud_id = res.get("id")
                print(f"✅ created custom audience id {aud_id}")
            else:
                print(f"✓ reusing custom audience id {aud_id}")
            for schema, hashes in (("EMAIL_SHA256", emails), ("PHONE_SHA256", phones)):
                if not hashes:
                    continue
                g._request("POST", f"{aud_id}/users", data={
                    "payload": json.dumps(
                        {"schema": schema, "data": [[h] for h in sorted(hashes)]})})
                print(f"✅ uploaded {len(hashes)} {schema} hashes")
            if lal_name in existing:
                print(f"✓ LAL already exists: id {existing[lal_name]}")
            else:
                res = g._request("POST", f"{acct}/customaudiences", data={
                    "name": lal_name, "subtype": "LOOKALIKE",
                    "origin_audience_id": aud_id,
                    "lookalike_spec": json.dumps({"ratio": LAL_RATIO, "country": country})})
                print(f"✅ created LAL id {res.get('id')} (populates over ~6-24h)")
        except GraphError as e:
            print(f"❌ [{label}] {e} — continuing")


if __name__ == "__main__":
    main()
