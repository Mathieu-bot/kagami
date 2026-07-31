"""Read-only SQL guard for the Data Explorer (defense in depth).

SQL is not parsed with a full grammar here; instead we apply three cheap
checks and rely on the database layer for the final guarantee:

  1. **Single statement** — any ``;`` is rejected (blocks ``SELECT 1;
     DROP TABLE ...`` style multi-statement payloads).
  2. **Allowed start** — the statement must begin with SELECT / WITH /
     EXPLAIN.
  3. **Result cap** — a ``LIMIT`` clause is appended when missing so the
     small production VM is never asked to materialize a huge result.

The ``config.query()`` layer additionally runs every statement inside a
``READ ONLY`` transaction, so even a bypass cannot modify the database.
"""

import re

_ALLOWED_START_RE = re.compile(r"^\s*(SELECT|WITH|EXPLAIN)\b", re.IGNORECASE)
_SEMICOLON_RE = re.compile(r";")
_HAS_LIMIT_RE = re.compile(r"\bLIMIT\s+\d+(\s+OFFSET\s+\d+)?\s*$", re.IGNORECASE)


def is_read_only_sql(sql: str) -> bool:
    """Return True if ``sql`` is a single read-only statement."""
    if not sql or not sql.strip():
        return False
    if _SEMICOLON_RE.search(sql):
        return False
    return bool(_ALLOWED_START_RE.match(sql))


def enforce_limit(sql: str, max_rows: int = 1000) -> str:
    """Append ``LIMIT max_rows`` unless the statement is already capped."""
    if sql.upper().startswith("EXPLAIN"):
        return sql
    if _HAS_LIMIT_RE.search(sql):
        return sql
    return f"{sql} LIMIT {max_rows}"
