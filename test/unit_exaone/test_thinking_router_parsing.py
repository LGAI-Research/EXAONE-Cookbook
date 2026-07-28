"""Tests for thinking_router JSON parsing repair and the planner's graceful logging.

EXAONE occasionally emits slightly malformed JSON for the planner's screen_catalog /
evaluate_progress steps (unescaped inner quote, truncation at max_new_tokens, trailing
comma). parse_json_object now repairs those before giving up, and the planner logs a
recovered failure as a one-line WARNING instead of a full ERROR stack trace.
"""

from __future__ import annotations

import json
import unittest
import unittest.mock

from exaone.agents.next_step_planner import NextStepPlanner
from exaone.agents.thinking_router.parsing import parse_json_object
from exaone.output.auto_repair import AutoRepair


class TestParseJsonObjectRepair(unittest.TestCase):
    def test_valid_json_unchanged(self):
        self.assertEqual(
            parse_json_object('{"answerable": false, "tool_agent_key": "tool"}'),
            {"answerable": False, "tool_agent_key": "tool"},
        )

    def test_recovers_truncated_object(self):
        # (en) Cut off mid-string (max_new_tokens) — unclosed string + braces.
        # (kr) 문자열 중간 잘림(max_new_tokens) — 미닫힌 문자열 + 괄호.
        out = parse_json_object('{"answerable": true, "tool_agent_key": "tool", "rationale": "got cut o')
        self.assertTrue(out["answerable"])
        self.assertEqual(out["tool_agent_key"], "tool")

    def test_recovers_unescaped_inner_quote_by_salvaging_leading_fields(self):
        # (en) Unescaped quote inside rationale breaks strict JSON; leading fields are salvaged.
        # (kr) rationale 내부 미이스케이프 따옴표로 엄격 JSON 깨짐; 선행 필드를 살린다.
        broken = (
            '{\n  "answerable": true,\n  "tool_agent_key": "tool",\n'
            '  "rationale": "user said "100달러" so",\n'
            '  "suggested_tools": ["convert_money"]\n}'
        )
        out = parse_json_object(broken)
        self.assertIsInstance(out, dict)
        self.assertTrue(out["answerable"])
        self.assertEqual(out["tool_agent_key"], "tool")

    def test_recovers_trailing_comma(self):
        out = parse_json_object('{"answerable": true, "tool_agent_key": "tool",}')
        self.assertEqual(out, {"answerable": True, "tool_agent_key": "tool"})

    def test_recovers_from_code_fence(self):
        out = parse_json_object('```json\n{"answerable": true, "tool_agent_key": "tool"}\n```')
        self.assertTrue(out["answerable"])

    def test_unrecoverable_garbage_still_raises(self):
        # (en) Truly non-JSON re-raises so callers can fall back deterministically.
        # (kr) 진짜 비-JSON 은 재-raise 하여 호출자가 결정적으로 fallback 하게 한다.
        with self.assertRaises(json.JSONDecodeError):
            parse_json_object("this is not json at all")


class TestAutoRepairObject(unittest.TestCase):
    def test_repair_rebuilds_object_not_inner_array(self):
        # (en) .process() may extract a valid inner array; .repair() rebuilds the object.
        # (kr) .process() 는 내부 배열을 추출할 수 있으나, .repair() 는 object 로 복구한다.
        broken = '{"answerable": true, "tool_agent_key": "tool", "rationale": "a "b" c", "suggested_tools": ["x"]}'
        repaired = AutoRepair().repair(broken)
        self.assertTrue(repaired.success)
        self.assertIsInstance(repaired.data, dict)
        self.assertTrue(repaired.data["answerable"])

    def test_repair_fails_on_garbage(self):
        self.assertFalse(AutoRepair().repair("no json here").success)


class TestScreenCatalogRepairAndLogging(unittest.TestCase):
    _CATALOG = [{"qualified_name": "tool.weather", "description": "weather"}]

    def _client(self, content: str) -> unittest.mock.Mock:
        client = unittest.mock.Mock()
        client.chat.return_value = unittest.mock.Mock(content=content)
        return client

    def test_repairable_response_flows_through_without_fallback(self):
        # (en) Trailing comma is invalid strict JSON but repaired → real verdict, no fallback.
        # (kr) trailing comma 는 엄격 JSON 위반이나 복구됨 → 실제 판정, fallback 아님.
        client = self._client(
            '{"answerable": false, "tool_agent_key": "tool", "rationale": "no fit", "suggested_tools": [],}'
        )
        planner = NextStepPlanner(client, "m")
        result = planner.screen_catalog("tell me a joke", catalog=self._CATALOG)
        self.assertFalse(result.answerable)
        self.assertNotEqual(result.rationale, "screen_catalog_failed_default_answerable")

    def test_unrecoverable_response_warns_without_traceback_and_falls_back(self):
        client = self._client("totally not json")
        planner = NextStepPlanner(client, "m")
        with self.assertLogs("exaone.agents.next_step_planner", level="WARNING") as cm:
            result = planner.screen_catalog("q", catalog=self._CATALOG)
        # (en) Recovered fallback: answerable defaults to True.
        # (kr) 복구 fallback: answerable 은 True 로 기본 처리.
        self.assertTrue(result.answerable)
        self.assertEqual(result.rationale, "screen_catalog_failed_default_answerable")
        # (en) Exactly one WARNING (not ERROR) and no attached traceback (not logger.exception).
        # (kr) 정확히 WARNING 한 건(ERROR 아님)이고 트레이스백 미첨부(logger.exception 아님).
        self.assertEqual(len(cm.records), 1)
        self.assertEqual(cm.records[0].levelname, "WARNING")
        self.assertIsNone(cm.records[0].exc_info)


if __name__ == "__main__":
    unittest.main()
