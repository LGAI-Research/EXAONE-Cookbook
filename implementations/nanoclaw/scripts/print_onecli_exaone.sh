#!/usr/bin/env bash
# (en) Print OneCLI secret registration hints for EXAONE (does not call onecli).
#      Thin wrapper — logic lives in implementations/gallery.py (Windows: implementations\nanoclaw\scripts\print_onecli_exaone.cmd).
# (kr) implementation .env 기준 EXAONE OneCLI secret 등록 힌트를 출력한다(onecli 호출 안 함).
#      얇은 래퍼 — 로직은 implementations/gallery.py 에 있다(Windows: implementations\nanoclaw\scripts\print_onecli_exaone.cmd).
#
# Usage (cookbook root):
#   implementations/nanoclaw/scripts/print_onecli_exaone.sh
set -euo pipefail

_GALLERY="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")/../.." && pwd)/gallery.py"
exec uv run --no-project --quiet python "$_GALLERY" nanoclaw-onecli "$@"
