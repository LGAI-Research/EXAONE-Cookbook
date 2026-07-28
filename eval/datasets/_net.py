"""
(en) Tiny network helper used by loaders/tests to decide whether to skip when
HuggingFace is unreachable. No third-party dependency.

(kr) 로더/테스트가 HuggingFace 접근 불가 시 skip 여부를 결정하기 위한 경량 네트워크 헬퍼이다.
서드파티 의존성이 없다.
"""
from __future__ import annotations

import os
import socket


def is_online(host: str = "huggingface.co", port: int = 443, timeout: float = 2.0) -> bool:
    """
    (en) Return True if a TCP connection to `host:port` succeeds within `timeout` seconds.
    Honours `EVAL_DATASETS_FORCE_OFFLINE=1` for deterministic offline testing.
    (kr) `host:port`에 `timeout`초 이내 TCP 연결이 성공하면 True를 반환한다.
    `EVAL_DATASETS_FORCE_OFFLINE=1`을 인식하여 결정적 오프라인 테스트가 가능하다.
    """
    if os.environ.get("EVAL_DATASETS_FORCE_OFFLINE", "").strip() in {"1", "true", "yes"}:
        return False
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


__all__ = ["is_online"]
