"""
infrastructure/setup 전용 설정. 프로젝트 루트 .env 사용 (standalone).

load_config(env) → SetupConfig. env: dev | docker | docker_container
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

_SETUP_DIR = Path(__file__).resolve().parent
_ROOT = _SETUP_DIR.parent.parent
_ENV_PATH = _ROOT / ".env"
if _ENV_PATH.is_file():
    with open(_ENV_PATH, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, _, v = line.partition("=")
                k, v = k.strip(), v.strip().strip("'\"").strip()
                if k:
                    os.environ.setdefault(k, v)


@dataclass(frozen=True)
class PostgresSettings:
    host: str
    port: int
    user: str
    password: str
    dbname: str
    sslmode: str = "prefer"

    @property
    def url(self) -> str:
        return (
            f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.dbname}"
            f"?sslmode={self.sslmode}"
        )


@dataclass(frozen=True)
class PgVectorSettings:
    table_name: str = "embeddings"
    embedding_dim: int = 384
    index_type: str = "ivfflat"
    lists: int = 100


@dataclass(frozen=True)
class EmbeddingSettings:
    base_url: str
    api_key: str | None
    model: str = "intfloat/multilingual-e5-small"
    dimensions: int = 384
    batch_size: int = 32


@dataclass
class SetupConfig:
    env: str
    postgres: PostgresSettings | None = None
    pgvector: PgVectorSettings | None = None
    embedding: EmbeddingSettings | None = None
    debug: bool = False
    extra: dict[str, Any] = field(default_factory=dict)


def _env(key: str, default: str = "") -> str:
    return os.environ.get(key, default).strip()


def _env_int(key: str, default: int) -> int:
    v = _env(key)
    if not v:
        return default
    try:
        return int(v)
    except ValueError:
        return default


def env_bool(name: str, default: bool = False) -> bool:
    v = _env(name).lower()
    if not v:
        return default
    return v in ("1", "true", "yes", "on")


def load_config(env: str = "dev") -> SetupConfig:
    """env: dev | docker | docker_container. 프로젝트 루트 .env 에서 읽고 없으면 기본값."""
    e = env.strip().lower()
    pg_host = _env("POSTGRES_HOST", "localhost")
    pg_port = _env_int("POSTGRES_PORT", 5432)
    pg_user = _env("POSTGRES_USER", "exaone")
    pg_password = _env("POSTGRES_PASSWORD", "exaone")
    pg_dbname = _env("POSTGRES_DBNAME", "exaone")
    pg_sslmode = _env("POSTGRES_SSLMODE", "prefer")

    if e == "docker":
        pg_host = _env("DOCKER_POSTGRES_HOST", "localhost")
        pg_port = _env_int("DOCKER_POSTGRES_PORT", 5432)
        pg_user = _env("DOCKER_POSTGRES_USER", "exaone")
        pg_password = _env("DOCKER_POSTGRES_PASSWORD", "exaone")
        pg_dbname = _env("DOCKER_POSTGRES_DBNAME", "exaone")
        emb_url = _env("DOCKER_EMBEDDING_BASE_URL", "http://localhost:8000")
        emb_dim = _env_int("DOCKER_PGVECTOR_EMBEDDING_DIM", 384)
    elif e == "docker_container":
        pg_host = _env("DOCKER_CONTAINER_POSTGRES_HOST", "db")
        pg_port = _env_int("DOCKER_CONTAINER_POSTGRES_PORT", 5432)
        pg_user = _env("DOCKER_CONTAINER_POSTGRES_USER", "exaone")
        pg_password = _env("DOCKER_CONTAINER_POSTGRES_PASSWORD", "exaone")
        pg_dbname = _env("DOCKER_CONTAINER_POSTGRES_DBNAME", "exaone")
        emb_url = _env("DOCKER_CONTAINER_EMBEDDING_BASE_URL", "http://embedding:80")
        emb_dim = _env_int("DOCKER_CONTAINER_PGVECTOR_EMBEDDING_DIM", 384)
    else:
        emb_url = _env("EMBEDDING_BASE_URL", "http://localhost:8000")
        emb_dim = _env_int("PGVECTOR_EMBEDDING_DIM", 384)

    if e in ("docker", "docker_container"):
        postgres = PostgresSettings(
            host=pg_host, port=pg_port, user=pg_user, password=pg_password, dbname=pg_dbname, sslmode=pg_sslmode,
        )
        pgvector = PgVectorSettings(
            table_name=_env("PGVECTOR_TABLE_NAME", "embeddings"),
            embedding_dim=emb_dim,
            index_type=_env("PGVECTOR_INDEX_TYPE", "ivfflat"),
            lists=_env_int("PGVECTOR_LISTS", 100),
        )
        embedding = EmbeddingSettings(
            base_url=emb_url,
            api_key=None,
            model=_env("DOCKER_EMBEDDING_MODEL", "intfloat/multilingual-e5-small"),
            dimensions=emb_dim,
            batch_size=_env_int("EMBEDDING_BATCH_SIZE", 32),
        )
        return SetupConfig(
            env=e, postgres=postgres, pgvector=pgvector, embedding=embedding,
            debug=env_bool("DEBUG", True), extra={},
        )

    postgres = None
    pgvector = None
    embedding = None
    if env_bool("POSTGRES_ENABLED", True):
        postgres = PostgresSettings(
            host=pg_host, port=pg_port, user=pg_user, password=pg_password, dbname=pg_dbname, sslmode=pg_sslmode,
        )
        pgvector = PgVectorSettings(
            table_name=_env("PGVECTOR_TABLE_NAME", "embeddings"),
            embedding_dim=_env_int("PGVECTOR_EMBEDDING_DIM", emb_dim),
            index_type=_env("PGVECTOR_INDEX_TYPE", "ivfflat"),
            lists=_env_int("PGVECTOR_LISTS", 100),
        )
    if env_bool("EMBEDDING_ENABLED", True):
        embedding = EmbeddingSettings(
            base_url=_env("EMBEDDING_BASE_URL", "http://localhost:8000"),
            api_key=_env("EMBEDDING_API_KEY") or None,
            model=_env("EMBEDDING_MODEL", "intfloat/multilingual-e5-small"),
            dimensions=_env_int("EMBEDDING_DIMENSIONS", 384),
            batch_size=_env_int("EMBEDDING_BATCH_SIZE", 32),
        )
    return SetupConfig(
        env="dev", postgres=postgres, pgvector=pgvector, embedding=embedding,
        debug=env_bool("DEBUG", True), extra={},
    )
