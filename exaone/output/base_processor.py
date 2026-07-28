"""
(en) Common base for Structured Output processing.
All post-process stages follow this interface.

(kr) Structured Output 처리의 공통 베이스이다.
모든 post-process 단계는 이 인터페이스를 따른다.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any


@dataclass
class ProcessorResult:
    """
    (en) Result of a single processing stage.

    (kr) 단일 처리 단계 결과이다.
    """
    success: bool
    # (en) Parsed/validated object (dict, list, etc.)
    # (kr) 파싱·검증된 객체(dict, list 등)
    data: Any
    raw: str | None = None
    error: str | None = None


class BaseOutputProcessor(ABC):
    """
    (en) Common interface for output post-processing stages.

    (kr) 출력 후처리 단계 공통 인터페이스이다.
    """

    @abstractmethod
    def process(self, raw_text: str) -> ProcessorResult:
        """
        (en) Accept raw_text and return a processing result.

        (kr) 원문(raw_text)을 받아 처리 결과를 반환한다.
        """
        ...

    def __call__(self, raw_text: str) -> ProcessorResult:
        return self.process(raw_text)
