#!/usr/bin/env bash
#
# (en) NanoClaw + EXAONE demo helper — vendor OpenCode files and render env under
#      implementations/nanoclaw/ only. Does NOT modify submodules/nanoclaw.
# (kr) NanoClaw + EXAONE 데모 헬퍼 — implementations/nanoclaw/ 에만 vendor·env 생성.
#      submodules/nanoclaw 는 수정하지 않는다.
#
# Usage (cookbook root):
#   implementations/nanoclaw/run_cli_demo.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
COOKBOOK_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
OUT_DIR="$SCRIPT_DIR/_out"
UV_RUN="$COOKBOOK_ROOT/implementations/uv_run.sh"

log() { printf '[run-cli-demo] %s\n' "$*"; }

for arg in "$@"; do
  case "$arg" in
    -h|--help)
      sed -n '2,11p' "$0"
      exit 0
      ;;
    *) log "unknown arg: $arg (only -h/--help supported)"; exit 2 ;;
  esac
done

write_steps_json() {
  mkdir -p "$OUT_DIR"
  "$UV_RUN" nanoclaw python - "$OUT_DIR/demo_steps.json" <<'PY'
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from common.exaone_env import load_exaone_env, openai_compat_kwargs

out = Path(sys.argv[1])
load_exaone_env()
kw = openai_compat_kwargs()
payload = {
    "timestamp": datetime.now(timezone.utc).isoformat(),
    "status": "artifacts_ready",
    "submodule_policy": "submodules/nanoclaw is read-only — apply vendor bundle in your fork",
    "model": kw["model"],
    "base_url": kw["base_url"],
    "integration_path": "B — add-opencode + EXAONE custom provider",
    "vendor_dir": "implementations/nanoclaw/vendor/opencode-from-providers",
    "env_file": "implementations/nanoclaw/_out/nanoclaw.exaone.env",
    "apply_doc": "implementations/nanoclaw/vendor/opencode-from-providers/APPLY-TO-YOUR-NANOCLAW-FORK.md",
    "demo_question_ko": (
        "EXAONE이 이 NanoClaw 에이전트의 LLM 백본이라는 걸 한국어로 한 문장만 말해줘."
    ),
}
out.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print("saved:", out)
PY
}

main() {
  cd "$COOKBOOK_ROOT"

  log "Phase 0 — prerequisite smoke"
  "$UV_RUN" nanoclaw python scripts/check_env.py || true

  log "Phase 1 — vendor OpenCode files (implementations/nanoclaw/vendor/ only)"
  "$SCRIPT_DIR/apply-opencode-from-providers.sh"

  log "Phase 2 — render EXAONE env (_out/nanoclaw.exaone.env)"
  "$SCRIPT_DIR/scripts/sync_nanoclaw_env.sh"

  log "OneCLI registration hints:"
  "$SCRIPT_DIR/scripts/print_onecli_exaone.sh" | head -20

  write_steps_json

  if [[ "${RUN_LIVE_TURN:-0}" == "1" ]]; then
    log "Phase 3 — EXAONE 1-turn proof (cookbook, no Docker)"
    "$UV_RUN" nanoclaw python run_exaone_turn.py
    log "Phase 3b — validate _out/nanoclaw_turn.json"
    "$UV_RUN" nanoclaw python eval_smoke.py
  else
    log "Phase 3 — skip live turn (set RUN_LIVE_TURN=1 to call EXAONE API)"
  fi

  cat <<'EOF'

=== NanoClaw + EXAONE — next steps (submodule NOT modified) ===

Cookbook keeps submodules/nanoclaw as a read-only pin. Use your own NanoClaw fork:

1. Vendor bundle:
   implementations/nanoclaw/vendor/opencode-from-providers/APPLY-TO-YOUR-NANOCLAW-FORK.md

2. Merge env into YOUR fork .env:
   cat implementations/nanoclaw/_out/nanoclaw.exaone.env

3. OneCLI: see commands printed above.

4. Build + CLI chat in YOUR fork (not the submodule):
   bash nanoclaw.sh
   groups/<folder>/container.json → "provider": "opencode"
   pnpm run chat

5. Korean demo question:
   EXAONE이 이 NanoClaw 에이전트의 LLM 백본이라는 걸 한국어로 한 문장만 말해줘.

Cookbook EXAONE 1-turn (no Docker):
   RUN_LIVE_TURN=1 implementations/nanoclaw/run_cli_demo.sh
   # or: ./implementations/uv_run.sh nanoclaw python run_exaone_turn.py

Sample turn shape: implementations/nanoclaw/samples/turn.example.json

EOF
}

main "$@"
