"""
OpenAPI 호환 embedding API. CPU 전용.
기본 모델: intfloat/multilingual-e5-small (384차원). query/passage prefix 자동 처리.
모델은 첫 요청 시 로드(lazy)하여 컨테이너 기동 실패를 줄임.
"""
from __future__ import annotations

import os
import ssl
from contextlib import asynccontextmanager

# 회사 프록시 등에서 HF 다운로드 시 SSL 오류 방지: 모든 HTTP 클라이언트에 적용
_disable_ssl = os.environ.get("EMBEDDING_DISABLE_SSL_VERIFY", "").strip().lower() in ("1", "true", "yes")
if _disable_ssl:
    ssl._create_default_https_context = ssl._create_unverified_context
    try:
        from huggingface_hub import set_client_factory
        import httpx
        set_client_factory(lambda: httpx.Client(verify=False))
    except ImportError:
        try:
            import requests
            from huggingface_hub import configure_http_backend
            def _legacy_session():
                s = requests.Session()
                s.verify = False
                return s
            configure_http_backend(backend_factory=_legacy_session)
        except Exception:
            pass

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

MODEL_NAME = os.environ.get("EMBEDDING_MODEL", "intfloat/multilingual-e5-small")
model = None


def _ensure_model():
    global model
    if model is None:
        from sentence_transformers import SentenceTransformer
        model = SentenceTransformer(MODEL_NAME)
    return model


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    global model
    model = None


app = FastAPI(title="Embedding API (e5 multilingual)", lifespan=lifespan)


class EmbeddingRequest(BaseModel):
    model: str = "default"
    input: list[str] | str


class EmbeddingItem(BaseModel):
    object: str = "embedding"
    embedding: list[float]
    index: int


class EmbeddingResponse(BaseModel):
    object: str = "list"
    data: list[EmbeddingItem]
    model: str


def _prefix(texts: list[str], prefix: str) -> list[str]:
    return [f"{prefix} {t}" for t in texts]


@app.post("/v1/embeddings", response_model=EmbeddingResponse)
def embeddings(req: EmbeddingRequest):
    try:
        m = _ensure_model()
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Model not loaded: {e!s}")
    if isinstance(req.input, str):
        texts = [req.input]
    else:
        texts = list(req.input)
    if not texts:
        return EmbeddingResponse(data=[], model=MODEL_NAME)
    if len(texts) == 1:
        prefixed = _prefix(texts, "query:")
    else:
        prefixed = _prefix(texts, "passage:")
    vecs = m.encode(prefixed, normalize_embeddings=True)
    if len(vecs.shape) == 1:
        vecs = vecs.reshape(1, -1)
    data = [EmbeddingItem(embedding=vec.tolist(), index=i) for i, vec in enumerate(vecs)]
    return EmbeddingResponse(data=data, model=MODEL_NAME)


@app.get("/health")
def health():
    loaded = model is not None
    return {"status": "ok", "model": MODEL_NAME, "model_loaded": loaded}
