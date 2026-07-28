#!/usr/bin/env python3
"""
MS MARCO 데이터를 임베딩하여 PostgreSQL에 저장. vector_rag(pgvector) + graph_rag(엔티티·관계) 빌드.
infrastructure/setup step3_build_rag.sh 에서 호출. standalone.
"""
from __future__ import annotations

import logging
import os
import random
import re
import sys
import time
from pathlib import Path

import infrastructure.setup._bootstrap  # noqa: F401 — ROOT on sys.path
from infrastructure.setup._bootstrap import ROOT
from infrastructure.setup.config import env_bool, load_config

logger = logging.getLogger(__name__)

from tqdm import tqdm

from infrastructure.database.postgres import PgGraphAdapter
from infrastructure.embedding import create_embedder_from_config
from llama_index.core.schema import TextNode
from llama_index.vector_stores.postgres import PGVectorStore

_IDENTIFIER_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def _env_positive_int_or_none(name: str) -> int | None:
    """Parse a positive int from env; 0 or unset means unlimited (full ingest)."""
    v = os.environ.get(name, "").strip()
    if not v:
        return None
    try:
        n = int(v)
    except ValueError:
        logger.warning("Invalid %s=%r — treating as unlimited.", name, v)
        return None
    if n <= 0:
        return None
    return n


def _validate_identifier(value: str, field: str) -> str:
    if not _IDENTIFIER_RE.match(value):
        raise ValueError(f"Invalid {field}: {value!r}")
    return value


def load_ms_marco(ms_marco_path: Path | None = None):
    """MS MARCO 데이터셋 로드. 프로젝트 루트 _temp/ms_marco 에 있으면 load_from_disk, 없으면 Hugging Face."""
    if ms_marco_path and (ms_marco_path / "dataset_info.json").exists():
        from datasets import load_from_disk
        logger.info("Using local _temp: %s", ms_marco_path.resolve())
        return load_from_disk(str(ms_marco_path))
    if ms_marco_path and ms_marco_path.is_dir() and not (ms_marco_path / "dataset_info.json").exists():
        logger.warning(
            "%s 는 있지만 dataset_info.json 이 없습니다. step1_downloads.sh 로 완전히 받았는지 확인하세요. "
            "Hub에서 다시 시도합니다.",
            ms_marco_path,
        )
    # step1 `download_msmarco_to_disk.py` 와 동일: Hub httpx 클라 + HF_TOKEN + 권장 dataset id
    _setup = Path(__file__).resolve().parent
    if str(_setup) not in sys.path:
        sys.path.insert(0, str(_setup))
    import hf_hub_httpx  # noqa: E402
    hf_hub_httpx.apply_huggingface_http_client()

    cache_dir = ms_marco_path.parent / "hf_datasets_cache" if ms_marco_path else None
    if cache_dir:
        os.environ["HF_DATASETS_CACHE"] = str(cache_dir)
    from datasets import load_dataset
    token = os.environ.get("HF_TOKEN") or None
    last_err: Exception | None = None
    # 짧은 id `ms_marco` 는 리다이렉트/캐시 꼬임 시 Hub API JSONDecodeError(빈 body) 를 유발 — microsoft/ 을 먼저
    for name in ("microsoft/ms_marco", "ms_marco"):
        for attempt in range(1, 6):
            try:
                logger.info("Loading MS MARCO from Hub (id=%r, attempt %d/5)…", name, attempt)
                return load_dataset(
                    name,
                    "v1.1",
                    trust_remote_code=False,
                    token=token,
                )
            except Exception as e:
                last_err = e
                logger.warning("load_dataset failed: %s", e)
                if attempt < 5:
                    w = min(60.0, 2.0**attempt) + random.uniform(0, 2.0)
                    logger.info("Retrying in %.0fs (HF: HF_TOKEN, proxy, rate limits)…", w)
                    time.sleep(w)
    if last_err:
        raise last_err
    raise RuntimeError("load_ms_marco: no dataset and no error (unexpected)")


def _chunk_from_item(item, row_query_id: str, split_name: str) -> tuple[str, dict] | None:
    """MS MARCO passage 항목에서 (content, metadata) 추출. 없으면 None."""
    if isinstance(item, dict):
        chunk = item.get("passage_text") or item.get("doc_chunk") or item.get("chunk") or ""
        meta = {
            "source": "ms_marco",
            "query_id": row_query_id,
            "split": split_name,
            "is_selected": item.get("is_selected", 0),
            "url": item.get("url", ""),
        }
    elif isinstance(item, str):
        chunk = item
        meta = {"source": "ms_marco", "query_id": row_query_id, "split": split_name}
    else:
        chunk = str(item) if item else ""
        meta = {"source": "ms_marco", "query_id": row_query_id, "split": split_name}
    if not chunk or not str(chunk).strip():
        return None
    return (str(chunk).strip(), meta)


def _vector_data_table_has_rows(postgres_url: str, pgvector_table_name: str) -> bool:
    """LlamaIndex PGVectorStore 가 쓰는 ``data_<table_name>`` 에 행이 하나라도 있는지."""
    import psycopg as _pg
    from psycopg import sql as _pg_sql

    safe = _validate_identifier(pgvector_table_name, "pgvector.table_name")
    vec_table = f"data_{safe}"
    try:
        with _pg.connect(postgres_url) as _c:
            with _c.cursor() as _cur:
                _cur.execute(
                    _pg_sql.SQL("SELECT 1 FROM {} LIMIT 1").format(_pg_sql.Identifier(vec_table))
                )
                return _cur.fetchone() is not None
    except Exception:
        return False


def collect_contexts(
    dataset,
    max_contexts: int | None = None,
) -> list[tuple[str, dict]]:
    """MS MARCO passages에서 고유 (content, metadata) 수집. max_contexts 이면 조기 종료."""
    seen: set[int] = set()
    out: list[tuple[str, dict]] = []
    split_name = "train" if "train" in dataset else list(dataset.keys())[0]
    split = dataset[split_name]
    for row in tqdm(split, desc="Collecting contexts", unit="row"):
        query_id = str(row.get("query_id") or "")
        passages = row.get("passages") or {}
        texts = passages.get("passage_text", []) if isinstance(passages, dict) else []
        selected = passages.get("is_selected", []) if isinstance(passages, dict) else []
        urls = passages.get("url", []) if isinstance(passages, dict) else []

        for idx, text in enumerate(texts):
            parsed = _chunk_from_item(
                {
                    "passage_text": text,
                    "is_selected": selected[idx] if idx < len(selected) else 0,
                    "url": urls[idx] if idx < len(urls) else "",
                },
                row_query_id=query_id,
                split_name=split_name,
            )
            if not parsed:
                continue
            chunk, meta = parsed
            sig = hash(chunk)
            if sig in seen:
                continue
            seen.add(sig)
            out.append((chunk, meta))
            if max_contexts is not None and len(out) >= max_contexts:
                return out
    return out


def main() -> int:
    config = load_config("dev")
    if not config.postgres:
        logger.error("POSTGRES_ENABLED required. Check 프로젝트 루트 .env")
        return 1
    if not config.pgvector or not config.embedding:
        logger.error("pgvector and embedding config required.")
        return 1

    skip_vector_explicit = env_bool("STEP3_SKIP_VECTOR_INGEST")
    reuse_vectors_if_nonempty = env_bool("STEP3_REUSE_VECTORS_IF_NONEMPTY")
    skip_graph = env_bool("STEP3_SKIP_GRAPH_BUILD")

    skip_vector = skip_vector_explicit
    if not skip_vector and reuse_vectors_if_nonempty:
        if _vector_data_table_has_rows(config.postgres.url, config.pgvector.table_name):
            logger.info(
                "STEP3_REUSE_VECTORS_IF_NONEMPTY=1 이고 기존 벡터 테이블에 데이터가 있어 "
                "벡터 TRUNCATE·임베딩·MS MARCO 로드를 건너뜁니다."
            )
            skip_vector = True

    ms_marco_path = ROOT / "_temp" / "ms_marco"
    ds = None
    contexts: list[tuple[str, dict]] = []

    max_contexts = _env_positive_int_or_none("STEP3_MAX_CONTEXTS")

    if not skip_vector:
        logger.info("Loading MS MARCO dataset...")
        ds = load_ms_marco(ms_marco_path)
        contexts = collect_contexts(ds, max_contexts=max_contexts)
        if max_contexts is not None:
            logger.info(
                "Collected %d unique contexts from MS MARCO (STEP3_MAX_CONTEXTS=%d cap).",
                len(contexts),
                max_contexts,
            )
        else:
            logger.info("Collected %d unique contexts from MS MARCO.", len(contexts))
        if not contexts:
            logger.error("No contexts to embed.")
            return 1

        # 적재(write): LlamaIndex PGVectorStore 사용 — 스키마 자동 생성 + 배치 insert.
        # 검색(read)은 exaone.retrieval 쪽 PgVectorAdapter 가 담당 (여기서는 import 하지 않음).
        embedder = create_embedder_from_config(config.embedding)
        vector_store = PGVectorStore.from_params(
            host=config.postgres.host,
            port=config.postgres.port,
            user=config.postgres.user,
            password=config.postgres.password,
            database=config.postgres.dbname,
            table_name=config.pgvector.table_name,
            embed_dim=config.pgvector.embedding_dim,
            # (en) Build an HNSW ANN index (cosine) so vector search is not a brute-force full scan;
            # keeps query latency flat as the table grows. Created on table setup.
            # (kr) HNSW ANN 인덱스(코사인)를 만들어 벡터 검색이 전수 스캔이 되지 않게 한다.
            # 테이블 행이 늘어도 질의 지연이 평탄. 테이블 생성 시 함께 만들어진다.
            hnsw_kwargs={
                "hnsw_m": 16,
                "hnsw_ef_construction": 64,
                "hnsw_ef_search": 40,
                "hnsw_dist_method": "vector_cosine_ops",
            },
        )

        # 재실행 시 중복 누적 방지 — 벡터 테이블 비우고 다시 채움.
        # (PGVectorStore 가 내부적으로 `data_<table_name>` 이름을 사용)
        import psycopg as _pg
        from psycopg import sql as _pg_sql
        _vec_table = f"data_{_validate_identifier(config.pgvector.table_name, 'pgvector.table_name')}"
        try:
            with _pg.connect(config.postgres.url) as _c:
                with _c.cursor() as _cur:
                    _cur.execute(
                        _pg_sql.SQL("TRUNCATE {}").format(_pg_sql.Identifier(_vec_table))
                    )
                _c.commit()
            logger.info("Vector 테이블 TRUNCATE: %s", _vec_table)
        except Exception as _e:
            # 아직 테이블이 없으면 PGVectorStore.add 가 만들어줌 — 에러 무시.
            logger.info("Vector 테이블 TRUNCATE skip (%s)", _e)

        batch_size = config.embedding.batch_size
        inserted = 0
        batch_indices = list(range(0, len(contexts), batch_size))
        for i in tqdm(batch_indices, desc="Vector RAG (embed + insert)", unit="batch"):
            batch = contexts[i : i + batch_size]
            texts = [c[0] for c in batch]
            metas = [c[1] for c in batch]
            vectors = embedder.embed_batch(texts)
            nodes = [
                TextNode(text=texts[j], metadata=metas[j], embedding=vectors[j])
                for j in range(len(batch))
            ]
            vector_store.add(nodes)
            inserted += len(nodes)
        logger.info("Vector RAG done: %d chunks in %s.", inserted, config.pgvector.table_name)
    else:
        logger.info(
            "벡터 적재 생략 (STEP3_SKIP_VECTOR_INGEST 또는 STEP3_REUSE_VECTORS_IF_NONEMPTY). "
            "그래프 단계는 MS MARCO 컨텍스트가 없으면 자동으로 건너뜁니다."
        )

    if skip_graph:
        logger.info("STEP3_SKIP_GRAPH_BUILD=1 — 그래프 적재·엔티티 추출 전체를 건너뜁니다.")
        return 0

    if not contexts or ds is None:
        logger.info(
            "그래프 구축 생략: MS MARCO 컨텍스트가 없습니다. "
            "그래프까지 다시 만들려면 STEP3_SKIP_VECTOR_INGEST / REUSE 를 끄고 step3 를 실행하세요."
        )
        return 0

    graph_adapter = PgGraphAdapter(connection_url=config.postgres.url)
    graph_adapter.ensure_schema()
    # 재실행 시 중복 누적 방지 — 엔티티·관계 모두 비움.
    graph_adapter.truncate_graph()
    logger.info("Graph 테이블 TRUNCATE 완료")
    benchmark = graph_adapter.upsert_entity(
        "MS_MARCO_benchmark", type_="benchmark",
        description="MS MARCO RAG evaluation benchmark.",
    )
    src_entity = graph_adapter.upsert_entity(
        "ms_marco", type_="source", description="MS MARCO source: ms_marco",
    )
    graph_adapter.insert_relation(src_entity, benchmark, "part_of")
    logger.info("Graph RAG done: 1 source entity.")

    # --- Entity extraction from document chunks (batch DB inserts) ---
    # Pass 1: spaCy 로 모든 청크에서 엔티티 추출, 메모리에 누적 (DB 접근 없음).
    # Pass 2: 고유 엔티티 목록을 1회 배치 upsert → name+type → id 매핑 확보.
    # Pass 3: 청크별 co-occurrence 쌍을 id 로 매핑해 배치 insert.
    # 단건 insert (이전 구현) 는 청크당 수십 회 DB 왕복으로 수 시간 소요 — 배치로 분 단위.
    from infrastructure.ingestion.entity_extractor import EntityExtractor

    extractor = EntityExtractor()
    per_chunk_keys: list[list[tuple[str, str]]] = []  # chunk idx → [(name, type), ...]
    entity_tuples: list[tuple[str, str, str | None]] = []  # unique (name, type, desc)
    seen_keys: set[tuple[str, str]] = set()

    for chunk_text, _meta in tqdm(contexts, desc="Graph RAG (entity extract)", unit="chunk"):
        ents = extractor.extract(chunk_text)[:10]  # 청크당 최대 10개
        keys: list[tuple[str, str]] = []
        for ent in ents:
            key = (ent.name, ent.type)
            if key not in seen_keys:
                seen_keys.add(key)
                desc = chunk_text[:200] if ent.description is None else ent.description
                entity_tuples.append((ent.name, ent.type, desc))
            keys.append(key)
        per_chunk_keys.append(keys)

    logger.info("Graph RAG extracted %d unique entities (spaCy NER).", len(entity_tuples))

    # Pass 2: 대량 upsert (기본 배치 500행)
    name_type_to_id = graph_adapter.upsert_entities_batch(entity_tuples)
    logger.info("Graph RAG entities inserted: %d rows.", len(name_type_to_id))

    # Pass 3: 청크별 co-occurrence 관계 — 같은 청크의 엔티티들끼리 최대 4개씩 페어링
    relations: list[tuple[int, int, str]] = []
    for keys in per_chunk_keys:
        ids = [name_type_to_id[k] for k in keys if k in name_type_to_id]
        for i in range(len(ids)):
            for j in range(i + 1, min(i + 5, len(ids))):
                relations.append((ids[i], ids[j], "co_occurs"))

    rel_count = graph_adapter.insert_relations_batch(relations)
    logger.info(
        "Graph RAG entities done: %d entities, %d co-occurrence relations.",
        len(name_type_to_id), rel_count,
    )

    return 0


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    sys.exit(main())
