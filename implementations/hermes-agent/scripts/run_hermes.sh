#!/usr/bin/env bash
# (en) Run Hermes with EXAONE env + SSL patch (submodule uv venv).
#      Thin wrapper — logic lives in implementations/gallery.py (Windows: implementations\hermes-agent\run_hermes.cmd).
# (kr) EXAONE env + SSL 패치로 Hermes 실행(submodule uv venv).
#      얇은 래퍼 — 로직은 implementations/gallery.py 에 있다(Windows: implementations\hermes-agent\run_hermes.cmd).
#
# Usage (cookbook root):
#   implementations/hermes-agent/scripts/run_hermes.sh [hermes args...]
set -euo pipefail

_GALLERY="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")/../.." && pwd)/gallery.py"
exec uv run --no-project --quiet python "$_GALLERY" hermes "$@"
