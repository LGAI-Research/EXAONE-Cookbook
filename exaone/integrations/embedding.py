"""
(en) Embedding server reachability and `Embedder` builder (`infrastructure.embedding`).

Heavy dependencies load only when `build_embedder_from_env` is called.

(kr) Embedding 서버 reachability 및 `Embedder` 빌더이다(`infrastructure.embedding`).

`build_embedder_from_env` 호출 시에만 무거운 의존성을 로드한다.
"""
from __future__ import annotations

import os
import socket
from typing import Any
from urllib.parse import urlparse

from exaone.integrations.infra_env import (
    embedding_base_url_from_env,
    embedding_batch_from_env,
    embedding_dim_from_env,
)


def _parse_host_port(url: str) -> tuple[str, int] | None:
    try:
        parsed = urlparse(url if "://" in url else f"http://{url}")
        if not parsed.hostname:
            return None
        default_port = 443 if parsed.scheme == "https" else 80
        return parsed.hostname, parsed.port or default_port
    except Exception:
        return None


def embedding_server_reachable(base_url: str, timeout_sec: int = 3) -> bool:
    hp = _parse_host_port(base_url)
    if hp is None:
        return False
    host, port = hp
    try:
        with socket.create_connection((host, port), timeout=timeout_sec):
            return True
    except OSError:
        return False


def build_embedder_from_env() -> Any:
    from infrastructure.embedding import Embedder

    return Embedder(
        base_url=embedding_base_url_from_env(),
        api_key=os.environ.get("EMBEDDING_API_KEY") or None,
        model=(os.environ.get("EMBEDDING_MODEL") or "intfloat/multilingual-e5-small").strip(),
        dimensions=embedding_dim_from_env(),
        batch_size=embedding_batch_from_env(),
    )


__all__ = [
    "build_embedder_from_env",
    "embedding_base_url_from_env",
    "embedding_batch_from_env",
    "embedding_dim_from_env",
    "embedding_server_reachable",
]
