#!/usr/bin/env bash
# (en) Print NanoClaw + EXAONE prerequisite checklist (no package installs).
#      Thin wrapper — logic lives in implementations/gallery.py (Windows: implementations\nanoclaw\scripts\install_prerequisites.cmd).
# (kr) NanoClaw + EXAONE 선수 조건 체크리스트 출력(패키지 자동 설치 없음).
#      얇은 래퍼 — 로직은 implementations/gallery.py 에 있다(Windows: implementations\nanoclaw\scripts\install_prerequisites.cmd).
#
# Usage (cookbook root):
#   implementations/nanoclaw/scripts/install_prerequisites.sh
set -euo pipefail

_GALLERY="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")/../.." && pwd)/gallery.py"
exec uv run --no-project --quiet python "$_GALLERY" nanoclaw-prereqs "$@"
