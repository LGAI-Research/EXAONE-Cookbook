"""
임베딩 API 클라이언트. OpenAPI 호환 /embeddings 엔드포인트 사용. HTTP 는 requests 사용.
503(모델 로딩 중 등) 시 재시도.
"""
from __future__ import annotations

import time
from typing import Any

import requests


class Embedder:
    """OpenAPI 호환 embeddings API (예: OpenAI, Friendli, 로컬 embedding 서버 등)."""

    def __init__(
        self,
        base_url: str,
        api_key: str | None = None,
        model: str = "text-embedding-3-small",
        dimensions: int | None = 1536,
        batch_size: int = 32,
    ):
        self.base_url = base_url.rstrip("/")
        if not self.base_url.endswith("/v1"):
            self.base_url = self.base_url + "/v1" if "v1" not in self.base_url else self.base_url
        self.api_key = api_key
        self.model = model
        self.dimensions = dimensions
        self.batch_size = batch_size

    def embed_one(self, text: str) -> list[float]:
        """단일 텍스트 임베딩."""
        return self.embed_batch([text])[0]

    def embed_batch(
        self,
        texts: list[str],
        max_retries_503: int = 5,
        retry_delay_seconds: float = 15.0,
    ) -> list[list[float]]:
        """여러 텍스트 일괄 임베딩. 입력 순서 유지. 503 시 재시도(모델 로딩 대기)."""
        if not texts:
            return []
        out: list[list[float]] = []
        url = f"{self.base_url}/embeddings"
        headers: dict[str, str] = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        for i in range(0, len(texts), self.batch_size):
            batch = texts[i : i + self.batch_size]
            payload: dict[str, Any] = {
                "model": self.model,
                "input": [t[:8192] for t in batch],  # 일부 API는 입력 길이 제한
            }
            if self.dimensions is not None:
                payload["dimensions"] = self.dimensions

            for attempt in range(max_retries_503 + 1):
                try:
                    resp = requests.post(
                        url,
                        json=payload,
                        headers=headers,
                        timeout=120,
                    )
                    resp.raise_for_status()
                    body = resp.json()
                    break
                except requests.exceptions.HTTPError as e:
                    if e.response is not None and e.response.status_code == 503 and attempt < max_retries_503:
                        time.sleep(retry_delay_seconds)
                        continue
                    raise

            for item in body.get("data", []):
                emb = item.get("embedding")
                if emb is not None:
                    out.append(emb)
        return out


def create_embedder_from_config(embedding_settings: Any) -> Embedder:
    """exaone.config.EmbeddingSettings 로 Embedder 생성."""
    return Embedder(
        base_url=embedding_settings.base_url,
        api_key=embedding_settings.api_key,
        model=embedding_settings.model,
        dimensions=embedding_settings.dimensions,
        batch_size=embedding_settings.batch_size,
    )
