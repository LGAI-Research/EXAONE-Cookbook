#!/usr/bin/env bash
# (en) Source EXAONE + HERMES_HOME exports: source implementations/hermes-agent/scripts/env.sh
# (kr) EXAONE + HERMES_HOME export — source implementations/hermes-agent/scripts/env.sh
set -euo pipefail

_ENV_SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)"
_ENV_ROOT="$(cd "${_ENV_SCRIPT_DIR}/../../.." && pwd)"
eval "$("${_ENV_ROOT}/implementations/uv_run.sh" hermes-agent python "${_ENV_SCRIPT_DIR}/hermes_glue.py" export-shell)"
mkdir -p "${HERMES_HOME}"
