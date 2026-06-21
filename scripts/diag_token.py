"""Read-only credential diagnostic for the (#200) 'Provide valid app ID' error.

Prints only SHAPES and booleans — never the secret values themselves — plus the
result of /me (signed + unsigned) and one ad-account read, so we can pinpoint a
bad/swapped/wrong-type token in a single run.
"""
from __future__ import annotations

import re

from adbot.clients.graph import GraphClient, GraphError
from adbot.commands import graph_client
from adbot.settings import load_settings

HEX32 = re.compile(r"[0-9a-fA-F]{32}")


def main() -> None:
    s = load_settings()
    tok = s.secrets.meta_token or ""
    sec = s.secrets.meta_app_secret or ""

    print("=== credential shapes (no values shown) ===")
    print(f"token         : len={len(tok)}  startswith_EAA={tok.startswith('EAA')}  "
          f"looks_like_app_secret={bool(HEX32.fullmatch(tok))}  "
          f"has_space_or_quote={any(c in tok for c in ' \"\\'')}")
    print(f"app_secret    : len={len(sec)}  is_32_hex={bool(HEX32.fullmatch(sec))}  "
          f"has_space_or_quote={any(c in sec for c in ' \"\\'')}")
    print(f"token==secret : {bool(tok) and tok == sec}   (True => the two secrets are swapped/identical)")
    print(f"account_path  : {s.meta.account_path}")
    print()

    print("=== live calls ===")
    checks = [
        ("/me  signed  ", lambda: graph_client(s).me()),
        ("/me  unsigned", lambda: GraphClient(tok, '').me()),
        ("account read ", lambda: graph_client(s).list_campaigns(s.meta.account_path)[:1]),
    ]
    for label, call in checks:
        try:
            print(f"OK   {label}: {str(call())[:140]}")
        except GraphError as exc:
            print(f"FAIL {label}: {exc}")
        except Exception as exc:  # noqa: BLE001
            print(f"ERR  {label}: {type(exc).__name__}: {str(exc)[:140]}")


if __name__ == "__main__":
    main()
