#!/usr/bin/env bash
# (en) Non-interactive browser-use + EXAONE demo orchestrator.
# (kr) 비대화형 browser-use + EXAONE 데모 오케스트레이터.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
UV_RUN="$ROOT/implementations/uv_run.sh"

cd "$ROOT"

log() { printf '[browser-use-demo] %s\n' "$*"; }

log "Phase 0 — env smoke"
"$UV_RUN" browser-use python scripts/check_env.py

log "Phase 0b — Playwright chromium"
"$UV_RUN" browser-use python -m playwright install chromium

if [[ "${RUN_LIVE_TURN:-0}" == "1" ]]; then
  log "Phase 1 — example.com task + validate (_out/run.json)"
  "$UV_RUN" browser-use python eval_smoke.py --run
else
  log "Phase 1 — skip live turn (set RUN_LIVE_TURN=1 to call EXAONE API + browser)"
  cat <<'EOF'

=== browser-use + EXAONE — live test ===
  RUN_LIVE_TURN=1 implementations/browser-use/run_cli_demo.sh
  # or: ./implementations/uv_run.sh browser-use python eval_smoke.py --run

EOF
fi
