#!/usr/bin/env bash
# (en) Run a command in an implementation's isolated uv venv (separate from cookbook).
#      Thin wrapper — logic lives in implementations/gallery.py (Windows: implementations\uv_run.cmd).
# (kr) implementation 전용 uv venv 에서 명령을 실행한다(cookbook 과 분리).
#      얇은 래퍼 — 로직은 implementations/gallery.py 에 있다(Windows: implementations\uv_run.cmd).
#
# Usage (cookbook root):
#   ./implementations/uv_run.sh smolagents python run_agent.py
set -euo pipefail

_GALLERY="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")/." && pwd)/gallery.py"
exec uv run --no-project --quiet python "$_GALLERY" uv-run "$@"
