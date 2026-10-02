#!/usr/bin/env bash
# (en) NanoClaw + EXAONE demo helper (does NOT modify submodules/nanoclaw).
#      Thin wrapper — logic lives in implementations/gallery.py (Windows: implementations\nanoclaw\run_cli_demo.cmd).
# (kr) NanoClaw + EXAONE 데모 헬퍼(submodules/nanoclaw 는 수정하지 않음).
#      얇은 래퍼 — 로직은 implementations/gallery.py 에 있다(Windows: implementations\nanoclaw\run_cli_demo.cmd).
#
# Usage (cookbook root):
#   implementations/nanoclaw/run_cli_demo.sh [--live]
set -euo pipefail

_GALLERY="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")/.." && pwd)/gallery.py"
exec uv run --no-project --quiet python "$_GALLERY" demo nanoclaw "$@"
