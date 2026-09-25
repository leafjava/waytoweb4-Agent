"""Atomic local policy file used independently by paper workers."""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path


def write_policy(path: Path, version: int, allowed_leaders: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    body = json.dumps({"version": version, "allowed_leaders": allowed_leaders}, sort_keys=True)
    fd, tmp = tempfile.mkstemp(prefix=path.name, dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(body)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


__all__ = ["write_policy"]
