# OpenAPI 호환 embedding: 서버(app) + 클라이언트(Embedder).
# 서버: uvicorn infrastructure.embedding.app:app
from .embedder import Embedder, create_embedder_from_config

__all__ = ["app", "Embedder", "create_embedder_from_config"]


def __getattr__(name: str):
    if name == "app":
        from .app import app

        return app
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
