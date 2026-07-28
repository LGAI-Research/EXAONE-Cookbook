"""
Hugging Face Hub + datasets: SSL/프록시와 동일한 httpx 클라이언트(이벤트 훅) 설정.

`download_msmarco_to_disk.py` / `build_rag_from_ms_marco.py` 가 공유합니다.
`datasets` / `huggingface_hub` import **이전**에 `sync_hf_hub_ssl_env_from_dotenv_keys()` 를 호출하는 것이 안전합니다.
"""
from __future__ import annotations

import os
import sys


def sync_hf_hub_ssl_env_from_dotenv_keys() -> None:
    """DISABLE_SSL_VERIFY 등을 HF_HUB_DISABLE_SSL_VERIFICATION 으로 맞춤."""

    def t(name: str) -> bool:
        return os.environ.get(name, "").strip().lower() in ("1", "true", "yes", "on")

    if t("HF_HUB_DISABLE_SSL_VERIFICATION") or t("DISABLE_SSL_VERIFY") or t("EMBEDDING_DISABLE_SSL_VERIFY"):
        os.environ["HF_HUB_DISABLE_SSL_VERIFICATION"] = "1"


def _env_truthy(name: str) -> bool:
    return os.environ.get(name, "").strip().lower() in ("1", "true", "yes", "on")


def _ssl_verify_fully_disabled() -> bool:
    for key in (
        "HF_HUB_DISABLE_SSL_VERIFICATION",
        "DISABLE_SSL_VERIFY",
        "EMBEDDING_DISABLE_SSL_VERIFY",
    ):
        if _env_truthy(key):
            return True
    return False


def _ca_bundle_path() -> str | None:
    for key in ("REQUESTS_CA_BUNDLE", "SSL_CERT_FILE", "CURL_CA_BUNDLE"):
        p = os.environ.get(key, "").strip()
        if p and os.path.isfile(p):
            return p
    return None


def _httpx_verify_arg() -> bool | str:
    if _ssl_verify_fully_disabled():
        return False
    ca = _ca_bundle_path()
    if ca:
        return ca
    return True


def apply_huggingface_http_client() -> None:
    """
    huggingface_hub.utils._http 와 동일한 event_hooks + verify + trust_env.
    Hub 가 빈 JSON / JSONDecodeError 를 내는 환경(회사망·잘못된 프록시)에서 step1 download 와 step3 RAG build 가 동일하게 동작하도록.
    """
    try:
        import httpx
        from huggingface_hub.utils._http import hf_request_event_hook, set_client_factory
        try:
            from huggingface_hub.utils._http import close_session
        except ImportError:  # 구버전 / 비표준 휠
            def close_session() -> None:  # type: ignore[misc]
                pass
    except Exception as e:  # noqa: BLE001
        print("huggingface_hub/httpx 설정 실패:", e, file=sys.stderr)
        return

    if _ssl_verify_fully_disabled():
        import ssl

        ssl._create_default_https_context = ssl._create_unverified_context

    verify = _httpx_verify_arg()
    timeout = httpx.Timeout(300.0, connect=60.0)

    def _factory() -> "httpx.Client":
        return httpx.Client(
            event_hooks={"request": [hf_request_event_hook]},
            follow_redirects=True,
            timeout=timeout,
            verify=verify,
            trust_env=True,
        )

    close_session()
    set_client_factory(_factory)
    if _env_truthy("HUB_DEBUG"):
        print(f"[HUB_DEBUG] httpx verify={verify!r} trust_env=True", file=sys.stderr, flush=True)


# import 시점: download 스크립트가 상단에서 이 모듈을 로드하도록 하면, datasets import 전에 env 동기화.
sync_hf_hub_ssl_env_from_dotenv_keys()
