#!/usr/bin/env bash
# (en) Source EXAONE + HERMES_HOME exports: source implementations/hermes-agent/scripts/env.sh
# (kr) EXAONE + HERMES_HOME export — source implementations/hermes-agent/scripts/env.sh
set -euo pipefail

_ENV_SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)"
_ENV_ROOT="$(cd "${_ENV_SCRIPT_DIR}/../../.." && pwd)"
# (en) tr -d '\r': Windows python prints CRLF, which would leak '\r' into values under Git Bash.
# (kr) tr -d '\r': Windows python 은 CRLF 로 출력해 Git Bash 에서 값 끝에 '\r' 이 붙는다.
eval "$("${_ENV_ROOT}/implementations/uv_run.sh" hermes-agent python "${_ENV_SCRIPT_DIR}/hermes_glue.py" export-shell | tr -d '\r')"
mkdir -p "${HERMES_HOME}"
