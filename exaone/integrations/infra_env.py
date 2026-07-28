"""
(en) Env getters for Postgres / embedding (stdlib + exaone.config only).

Actual DB and TEI clients load in `exaone.integrations.postgres` / `exaone.integrations.embedding`.

(kr) Postgres / embedding 관련 env getter이다(stdlib + exaone.config만).

실제 DB·TEI 클라이언트는 `exaone.integrations.postgres` / `exaone.integrations.embedding`에서 로드한다.
"""
from __future__ import annotations

import os

from exaone.config import load_project_env


def postgres_url_from_env() -> str:
    load_project_env()
    host = (os.environ.get("POSTGRES_HOST") or "localhost").strip()
    port = (os.environ.get("POSTGRES_PORT") or "5432").strip()
    user = (os.environ.get("POSTGRES_USER") or "exaone").strip()
    password = (os.environ.get("POSTGRES_PASSWORD") or "exaone").strip()
    dbname = (os.environ.get("POSTGRES_DBNAME") or "exaone").strip()
    sslmode = (os.environ.get("POSTGRES_SSLMODE") or "prefer").strip()
    return f"postgresql://{user}:{password}@{host}:{port}/{dbname}?sslmode={sslmode}"


def vector_table_name_from_env() -> str:
    load_project_env()
    return (os.environ.get("PGVECTOR_TABLE_NAME") or "data_embeddings").strip()


def embedding_base_url_from_env() -> str:
    load_project_env()
    return (os.environ.get("EMBEDDING_BASE_URL") or "http://localhost:8000").strip()


def embedding_dim_from_env() -> int:
    load_project_env()
    return int(
        (os.environ.get("PGVECTOR_EMBEDDING_DIM") or os.environ.get("EMBEDDING_DIMENSIONS") or "384").strip()
    )


def embedding_batch_from_env() -> int:
    load_project_env()
    return int((os.environ.get("EMBEDDING_BATCH_SIZE") or "32").strip())


__all__ = [
    "embedding_base_url_from_env",
    "embedding_batch_from_env",
    "embedding_dim_from_env",
    "postgres_url_from_env",
    "vector_table_name_from_env",
]
