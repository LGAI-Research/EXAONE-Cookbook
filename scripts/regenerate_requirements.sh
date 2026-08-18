#!/usr/bin/env bash
# (en) Regenerate requirements.txt from uv.lock (recipes/eval/exaone — no Proof Gallery deps).
# (kr) uv.lock 에서 requirements.txt 재생성(recipes/eval/exaone — Proof Gallery 의존성 제외).
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")/.." && pwd)"
cd "$ROOT"
uv lock
uv export --no-dev --no-emit-workspace --no-hashes -o requirements.txt
echo "wrote $ROOT/requirements.txt"
