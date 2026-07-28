#!/usr/bin/env bash
# step1: TEI 모델 캐시 + MS MARCO 데이터 다운로드 (프로젝트 루트 _temp 사용)
# 공통 셋업. infrastructure/setup 기준으로 프로젝트 루트 = ../..
set -e
SETUP_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(cd "$SETUP_DIR/../.." && pwd)"
ROOT_TEMP="$ROOT/_temp"
ROOT_ENV="$ROOT/.env"
if [ -f "$ROOT_ENV" ]; then
  set -a
  source "$ROOT_ENV"
  set +a
fi
if [ -n "${HF_TOKEN:-}" ]; then
  export HF_TOKEN
  echo "Using HF_TOKEN for downloads."
fi

mkdir -p "$ROOT_TEMP"
echo "[1/2] Downloading TEI model (intfloat/multilingual-e5-small) into $ROOT_TEMP..."
if [ "${DISABLE_SSL_VERIFY:-0}" = "1" ] || [ "${EMBEDDING_DISABLE_SSL_VERIFY:-0}" = "1" ]; then
  (cd "$ROOT" && HF_HUB_CACHE="$ROOT_TEMP" DISABLE_SSL_VERIFY=1 python3 -c "
import os, ssl, sys
if os.environ.get('DISABLE_SSL_VERIFY','').lower() in ('1','true','yes'):
    ssl._create_default_https_context = ssl._create_unverified_context
    try:
        from huggingface_hub import set_client_factory
        import httpx
        set_client_factory(lambda: httpx.Client(verify=False))
    except Exception:
        pass
from huggingface_hub import snapshot_download
cache = os.environ.get('HF_HUB_CACHE', '_temp')
token = os.environ.get('HF_TOKEN') or None
model_id = os.environ.get('TEI_MODEL_ID', 'intfloat/multilingual-e5-small')
snapshot_download(repo_id=model_id, cache_dir=cache, token=token)
print('TEI model done.', flush=True)
") || exit 1
else
  (cd "$ROOT" && HF_HUB_CACHE="$ROOT_TEMP" python3 -c "
from huggingface_hub import snapshot_download
import os
cache = os.environ.get('HF_HUB_CACHE', '_temp')
token = os.environ.get('HF_TOKEN') or None
model_id = os.environ.get('TEI_MODEL_ID', 'intfloat/multilingual-e5-small')
snapshot_download(repo_id=model_id, cache_dir=cache, token=token)
print('TEI model done.', flush=True)
") || exit 1
fi

echo "[2/2] Downloading MS MARCO dataset into $ROOT_TEMP/ms_marco..."
# download_msmarco_to_disk.py: retries on transient Hub JSON/empty responses; set HF_TOKEN in .env to reduce rate limits
if [ "${DISABLE_SSL_VERIFY:-0}" = "1" ] || [ "${EMBEDDING_DISABLE_SSL_VERIFY:-0}" = "1" ]; then
  export DISABLE_SSL_VERIFY="${DISABLE_SSL_VERIFY:-1}"
fi
(cd "$ROOT" && python3 "$SETUP_DIR/download_msmarco_to_disk.py" "_temp/ms_marco") || {
  echo "MS MARCO 단계 실패. 위 로그를 확인하세요." >&2
  echo "  - SSL: 'CERTIFICATE_VERIFY_FAILED ... self-signed certificate in certificate chain' 이면 회사망 CA 문제입니다(레이트리밋 아님)." >&2
  echo "    → infrastructure/setup/README.md '문제 해결 — SSL 인증서' 참고(.env 에 REQUESTS_CA_BUNDLE/SSL_CERT_FILE 설정 후 재실행)." >&2
  echo "  - 레이트리밋/빈 JSON: .env 에 HF_TOKEN 설정." >&2
  exit 1
}

echo "step1_downloads.sh done: $ROOT_TEMP (TEI cache) + $ROOT_TEMP/ms_marco (MS MARCO)."
