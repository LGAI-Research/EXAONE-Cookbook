#!/usr/bin/env bash
# step4: graph_entities + graph_relations 기반으로 communities·reports 생성.
# 공통 셋업. step3 완료 후 실행. infrastructure/setup/build_graph_communities.py 호출.
set -e
SETUP_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(cd "$SETUP_DIR/../.." && pwd)"
ROOT_ENV="$ROOT/.env"
if [ -f "$ROOT_ENV" ]; then
  set -a
  source "$ROOT_ENV"
  set +a
fi

echo "Building graph communities and reports (step4)..."
cd "$ROOT"
python3 infrastructure/setup/build_graph_communities.py || exit 1
echo "step4_build_graph.sh done: graph_communities and graph_reports ready."
