"""
(en) Postgres health checks and adapter builders (repo `infrastructure` + `psycopg`).

Does not import `psycopg` at module import time; loads on function call.

(kr) Postgres 점검·어댑터 빌더이다(레포 `infrastructure` + `psycopg`).

모듈 import 시점에는 `psycopg`를 끌어오지 않고, 함수 호출 시 로드한다.
"""
from __future__ import annotations

from typing import Any

from exaone.integrations.infra_env import (
    embedding_dim_from_env,
    postgres_url_from_env,
    vector_table_name_from_env,
)

_LLAMA_INDEX_PREFIX = "data_"


def _table_candidates(table_name: str) -> tuple[str, ...]:
    name = (table_name or "").strip()
    if not name:
        return ()
    if name.startswith(_LLAMA_INDEX_PREFIX):
        return (name, name[len(_LLAMA_INDEX_PREFIX):])
    return (name, _LLAMA_INDEX_PREFIX + name)


def postgres_available(url: str, timeout_sec: int = 3) -> bool:
    import psycopg

    try:
        with psycopg.connect(url, connect_timeout=timeout_sec) as _:
            return True
    except Exception:
        return False


def _table_exists(url: str, table_name: str, timeout_sec: int) -> bool:
    import psycopg
    from psycopg import sql as psql

    if not table_name:
        return False
    try:
        with psycopg.connect(url, connect_timeout=timeout_sec) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    psql.SQL("SELECT 1 FROM {tbl} LIMIT 0").format(
                        tbl=psql.Identifier(table_name)
                    )
                )
        return True
    except Exception:
        return False


def vector_table_available(url: str, table_name: str, timeout_sec: int = 3) -> bool:
    return resolve_vector_table_name(url, table_name, timeout_sec) is not None


def resolve_vector_table_name(
    url: str, table_name: str, timeout_sec: int = 3
) -> str | None:
    for candidate in _table_candidates(table_name):
        if _table_exists(url, candidate, timeout_sec):
            return candidate
    return None


def graph_tables_available(url: str, timeout_sec: int = 3) -> bool:
    return _table_exists(url, "graph_entities", timeout_sec) and _table_exists(
        url, "graph_relations", timeout_sec
    )


def build_vector_adapter_from_env(
    url: str,
    embedder: Any,
    *,
    table_name: str | None = None,
) -> Any:
    from infrastructure.database.postgres import PgVectorAdapter

    resolved = (table_name or vector_table_name_from_env()).strip()
    return PgVectorAdapter(
        connection_url=url,
        embedder=embedder,
        table_name=resolved,
        embed_dim=embedding_dim_from_env(),
        text_column="text",
        metadata_column="metadata_",
    )


def build_graph_adapter_from_env(url: str) -> Any:
    from infrastructure.database.postgres import PgGraphAdapter

    return PgGraphAdapter(connection_url=url)


__all__ = [
    "build_graph_adapter_from_env",
    "build_vector_adapter_from_env",
    "graph_tables_available",
    "postgres_available",
    "postgres_url_from_env",
    "resolve_vector_table_name",
    "vector_table_available",
    "vector_table_name_from_env",
]
