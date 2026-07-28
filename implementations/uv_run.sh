#!/usr/bin/env bash
# (en) Run a command in an implementation's isolated uv venv (separate from cookbook).
# (kr) implementation 전용 uv venv 에서 명령을 실행한다(cookbook 과 분리).
#
# Usage (cookbook root):
#   ./implementations/uv_run.sh <repo> python run_agent.py
#   ./implementations/uv_run.sh smolagents python scripts/check_env.py
#
set -euo pipefail

if [[ $# -lt 2 ]]; then
  echo "usage: implementations/uv_run.sh <repo> <command> [args...]" >&2
  echo "example: implementations/uv_run.sh smolagents python run_agent.py" >&2
  exit 2
fi

REPO="$1"
shift

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
IMPL="$SCRIPT_DIR/$REPO"

if [[ ! -d "$IMPL" ]]; then
  echo "unknown implementation repo: $REPO (expected $IMPL)" >&2
  exit 2
fi

if [[ ! -f "$IMPL/pyproject.toml" ]]; then
  echo "missing pyproject.toml: $IMPL/pyproject.toml" >&2
  exit 2
fi

cd "$ROOT"
export PYTHONPATH="$SCRIPT_DIR"
if [[ -z "${EXAONE_IMPL_DIR:-}" ]]; then
  export EXAONE_IMPL_DIR="$IMPL"
fi

exec uv run --project "$IMPL" --directory "$IMPL" "$@"
