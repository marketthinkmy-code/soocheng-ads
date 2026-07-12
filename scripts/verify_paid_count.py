"""Read-only reconciliation: why the sheet shows 544 paid students but parse_sales
kept 455. Prints ONLY counts, header names, and blank-pattern breakdown — never a
student's name/contact. Also lists every tab's row count to rule out a second tab.
"""
from __future__ import annotations

from adbot import cpa
from adbot.clients.sheets import SheetsClient
from adbot.settings import load_settings


def main() -> None:
    s = load_settings()
    sc = SheetsClient(s.secrets.google_sa_json)

    meta = sc._svc.spreadsheets().get(spreadsheetId=s.cpa.spreadsheet_id).execute()
    print("TABS in the spreadsheet (rows are the sheet grid size, incl. blanks):")
    for sh in meta.get("sheets", []):
        p = sh["properties"]
        print(f"  gid={p.get('sheetId'):>10}  rows~{p.get('gridProperties', {}).get('rowCount')}"
              f"  cols~{p.get('gridProperties', {}).get('columnCount')}  title={p.get('title')}")

    values = sc.read_tab(s.cpa.spreadsheet_id, s.cpa.sales_tab)
    print(f"\nTab read: '{s.cpa.sales_tab}' — {len(values)} non-empty rows returned by the API")

    sales, cols, header = cpa.parse_sales(values, s.cpa.price_myr)
    header_idx = next(i for i, r in enumerate(values) if r == header)
    data = values[header_idx + 1:]
    print(f"header row index = {header_idx}  (so data rows = {len(data)})")
    print(f"column mapping   = {cols}")
    print(f"header cells     = {header}")

    both = c_only = a_only = neither = truly_empty = 0
    neither_with_date = 0
    for row in data:
        def cell(key):
            idx = cols.get(key, -1)
            return row[idx] if 0 <= idx < len(row) else ""
        c, a = cpa.norm(cell("campaign")), cpa.norm(cell("ad"))
        if not any(str(x).strip() for x in row):
            truly_empty += 1
            continue
        if c and a:
            both += 1
        elif c:
            c_only += 1
        elif a:
            a_only += 1
        else:
            neither += 1
            if cpa.parse_date(cell("date")):
                neither_with_date += 1

    print("\nRECONCILIATION")
    print(f"  data rows below header          : {len(data)}")
    print(f"    campaign + ad both present    : {both}")
    print(f"    campaign only (no ad)         : {c_only}")
    print(f"    ad only (no campaign)         : {a_only}")
    print(f"    NO campaign & NO ad (dropped) : {neither}   <- organic / manual, no UTM"
          f"  ({neither_with_date} of them have a valid date)")
    print(f"    truly empty rows              : {truly_empty}")
    print(f"  parse_sales kept                : {len(sales)}  (= both + c_only + a_only)")
    print(f"  attributed to an ad             : {both + a_only}")
    print("\nDONE.")


if __name__ == "__main__":
    main()
