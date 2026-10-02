#!/usr/bin/env bash
# (en) Run Proof Gallery live smokes (all implementations or one --repo).
#      Thin wrapper — logic lives in implementations/gallery.py (Windows: implementations\run_live_smoke.cmd).
# (kr) Proof Gallery 라이브 스모크를 실행한다(전체 또는 --repo 하나).
#      얇은 래퍼 — 로직은 implementations/gallery.py 에 있다(Windows: implementations\run_live_smoke.cmd).
#
# Usage (cookbook root):
#   implementations/run_live_smoke.sh [--repo smolagents] [--live] [--crew]
set -euo pipefail

_GALLERY="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")/." && pwd)/gallery.py"
exec uv run --no-project --quiet python "$_GALLERY" live-smoke "$@"
