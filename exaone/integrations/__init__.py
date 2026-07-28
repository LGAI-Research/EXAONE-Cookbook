"""
(en) Reference CLI helpers and external integrations (exit codes, env-based LLM factory, optional Postgres/embedding).

Heavy submodules (`postgres`, `embedding`) are not re-exported from this package ``__init__``.
Import directly from `exaone.integrations.postgres`, etc. when needed.

(kr) 참조 구현·CLI용 헬퍼 및 외부 연동 모듈이다(exit code, env 기반 LLM 팩토리, 선택적 Postgres/embedding).

무거운 서브모듈(`postgres`, `embedding`)은 이 패키지 `__init__`에서 re-export하지 않는다.
필요 시 `exaone.integrations.postgres` 등으로 직접 import 한다.
"""
from exaone.integrations.llm_env import build_llm_from_env

__all__ = ["build_llm_from_env"]
