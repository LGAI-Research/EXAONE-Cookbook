"""
(en) Schema-based validation (JSON Schema or simple required-key checks).
Validates using schema only, with no external DB or network dependency.

(kr) 스키마 기반 검증(JSON Schema 또는 간단한 필수 키 검사)이다.
외부 DB/네트워크 의존 없이 스키마만으로 검증한다.
"""
from __future__ import annotations

from exaone.output.base_processor import BaseOutputProcessor, ProcessorResult
from typing import Any


class SchemaValidator(BaseOutputProcessor):
    """
    (en) Validates dict/list structure. Schema is specified via required_keys or json_schema.

    (kr) dict/list 구조에 대한 검증이다. 스키마는 required_keys 또는 json_schema로 지정한다.
    """

    def __init__(
        self,
        required_keys: list[str] | None = None,
        json_schema: dict[str, Any] | None = None,
    ):
        self.required_keys = required_keys or []
        self.json_schema = json_schema

    def process(self, raw_text: str) -> ProcessorResult:
        # (en) If raw_text is a JSON string, parse then validate; raw_decode parses first value only (avoids "Extra data")
        # (kr) raw_text가 JSON 문자열이면 파싱 후 검증한다. raw_decode로 첫 값만 파싱해 "Extra data"를 방지한다
        import json
        try:
            if isinstance(raw_text, str):
                s = raw_text.strip()
                if not s:
                    data = None
                else:
                    data, _ = json.JSONDecoder().raw_decode(s)
            else:
                data = raw_text
        except (TypeError, json.JSONDecodeError):
            return ProcessorResult(
                success=False,
                data=None,
                raw=str(raw_text),
                error="invalid json for validation",
            )
        result = self.validate_data(data)
        return ProcessorResult(
            success=result.success,
            data=result.data,
            raw=raw_text,
            error=result.error,
        )

    def _validate(self, data: Any) -> str | None:
        if self.json_schema:
            return self._validate_json_schema(data)
        if self.required_keys:
            if not isinstance(data, dict):
                return f"expected JSON object, got {type(data).__name__}"
            missing = [k for k in self.required_keys if k not in data]
            if missing:
                return f"missing required keys: {missing}"
        return None

    def _validate_json_schema(self, data: Any) -> str | None:
        try:
            import jsonschema
            jsonschema.validate(instance=data, schema=self.json_schema)
            return None
        except ImportError:
            return "jsonschema not installed"
        except Exception as e:
            return str(e)

    def validate_data(self, data: Any) -> ProcessorResult:
        """
        (en) Validate already-parsed data only (for internal pipeline use).

        (kr) 이미 파싱된 데이터에 대해 검증만 수행한다(파이프라인 내부용).
        """
        if data is None:
            return ProcessorResult(success=False, data=None, error="null data")
        err = self._validate(data)
        if err:
            return ProcessorResult(success=False, data=data, error=err)
        return ProcessorResult(success=True, data=data)
