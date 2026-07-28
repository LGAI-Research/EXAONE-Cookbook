#!/usr/bin/env bash
# (en) Non-interactive smoke: check → render → ping → doctor.
# (kr) 비대화형 스모크: check → render → ping → doctor.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
UV_RUN="$ROOT/implementations/uv_run.sh"
GLUE="scripts/hermes_glue.py"

cd "$ROOT"

echo "== check =="
"$UV_RUN" hermes-agent python "$GLUE" check

echo "== render .hermes/config.yaml =="
"$UV_RUN" hermes-agent python "$GLUE" render

echo "== EXAONE ping =="
"$UV_RUN" hermes-agent python "$GLUE" ping

echo "== validate _out/cli_smoke.json =="
"$UV_RUN" hermes-agent python eval_smoke.py

echo "== hermes doctor =="
# shellcheck disable=SC1091
source "$SCRIPT_DIR/scripts/env.sh"
"$UV_RUN" hermes-agent python "$GLUE" link-cli || true
if ! command -v rg >/dev/null 2>&1 && command -v brew >/dev/null 2>&1; then
  brew install ripgrep || true
fi
"$SCRIPT_DIR/scripts/run_hermes.sh" doctor || true

cat <<'EOF'

== smoke OK ==
  NEXT  source implementations/hermes-agent/scripts/env.sh
        implementations/hermes-agent/scripts/run_hermes.sh
        # /model custom:exaone/<EXAONE_MODEL>
  NOTE  doctor OAuth/web/discord ⚠ → EXAONE-only 데모에서는 무시
EOF
