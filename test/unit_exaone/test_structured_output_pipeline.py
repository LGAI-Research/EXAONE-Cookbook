from __future__ import annotations

from exaone.output.schema_validator import SchemaValidator
from exaone.output.structured_response import StructuredOutputPipeline


class TestStructuredOutputPipeline:
    def test_extract_and_validate_success(self):
        pipeline = StructuredOutputPipeline(required_keys=["answer"])
        out = pipeline.process('prefix {"answer":"ok","confidence":0.8} suffix')
        assert out.success is True
        assert out.data["answer"] == "ok"
        assert out.error is None

    def test_validation_failure_when_required_key_missing(self):
        pipeline = StructuredOutputPipeline(required_keys=["answer"])
        out = pipeline.process('{"confidence":0.5}')
        assert out.success is False
        assert out.error is not None
        assert "missing required keys" in out.error

    def test_repair_path_handles_truncated_json(self):
        pipeline = StructuredOutputPipeline(required_keys=["answer"], max_repair_attempts=1)
        out = pipeline.process('{"answer":"ok","items":[1,2')
        assert out.success is True
        assert out.data["answer"] == "ok"
        assert out.data["items"] == [1, 2]

    def test_unclosed_outer_object_with_complete_inner_array_self_heals(self):
        # (en) Regression: model omitted the top-level closing brace but the inner array is
        # complete. The pipeline must repair to the FULL object (not validate the inner array
        # against the top-level object schema, which previously failed with a misleading error).
        # (kr) 회귀: 모델이 최상위 닫는 중괄호를 빼먹었지만 안쪽 배열은 완결됨. 파이프라인은
        # 전체 객체로 복구해야 한다(안쪽 배열을 최상위 스키마로 검증해 오해성 에러를 내던 버그).
        schema = {
            "type": "object",
            "required": ["meeting_title", "action_items"],
            "properties": {
                "meeting_title": {"type": "string"},
                "action_items": {"type": "array", "items": {"type": "object"}},
            },
            "additionalProperties": False,
        }
        raw = (
            '{"meeting_title": "AX 킥오프", "action_items": ['
            '{"assignee": "김민수"}, {"assignee": "이서연"}]'
        )  # (note) missing trailing }
        out = StructuredOutputPipeline(json_schema=schema, max_repair_attempts=1).process(raw)
        assert out.success is True
        assert out.data["meeting_title"] == "AX 킥오프"
        assert len(out.data["action_items"]) == 2

    def test_validation_failure_skips_repair_loop(self):
        pipeline = StructuredOutputPipeline(required_keys=["answer"], max_repair_attempts=3)
        out = pipeline.process('{"confidence":0.5}')
        assert out.success is False
        assert "missing required keys" in (out.error or "")

    def test_empty_input_fails_fast(self):
        pipeline = StructuredOutputPipeline(required_keys=["answer"])
        out = pipeline.process("   ")
        assert out.success is False
        assert out.data is None
        assert out.error == "empty"

    def test_validation_failure_when_json_is_not_object(self):
        pipeline = StructuredOutputPipeline(required_keys=["answer"])
        out = pipeline.process("[1, 2, 3]")
        assert out.success is False
        assert "expected JSON object" in (out.error or "")

class TestSchemaValidator:
    def test_required_keys_rejects_list(self):
        validator = SchemaValidator(required_keys=["answer"])
        result = validator.validate_data([1, 2])
        assert result.success is False
        assert result.error == "expected JSON object, got list"

    def test_required_keys_rejects_int(self):
        validator = SchemaValidator(required_keys=["answer"])
        result = validator.validate_data(42)
        assert result.success is False
        assert result.error == "expected JSON object, got int"

    def test_required_keys_rejects_str(self):
        validator = SchemaValidator(required_keys=["answer"])
        result = validator.validate_data("hello")
        assert result.success is False
        assert result.error == "expected JSON object, got str"
