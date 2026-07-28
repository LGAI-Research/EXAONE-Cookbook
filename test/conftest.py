"""
(en) pytest shared: repo root on sys.path and root `.env` via setdefault.

(kr) pytest 공통: repo 루트 sys.path 및 루트 `.env` setdefault 로드.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

# (en) Load cookbook root `.env` only (setdefault — does not override existing env).
# (kr) cookbook 루트 `.env` 만 로드한다(setdefault — 기존 env 는 덮어쓰지 않음).
_env_path = REPO_ROOT / ".env"
if _env_path.is_file():
    with open(_env_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, _, v = line.partition("=")
                v = v.strip().strip("'\"").strip()
                if " #" in v:
                    v = v.split(" #", 1)[0].strip()
                k = k.strip()
                if k:
                    os.environ.setdefault(k, v)


def _mock_embedding_response(dim: int = 384, num: int = 1):
    return {
        "data": [{"embedding": [0.1] * dim, "index": i} for i in range(num)],
    }
