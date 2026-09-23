"""FastAPI app factory + lifespan.

We do the smallest amount of work at startup: load the JSON ledger,
wire up routers, and install the CORS middleware. The async lock
inside AppState is per-instance so tests can swap state cleanly.
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .engine import cancel_all
from .deps import close_passport_backend
from .routers import engine, face, health, passport, redline, spec, state as state_router
from .state import AppState


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Load the ledger at start; cancel engine tasks at shutdown."""
    ledger_path: Path = settings.ledger_path
    state = AppState(ledger_path=ledger_path)
    state.load()
    await state.reconcile_after_restart()
    app.state.app_state = state
    try:
        yield
    finally:
        await cancel_all()
        await close_passport_backend()


def create_app() -> FastAPI:
    app = FastAPI(
        title="waytoweb4-agent backend",
        version="0.1.0",
        lifespan=lifespan,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[settings.frontend_origin, "http://localhost:5173"],
        # The demo has no cookie-based authentication.
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(spec.router)
    app.include_router(face.router)
    app.include_router(passport.router)
    app.include_router(engine.router)
    app.include_router(redline.router)
    app.include_router(state_router.router)
    app.include_router(health.router)
    return app


app = create_app()


__all__ = ["app", "create_app", "lifespan"]
