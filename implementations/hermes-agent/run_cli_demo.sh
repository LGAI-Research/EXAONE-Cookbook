#!/usr/bin/env bash
# (en) Non-interactive smoke: check -> render -> ping -> doctor.
#      Thin wrapper — logic lives in implementations/gallery.py (Windows: implementations\hermes-agent\run_cli_demo.cmd).
# (kr) 비대화형 스모크: check → render → ping → doctor.
#      얇은 래퍼 — 로직은 implementations/gallery.py 에 있다(Windows: implementations\hermes-agent\run_cli_demo.cmd).
#
# Usage (cookbook root):
#   implementations/hermes-agent/run_cli_demo.sh [--live]
set -euo pipefail

_GALLERY="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")/.." && pwd)/gallery.py"
exec uv run --no-project --quiet python "$_GALLERY" demo hermes-agent "$@"
