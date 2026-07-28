#!/usr/bin/env bash
# (en) Run Hermes with EXAONE env + SSL patch (submodule uv venv).
# (kr) EXAONE env + SSL 패치로 Hermes 실행(submodule uv venv).
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)"
ROOT="$(cd "${SCRIPT_DIR}/../../.." && pwd)"
IMPL="${SCRIPT_DIR}/.."
SUBMODULE="${ROOT}/submodules/hermes-agent"
_UV_RUN="${ROOT}/implementations/uv_run.sh"
_GLUE="${SCRIPT_DIR}/hermes_glue.py"

eval "$("$_UV_RUN" hermes-agent python "${_GLUE}" export-shell)"

if [[ ! -d "${SUBMODULE}" ]]; then
  echo "missing upstream: ${SUBMODULE}" >&2
  echo "run: git clone https://github.com/NousResearch/hermes-agent.git submodules/hermes-agent" >&2
  exit 1
fi
if [[ ! -x "${SUBMODULE}/.venv/bin/hermes" ]]; then
  echo "== bootstrapping submodules/hermes-agent venv (first run may take a minute) =="
  (cd "${SUBMODULE}" && uv sync --frozen 2>/dev/null) || (cd "${SUBMODULE}" && uv sync)
fi

# (en) CWD is impl glue — never submodules/ (agent file tools write relative paths).
# (kr) CWD 는 impl 접착층 — submodules/ 아님(에이전트 파일 도구가 상대경로로 씀).
cd "${IMPL}"
exec "${SUBMODULE}/.venv/bin/python" "${_GLUE}" run "$@"
