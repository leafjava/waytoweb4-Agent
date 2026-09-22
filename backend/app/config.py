"""Runtime settings for the backend.

We intentionally keep this tiny -- env vars are loaded once at
import time. If you need hot-reload of settings, turn this into a
function that reads from `os.environ` on every call.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


def _backend_root() -> Path:
    # backend/app/config.py -> backend/
    return Path(__file__).resolve().parent.parent


@dataclass(frozen=True)
class Settings:
    passport_backend: str        # "mock" | "sepolia"
    trip_seconds: int            # seconds for the mock engine to drawdown -> maxLoss
    ledger_path: Path            # JSON ledger for the mock backend
    frontend_origin: str         # for CORS
    chain_id_sepolia: int        # 11155111

    @classmethod
    def load(cls) -> "Settings":
        backend = os.environ.get("PASSPORT_BACKEND", "mock").strip().lower()
        if backend not in {"mock", "local", "sepolia"}:
            raise ValueError(
                f"PASSPORT_BACKEND must be 'mock', 'local' or 'sepolia'; got {backend!r}"
            )
        return cls(
            passport_backend=backend,
            trip_seconds=int(os.environ.get("TRIP_SECONDS", "60")),
            ledger_path=Path(
                os.environ.get(
                    "LEDGER_PATH",
                    str(_backend_root() / "var" / "passports.json"),
                )
            ),
            frontend_origin=os.environ.get(
                "FRONTEND_ORIGIN", "http://localhost:5173"
            ),
            chain_id_sepolia=11155111,
        )


settings = Settings.load()
