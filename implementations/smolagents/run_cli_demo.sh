#!/usr/bin/env bash
# (en) Non-interactive smolagents + EXAONE demo orchestrator.
# (kr) 비대화형 smolagents + EXAONE 데모 오케스트레이터.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
UV_RUN="$ROOT/implementations/uv_run.sh"

cd "$ROOT"

log() { printf '[smolagents-demo] %s\n' "$*"; }

log "Phase 0 — prerequisite smoke"
"$UV_RUN" smolagents python scripts/check_env.py

if [[ "${RUN_LIVE_TURN:-0}" == "1" ]]; then
  log "Phase 1 — E2E agent run + validate (_out/run.json)"
  "$UV_RUN" smolagents python eval_smoke.py --run
else
  log "Phase 1 — skip live turn (set RUN_LIVE_TURN=1 to call EXAONE API)"
  cat <<'EOF'

=== smolagents + EXAONE — live test ===
  RUN_LIVE_TURN=1 implementations/smolagents/run_cli_demo.sh
  # or: ./implementations/uv_run.sh smolagents python eval_smoke.py --run

EOF
fi
