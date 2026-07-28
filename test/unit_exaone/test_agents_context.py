"""
exaone 에이전트의 context_management 연동 시나리오 테스트.
- 인풋 > max_token → 에러 반환, LLM 미호출
- 인풋 recommended~max → 압축 후 진행
- 아웃풋 max_new_tokens 캡 적용
- 멀티턴 중 컨텍스트 > recommended → 턴 후 압축
LLM·context_management는 mock으로 검증.
"""
from __future__ import annotations

import unittest.mock

import pytest

from exaone.agents.base_agent import BaseAgent
from exaone.llm import ExaoneMessage, ExaoneGenerateOptions, ExaoneResponse
from exaone.tools.results import tool_failure_payload
from exaone.tools.tool_registry import ToolRegistry


def _make_messages(*contents: str):
    return [ExaoneMessage(role="user", content=c) for c in contents]


class TestAgentInputOverMaxReturnsError:
    """1) 인풋이 max_token 초과 시 에러만 반환하고 LLM은 호출되지 않음."""

    def test_run_reason_tool_loop_returns_error_when_ensure_returns_error(self):
        from exaone.agents.base_agent import BaseAgent

        msgs = [ExaoneMessage(role="user", content="Hello")]
        mock_llm = unittest.mock.Mock(spec=["chat"])

        with unittest.mock.patch(
            "exaone.agents.base_agent.ensure_input_within_limit",
            return_value=(msgs, "입력 컨텍스트가 너무 깁니다 (예상 150000 토큰). 최대 128000 토큰 이하로 줄여 주세요."),
        ):
            result = BaseAgent._run_reason_tool_loop(
                mock_llm,
                msgs,
                tool_executor=lambda n, a: {},
                options=ExaoneGenerateOptions(max_new_tokens=4096),
                max_turns=2,
            )
        assert result.error is not None
        assert "너무 깁니다" in result.error
        assert result.turns_used == 0
        mock_llm.chat.assert_not_called()


class TestAgentInputBetweenRecommendedAndMaxCompresses:
    """2) 인풋이 recommended 초과 ~ max 이하일 때 압축된 메시지로 진행."""

    def test_run_reason_tool_loop_uses_compressed_messages_when_ensure_returns_compressed(self):
        from exaone.agents.base_agent import BaseAgent

        original = [ExaoneMessage(role="user", content="Very long " * 2000)]
        compressed = [ExaoneMessage(role="user", content="[요약] Short")]
        mock_llm = unittest.mock.Mock(spec=["chat"])
        mock_llm.chat.return_value = ExaoneResponse(
            content='{"answer": "OK", "confidence": "high"}',
            tool_calls=None,
        )

        with unittest.mock.patch(
            "exaone.agents.base_agent.ensure_input_within_limit",
            return_value=(compressed, None),
        ):
            result = BaseAgent._run_reason_tool_loop(
                mock_llm,
                original,
                tool_executor=lambda n, a: {},
                options=ExaoneGenerateOptions(max_new_tokens=4096),
                max_turns=1,
            )
        assert result.error is None
        mock_llm.chat.assert_called_once()
        # 실제로 LLM에 넘긴 메시지는 압축된 것
        call_args = mock_llm.chat.call_args
        passed_messages = call_args[0][0]
        assert len(passed_messages) == 2  # compressed(1) + final turn instruction
        assert getattr(passed_messages[0], "content", None) == "[요약] Short"


class TestAgentOutputMaxNewTokensCapped:
    """3) 아웃풋 요청 시 max_new_tokens가 cap_max_new_tokens로 캡되어 전달됨."""

    def test_reason_node_passes_capped_max_new_tokens_to_llm(self):
        from exaone.agents.base_agent import BaseAgent

        msgs = [ExaoneMessage(role="user", content="Hi")]
        mock_llm = unittest.mock.Mock(spec=["chat"])
        mock_llm.chat.return_value = ExaoneResponse(content='{"answer": "x", "confidence": "low"}', tool_calls=None)

        cap_calls = []

        def record_cap(input_tokens: int, requested: int, **kwargs):
            cap_calls.append((input_tokens, requested))
            return min(1024, requested)

        with unittest.mock.patch("exaone.agents.base_agent.ensure_input_within_limit", return_value=(msgs, None)):
            with unittest.mock.patch("exaone.agents.base_agent.cap_max_new_tokens", side_effect=record_cap):
                BaseAgent._run_reason_tool_loop(
                    mock_llm,
                    msgs,
                    tool_executor=lambda n, a: {},
                    options=ExaoneGenerateOptions(max_new_tokens=99999),
                    max_turns=1,
                )
        assert len(cap_calls) >= 1
        # reason_node 내부에서 cap_max_new_tokens(input_tokens, opts.max_new_tokens) 호출됨
        assert cap_calls[0][1] == 99999


class TestAgentContextReservedNewTokens:
    """ensure/compress 호출 시 opts.max_new_tokens(캡 전) 및 turn_opts.max_new_tokens 전달."""

    def test_ensure_called_with_reserved_from_options(self):
        msgs = [ExaoneMessage(role="user", content="Hi")]
        mock_llm = unittest.mock.Mock(spec=["chat"])
        mock_llm.chat.return_value = ExaoneResponse(content="ok", tool_calls=None)

        with unittest.mock.patch(
            "exaone.agents.base_agent.ensure_input_within_limit"
        ) as mock_ensure:
            mock_ensure.return_value = (msgs, None)
            with unittest.mock.patch(
                "exaone.agents.base_agent.compress_messages_for_turn",
                side_effect=lambda m, _llm, **kwargs: m,
            ):
                BaseAgent._run_reason_tool_loop(
                    mock_llm,
                    msgs,
                    tool_executor=lambda _n, _a: {},
                    options=ExaoneGenerateOptions(max_new_tokens=8192),
                    max_turns=1,
                )
        assert mock_ensure.call_args.kwargs.get("reserved_new_tokens") == 8192

    def test_compress_called_with_turn_opts_max_new_tokens(self):
        msgs = [ExaoneMessage(role="user", content="Ask")]
        mock_llm = unittest.mock.Mock(spec=["chat"])
        mock_llm.chat.return_value = ExaoneResponse(content="answer", tool_calls=None)
        compress_kwargs: list[dict] = []

        def record_compress(_msgs, _llm, **kwargs):
            compress_kwargs.append(kwargs)
            return _msgs

        with unittest.mock.patch(
            "exaone.agents.base_agent.ensure_input_within_limit",
            return_value=(msgs, None),
        ):
            with unittest.mock.patch(
                "exaone.agents.base_agent.compress_messages_for_turn",
                side_effect=record_compress,
            ):
                with unittest.mock.patch(
                    "exaone.agents.base_agent.cap_max_new_tokens",
                    side_effect=lambda _inp, req, **kw: min(2048, req),
                ):
                    BaseAgent._run_reason_tool_loop(
                        mock_llm,
                        msgs,
                        tool_executor=lambda _n, _a: {},
                        options=ExaoneGenerateOptions(max_new_tokens=8192),
                        max_turns=1,
                    )
        assert compress_kwargs
        assert compress_kwargs[0].get("reserved_new_tokens") == 2048


class TestAgentMultiTurnCompressesWhenOverRecommended:
    """4) 멀티턴 중 컨텍스트가 recommended 초과 시 compress_messages_for_turn 호출."""

    def test_compress_called_after_turn_when_new_messages_exceed_recommended(self):
        from exaone.agents.base_agent import BaseAgent

        # 한 턴에서 LLM이 긴 응답을 반환하면 new_messages 토큰이 recommended 초과 가능
        long_content = "x" * 20000  # 대략 5000 토큰
        msgs = [ExaoneMessage(role="user", content="Ask something")]
        mock_llm = unittest.mock.Mock(spec=["chat"])
        mock_llm.chat.return_value = ExaoneResponse(content=long_content, tool_calls=None)

        compress_calls = []

        def record_compress(msgs_in, llm, **kwargs):
            compress_calls.append(len(msgs_in))
            # 압축 결과: system 없이 user 1개만 반환하면 다음 턴에서 계속 진행 가능
            from exaone.llm import ExaoneMessage
            return [ExaoneMessage(role="user", content="[요약]")]

        with unittest.mock.patch("exaone.agents.base_agent.ensure_input_within_limit", return_value=(msgs, None)):
            with unittest.mock.patch(
                "exaone.agents.base_agent.compress_messages_for_turn",
                side_effect=record_compress,
            ):
                BaseAgent._run_reason_tool_loop(
                    mock_llm,
                    msgs,
                    tool_executor=lambda n, a: {},
                    options=ExaoneGenerateOptions(max_new_tokens=4096),
                    max_turns=2,
                )
        # reason_node에서 new_messages 토큰이 recommended 초과면 compress 호출
        assert len(compress_calls) >= 1
        assert compress_calls[0] >= 2  # 기존 메시지 + assistant 응답


class TestAgentConsecutiveToolErrors:
    """tool_failure_payload 반환만 consecutive_tool_errors에 반영."""

    def test_run_reason_tool_loop_stops_on_tool_failure_payload(self):
        msgs = [ExaoneMessage(role="user", content="Hi")]
        mock_llm = unittest.mock.Mock(spec=["chat"])
        tool_call = {
            "id": "call_1",
            "function": {"name": "missing_tool", "arguments": "{}"},
        }
        llm_calls = {"n": 0}

        def chat_side_effect(*_args, **_kwargs):
            llm_calls["n"] += 1
            return ExaoneResponse(content="", tool_calls=[tool_call])

        mock_llm.chat.side_effect = chat_side_effect
        registry = ToolRegistry()

        with unittest.mock.patch(
            "exaone.agents.base_agent.ensure_input_within_limit",
            return_value=(msgs, None),
        ):
            with unittest.mock.patch(
                "exaone.agents.base_agent.compress_messages_for_turn",
                side_effect=lambda m, _llm, **_kw: m,
            ):
                result = BaseAgent._run_reason_tool_loop(
                    mock_llm,
                    msgs,
                    tool_executor=registry.execute,
                    options=ExaoneGenerateOptions(max_new_tokens=100),
                    max_turns=10,
                    max_consecutive_tool_errors=3,
                )

        assert result.error is not None
        assert "consecutive tool execution" in result.error.lower()
        assert llm_calls["n"] == 3

    def test_run_reason_tool_loop_ignores_plain_error_dict(self):
        msgs = [ExaoneMessage(role="user", content="Hi")]
        mock_llm = unittest.mock.Mock(spec=["chat"])
        tool_call = {
            "id": "call_1",
            "function": {"name": "my_tool", "arguments": "{}"},
        }
        llm_calls = {"n": 0}

        def chat_side_effect(*_args, **_kwargs):
            llm_calls["n"] += 1
            if llm_calls["n"] >= 5:
                return ExaoneResponse(content='{"answer": "done"}', tool_calls=None)
            return ExaoneResponse(content="", tool_calls=[tool_call])

        mock_llm.chat.side_effect = chat_side_effect

        def plain_error_executor(_name, _args):
            return {"error": "failed"}

        with unittest.mock.patch(
            "exaone.agents.base_agent.ensure_input_within_limit",
            return_value=(msgs, None),
        ):
            with unittest.mock.patch(
                "exaone.agents.base_agent.compress_messages_for_turn",
                side_effect=lambda m, _llm, **_kw: m,
            ):
                result = BaseAgent._run_reason_tool_loop(
                    mock_llm,
                    msgs,
                    tool_executor=plain_error_executor,
                    options=ExaoneGenerateOptions(max_new_tokens=100),
                    max_turns=10,
                    max_consecutive_tool_errors=3,
                )

        assert result.error is None
        assert llm_calls["n"] == 5

    def test_invalid_tool_arguments_json_skips_executor(self):
        msgs = [ExaoneMessage(role="user", content="Hi")]
        mock_llm = unittest.mock.Mock(spec=["chat"])
        tool_call = {
            "id": "call_1",
            "function": {"name": "my_tool", "arguments": "not-json"},
        }
        mock_llm.chat.side_effect = [
            ExaoneResponse(content="", tool_calls=[tool_call]),
            ExaoneResponse(content='{"answer": "done"}', tool_calls=None),
        ]
        executor_calls: list[tuple[str, dict]] = []

        def tracking_executor(name, args):
            executor_calls.append((name, args))
            return {"ok": True}

        with unittest.mock.patch(
            "exaone.agents.base_agent.ensure_input_within_limit",
            return_value=(msgs, None),
        ), unittest.mock.patch(
            "exaone.agents.base_agent.compress_messages_for_turn",
            side_effect=lambda m, _llm, **_kw: m,
        ):
            events = list(
                BaseAgent._iter_reason_tool_loop(
                    mock_llm,
                    msgs,
                    tool_executor=tracking_executor,
                    options=ExaoneGenerateOptions(max_new_tokens=100),
                    max_turns=5,
                )
            )

        assert executor_calls == []
        tool_ends = [e for e in events if e.type == "tool_end"]
        assert len(tool_ends) == 1
        assert "Invalid tool arguments JSON" in tool_ends[0].payload["result_preview"]

    def test_non_object_tool_arguments_skips_executor(self):
        msgs = [ExaoneMessage(role="user", content="Hi")]
        mock_llm = unittest.mock.Mock(spec=["chat"])
        tool_call = {
            "id": "call_1",
            "function": {"name": "my_tool", "arguments": "[1, 2, 3]"},
        }
        mock_llm.chat.side_effect = [
            ExaoneResponse(content="", tool_calls=[tool_call]),
            ExaoneResponse(content='{"answer": "done"}', tool_calls=None),
        ]
        executor_calls: list[tuple[str, dict]] = []

        def tracking_executor(name, args):
            executor_calls.append((name, args))
            return {"ok": True}

        with unittest.mock.patch(
            "exaone.agents.base_agent.ensure_input_within_limit",
            return_value=(msgs, None),
        ), unittest.mock.patch(
            "exaone.agents.base_agent.compress_messages_for_turn",
            side_effect=lambda m, _llm, **_kw: m,
        ):
            events = list(
                BaseAgent._iter_reason_tool_loop(
                    mock_llm,
                    msgs,
                    tool_executor=tracking_executor,
                    options=ExaoneGenerateOptions(max_new_tokens=100),
                    max_turns=5,
                )
            )

        assert executor_calls == []
        tool_ends = [e for e in events if e.type == "tool_end"]
        assert len(tool_ends) == 1
        assert "must be a JSON object" in tool_ends[0].payload["result_preview"]

    def test_invalid_tool_arguments_count_toward_consecutive_errors(self):
        msgs = [ExaoneMessage(role="user", content="Hi")]
        mock_llm = unittest.mock.Mock(spec=["chat"])
        tool_call = {
            "id": "call_1",
            "function": {"name": "my_tool", "arguments": "not-json"},
        }
        llm_calls = {"n": 0}

        def chat_side_effect(*_args, **_kwargs):
            llm_calls["n"] += 1
            return ExaoneResponse(content="", tool_calls=[tool_call])

        mock_llm.chat.side_effect = chat_side_effect

        with unittest.mock.patch(
            "exaone.agents.base_agent.ensure_input_within_limit",
            return_value=(msgs, None),
        ), unittest.mock.patch(
            "exaone.agents.base_agent.compress_messages_for_turn",
            side_effect=lambda m, _llm, **_kw: m,
        ):
            result = BaseAgent._run_reason_tool_loop(
                mock_llm,
                msgs,
                tool_executor=lambda _n, _a: {"ok": True},
                options=ExaoneGenerateOptions(max_new_tokens=100),
                max_turns=10,
                max_consecutive_tool_errors=3,
            )

        assert result.error is not None
        assert "consecutive tool execution" in result.error.lower()
        assert llm_calls["n"] == 3

    def test_run_reason_tool_loop_resets_consecutive_errors_on_success(self):
        msgs = [ExaoneMessage(role="user", content="Hi")]
        mock_llm = unittest.mock.Mock(spec=["chat"])
        tool_call = {
            "id": "call_1",
            "function": {"name": "my_tool", "arguments": "{}"},
        }
        llm_calls = {"n": 0}

        def chat_side_effect(*_args, **_kwargs):
            llm_calls["n"] += 1
            if llm_calls["n"] >= 5:
                return ExaoneResponse(content='{"answer": "done"}', tool_calls=None)
            return ExaoneResponse(content="", tool_calls=[tool_call])

        mock_llm.chat.side_effect = chat_side_effect

        def alternating_executor(_name, _args):
            if llm_calls["n"] == 2:
                return {"ok": True}
            return tool_failure_payload("failed")

        with unittest.mock.patch(
            "exaone.agents.base_agent.ensure_input_within_limit",
            return_value=(msgs, None),
        ):
            with unittest.mock.patch(
                "exaone.agents.base_agent.compress_messages_for_turn",
                side_effect=lambda m, _llm, **_kw: m,
            ):
                result = BaseAgent._run_reason_tool_loop(
                    mock_llm,
                    msgs,
                    tool_executor=alternating_executor,
                    options=ExaoneGenerateOptions(max_new_tokens=100),
                    max_turns=10,
                    max_consecutive_tool_errors=3,
                )

        assert result.error is None
        assert llm_calls["n"] == 5


class TestAgentMaxTurnsExhausted:
    """max_turns 소진을 (1) 의도된 hand-off / (2) 진짜 STALL로 정확히 분류한다.
    자연 종료·조기 종료 시 기존 error 보존은 유지한다."""

    def test_run_reason_tool_loop_flags_handoff_when_max_turns_exhausted_with_tool_calls(self):
        """모든 turn이 tool_call로 끝나는 흐름은 caller가 다음 reasoning step을
        스스로 운전한다는 의미의 hand-off로 분류한다 (옵션 E). 이전에는 ERROR로
        오인되어 ToolAgent.enrich 단계가 첫 도구 호출 직후 abort됐다."""
        msgs = [ExaoneMessage(role="user", content="Hi")]
        mock_llm = unittest.mock.Mock(spec=["chat"])
        tool_call = {
            "id": "call_1",
            "function": {"name": "my_tool", "arguments": "{}"},
        }
        mock_llm.chat.return_value = ExaoneResponse(content="", tool_calls=[tool_call])

        with unittest.mock.patch(
            "exaone.agents.base_agent.ensure_input_within_limit",
            return_value=(msgs, None),
        ):
            with unittest.mock.patch(
                "exaone.agents.base_agent.compress_messages_for_turn",
                side_effect=lambda m, _llm, **_kw: m,
            ):
                result = BaseAgent._run_reason_tool_loop(
                    mock_llm,
                    msgs,
                    tool_executor=lambda _n, _a: {"ok": True},
                    options=ExaoneGenerateOptions(max_new_tokens=100),
                    max_turns=3,
                )

        assert result.error is None
        assert result.terminated_after_tool_round is True
        assert mock_llm.chat.call_count == 3
        # 마지막 메시지는 tool 실행 결과; 직전 assistant는 tool_calls를 가진다.
        assert getattr(result.messages[-1], "role", None) == "tool"
        last_assistant = next(
            (m for m in reversed(result.messages) if getattr(m, "role", None) == "assistant"),
            None,
        )
        assert last_assistant is not None and getattr(last_assistant, "tool_calls", None)

    def test_run_reason_tool_loop_max_turns_one_with_tool_call_is_intended_handoff(self):
        """max_turns=1로 호출한 caller(ToolAgent.enrich step)는 'LLM 1회 + tool 1회 실행'을
        명시적으로 의도한다. 결과적으로 error는 None, terminated_after_tool_round는 True여야
        한다 (BFCL simple 시나리오 회귀)."""
        msgs = [ExaoneMessage(role="user", content="Solve 5!")]
        mock_llm = unittest.mock.Mock(spec=["chat"])
        tool_call = {
            "id": "call_1",
            "function": {"name": "math_factorial", "arguments": '{"number": 5}'},
        }
        mock_llm.chat.return_value = ExaoneResponse(content="", tool_calls=[tool_call])

        executed: list[tuple[str, dict]] = []

        def executor(name, args):
            executed.append((name, args))
            return {"result": 120}

        with unittest.mock.patch(
            "exaone.agents.base_agent.ensure_input_within_limit",
            return_value=(msgs, None),
        ):
            with unittest.mock.patch(
                "exaone.agents.base_agent.compress_messages_for_turn",
                side_effect=lambda m, _llm, **_kw: m,
            ):
                result = BaseAgent._run_reason_tool_loop(
                    mock_llm,
                    msgs,
                    tool_executor=executor,
                    options=ExaoneGenerateOptions(max_new_tokens=100),
                    max_turns=1,
                )

        assert result.error is None
        assert result.terminated_after_tool_round is True
        assert mock_llm.chat.call_count == 1
        assert executed == [("math_factorial", {"number": 5})]
        # tool round가 메시지에 정상적으로 반영되었음을 확인.
        assert getattr(result.messages[-1], "role", None) == "tool"

    def test_run_reason_tool_loop_no_error_when_final_response_has_no_tool_calls(self):
        msgs = [ExaoneMessage(role="user", content="Hi")]
        mock_llm = unittest.mock.Mock(spec=["chat"])
        tool_call = {
            "id": "call_1",
            "function": {"name": "my_tool", "arguments": "{}"},
        }
        llm_calls = {"n": 0}

        def chat_side_effect(*_args, **_kwargs):
            llm_calls["n"] += 1
            if llm_calls["n"] >= 2:
                return ExaoneResponse(content='{"answer": "done"}', tool_calls=None)
            return ExaoneResponse(content="", tool_calls=[tool_call])

        mock_llm.chat.side_effect = chat_side_effect

        with unittest.mock.patch(
            "exaone.agents.base_agent.ensure_input_within_limit",
            return_value=(msgs, None),
        ):
            with unittest.mock.patch(
                "exaone.agents.base_agent.compress_messages_for_turn",
                side_effect=lambda m, _llm, **_kw: m,
            ):
                result = BaseAgent._run_reason_tool_loop(
                    mock_llm,
                    msgs,
                    tool_executor=lambda _n, _a: {"ok": True},
                    options=ExaoneGenerateOptions(max_new_tokens=100),
                    max_turns=3,
                )

        assert result.error is None
        assert result.terminated_after_tool_round is False
        assert llm_calls["n"] == 2

    def test_run_reason_tool_loop_does_not_overwrite_existing_error_on_early_break(self):
        msgs = [ExaoneMessage(role="user", content="Hi")]
        mock_llm = unittest.mock.Mock(spec=["chat"])
        input_err = "입력 컨텍스트가 너무 깁니다."

        with unittest.mock.patch(
            "exaone.agents.base_agent.ensure_input_within_limit",
            return_value=(msgs, input_err),
        ):
            result = BaseAgent._run_reason_tool_loop(
                mock_llm,
                msgs,
                tool_executor=lambda _n, _a: {},
                options=ExaoneGenerateOptions(max_new_tokens=100),
                max_turns=5,
            )

        assert result.error == input_err
        mock_llm.chat.assert_not_called()
