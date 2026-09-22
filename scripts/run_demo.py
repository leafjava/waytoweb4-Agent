"""One-shot launcher for the demo.

Boots the FastAPI backend on :8000 and the Vite dev server on
:5173, then waits for both to be reachable, then parks on Ctrl-C
to clean up.

Usage:

    python scripts/run_demo.py

Environment:

    PASSPORT_BACKEND=mock|sepolia  (default mock)
    KILN_API_KEY=...                (omit for the offline mock Kiln)
    FRONTEND_ORIGIN=http://...      (default http://localhost:5173)
    BACKEND_PORT=8000               (override if needed)
    FRONTEND_PORT=5173              (override if needed)
"""

from __future__ import annotations

import os
import signal
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKEND_DIR = ROOT / "backend"
FRONTEND_DIR = ROOT / "frontend"

BACKEND_PORT = int(os.environ.get("BACKEND_PORT", "8000"))
FRONTEND_PORT = int(os.environ.get("FRONTEND_PORT", "5173"))


def _http_ok(url: str, timeout: float = 1.0) -> bool:
    try:
        with urllib.request.urlopen(url, timeout=timeout) as r:
            return 200 <= r.status < 500
    except Exception:
        return False


def _wait_for(url: str, label: str, timeout_s: float = 30.0) -> bool:
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        if _http_ok(url):
            print(f"[ok] {label} ready at {url}")
            return True
        time.sleep(0.4)
    print(f"[warn] {label} did NOT become ready at {url} within {timeout_s}s")
    return False


def _start_backend() -> subprocess.Popen:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(ROOT)
    cmd = [
        sys.executable,
        "-m",
        "uvicorn",
        "backend.app.main:app",
        "--host",
        "127.0.0.1",
        "--port",
        str(BACKEND_PORT),
        "--log-level",
        "info",
    ]
    print(f"[boot] backend: {' '.join(cmd)}")
    return subprocess.Popen(cmd, cwd=str(ROOT), env=env)


def _start_frontend() -> subprocess.Popen:
    npm_cmd = "npm.cmd" if sys.platform.startswith("win") else "npm"
    cmd = [npm_cmd, "run", "dev", "--", "--port", str(FRONTEND_PORT), "--host"]
    print(f"[boot] frontend: {' '.join(cmd)} (cwd={FRONTEND_DIR})")
    # Windows shells need shell=False but the .cmd is fine to invoke directly.
    return subprocess.Popen(cmd, cwd=str(FRONTEND_DIR))


def main() -> int:
    procs: list[subprocess.Popen] = []
    try:
        procs.append(_start_backend())
        procs.append(_start_frontend())

        backend_ok = _wait_for(f"http://127.0.0.1:{BACKEND_PORT}/api/health", "backend")
        frontend_ok = _wait_for(f"http://127.0.0.1:{FRONTEND_PORT}/", "frontend")

        print()
        print("=" * 60)
        print(f"  backend  http://127.0.0.1:{BACKEND_PORT}  ({'OK' if backend_ok else 'DOWN'})")
        print(f"  frontend http://localhost:{FRONTEND_PORT}  ({'OK' if frontend_ok else 'DOWN'})")
        print("  Open the FRONTEND URL in your browser to run the demo.")
        print("  Press Ctrl-C to stop both services.")
        print("=" * 60)

        while True:
            time.sleep(0.5)
            if any(p.poll() is not None for p in procs):
                # Someone died on its own; surface it.
                for p in procs:
                    if p.returncode is not None and p.returncode != 0:
                        print(f"[error] child exited rc={p.returncode}: {p.args}")
                break
    except KeyboardInterrupt:
        print("\n[shutdown] Ctrl-C received")
    finally:
        for p in procs:
            try:
                p.terminate()
            except Exception:
                pass
        for p in procs:
            try:
                p.wait(timeout=4)
            except subprocess.TimeoutExpired:
                try:
                    p.kill()
                except Exception:
                    pass
    return 0


if __name__ == "__main__":
    sys.exit(main())