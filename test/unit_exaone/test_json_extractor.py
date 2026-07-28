from __future__ import annotations

from exaone.output.json_extractor import JsonExtractor, normalize_to_json_substring


class TestJsonExtractor:
    def test_extracts_object_from_json_fence(self):
        extractor = JsonExtractor()
        raw = """
설명 문장
```json
{"answer":"ok","confidence":0.8}
```
추가 텍스트
"""
        result = extractor.process(raw)
        assert result.success is True
        assert result.data == {"answer": "ok", "confidence": 0.8}

    def test_extracts_first_json_from_plain_text_with_trailing_content(self):
        extractor = JsonExtractor()
        raw = 'prefix {"answer":"ok","items":[1,2]} trailing text'
        result = extractor.process(raw)
        assert result.success is True
        assert result.data == {"answer": "ok", "items": [1, 2]}

    def test_strips_thinking_block_before_parsing(self):
        extractor = JsonExtractor()
        raw = "<think>internal reasoning</think> {\"answer\":\"visible\"} 끝"
        result = extractor.process(raw)
        assert result.success is True
        assert result.data == {"answer": "visible"}

    def test_handles_apostrophe_inside_json_string_value(self):
        extractor = JsonExtractor()
        raw = '{"answer":"i\'m fine"}'
        result = extractor.process(raw)
        assert result.success is True
        assert result.data == {"answer": "i'm fine"}

    def test_prefers_first_valid_fenced_json_when_multiple_blocks_exist(self):
        extractor = JsonExtractor()
        raw = """
```text
not a json block
```
```json
{"k":"v"}
```
"""
        result = extractor.process(raw)
        assert result.success is True
        assert result.data == {"k": "v"}

    def test_returns_failure_when_no_valid_json_object_or_array(self):
        extractor = JsonExtractor()
        raw = "json처럼 보이지만 {oops:1} 만 있고 유효하지 않음"
        result = extractor.process(raw)
        assert result.success is False
        assert result.data is None
        assert result.error == "no valid json object/array found"

    def test_unclosed_outer_object_does_not_return_inner_array(self):
        # (en) Top object is missing its closing brace but the inner array is complete.
        # Extractor must NOT grab the inner array (which would validate against the wrong
        # schema node); it defers to the repair stage by reporting failure.
        # (kr) 최상위 객체의 닫는 중괄호가 없고 안쪽 배열만 완결된 경우. 추출기는 안쪽 배열을
        # 집으면 안 되며(잘못된 스키마 노드로 검증됨), 실패를 알려 repair 단계로 넘긴다.
        extractor = JsonExtractor()
        raw = '{"title": "T", "items": [{"a": 1}, {"a": 2}]'
        result = extractor.process(raw)
        assert result.success is False
        assert result.data is None


class TestNormalizeToJsonSubstring:
    def test_returns_substring_starting_at_first_json(self):
        raw = "설명... [1,2,3] trailing"
        normalized = normalize_to_json_substring(raw)
        assert normalized is not None
        assert normalized.startswith("[1,2,3]")

    def test_returns_none_when_no_json_start(self):
        assert normalize_to_json_substring("plain text only") is None
