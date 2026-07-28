#!/usr/bin/env bash
# step3: MS MARCO 데이터 임베딩 후 PostgreSQL에 저장 (vector_rag + graph_rag).
# 공통 셋업. step2로 db, embedding 기동된 상태에서 실행. infrastructure/setup/build_rag_from_ms_marco.py 호출.
set -e
SETUP_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(cd "$SETUP_DIR/../.." && pwd)"
ROOT_ENV="$ROOT/.env"
if [ -f "$ROOT_ENV" ]; then
  set -a
  source "$ROOT_ENV"
  set +a
fi

if [ ! -d "$ROOT/_temp/ms_marco" ]; then
  echo "Run step1_downloads.sh first ($ROOT/_temp/ms_marco not found)."
  exit 1
fi

echo "Building RAG from MS MARCO (vector + graph)..."
if [ -n "${STEP3_MAX_CONTEXTS:-}" ] && [ "${STEP3_MAX_CONTEXTS:-0}" -gt 0 ] 2>/dev/null; then
  echo "(env) STEP3_MAX_CONTEXTS=${STEP3_MAX_CONTEXTS} — MS MARCO 서브샘플 ingest."
fi
if [ "${STEP3_SKIP_GRAPH_BUILD:-0}" != "1" ]; then
  echo "[preflight] spaCy NER model for graph RAG (xx_ent_wiki_sm, ~11MB if first run)..."
  (cd "$ROOT" && python3 -m infrastructure.ingestion.spacy_model) || exit 1
fi
if [ "${STEP3_REUSE_VECTORS_IF_NONEMPTY:-0}" = "1" ] || [ "${STEP3_SKIP_VECTOR_INGEST:-0}" = "1" ]; then
  echo "(env) STEP3_REUSE_VECTORS_IF_NONEMPTY / STEP3_SKIP_VECTOR_INGEST — 벡터 재적재 생략 모드일 수 있음."
fi
cd "$ROOT"
python3 infrastructure/setup/build_rag_from_ms_marco.py || exit 1
echo "step3_build_rag.sh done: vector_rag and graph_rag ready."
