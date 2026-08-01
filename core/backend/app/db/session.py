"""
NeuroSync — Engine and session factory.

Synchronous SQLAlchemy, deliberately (doc 10 D-007). The service layer is sync
CPU-bound code called from async endpoints; a single-row INSERT is ~1 ms beside a
~260 ms analysis, so an async driver would buy nothing and would force the whole
service layer to be async-ified inside a persistence task.
"""
from __future__ import annotations

import logging
from typing import Any

from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

logger = logging.getLogger(__name__)


def build_engine(url: str, echo: bool = False) -> Engine:
    """
    Create an Engine for `url`, applying the settings each dialect needs.

    PostgreSQL is the production target; SQLite is supported so local
    development and the restart probe exercise the same code path without a
    server (doc 10 D-007).
    """
    kwargs: dict[str, Any] = {"echo": echo, "future": True}

    if url.startswith("sqlite"):
        # FastAPI hands sync work to a threadpool, so connections cross threads.
        kwargs["connect_args"] = {"check_same_thread": False}
    else:
        # Managed Postgres closes idle connections; pre_ping avoids handing a
        # dead one to a request. recycle stays under typical 5-minute idle caps.
        kwargs.update(pool_pre_ping=True, pool_recycle=280, pool_size=5, max_overflow=5)

    engine = create_engine(url, **kwargs)

    if url.startswith("sqlite"):
        @event.listens_for(engine, "connect")
        def _enforce_sqlite_fks(dbapi_connection, _record):  # pragma: no cover - trivial
            # SQLite ignores foreign keys unless asked; without this the
            # analyses→feedback cascade silently does nothing.
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

    logger.info("Database engine created (%s)", engine.dialect.name)
    return engine


def build_session_factory(engine: Engine) -> sessionmaker[Session]:
    return sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def redact(url: str) -> str:
    """Strip credentials from a database URL so it is safe to log or return."""
    if "@" not in url:
        return url
    scheme, _, rest = url.partition("://")
    _credentials, _, host = rest.rpartition("@")
    return f"{scheme}://***@{host}"
