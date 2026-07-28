"""
(en) Environment bootstrap for eval runs: repo paths and a tiny `.env` loader.
No dependency on python-dotenv so CI and notebooks can run with zero extra installs.

(kr) eval 실행용 환경 bootstrap. repo 경로와 경량 `.env` 로더.
python-dotenv 없이 CI·노트북에서 동작한다.
"""
from __future__ import annotations

import os
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ENV_FILE = REPO_ROOT / ".env"
DEFAULT_REPORTS_DIR = REPO_ROOT / "eval" / "reports"


def load_dotenv(path: Path | None = None) -> int:
    """
    (en) Populate `os.environ` from a `.env` file. Existing keys are never
    overwritten. Returns the number of keys added.

    (kr) `.env`에서 `os.environ`을 채운다. 이미 있는 키는 덮어쓰지 않는다.
    추가된 키 개수를 반환한다.
    """
    env_path = path or DEFAULT_ENV_FILE
    if not env_path.is_file():
        return 0
    count = 0
    for raw in env_path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip().strip("'\"").strip()
        if " #" in value:
            value = value.split(" #", 1)[0].strip()
        if not key or key in os.environ:
            continue
        os.environ[key] = value
        count += 1
    return count


def slug_endpoint(url: str) -> str:
    """(en) Short endpoint label for reports. (kr) 리포트용 endpoint 슬러그."""
    return (url or "").replace("https://", "").replace("http://", "").rstrip("/")


def configure_hf_hub_ssl() -> None:
    """
    (en) After ``load_dotenv``, align Hugging Face Hub / ``datasets`` with corporate TLS
    settings (``DISABLE_SSL_VERIFY``, ``HF_HUB_DISABLE_SSL_VERIFICATION``, CA bundle).
    No-op if ``infrastructure/setup/hf_hub_httpx.py`` is unavailable.

    (kr) ``load_dotenv`` 이후 HF Hub / ``datasets``에 사내망 TLS 설정을 맞춘다
    (``DISABLE_SSL_VERIFY``, ``HF_HUB_DISABLE_SSL_VERIFICATION``, CA bundle).
    ``infrastructure/setup/hf_hub_httpx.py``가 없으면 no-op.
    """
    try:
        from infrastructure.setup.hf_hub_httpx import (
            apply_huggingface_http_client,
            sync_hf_hub_ssl_env_from_dotenv_keys,
        )
    except ImportError:
        return
    sync_hf_hub_ssl_env_from_dotenv_keys()
    apply_huggingface_http_client()


__all__ = [
    "REPO_ROOT",
    "DEFAULT_ENV_FILE",
    "DEFAULT_REPORTS_DIR",
    "load_dotenv",
    "slug_endpoint",
    "configure_hf_hub_ssl",
]
