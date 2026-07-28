#!/usr/bin/env bash
# (en) Non-interactive CrewAI + EXAONE demo orchestrator.
# (kr) 비대화형 CrewAI + EXAONE 데모 오케스트레이터.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
UV_RUN="$ROOT/implementations/uv_run.sh"

cd "$ROOT"

log() { printf '[crewai-demo] %s\n' "$*"; }

log "Phase 0 — import smoke"
"$UV_RUN" crewai python scripts/check_env.py

if [[ "${RUN_LIVE_TURN:-0}" == "1" ]]; then
  if [[ "${RUN_LIVE_CREW:-0}" == "1" ]]; then
    log "Phase 1 — spike + 3-agent crew + validate"
    "$UV_RUN" crewai python eval_smoke.py --run --full
  else
    log "Phase 1 — spike LLM + validate (_out/spike_llm.json)"
    "$UV_RUN" crewai python eval_smoke.py --run
  fi
else
  log "Phase 1 — skip live turn (set RUN_LIVE_TURN=1 to call EXAONE API)"
  cat <<'EOF'

=== CrewAI + EXAONE — live test ===
  RUN_LIVE_TURN=1 implementations/crewai/run_cli_demo.sh
  RUN_LIVE_TURN=1 RUN_LIVE_CREW=1 implementations/crewai/run_cli_demo.sh   # + run_crew.py

EOF
fi
