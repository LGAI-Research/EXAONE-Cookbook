"""
(en) Final Structured Output: enforced JSON format and post-process pipeline.
Orchestrates extract, validate, and repair stages with clear separation.

(kr) 최종 Structured Output: JSON 양식 강제 및 post-process 파이프라인이다.
extract/validate/repair 단계를 명확히 분리해 오케스트레이션한다.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from exaone.output.base_processor import ProcessorResult
from exaone.output.json_extractor import JsonExtractor
from exaone.output.schema_validator import SchemaValidator
from exaone.output.auto_repair import AutoRepair
from exaone.output.pipeline_stages import OutputPipelineStages, StructuredOutputOrchestrator


@dataclass
class StructuredResponse:
    """
    (en) Structured response exported to the end user or system.

    (kr) 최종 사용자/시스템에보낼 구조화 응답이다.
    """
    success: bool
    # (en) dict | list (JSON-serializable)
    # (kr) dict | list(JSON 직렬화 가능)
    data: Any
    raw_content: str | None = None
    error: str | None = None

    def to_json_string(self) -> str:
        """
        (en) Serialize to a JSON string unconditionally.

        (kr) 반드시 JSON 문자열로 직렬화한다.
        """
        if not self.success and self.data is None:
            return json.dumps({
                "success": self.success,
                "data": None,
                "error": self.error,
                "raw_content": self.raw_content,
            }, ensure_ascii=False, indent=2)
        return json.dumps({
            "success": self.success,
            "data": self.data,
            "error": self.error,
            "raw_content": self.raw_content,
        }, ensure_ascii=False, indent=2)


class StructuredOutputPipeline:
    """
    (en) Runs LLM raw text through Extract -> Validate -> (if needed) Repair -> Re-validate
    to guarantee a final JSON-formatted response.

    (kr) LLM 원문을 Extract -> Validate -> (필요 시) Repair -> Re-validate 순서로 실행해
    최종 JSON 형식 응답을 보장한다.
    """

    def __init__(
        self,
        required_keys: list[str] | None = None,
        json_schema: dict[str, Any] | None = None,
        max_repair_attempts: int = 1,
    ):
        self.stages = OutputPipelineStages(
            extractor=JsonExtractor(),
            repairer=AutoRepair(),
            validator=SchemaValidator(
            required_keys=required_keys,
            json_schema=json_schema,
            ),
        )
        self.orchestrator = StructuredOutputOrchestrator(
            stages=self.stages,
            max_repair_attempts=max_repair_attempts,
        )

    def process(self, raw_llm_output: str) -> StructuredResponse:
        """
        (en) Accept LLM raw text and return a StructuredResponse in JSON format.

        (kr) LLM 원문을 받아 반드시 JSON 양식의 StructuredResponse를 반환한다.
        """
        result: ProcessorResult = self.orchestrator.process(raw_llm_output)
        if result.success:
            return StructuredResponse(
                success=True,
                data=result.data,
                raw_content=result.raw,
            )
        return StructuredResponse(
            success=False,
            data=result.data,
            raw_content=result.raw,
            error=result.error,
        )

    def __call__(self, raw_llm_output: str) -> StructuredResponse:
        return self.process(raw_llm_output)
