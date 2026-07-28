-- LEGACY / manual-only DDL. step3 는 LlamaIndex PGVectorStore 로 `data_<table>` (예: data_embeddings, 384dim) 을 만듭니다.
-- 아래 `embeddings` 테이블(1536dim)은 OpenAI 차원 예시이며, 자동 setup 경로와 다릅니다.

-- =============================================================================
-- 1. pgvector 확장 및 벡터 테이블 (RAG / semantic search)
-- =============================================================================
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS embeddings (
    id          BIGSERIAL PRIMARY KEY,
    content     TEXT NOT NULL,
    metadata    JSONB DEFAULT '{}',
    embedding   vector(1536)  -- OpenAI text-embedding-3-small 등 1536 차원
);

-- IVFFlat 인덱스 (대량 데이터 시 검색 가속). lists 는 행 수에 비례해 조정 (예: sqrt(행수))
CREATE INDEX IF NOT EXISTS embeddings_embedding_idx
ON embeddings
USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

-- HNSW (선택): 더 정확하지만 메모리/빌드 비용 큼
-- CREATE INDEX embeddings_hnsw_idx ON embeddings USING hnsw (embedding vector_cosine_ops);

-- =============================================================================
-- 2. 그래프 테이블 (GraphRAG: 엔티티·관계)
-- =============================================================================
CREATE TABLE IF NOT EXISTS graph_entities (
    id          BIGSERIAL PRIMARY KEY,
    name        TEXT NOT NULL,
    type        TEXT NOT NULL DEFAULT 'entity',
    description TEXT,
    metadata    JSONB DEFAULT '{}',
    UNIQUE(name, type)
);

CREATE TABLE IF NOT EXISTS graph_relations (
    id            BIGSERIAL PRIMARY KEY,
    head_id       BIGINT NOT NULL REFERENCES graph_entities(id),
    tail_id       BIGINT NOT NULL REFERENCES graph_entities(id),
    relation_type TEXT NOT NULL,
    payload       JSONB DEFAULT '{}'
);

CREATE INDEX IF NOT EXISTS idx_graph_entities_name ON graph_entities(name);
CREATE INDEX IF NOT EXISTS idx_graph_relations_head ON graph_relations(head_id);
CREATE INDEX IF NOT EXISTS idx_graph_relations_tail ON graph_relations(tail_id);

-- =============================================================================
-- 2-2. GraphRAG: communities & reports (step4_build_graph.sh 에서 생성)
-- =============================================================================
CREATE TABLE IF NOT EXISTS graph_communities (
    id          BIGSERIAL PRIMARY KEY,
    name        TEXT NOT NULL,
    description TEXT,
    entity_ids  JSONB NOT NULL DEFAULT '[]',
    metadata    JSONB DEFAULT '{}'
);

CREATE TABLE IF NOT EXISTS graph_reports (
    id           BIGSERIAL PRIMARY KEY,
    community_id BIGINT NOT NULL REFERENCES graph_communities(id) ON DELETE CASCADE,
    content      TEXT NOT NULL,
    report_type  TEXT NOT NULL DEFAULT 'summary'
);

CREATE INDEX IF NOT EXISTS idx_graph_reports_community ON graph_reports(community_id);

-- =============================================================================
-- 3. 대화 메모리 (선택. 에이전트 세션/대화 저장)
-- =============================================================================
CREATE TABLE IF NOT EXISTS conversation_memory (
    id         BIGSERIAL PRIMARY KEY,
    session_id TEXT NOT NULL,
    role       TEXT NOT NULL,
    content    TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_conversation_memory_session ON conversation_memory(session_id);
