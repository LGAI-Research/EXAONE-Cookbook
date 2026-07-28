"""
(en) Orchestrator with clearly separated structured output processing stages.

Order:
1) Extract  : parse first valid JSON object/array from raw text
2) Validate : schema/required key validation on parsed data
3) Repair   : string recovery and re-extract/re-validate only on parse failure
4) Re-validate

(kr) Structured output 처리 단계를 명확히 분리한 오케스트레이터이다.

순서:
1) Extract  : 원문에서 첫 유효 JSON object/array 파싱
2) Validate : 파싱된 데이터의 스키마/required key 검증
3) Repair   : 파싱 실패 시에만 문자열 복구 후 재추출·재검증
4) Re-validate
"""
from __future__ import annotations

from dataclasses import dataclass

from exaone.output.base_processor import ProcessorResult
from exaone.output.json_extractor import JsonExtractor
from exaone.output.auto_repair import AutoRepair
from exaone.output.schema_validator import SchemaValidator


@dataclass
class OutputPipelineStages:
    """
    (en) Configuration object that explicitly bundles per-stage components.

    (kr) 단계별 구성요소를 명시적으로 묶은 설정 객체이다.
    """

    extractor: JsonExtractor
    validator: SchemaValidator
    repairer: AutoRepair


class StructuredOutputOrchestrator:
    """
    (en) Orchestrator that runs extract, validate, and repair stages sequentially.

    (kr) extract/validate/repair 단계를 순차 실행하는 오케스트레이터이다.
    """

    def __init__(self, stages: OutputPipelineStages, max_repair_attempts: int = 1):
        self.stages = stages
        self.max_repair_attempts = max(0, max_repair_attempts)

    def process(self, raw_text: str) -> ProcessorResult:
        if not raw_text or not raw_text.strip():
            return ProcessorResult(success=False, data=None, raw=raw_text, error="empty")

        # (en) 1) extract
        # (kr) 1) 추출
        parsed = self.stages.extractor.process(raw_text)
        if parsed.success:
            # (en) 2) validate
            # (kr) 2) 검증
            validated = self.stages.validator.validate_data(parsed.data)
            if validated.success:
                return ProcessorResult(success=True, data=validated.data, raw=raw_text)
            # (en) Parsed OK but schema/required keys failed — string repair cannot fix
            # (kr) 파싱은 됐으나 스키마·required key 실패. 문자열 repair로는 해결할 수 없다
            return ProcessorResult(
                success=False,
                data=validated.data,
                raw=raw_text,
                error=validated.error,
            )

        last = parsed

        # (en) 3) repair + 4) re-validate (parse failures only)
        # (kr) 3) repair + 4) 재검증(파싱 실패만)
        repair_attempts = self._effective_repair_attempts()
        current_raw = raw_text
        for _ in range(repair_attempts):
            repaired = self.stages.repairer.process(current_raw)
            if not repaired.success:
                last = repaired
                continue
            validated = self.stages.validator.validate_data(repaired.data)
            if validated.success:
                return ProcessorResult(
                    success=True,
                    data=validated.data,
                    raw=repaired.raw or raw_text,
                )
            last = ProcessorResult(
                success=False,
                data=validated.data,
                raw=raw_text,
                error=validated.error,
            )
            if getattr(self.stages.repairer, "supports_retry", False) and repaired.raw:
                current_raw = repaired.raw
            else:
                break

        return last

    def _effective_repair_attempts(self) -> int:
        """
        (en) Deterministic repairers such as AutoRepair are meaningful for at most one attempt.

        (kr) AutoRepair 등 결정적 repairer는 1회만 의미 있다.
        """
        if self.max_repair_attempts <= 1:
            return self.max_repair_attempts
        if getattr(self.stages.repairer, "supports_retry", False):
            return self.max_repair_attempts
        return 1
