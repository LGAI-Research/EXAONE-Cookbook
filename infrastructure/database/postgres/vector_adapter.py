"""
pgvector 테이블 기반 벡터 검색. exaone.retrieval.VectorRetrievalStrategy 에 embed_fn, search_fn 제공.
LlamaIndex step3로 생성된 테이블(text, metadata_, embedding) 또는 schema.sql 스타일(content, metadata, embedding) 지원.
"""
from __future__ import annotations

import logging
import re
from typing import Any, Callable

try:
    import psycopg
    from psycopg import sql as psycopg_sql
except ImportError:
    psycopg = None
    psycopg_sql = None

logger = logging.getLogger(__name__)
_IDENTIFIER_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


class PgVectorAdapter:
    """
    Postgres pgvector 테이블에서 쿼리 임베딩으로 유사도 검색.
    embedder: infrastructure.embedding.Embedder (embed_one 제공).
    """

    def __init__(
        self,
        connection_url: str,
        embedder: Any,
        table_name: str = "embeddings",
        embed_dim: int = 384,
        text_column: str = "text",
        metadata_column: str = "metadata_",
    ):
        if psycopg is None:
            raise ImportError("psycopg 필요: pip install 'psycopg[binary]'")
        self.connection_url = connection_url
        self.embedder = embedder
        self.table_name = self._validate_identifier(table_name, "table_name")
        self.embed_dim = embed_dim
        self.text_column = self._validate_identifier(text_column, "text_column")
        self.metadata_column = self._validate_identifier(metadata_column, "metadata_column")
        self._connection = None

    @staticmethod
    def _validate_identifier(value: str, field: str) -> str:
        """SQL identifier(테이블/컬럼명) 검증."""
        if not _IDENTIFIER_RE.match(value):
            raise ValueError(f"Invalid {field}: {value!r}")
        return value

    def _conn(self, force_reconnect: bool = False):
        if force_reconnect and self._connection is not None:
            try:
                self._connection.close()
            except Exception:
                pass
            self._connection = None
        if self._connection is None or getattr(self._connection, "closed", False):
            self._connection = psycopg.connect(self.connection_url)
        return self._connection

    def _fetchall_with_retry(self, query: Any, params: tuple[Any, ...]) -> list[tuple[Any, ...]]:
        last_error: Exception | None = None
        for attempt in range(2):
            try:
                conn = self._conn(force_reconnect=(attempt > 0))
                with conn.cursor() as cur:
                    cur.execute(query, params)
                    return cur.fetchall()
            except Exception as exc:
                last_error = exc
                logger.debug("pgvector query failed (attempt=%d): %s", attempt + 1, exc)
        raise last_error if last_error is not None else RuntimeError("vector query failed")

    def _build_similarity_query(self, table: str, text_col: str, metadata_col: str):
        return psycopg_sql.SQL(
            "SELECT {text_col}, {metadata_col}, 1 - (embedding <=> %s::vector) AS score "
            "FROM {table_name} ORDER BY embedding <=> %s::vector LIMIT %s"
        ).format(
            text_col=psycopg_sql.Identifier(text_col),
            metadata_col=psycopg_sql.Identifier(metadata_col),
            table_name=psycopg_sql.Identifier(table),
        )

    def _run_search(self, vec_str: str, top_k: int) -> list[dict[str, Any]]:
        """vec_str으로 유사도 검색. (text, metadata_) 실패 시 (content, metadata) 또는 data_embeddings 테이블 재시도."""
        sql_primary = self._build_similarity_query(self.table_name, self.text_column, self.metadata_column)
        try:
            rows = self._fetchall_with_retry(sql_primary, (vec_str, vec_str, top_k))
        except Exception as e:
            err_msg = str(e).lower()
            # 테이블 없음: LlamaIndex는 "data_embeddings" 생성. embeddings 없으면 data_embeddings 시도.
            if "does not exist" in err_msg and self.table_name == "embeddings":
                try:
                    rows = self._fetchall_with_retry(
                        self._build_similarity_query("data_embeddings", "text", "metadata_"),
                        (vec_str, vec_str, top_k),
                    )
                except Exception:
                    return []
            elif self.text_column == "text" and self.metadata_column == "metadata_":
                try:
                    rows = self._fetchall_with_retry(
                        self._build_similarity_query(self.table_name, "content", "metadata"),
                        (vec_str, vec_str, top_k),
                    )
                except Exception:
                    return []
            else:
                return []
        return [
            {"text": r[0] or "", "content": r[0] or "", "score": float(r[2]) if r[2] is not None else 0.0, "metadata": r[1] or {}}
            for r in rows
        ]

    def search(self, query: str, top_k: int = 5) -> list[dict[str, Any]]:
        """쿼리 문자열을 임베딩해 pgvector 유사도 검색. 반환: [{"text", "content", "score", "metadata"}, ...]."""
        try:
            vector = self.embedder.embed_one(query)
        except Exception:
            return []
        if not vector or len(vector) != self.embed_dim:
            return []
        vec_str = "[" + ",".join(str(float(x)) for x in vector) + "]"
        return self._run_search(vec_str, top_k)

    def embed_fn_for_exaone(self) -> Callable[[str], list[float]]:
        """exaone VectorRetrievalStrategy용 embed_fn."""

        def fn(text: str) -> list[float]:
            return self.embedder.embed_one(text)

        return fn

    def search_fn_for_exaone(self, top_k_default: int = 5) -> Callable[[list[float], int], list[dict[str, Any]]]:
        """exaone VectorRetrievalStrategy용 search_fn. (vector, top_k) -> hits."""

        def fn(vector: list[float], top_k: int = top_k_default) -> list[dict[str, Any]]:
            if not vector or len(vector) != self.embed_dim:
                return []
            vec_str = "[" + ",".join(str(float(x)) for x in vector) + "]"
            return self._run_search(vec_str, top_k)

        return fn

    def close(self) -> None:
        if self._connection is not None and not getattr(self._connection, "closed", True):
            self._connection.close()

    def __del__(self):
        try:
            self.close()
        except Exception:
            pass
