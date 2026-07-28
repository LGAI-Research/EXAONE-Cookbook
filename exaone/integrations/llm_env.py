"""
(en) Build ExaoneAPIClient from root `.env` (scripts and track demos).

(kr) root `.env` 기반 ExaoneAPIClient 생성 (스크립트·트랙 데모용).
"""
from __future__ import annotations

import logging
import os
import sys

from exaone.config import load_project_env
from exaone.integrations.exit_codes import EXIT_CONFIG
from exaone.llm import ExaoneAPIClient

logger = logging.getLogger(__name__)


def build_llm_from_env() -> ExaoneAPIClient:
    load_project_env()
    base_url = (os.environ.get("EXAONE_BASE_URL") or "").strip()
    api_key = (os.environ.get("EXAONE_API_KEY") or "").strip()
    if not base_url:
        logger.error(
            "EXAONE_BASE_URL을 root/.env 에 설정하세요 (OpenAI 호환 base, /v1 로 끝나는 URL)."
        )
        sys.exit(EXIT_CONFIG)
    if not api_key:
        logger.error("EXAONE_API_KEY를 root/.env 에 설정하세요.")
        sys.exit(EXIT_CONFIG)
    model = (os.environ.get("EXAONE_MODEL") or "").strip() or ExaoneAPIClient.DEFAULT_MODEL
    return ExaoneAPIClient(base_url=base_url, api_key=api_key, model=model)


__all__ = ["build_llm_from_env"]
