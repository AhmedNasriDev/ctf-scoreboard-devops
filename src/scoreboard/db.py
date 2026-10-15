"""Engine and session handling.

SQLite by default so the application starts with no infrastructure at all.
Point DATABASE_URL at Postgres and nothing else changes -- which is the whole
point: the same code runs on SQLite and on Postgres.

A database that cannot be reached at start-up does NOT stop the process.
The service starts, answers /healthz, and reports 503 on /readyz until the
database becomes reachable; every probe retries the connection. That is the
behaviour lab sheet 4 (Part C) asks you to observe: a pod whose dependency
is down is taken out of the Service and left running, rather than restarted
in a loop.
"""

from __future__ import annotations

import logging
import threading
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

from sqlalchemy import Engine, create_engine, text
from sqlalchemy.orm import Session, sessionmaker

from .models import Base

log = logging.getLogger("scoreboard.db")

_engine: Engine | None = None
_Session: sessionmaker[Session] | None = None
_url: str | None = None
_lock = threading.Lock()


class DatabaseUnavailable(RuntimeError):
    """The database has not been reached yet, or cannot be reached now."""


def init_engine(database_url: str) -> Engine:
    """Create the engine and the tables. Safe to call more than once.

    Raises if the database cannot be reached or the tables cannot be created;
    callers that must survive that use :func:`try_init`.
    """
    global _engine, _Session, _url

    _url = database_url
    kwargs: dict[str, object] = {"future": True, "pool_pre_ping": True}
    if database_url.startswith("sqlite"):
        # SQLite refuses to be used from a thread other than the one that
        # opened it unless told otherwise, and the server is threaded.
        kwargs["connect_args"] = {"check_same_thread": False}
        path = database_url.split("///", 1)[-1]
        if path and path != ":memory:":
            Path(path).parent.mkdir(parents=True, exist_ok=True)
    elif database_url.startswith("postgresql"):
        # A probe has a timeout of one second by default. A connection
        # attempt that hangs for longer than that fails the probe anyway,
        # so fail fast and say why in the log.
        kwargs["connect_args"] = {"connect_timeout": 2}

    engine = create_engine(database_url, **kwargs)  # type: ignore[arg-type]
    Base.metadata.create_all(engine)
    _engine = engine
    _Session = sessionmaker(bind=engine, expire_on_commit=False, future=True)
    return engine


def try_init(database_url: str) -> bool:
    """Initialise if not already done. Never raises; returns success.

    Thread-safe: readiness probes arrive concurrently, and only one of them
    should be creating tables at a time.
    """
    global _url
    with _lock:
        _url = database_url
        if _engine is not None:
            return True
        try:
            init_engine(database_url)
        except Exception as exc:  # noqa: BLE001 - any failure means "not ready"
            log.error(
                "database not reachable; the service stays up and reports "
                "not ready until it is",
                extra={"error": f"{type(exc).__name__}: {exc}"},
            )
            return False
        return True


def reset() -> None:
    """Forget the engine. Used between tests that need a fresh start."""
    global _engine, _Session, _url
    with _lock:
        if _engine is not None:
            _engine.dispose()
        _engine, _Session, _url = None, None, None


def is_initialised() -> bool:
    return _engine is not None


def get_engine() -> Engine:
    if _engine is None:
        raise DatabaseUnavailable("the database has not been reached yet")
    return _engine


@contextmanager
def session_scope() -> Iterator[Session]:
    """A transaction. Commits on success, rolls back on any exception."""
    if _Session is None:
        raise DatabaseUnavailable("the database has not been reached yet")
    session = _Session()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def ping() -> bool:
    """Can we actually reach the database right now?

    This is what GET /readyz asks, and it is the difference between the two
    health endpoints: liveness asks whether the process is wedged, readiness
    asks whether it can serve. Restarting the process does not bring the
    database back, so a failing ping must not restart the container -- which
    is exactly why they are two endpoints and not one (lab sheet 4).
    """
    if _engine is None and (_url is None or not try_init(_url)):
        return False
    try:
        with get_engine().connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception:
        return False
