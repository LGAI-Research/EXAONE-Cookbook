"""
exaone.context_management 단위 테스트.
- 인풋 길이 검사(validate_input_tokens), 아웃풋 캡(cap_max_new_tokens)
- 토큰 추정(estimate_tokens_from_messages), 메시지 직렬화(messages_to_text)
- 진입 전 검사·압축(ensure_input_within_limit), 턴 후 압축(compress_messages_for_turn)
LLM 사용 구간은 mock으로 대체.
"""
from __future__ import annotations

import unittest.mock

import pytest

from exaone.context_management import (
    cap_max_new_tokens,
    compress_messages_for_turn,
    ensure_input_within_limit,
    estimate_tokens_from_messages,
    hard_cap_messages,
    max_input_tokens_for_context,
    message_role,
    messages_to_text,
    prepare_messages_for_llm_chat,
    split_leading_system,
    validate_input_tokens,
)
from exaone.config import get_max_new_tokens_default


def _messages_with_token_count_in_range(
    unit: str,
    *,
    min_tokens_exclusive: int,
    max_tokens_inclusive: int,
    prefix: list[dict] | None = None,
) -> list[dict]:
    """
    (en) Build message list whose ``estimate_tokens_from_messages`` falls in
    (min_tokens_exclusive, max_tokens_inclusive]. Uses exponential search +
    binary search so fixtures stay valid when the estimator switches (e.g. tiktoken).

    (kr) ``estimate_tokens_from_messages``가 (min, max] 구간에 들어가도록 메시지 리스트를
    만든다. 추정기 변경(tiktoken 등)에도 fixture가 깨지지 않도록 지수 탐색 + 이진 탐색을 쓴다.
    """
    prefix = prefix or []

    def _estimate(n: int) -> int:
        body = unit * n
        msgs = [*prefix, {"role": "user", "content": body}]
        return estimate_tokens_from_messages(msgs)

    hi = 1
    while _estimate(hi) <= min_tokens_exclusive:
        hi *= 2

    candidate: int | None = None
    left, right = 1, hi
    while left <= right:
        mid = (left + right) // 2
        est = _estimate(mid)
        if est <= min_tokens_exclusive:
            left = mid + 1
        elif est <= max_tokens_inclusive:
            candidate = mid
            left = mid + 1
        else:
            right = mid - 1

    if candidate is None:
        raise AssertionError(
            f"fixture: no n found with {min_tokens_exclusive} < tokens <= {max_tokens_inclusive}; "
            "widen the window or adjust unit/reserved/max"
        )
    return [*prefix, {"role": "user", "content": unit * candidate}]


class TestValidateInputTokens:
    """input + reserved 가 max 초과 시 에러 메시지 반환."""

    def test_under_max_returns_none(self):
        assert validate_input_tokens(100, max_tokens=128000) is None
        assert validate_input_tokens(128000, max_tokens=128000) is None

    def test_over_max_returns_error_message(self):
        err = validate_input_tokens(200000, max_tokens=128000)
        assert err is not None
        assert "너무 깁니다" in err
        assert "200000" in err
        assert "128000" in err

    def test_input_plus_reserved_over_max_returns_error(self):
        err = validate_input_tokens(
            125000, max_tokens=128000, reserved_new_tokens=4096
        )
        assert err is not None
        assert "생성 예약" in err
        assert "4096" in err

    def test_input_plus_reserved_within_max_returns_none(self):
        assert (
            validate_input_tokens(
                120000, max_tokens=128000, reserved_new_tokens=4096
            )
            is None
        )


class TestMaxInputTokensForContext:
    def test_subtracts_reserved(self):
        assert (
            max_input_tokens_for_context(
                max_context_tokens=128000, reserved_new_tokens=4096
            )
            == 123904
        )

    def test_reserved_exceeds_context_returns_minimum_slot(self):
        budget = max_input_tokens_for_context(
            max_context_tokens=1000, reserved_new_tokens=2000
        )
        assert budget == 250


class TestCapMaxNewTokens:
    """아웃풋 max_new_tokens를 input+output <= max_context 로 캡."""

    def test_requested_within_remaining_unchanged(self):
        # remaining = 100000, requested 4096 → 4096
        assert cap_max_new_tokens(28000, 4096, max_context_tokens=128000) == 4096

    def test_requested_over_remaining_capped(self):
        # remaining = 20000, requested 40960 → 20000
        assert cap_max_new_tokens(108000, 40960, max_context_tokens=128000) == 20000

    def test_no_remaining_returns_minimum(self):
        # remaining = 0 → 256
        assert cap_max_new_tokens(128000, 4096, max_context_tokens=128000) == 256
        assert cap_max_new_tokens(200000, 4096, max_context_tokens=128000) == 256


class TestMessagesToTextAndEstimate:
    """메시지 직렬화 및 토큰 추정."""

    def test_messages_to_text_dict_style(self):
        msgs = [
            {"role": "system", "content": "You are a bot."},
            {"role": "user", "content": "Hello"},
        ]
        text = messages_to_text(msgs)
        assert "system:" in text and "You are a bot" in text
        assert "user:" in text and "Hello" in text

    def test_estimate_tokens_increases_with_length(self):
        short = [{"role": "user", "content": "Hi"}]
        long = [{"role": "user", "content": "x" * 5000}]
        assert estimate_tokens_from_messages(long) > estimate_tokens_from_messages(short)


class TestEnsureInputWithinLimit:
    """진입 전: input+reserved > max → 에러, recommended 예산 초과 → 압축, 이하면 통과."""

    def test_under_recommended_returns_unchanged_and_no_error(self):
        msgs = [{"role": "user", "content": "Short query"}]
        out, err = ensure_input_within_limit(
            msgs,
            None,
            max_tokens=128000,
            recommended_tokens=8192,
        )
        assert err is None
        assert out is msgs

    def test_over_max_returns_error(self):
        # max_tokens=1000 으로 두고, 단어 반복으로 1000 토큰을 넘도록 구성.
        max_tok = 1000
        long_content = "token " * (max_tok * 3)
        msgs = [{"role": "system", "content": "Sys"}, {"role": "user", "content": long_content}]
        out, err = ensure_input_within_limit(
            msgs,
            None,
            max_tokens=max_tok,
            recommended_tokens=500,
        )
        assert err is not None
        assert "너무 깁니다" in err

    def test_between_recommended_and_max_compresses_via_llm(self):
        # recommended=1000 < estimated <= max=5000 이 되도록 단어 반복 기반 중간 길이 메시지.
        mid_content = "mid token " * 1500
        msgs = [
            {"role": "system", "content": "System"},
            {"role": "user", "content": mid_content},
        ]
        mock_llm = unittest.mock.Mock()
        with unittest.mock.patch(
            "exaone.context_management.messages._compress_with_llm",
            return_value=("[요약된 텍스트]", 100),
        ):
            out, err = ensure_input_within_limit(
                msgs,
                mock_llm,
                max_tokens=5000,
                recommended_tokens=1000,
                reserved_new_tokens=512,
            )
        assert err is None
        assert out is not msgs
        assert len(out) <= 3  # system + 요약 메시지 + (keep_last_n=1 이면 1개)
        assert estimate_tokens_from_messages(out) < estimate_tokens_from_messages(msgs)
        assert any(
            (m.get("content") if isinstance(m, dict) else getattr(m, "content", ""))
            and "요약" in str(
                m.get("content") if isinstance(m, dict) else getattr(m, "content", "")
            )
            for m in out
        )

    def test_oversized_compress_output_hard_capped_to_max_budget(self):
        """압축 LLM이 과도하게 긴 요약을 돌려도 prepare 단계에서 max 예산에 맞춘다."""
        reserved = 128
        max_ctx = 1000
        recommended = 500
        recommended_input_budget = max_input_tokens_for_context(
            max_context_tokens=recommended, reserved_new_tokens=reserved
        )
        max_input_budget = max_input_tokens_for_context(
            max_context_tokens=max_ctx, reserved_new_tokens=reserved
        )
        msgs = _messages_with_token_count_in_range(
            "mid token ",
            min_tokens_exclusive=recommended_input_budget,
            max_tokens_inclusive=max_input_budget,
            prefix=[{"role": "system", "content": "System"}],
        )
        mock_llm = unittest.mock.Mock()
        with unittest.mock.patch(
            "exaone.context_management.messages._compress_with_llm",
            return_value=("x " * 5000, 5000),
        ):
            out, err = ensure_input_within_limit(
                msgs,
                mock_llm,
                max_tokens=max_ctx,
                recommended_tokens=recommended,
                reserved_new_tokens=reserved,
            )
        assert err is None
        capped_reserved = cap_max_new_tokens(
            estimate_tokens_from_messages(out),
            reserved,
            max_context_tokens=max_ctx,
        )
        assert estimate_tokens_from_messages(out) + capped_reserved <= max_ctx

    def test_input_plus_reserved_over_recommended_triggers_compress(self):
        reserved = 2000
        recommended = 10_000
        input_budget = max_input_tokens_for_context(
            max_context_tokens=recommended, reserved_new_tokens=reserved
        )
        msgs = _messages_with_token_count_in_range(
            "word ",
            min_tokens_exclusive=input_budget,
            max_tokens_inclusive=recommended,
        )
        assert estimate_tokens_from_messages(msgs) > input_budget

        mock_llm = unittest.mock.Mock()
        with unittest.mock.patch(
            "exaone.context_management.messages._compress_with_llm",
            return_value=("[요약]", 50),
        ) as mock_compress:
            out, err = ensure_input_within_limit(
                msgs,
                mock_llm,
                max_tokens=50_000,
                recommended_tokens=recommended,
                reserved_new_tokens=reserved,
            )
        mock_compress.assert_called_once()
        assert err is None
        assert out is not msgs

    def test_input_plus_reserved_under_recommended_skips_compress(self):
        msgs = [{"role": "user", "content": "Short"}]
        mock_llm = unittest.mock.Mock()
        with unittest.mock.patch(
            "exaone.context_management.messages._compress_with_llm",
            side_effect=AssertionError("should not compress"),
        ):
            out, err = ensure_input_within_limit(
                msgs,
                mock_llm,
                max_tokens=50_000,
                recommended_tokens=10_000,
                reserved_new_tokens=2000,
            )
        assert err is None
        assert out is msgs


class TestSplitLeadingSystem:
    def test_no_leading_system(self):
        msgs = [{"role": "user", "content": "Hi"}]
        leading, body = split_leading_system(msgs)
        assert leading == []
        assert body == msgs

    def test_single_leading_system(self):
        msgs = [
            {"role": "system", "content": "S"},
            {"role": "user", "content": "U"},
        ]
        leading, body = split_leading_system(msgs)
        assert len(leading) == 1
        assert leading[0]["content"] == "S"
        assert body == [{"role": "user", "content": "U"}]

    def test_multiple_consecutive_leading_system(self):
        msgs = [
            {"role": "system", "content": "S1"},
            {"role": "system", "content": "S2"},
            {"role": "user", "content": "U"},
        ]
        leading, body = split_leading_system(msgs)
        assert len(leading) == 2
        assert [m["content"] for m in leading] == ["S1", "S2"]
        assert len(body) == 1

    def test_system_not_at_start_stays_in_body(self):
        msgs = [
            {"role": "user", "content": "U"},
            {"role": "system", "content": "Mid"},
        ]
        leading, body = split_leading_system(msgs)
        assert leading == []
        assert len(body) == 2


class TestMessageRole:
    def test_dict_and_object(self):
        from exaone.llm import ExaoneMessage

        assert message_role({"role": "System", "content": "x"}) == "system"
        assert message_role(ExaoneMessage(role="user", content="y")) == "user"


class TestCompressMessagesForTurn:
    """멀티턴 중 컨텍스트 압축: system 유지, 중간을 LLM 요약, 마지막 keep_last_n 유지."""

    def test_short_list_unchanged(self):
        msgs = [
            {"role": "system", "content": "S"},
            {"role": "user", "content": "U"},
        ]
        mock_llm = unittest.mock.Mock()
        out = compress_messages_for_turn(msgs, mock_llm, keep_last_n=2)
        assert out == msgs

    def test_single_body_over_target_still_compresses(self):
        long_content = "word " * 2000
        msgs = [
            {"role": "system", "content": "S"},
            {"role": "user", "content": long_content},
        ]
        with unittest.mock.patch(
            "exaone.context_management.messages._compress_with_llm",
            return_value=("[요약]", 10),
        ) as mock_compress:
            out = compress_messages_for_turn(
                msgs,
                unittest.mock.Mock(),
                keep_last_n=1,
                target_max_tokens=500,
            )
        mock_compress.assert_called_once()
        assert len(out) == 2
        assert estimate_tokens_from_messages(out) < estimate_tokens_from_messages(msgs)
        summary = out[1]
        content = summary.get("content") if isinstance(summary, dict) else summary.content
        assert "요약" in content

    def test_compression_structure_with_mock_llm(self):
        from exaone.llm import ExaoneMessage

        msgs = [
            ExaoneMessage(role="system", content="System prompt"),
            ExaoneMessage(role="user", content="First user"),
            ExaoneMessage(role="assistant", content="First assistant"),
            ExaoneMessage(role="user", content="Last user"),
        ]
        with unittest.mock.patch(
            "exaone.context_management.messages._compress_with_llm",
            return_value=("Summarized dialogue.", 50),
        ):
            out = compress_messages_for_turn(
                msgs,
                unittest.mock.Mock(),
                keep_last_n=1,
                target_max_tokens=1,
            )
        assert len(out) == 3  # system + 요약 1개 + last 1개
        _c = lambda m: getattr(m, "content", None) if hasattr(m, "content") else m.get("content", "")
        _r = lambda m: getattr(m, "role", None) if hasattr(m, "role") else m.get("role", "")
        assert _c(out[0]) == "System prompt"
        assert _r(out[1]) == "system"
        assert "Summarized" in _c(out[1])
        assert _c(out[-1]) == "Last user"

    def test_does_not_compress_when_input_within_budget(self):
        from exaone.llm import ExaoneMessage

        msgs = [
            ExaoneMessage(role="system", content="System prompt"),
            ExaoneMessage(role="user", content="hello"),
            ExaoneMessage(role="assistant", content="hi there"),
            ExaoneMessage(role="user", content="how are you?"),
        ]
        reserved = 4096
        target = 10_000
        budget = max_input_tokens_for_context(
            max_context_tokens=target, reserved_new_tokens=reserved
        )
        assert estimate_tokens_from_messages(msgs) <= budget
        with unittest.mock.patch(
            "exaone.context_management.messages._compress_with_llm",
            side_effect=AssertionError("_compress_with_llm should not be called"),
        ):
            out = compress_messages_for_turn(
                msgs,
                unittest.mock.Mock(),
                keep_last_n=2,
                target_max_tokens=target,
                reserved_new_tokens=reserved,
            )
        assert out == msgs

    def test_compresses_when_input_plus_reserved_over_target(self):
        reserved = 1000
        target = 5000
        budget = max_input_tokens_for_context(
            max_context_tokens=target, reserved_new_tokens=reserved
        )
        content = "word " * (budget + 200)
        msgs = [
            {"role": "system", "content": "S"},
            {"role": "user", "content": content},
        ]
        with unittest.mock.patch(
            "exaone.context_management.messages._compress_with_llm",
            return_value=("[요약]", 10),
        ) as mock_compress:
            compress_messages_for_turn(
                msgs,
                unittest.mock.Mock(),
                keep_last_n=1,
                target_max_tokens=target,
                reserved_new_tokens=reserved,
            )
        mock_compress.assert_called_once()

    def test_does_not_compress_when_under_target_tokens(self):
        from exaone.llm import ExaoneMessage

        msgs = [
            ExaoneMessage(role="system", content="System prompt"),
            ExaoneMessage(role="user", content="hello"),
            ExaoneMessage(role="assistant", content="hi there"),
            ExaoneMessage(role="user", content="how are you?"),
        ]
        with unittest.mock.patch(
            "exaone.context_management.messages._compress_with_llm",
            side_effect=AssertionError("_compress_with_llm should not be called"),
        ):
            out = compress_messages_for_turn(
                msgs,
                unittest.mock.Mock(),
                keep_last_n=2,
                target_max_tokens=10_000,
            )
        assert out == msgs

    def test_keeps_tool_run_verbatim_and_summarizes_non_tool_only(self):
        from exaone.llm import ExaoneMessage

        tool_call = {
            "id": "call_sales_1",
            "type": "function",
            "function": {"name": "get_sales", "arguments": "{}"},
        }
        msgs = [
            ExaoneMessage(role="system", content="System prompt"),
            ExaoneMessage(role="user", content="Compute total sales."),
            ExaoneMessage(
                role="assistant",
                content="",
                tool_calls=[tool_call],
            ),
            ExaoneMessage(
                role="tool",
                content='{"total": 12345, "currency": "KRW"}',
                tool_call_id="call_sales_1",
            ),
            ExaoneMessage(role="assistant", content="The total is 12345 KRW."),
            ExaoneMessage(role="user", content="Convert it to USD."),
        ]

        captured_input = {}

        def _fake_compress(input_text, *_args, **_kwargs):
            captured_input["text"] = input_text
            return "compressed non-tool history", 10

        with unittest.mock.patch(
            "exaone.context_management.messages._compress_with_llm",
            side_effect=_fake_compress,
        ):
            out = compress_messages_for_turn(
                msgs,
                unittest.mock.Mock(),
                keep_last_n=1,
                target_max_tokens=1,
            )

        assert '{"total": 12345, "currency": "KRW"}' not in captured_input["text"]
        assert "get_sales" not in captured_input["text"]
        _c = lambda m: getattr(m, "content", None) if hasattr(m, "content") else m.get("content", "")
        _r = lambda m: getattr(m, "role", None) if hasattr(m, "role") else m.get("role", "")
        assert _r(out[1]) == "system"  # 요약 메시지
        assert "compressed non-tool history" in _c(out[1])
        tool_idx = next(i for i, m in enumerate(out) if _r(m) == "tool")
        assert _r(out[tool_idx - 1]) == "assistant"
        assert getattr(out[tool_idx - 1], "tool_calls", None) == [tool_call]
        assert '{"total": 12345, "currency": "KRW"}' in _c(out[tool_idx])

    def test_without_leading_system_does_not_treat_first_message_as_system(self):
        from exaone.llm import ExaoneMessage

        msgs = [
            ExaoneMessage(role="user", content="First user"),
            ExaoneMessage(role="assistant", content="First assistant"),
            ExaoneMessage(role="user", content="Last user"),
        ]
        with unittest.mock.patch(
            "exaone.context_management.messages._compress_with_llm",
            return_value=("Summarized.", 50),
        ):
            out = compress_messages_for_turn(
                msgs,
                unittest.mock.Mock(),
                keep_last_n=1,
                target_max_tokens=1,
            )
        _r = lambda m: message_role(m)
        _c = lambda m: getattr(m, "content", None) if hasattr(m, "content") else m.get("content", "")
        assert _r(out[0]) == "system"
        assert "Summarized" in _c(out[0])
        assert _c(out[-1]) == "Last user"
        assert not any(_r(m) == "system" and _c(m) == "First user" for m in out)

    def test_preserves_multiple_leading_system_messages(self):
        from exaone.llm import ExaoneMessage

        msgs = [
            ExaoneMessage(role="system", content="Policy"),
            ExaoneMessage(role="system", content="Domain facts"),
            ExaoneMessage(role="user", content="Old user"),
            ExaoneMessage(role="assistant", content="Old assistant"),
            ExaoneMessage(role="user", content="Latest user"),
        ]
        with unittest.mock.patch(
            "exaone.context_management.messages._compress_with_llm",
            return_value=("Summarized.", 50),
        ):
            out = compress_messages_for_turn(
                msgs,
                unittest.mock.Mock(),
                keep_last_n=1,
                target_max_tokens=1,
            )
        _c = lambda m: getattr(m, "content", None) if hasattr(m, "content") else m.get("content", "")
        assert _c(out[0]) == "Policy"
        assert _c(out[1]) == "Domain facts"
        assert message_role(out[2]) == "system"
        assert "Summarized" in _c(out[2])
        assert _c(out[-1]) == "Latest user"

    def test_keeps_assistant_before_tool_even_without_tool_calls_field(self):
        from exaone.llm import ExaoneMessage

        msgs = [
            ExaoneMessage(role="system", content="System prompt"),
            ExaoneMessage(role="user", content="Compute total sales."),
            ExaoneMessage(role="assistant", content="I will call a tool."),
            ExaoneMessage(role="tool", content='{"total": 12345, "currency": "KRW"}'),
            ExaoneMessage(role="assistant", content="The total is 12345 KRW."),
            ExaoneMessage(role="user", content="Convert it to USD."),
        ]

        captured_input = {}

        def _fake_compress(input_text, *_args, **_kwargs):
            captured_input["text"] = input_text
            return "compressed non-tool history", 10

        with unittest.mock.patch(
            "exaone.context_management.messages._compress_with_llm",
            side_effect=_fake_compress,
        ):
            out = compress_messages_for_turn(
                msgs,
                unittest.mock.Mock(),
                keep_last_n=1,
                target_max_tokens=1,
            )

        assert "I will call a tool." not in captured_input["text"]
        assert '{"total": 12345, "currency": "KRW"}' not in captured_input["text"]
        _c = lambda m: getattr(m, "content", None) if hasattr(m, "content") else m.get("content", "")
        _r = lambda m: getattr(m, "role", None) if hasattr(m, "role") else m.get("role", "")
        tool_idx = next(i for i, m in enumerate(out) if _r(m) == "tool")
        assert _c(out[tool_idx - 1]) == "I will call a tool."


class TestCompressWithLlm:
    def test_returns_empty_on_chat_failure(self):
        from exaone.context_management.executor import _compress_with_llm

        mock_llm = unittest.mock.Mock()
        mock_llm.chat.side_effect = RuntimeError("API unavailable")
        text, tokens = _compress_with_llm("some context to summarize", mock_llm)
        assert text == ""
        assert tokens == 0


class TestCompressionLlmFailureFallback:
    """압축 LLM 실패 시 원본 메시지 유지(best-effort)."""

    def test_compress_messages_for_turn_hard_caps_when_compression_fails(self):
        long_content = "word " * 2000
        msgs = [
            {"role": "system", "content": "S"},
            {"role": "user", "content": long_content},
        ]
        mock_llm = unittest.mock.Mock()
        mock_llm.chat.side_effect = RuntimeError("API unavailable")
        reserved = get_max_new_tokens_default()
        out = compress_messages_for_turn(
            msgs,
            mock_llm,
            keep_last_n=1,
            target_max_tokens=500,
            reserved_new_tokens=reserved,
        )
        from exaone.context_management.constants import CONTEXT_LENGTH_MAX_TOKENS

        assert estimate_tokens_from_messages(out) + reserved <= CONTEXT_LENGTH_MAX_TOKENS

    def test_ensure_input_within_limit_hard_caps_when_compression_fails(self):
        mid_content = "mid token " * 1500
        msgs = [
            {"role": "system", "content": "System"},
            {"role": "user", "content": mid_content},
        ]
        mock_llm = unittest.mock.Mock()
        mock_llm.chat.side_effect = RuntimeError("API unavailable")
        max_ctx = 5000
        reserved = 256
        out, err = ensure_input_within_limit(
            msgs,
            mock_llm,
            max_tokens=max_ctx,
            recommended_tokens=1000,
            reserved_new_tokens=reserved,
        )
        assert err is None
        capped_reserved = cap_max_new_tokens(
            estimate_tokens_from_messages(out),
            reserved,
            max_context_tokens=max_ctx,
        )
        assert estimate_tokens_from_messages(out) + capped_reserved <= max_ctx


class TestPrepareMessagesForLlmChat:
    def test_input_plus_reserved_within_max(self):
        long_content = "word " * 8000
        msgs = [{"role": "user", "content": long_content}]
        reserved = 4096
        max_ctx = 10_000
        capped_msgs, capped_reserved = prepare_messages_for_llm_chat(
            msgs,
            reserved_new_tokens=reserved,
            max_context_tokens=max_ctx,
        )
        assert estimate_tokens_from_messages(capped_msgs) + capped_reserved <= max_ctx

    def test_caps_reserved_when_input_large(self):
        msgs = [{"role": "user", "content": "x " * 5000}]
        max_ctx = 1000
        capped_msgs, capped_reserved = prepare_messages_for_llm_chat(
            msgs,
            reserved_new_tokens=800,
            max_context_tokens=max_ctx,
        )
        # (en) Input is hard-capped to fit; output reservation honors the request within the freed window.
        # (kr) 입력은 hard cap 으로 한도에 맞추고, 출력 예약은 그 안에서 요청값을 존중한다.
        assert estimate_tokens_from_messages(capped_msgs) + capped_reserved <= max_ctx
        assert capped_reserved <= 800


class TestHardCapMessages:
    def test_drops_old_body_messages(self):
        msgs = [
            {"role": "system", "content": "Sys"},
            {"role": "user", "content": "old " * 500},
            {"role": "assistant", "content": "mid " * 500},
            {"role": "user", "content": "latest question"},
        ]
        capped = hard_cap_messages(msgs, max_input_tokens=200)
        assert estimate_tokens_from_messages(capped) <= 200
        assert capped[-1]["content"] == "latest question"
