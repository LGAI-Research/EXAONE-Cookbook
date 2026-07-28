#!/usr/bin/env bash
#
# (en) Render implementations/nanoclaw/.env EXAONE_* as OpenCode vars under _out/
#      only. Does NOT write submodules/nanoclaw/.env.
# (kr) implementations/nanoclaw/.env EXAONE_* 를 OpenCode 변수로 _out/ 에만 렌더한다.
#      submodules/nanoclaw/.env 는 쓰지 않는다.
#
# Usage (cookbook root):
#   implementations/nanoclaw/scripts/sync_nanoclaw_env.sh
#
# Env:
#   DRY_RUN=1   print block to stdout instead of writing _out/nanoclaw.exaone.env

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
NANOCLAW_IMPL="$(cd "$SCRIPT_DIR/.." && pwd)"
COOKBOOK_ROOT="$(cd "$NANOCLAW_IMPL/../.." && pwd)"
OUT_ENV="$NANOCLAW_IMPL/_out/nanoclaw.exaone.env"
UV_RUN="$COOKBOOK_ROOT/implementations/uv_run.sh"

log() { printf '[sync-nanoclaw-env] %s\n' "$*"; }

read_impl_exaone() {
  "$UV_RUN" nanoclaw python - <<'PY'
from common.exaone_env import load_exaone_env, openai_compat_kwargs

load_exaone_env()
kw = openai_compat_kwargs()
model = kw["model"]
print(kw["base_url"])
print(model)
print(f"exaone/{model}")
PY
}

main() {
  local exaone_block base_url model opencode_model
  exaone_block="$(read_impl_exaone)"
  base_url="$(printf '%s\n' "$exaone_block" | sed -n '1p')"
  model="$(printf '%s\n' "$exaone_block" | sed -n '2p')"
  opencode_model="$(printf '%s\n' "$exaone_block" | sed -n '3p')"

  local content="# --- implementations/nanoclaw/.env → NanoClaw OpenCode (generated) ---
# (en) Merge into YOUR NanoClaw fork .env — not submodules/nanoclaw (read-only pin).
# (kr) 본인 NanoClaw fork .env 에 병합 — submodules/nanoclaw(read-only pin) 에 쓰지 말 것.
# Generated: implementations/nanoclaw/scripts/sync_nanoclaw_env.sh
OPENCODE_PROVIDER=exaone
OPENCODE_MODEL=${opencode_model}
OPENCODE_SMALL_MODEL=${opencode_model}
ANTHROPIC_BASE_URL=${base_url}
"

  log "implementation model: ${model}"
  log "OPENCODE_MODEL: ${opencode_model}"
  log "ANTHROPIC_BASE_URL: ${base_url}"

  if [[ "${DRY_RUN:-0}" == "1" ]]; then
    printf '%s' "$content"
    return 0
  fi

  mkdir -p "$(dirname "$OUT_ENV")"
  printf '%s' "$content" > "$OUT_ENV"
  log "wrote: $OUT_ENV (gitignored _out/)"
  log "Next: implementations/nanoclaw/scripts/print_onecli_exaone.sh"
}

main "$@"
