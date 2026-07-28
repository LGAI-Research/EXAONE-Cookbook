#!/usr/bin/env python3
"""
SSE demo: stream ToolAgent internal events (turn / tool / optional LLM deltas).

Run:
    uvicorn recipes.track02_minimum_agent_loop.streaming_demo.app:app --reload --port 8765

Then:
    curl -N "http://127.0.0.1:8765/v1/agent/stream?query=hello&stream_llm=false"

With EXAONE_API_KEY set, uses real LLM. Without it, uses an in-process mock LLM.
"""
from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import Iterator

from fastapi import FastAPI, Query
from fastapi.responses import StreamingResponse

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from exaone.agents import AgentContext, ToolAgent  # noqa: E402
from exaone.agents.streaming import iter_agent_events_as_sse  # noqa: E402
from exaone.config import load_project_env  # noqa: E402
from exaone.integrations.llm_env import build_llm_from_env  # noqa: E402
from exaone.llm import ExaoneClient, ExaoneGenerateOptions, ExaoneMessage, ExaoneResponse  # noqa: E402
from exaone.llm.streaming import LlmStreamChunk  # noqa: E402

logger = logging.getLogger(__name__)
load_project_env()

app = FastAPI(title="EXAONE Agent SSE streaming demo")


class _MockStreamLLM(ExaoneClient):
    """Offline mock: one tool turn then final JSON."""

    DEFAULT_MODEL = "mock"

    def chat(
        self,
        messages: list[ExaoneMessage],
        options: ExaoneGenerateOptions | None = None,
    ) -> ExaoneResponse:
        turn = sum(1 for m in messages if getattr(m, "role", None) == "assistant")
        if turn == 0 and options and options.tools:
            return ExaoneResponse(
                content="",
                tool_calls=[
                    {
                        "id": "mock-1",
                        "function": {"name": "echo", "arguments": '{"text": "ping"}'},
                    }
                ],
                latency_ms=1.0,
            )
        return ExaoneResponse(
            content='{"answer": "mock ok", "confidence": "high"}',
            latency_ms=1.0,
        )

    def chat_stream(
        self,
        messages: list[ExaoneMessage],
        options: ExaoneGenerateOptions | None = None,
    ) -> Iterator[LlmStreamChunk]:
        resp = self.chat(messages, options=options)
        if resp.content:
            for i in range(0, len(resp.content), 8):
                yield LlmStreamChunk(kind="text", text=resp.content[i : i + 8])
        if resp.tool_calls:
            yield LlmStreamChunk(kind="tool_call", tool_calls=list(resp.tool_calls))
        yield LlmStreamChunk(kind="done", finish_reason="stop")


def _build_llm() -> ExaoneClient:
    try:
        return build_llm_from_env()
    except SystemExit:
        logger.warning("EXAONE API not configured — using mock LLM")
        return _MockStreamLLM()


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/v1/agent/stream")
def agent_stream(
    query: str = Query(..., min_length=1),
    stream_llm: bool = Query(
        False,
        description="Stream finalize-phase LLM tokens as llm_delta events",
    ),
    stream_enrich_reasoning: bool = Query(
        False,
        description="Stream enrich ReAct reasoning/content as llm_delta (verbose)",
    ),
) -> StreamingResponse:
    llm = _build_llm()
    from exaone.tools import ToolRegistry, tool_from_callable

    def _echo(_name: str, args: dict) -> dict:
        return {"echo": args.get("text", "")}

    echo_reg = ToolRegistry()
    echo_reg.register(
        tool_from_callable(
            "echo",
            {
                "type": "function",
                "function": {
                    "name": "echo",
                    "description": "Echo text back",
                    "parameters": {
                        "type": "object",
                        "properties": {"text": {"type": "string"}},
                        "required": ["text"],
                    },
                },
            },
            _echo,
        )
    )
    agent = ToolAgent(tool_registry=echo_reg, use_thinking_router=False)
    ctx = AgentContext(query=query)

    def _body() -> Iterator[str]:
        events = agent.run_stream(
            ctx,
            llm=llm,
            stream_llm=stream_llm,
            stream_enrich_reasoning=stream_enrich_reasoning,
            verbose=False,
        )
        yield from iter_agent_events_as_sse(events)

    return StreamingResponse(_body(), media_type="text/event-stream")
