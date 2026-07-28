#!/usr/bin/env bash
#
# (en) Print NanoClaw + EXAONE prerequisite checklist (no package installs).
# (kr) NanoClaw + EXAONE 선수 조건 체크리스트 출력(패키지 자동 설치 없음).
#
# Usage (cookbook root):
#   implementations/nanoclaw/scripts/install_prerequisites.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
COOKBOOK_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
UV_RUN="$COOKBOOK_ROOT/implementations/uv_run.sh"

log() { printf '[nanoclaw-prereq] %s\n' "$*"; }

main() {
  cd "$COOKBOOK_ROOT"
  log "Phase 0 JSON probe (Docker / Node / pnpm / submodule):"
  "$UV_RUN" nanoclaw python scripts/check_env.py || true
  cat <<'EOF'

=== Manual prerequisites (not installed by this script) ===

1. Docker Desktop or Docker Engine
2. Node.js 20+
3. pnpm 10+  (upstream nanoclaw.sh can bootstrap)
4. git clone https://github.com/nanocoai/nanoclaw.git submodules/nanoclaw
5. cp implementations/nanoclaw/.env.example implementations/nanoclaw/.env
6. uv sync --project implementations/nanoclaw

Cookbook E2E (EXAONE 1-turn, no Docker):
  ./implementations/uv_run.sh nanoclaw python run_exaone_turn.py

Full container E2E (your NanoClaw fork):
  implementations/nanoclaw/vendor/opencode-from-providers/APPLY-TO-YOUR-NANOCLAW-FORK.md

EOF
}

main "$@"
