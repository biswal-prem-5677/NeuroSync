"""
NeuroSync — Database layer (SQLAlchemy 2.0 ORM + engine/session management).

Owned by blueprint 09 (schema) and doc 12 §2 Cross-Cutting: State. Nothing
outside `app/state/sql_state.py` may import from here — doc 12 §4 Rule 5 keeps
`StateBackend` as the only persistence boundary the rest of the app sees.
"""
