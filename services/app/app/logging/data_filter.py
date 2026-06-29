from __future__ import annotations

import re
from typing import Any

MASK = "***"

# SQLAlchemy wraps the raw query and bound parameters in these blocks.
# psycopg2/asyncpg may also embed connection strings in error messages.
SQL_BLOCK = re.compile(r"\[SQL:.*?\]", re.DOTALL)
PARAMS_BLOCK = re.compile(r"\[parameters:.*?\]", re.DOTALL)
DB_CONNSTR = re.compile(
    r"\b(postgresql|mysql|sqlite|mongodb|redis)(\+\w+)?://\S+",
    re.IGNORECASE,
)

SENSITIVE_KEYS: frozenset[str] = frozenset(
    {
        "password",
        "passwd",
        "pass",
        "secret",
        "secret_key",
        "token",
        "access_token",
        "refresh_token",
        "id_token",
        "auth_token",
        "bearer_token",
        "bearer",
        "jwt",
        "session_token",
        "session",
        "oauth_token",
        "client_secret",
        "client_token",
        "authorization",
        "auth",
        "api_key",
        "apikey",
        "private_key",
        "signing_key",
        "credential",
        "credentials",
        "credit_card",
        "card_number",
        "cvv",
        "cvc",
        "ssn",
        "pin",
    }
)


def mask_sensitive(
    data: dict[str, Any] | list[Any] | None,
) -> dict[str, Any] | list[Any] | None:
    if data is None:
        return None
    if isinstance(data, list):
        return mask_list(data)
    return mask_dict(data)


def mask_dict(data: dict[str, Any]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in data.items():
        if isinstance(key, str) and key.lower() in SENSITIVE_KEYS:
            result[key] = MASK
        elif isinstance(value, dict):
            result[key] = mask_dict(value)
        elif isinstance(value, list):
            result[key] = mask_list(value)
        else:
            result[key] = value
    return result


def mask_list(items: list[Any]) -> list[Any]:
    return [mask_dict(item) if isinstance(item, dict) else item for item in items]


def sanitize_traceback(trace: str) -> str:
    """Strip SQL statements, bound parameters, and connection strings from a traceback string."""
    trace = SQL_BLOCK.sub("[SQL redacted]", trace)
    trace = PARAMS_BLOCK.sub("[parameters redacted]", trace)
    trace = DB_CONNSTR.sub("[connection string redacted]", trace)
    return trace
