"""
NeuroSync — Alembic environment (blueprint 09 §4).

The URL comes from `app.config` (NEUROSYNC_DATABASE_URL), never from alembic.ini,
so a migration cannot be applied to a different database than the one the app
talks to, and no credential is committed.

Offline mode is useful without a server:

    NEUROSYNC_DATABASE_URL=postgresql+psycopg://u:p@h/db \
        python -m alembic upgrade head --sql

emits the PostgreSQL DDL to stdout without connecting to anything.
"""
from __future__ import annotations

import sys
from logging.config import fileConfig
from pathlib import Path

from alembic import context
from sqlalchemy import engine_from_config, pool

# The backend root, so `import app.…` works however alembic was invoked.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.config import get_settings          # noqa: E402
from app.db.models import Base               # noqa: E402

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def _database_url() -> str:
    url = get_settings().database_url
    if not url:
        raise RuntimeError(
            "NEUROSYNC_DATABASE_URL is not set. Alembic will not guess a database "
            "to migrate — export it first, e.g.\n"
            "  export NEUROSYNC_DATABASE_URL=postgresql+psycopg://user:pass@host/neurosync"
        )
    return url


def run_migrations_offline() -> None:
    """Emit SQL to stdout without a live connection."""
    context.configure(
        url=_database_url(),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Apply migrations against a live database."""
    section = config.get_section(config.config_ini_section, {})
    section["sqlalchemy.url"] = _database_url()

    connectable = engine_from_config(section, prefix="sqlalchemy.", poolclass=pool.NullPool)

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            # SQLite cannot ALTER most things in place; batch mode rewrites the
            # table instead, so the same revision applies on both dialects.
            render_as_batch=connection.dialect.name == "sqlite",
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
