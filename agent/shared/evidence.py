"""Small append-only per-run evidence writer; secrets never enter records."""

from __future__ import annotations

import json
import os
import threading
from contextlib import contextmanager
from contextvars import ContextVar
from datetime import datetime, timezone
from pathlib import Path


class EvidenceWriter:
    def __init__(self, root: str | Path, run_id: str, source_mode: str):
        self.dir = Path(root) / run_id
        self.dir.mkdir(parents=True, exist_ok=True)
        self.run_id = run_id
        self.source_mode = source_mode
        self._lock = threading.Lock()
        self.write_json("manifest.json", {"schema_version": 1, "run_id": run_id, "source_mode": source_mode, "created_at": datetime.now(timezone.utc).isoformat()})

    def write_json(self, name: str, value: dict):
        (self.dir / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    def append(self, name: str, value: dict):
        with self._lock:
            with (self.dir / name).open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(value, ensure_ascii=False, separators=(",", ":")) + "\n")


_writer: EvidenceWriter | None = None
_active_writer: ContextVar[EvidenceWriter | None] = ContextVar("active_evidence_writer", default=None)


def get_evidence_writer() -> EvidenceWriter | None:
    global _writer
    active = _active_writer.get()
    if active is not None:
        return active
    root, run_id = os.environ.get("EVIDENCE_DIR"), os.environ.get("RUN_ID")
    if not root or not run_id:
        return None
    if _writer is None or _writer.run_id != run_id:
        _writer = EvidenceWriter(root, run_id, os.environ.get("KILN_MODE", "offline"))
    return _writer


@contextmanager
def use_evidence_writer(writer: EvidenceWriter | None):
    """Bind call evidence to the current backend workflow context."""
    token = _active_writer.set(writer)
    try:
        yield
    finally:
        _active_writer.reset(token)


__all__ = ["EvidenceWriter", "get_evidence_writer", "use_evidence_writer"]
