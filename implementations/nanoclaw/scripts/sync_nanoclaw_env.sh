#!/usr/bin/env bash
# (en) Render implementations/nanoclaw/.env EXAONE_* as OpenCode vars under _out/ only (DRY_RUN=1 prints only).
#      Thin wrapper — logic lives in implementations/gallery.py (Windows: implementations\nanoclaw\scripts\sync_nanoclaw_env.cmd).
# (kr) implementations/nanoclaw/.env EXAONE_* 를 OpenCode 변수로 _out/ 에만 렌더한다(DRY_RUN=1 이면 출력만).
#      얇은 래퍼 — 로직은 implementations/gallery.py 에 있다(Windows: implementations\nanoclaw\scripts\sync_nanoclaw_env.cmd).
#
# Usage (cookbook root):
#   implementations/nanoclaw/scripts/sync_nanoclaw_env.sh
set -euo pipefail

_GALLERY="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")/../.." && pwd)/gallery.py"
exec uv run --no-project --quiet python "$_GALLERY" nanoclaw-sync-env "$@"
