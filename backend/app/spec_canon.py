"""Canonical JSON serialisation.

`web3.keccak` is deterministic only when its input is deterministic.
Python's `json.dumps` is not: it depends on dict insertion order, key
quoting style, and Unicode escapes. This module pins the encoding so
that the same Spec dict always hashes to the same keccak.
"""

from __future__ import annotations

import json
from typing import Any


def canonical_json(obj: Any) -> str:
    """Render `obj` as a canonical UTF-8 JSON string.

    Rules:
        * sort_keys=True  -- dict keys in lexical order
        * separators=(",", ":") -- no spaces
        * ensure_ascii=False -- Chinese / Korean preserved as-is
        * default=str -- datetimes / decimals etc. become ISO strings
          (matches what a JSON Schema serialiser would emit)
    """
    return json.dumps(
        obj,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        default=str,
    )


__all__ = ["canonical_json"]