from __future__ import annotations

from eval.runners import naive_runner


class TestNaiveSingleShot:
    def test_no_tools_single_text_response(self, ifeval_like_task, chat_fn_scripted, make_chat_response):
        chat = chat_fn_scripted([make_chat_response(content="A haiku about a database")])
        trial = naive_runner.run_trial(ifeval_like_task, chat_fn=chat)
        assert trial.runner == "naive"
        assert trial.task_id == "ifeval.001"
        assert trial.turns == 1
        assert trial.final_content == "A haiku about a database"
        assert trial.tool_calls == []
        assert trial.input_tokens == 50
        assert trial.output_tokens == 30
        assert trial.error is None
        assert trial.finished

    def test_irrelevance_abstain_captured(self, irrelevance_task, chat_fn_scripted, make_chat_response):
        chat = chat_fn_scripted([make_chat_response(content="No tool applies.")])
        trial = naive_runner.run_trial(irrelevance_task, chat_fn=chat)
        assert trial.tool_calls == []
        assert trial.turns == 1


class TestNaiveToolLoop:
    def test_single_tool_call_then_final(
        self,
        bfcl_like_task,
        chat_fn_scripted,
        make_chat_response,
        make_assistant_tool_call,
    ):
        chat = chat_fn_scripted([
            make_chat_response(tool_calls=[make_assistant_tool_call("get_weather", {"city": "Seoul"})]),
            make_chat_response(content='{"weather": "sunny"}'),
        ])
        trial = naive_runner.run_trial(bfcl_like_task, chat_fn=chat)
        assert trial.turns == 2
        assert len(trial.tool_calls) == 1
        assert trial.tool_calls[0].name == "get_weather"
        assert trial.tool_calls[0].arguments == {"city": "Seoul"}
        assert trial.final_structured == {"weather": "sunny"}
        assert trial.input_tokens == 100  # 50 + 50

    def test_naive_does_not_dedupe_repeated_calls(
        self,
        bfcl_like_task,
        chat_fn_scripted,
        make_chat_response,
        make_assistant_tool_call,
    ):
        chat = chat_fn_scripted([
            make_chat_response(tool_calls=[
                make_assistant_tool_call("get_weather", {"city": "Seoul"}, call_id="c1"),
                make_assistant_tool_call("get_weather", {"city": "Seoul"}, call_id="c2"),
            ]),
            make_chat_response(content="done"),
        ])
        trial = naive_runner.run_trial(bfcl_like_task, chat_fn=chat)
        assert len(trial.tool_calls) == 2  # naive runner has no ledger

    def test_max_turns_stops_runaway_loop(
        self,
        bfcl_like_task,
        chat_fn_scripted,
        make_chat_response,
        make_assistant_tool_call,
    ):
        responses = [
            make_chat_response(tool_calls=[make_assistant_tool_call("get_weather", {"city": "X"})])
            for _ in range(3)
        ]
        chat = chat_fn_scripted(responses)
        trial = naive_runner.run_trial(bfcl_like_task, chat_fn=chat, max_turns=3)
        assert trial.finished is False
        assert trial.error is not None
        assert "max_turns" in trial.error


class TestNaiveErrorPaths:
    def test_chat_fn_exception_records_error(self, ifeval_like_task):
        def bad_chat(*, messages, tools):
            raise RuntimeError("boom")

        trial = naive_runner.run_trial(ifeval_like_task, chat_fn=bad_chat)
        assert trial.finished is False
        assert trial.error and "boom" in trial.error
        assert trial.turns == 1
