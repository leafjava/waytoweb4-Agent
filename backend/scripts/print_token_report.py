"""Print the current token / energy table to stdout.

Usage:

    python -m backend.scripts.print_token_report > token-table.md

Reads the process-wide `TokenLogger` populated by the demo flow and
emits the PRD §9 markdown table.
"""

from __future__ import annotations

from backend.app.token_report import render_report


def main() -> int:
    print(render_report())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())