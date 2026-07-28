from __future__ import annotations

import pytest

from eval.runners import harness_runner


def _has_harness() -> bool:
    try:
        from exaone.agents import ToolAgent  # noqa: F401
        from exaone.llm import ExaoneMessage, ExaoneResponse  # noqa: F401

        return True
    except Exception:
        return False


_HAS_HARNESS = _has_harness()
pytestmark = pytest.mark.skipif(not _HAS_HARNESS, reason="exaone harness not importable")


def _make_response(*, content="", tool_calls=None, usage=None, finish_reason="stop"):
    from exaone.llm import ExaoneResponse

    return ExaoneResponse(
        content=content,
        usage=usage or {"prompt_tokens": 50, "completion_tokens": 20, "total_tokens": 70},
        finish_reason=finish_reason,
        tool_calls=tool_calls,
        latency_ms=12.3,
    )


def _make_tool_call(name: str, arguments: dict, *, call_id: str = "call_1"):
    import json as _json

    return {
        "id": call_id,
        "type": "function",
        "function": {"name": name, "arguments": _json.dumps(arguments)},
    }


class TestHarnessSingleShot:
    def test_no_tools_text_response(self, ifeval_like_task, fake_exaone_client):
        llm = fake_exaone_client([_make_response(content="a haiku here")])
        trial = harness_runner.run_trial(
            ifeval_like_task,
            llm=llm,
            use_thinking_router=False,
            use_next_step_planner=False,
        )
        assert trial.runner == "harness"
        assert trial.task_id == "ifeval.001"
        assert trial.final_content
        assert trial.tool_calls == []
        assert trial.finished
        assert trial.error is None

    def test_irrelevance_no_calls_captured(self, irrelevance_task, fake_exaone_client):
        llm = fake_exaone_client([_make_response(content="No tool applies.")])
        trial = harness_runner.run_trial(
            irrelevance_task,
            llm=llm,
            use_thinking_router=False,
            use_next_step_planner=False,
        )
        assert trial.tool_calls == []
        assert trial.finished


class TestHarnessToolLoop:
    def test_tool_call_captured_by_registry(
        self,
        bfcl_like_task,
        fake_exaone_client,
    ):
        # ToolAgentCatalog registers a tool_registry under DEFAULT_TOOL_AGENT_KEY="tool"
        # and exposes the qualified name ``tool__get_weather`` to the LLM. The fake
        # LLM must emit the qualified form to match what the harness actually sees.
        qualified = "tool__get_weather"
        responses = [
            _make_response(tool_calls=[_make_tool_call(qualified, {"city": "Seoul"})]),
            _make_response(content='{"weather": "sunny"}'),
        ]
        responses.extend(_make_response(content='{"weather": "sunny"}') for _ in range(8))
        llm = fake_exaone_client(responses)
        trial = harness_runner.run_trial(
            bfcl_like_task,
            llm=llm,
            use_thinking_router=False,
            use_next_step_planner=False,
            max_turns=6,
        )
        assert len(trial.tool_calls) >= 1
        # ToolAgentCatalog dispatch strips the prefix before calling Tool.execute,
        # so our CapturedExecutor records the logical (unqualified) name. This
        # aligns naive (no catalog) and harness captures to the same key — exactly
        # what m3_tool_selection.normalize_tool_name relies on for comparison.
        assert trial.tool_calls[0].name == "get_weather"
        assert trial.tool_calls[0].arguments == {"city": "Seoul"}
        assert trial.input_tokens > 0

    def test_ledger_blocks_duplicate_calls(
        self,
        bfcl_like_task,
        fake_exaone_client,
    ):
        qualified = "tool__get_weather"
        responses = [
            _make_response(tool_calls=[
                _make_tool_call(qualified, {"city": "Seoul"}, call_id="c1"),
                _make_tool_call(qualified, {"city": "Seoul"}, call_id="c2"),
            ]),
            _make_response(content='{"weather": "sunny"}'),
        ]
        responses.extend(_make_response(content='{"weather": "sunny"}') for _ in range(8))
        llm = fake_exaone_client(responses)
        trial = harness_runner.run_trial(
            bfcl_like_task,
            llm=llm,
            use_thinking_router=False,
            use_next_step_planner=False,
            max_turns=6,
        )
        # ToolInvocationLedger deduplicates by canonical (name, arguments) — the
        # second duplicate is blocked at dispatch and never reaches our capture hook.
        unique = {(c.name, frozenset(c.arguments.items())) for c in trial.tool_calls}
        assert len(unique) == 1
        assert len(trial.tool_calls) == 1


class TestHarnessGracefulDegradation:
    def test_llm_exception_does_not_crash_runner(self, bfcl_like_task):
        # The harness wraps LLM failures into AgentResult; the runner should
        # still produce a valid TrialResult (no Python exception leaks out).
        class BoomLLM:
            DEFAULT_MODEL = "x"
            model = "x"

            def chat(self, messages, options=None):
                raise RuntimeError("boom")

        trial = harness_runner.run_trial(
            bfcl_like_task,
            llm=BoomLLM(),
            use_thinking_router=False,
            use_next_step_planner=False,
        )
        # runner returned cleanly regardless of inner failure path
        assert trial.runner == "harness"
        assert trial.task_id == bfcl_like_task.task_id
        # tool calls should be empty (LLM never produced any)
        assert trial.tool_calls == []
