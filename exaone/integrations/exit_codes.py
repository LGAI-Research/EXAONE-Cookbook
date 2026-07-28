"""
(en) Shared exit codes for CLI and reference scripts.

(kr) CLI·참조 스크립트용 공통 exit code이다.
"""
from __future__ import annotations

EXIT_OK = 0
EXIT_CONFIG = 1
EXIT_NO_CONTEXT = 2
EXIT_LLM = 3

__all__ = ["EXIT_OK", "EXIT_CONFIG", "EXIT_NO_CONTEXT", "EXIT_LLM"]
