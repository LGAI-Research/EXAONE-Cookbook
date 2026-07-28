#!/usr/bin/env bash
# step2: Docker 컨테이너 셋업 (db, embedding). step1에서 프로젝트 루트 _temp에 TEI 모델이 있어야 함.
# 공통 셋업. infrastructure/setup 에서 docker compose 실행 (docker-compose.yml 동일 디렉터리).
set -e
SETUP_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(cd "$SETUP_DIR/../.." && pwd)"
ROOT_ENV="$ROOT/.env"
if [ -f "$ROOT_ENV" ]; then
  set -a
  source "$ROOT_ENV"
  set +a
fi

echo "Building and starting db, embedding..."
cd "$SETUP_DIR"
docker compose up -d --build db embedding

echo "Waiting for db and embedding to be ready..."
# 헬스체크 URL 도 env 기반 — .env 의 EMBEDDING_BASE_URL 이 있으면 그 값, 없으면 기본 8000.
EMB_URL="${EMBEDDING_BASE_URL:-http://localhost:8000}"
for i in $(seq 1 90); do
  if docker compose exec -T db pg_isready -U exaone -d exaone 2>/dev/null && curl -sf -o /dev/null --connect-timeout 2 "$EMB_URL/health" 2>/dev/null; then
    echo "Services ready."
    break
  fi
  if [ "$i" -eq 90 ]; then
    echo "Timeout waiting for services."
    exit 1
  fi
  sleep 2
done

echo "step2_docker.sh done: db and embedding are up."
