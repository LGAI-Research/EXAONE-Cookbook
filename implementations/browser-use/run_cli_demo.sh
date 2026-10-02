#!/usr/bin/env bash
# (en) Non-interactive browser-use + EXAONE demo orchestrator.
#      Thin wrapper — logic lives in implementations/gallery.py (Windows: implementations\browser-use\run_cli_demo.cmd).
# (kr) 비대화형 browser-use + EXAONE 데모 오케스트레이터.
#      얇은 래퍼 — 로직은 implementations/gallery.py 에 있다(Windows: implementations\browser-use\run_cli_demo.cmd).
#
# Usage (cookbook root):
#   implementations/browser-use/run_cli_demo.sh [--live]
set -euo pipefail

_GALLERY="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")/.." && pwd)/gallery.py"
exec uv run --no-project --quiet python "$_GALLERY" demo browser-use "$@"
