#!/usr/bin/env python3
"""
(en) Micro-benchmark: ToolAgent enrich/finalize overhead (mock LLM, no API).

(kr) Micro-benchmark: ToolAgent enrich/finalize 오버헤드(mock LLM, API 없음).

Run from cookbook root:
    python test/perf/tool_agent_microbench.py
"""
from __future__ import annotations

import statistics
import sys
import time
import unittest.mock
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from exaone.agents import AgentContext, ToolAgent, build_rag_tool_registry
from exaone.agents.tool_agent_catalog import RAG_TOOL_AGENT_KEY
from exaone.llm import ExaoneResponse
from exaone.tools import ToolRegistry, tool_from_callable


def _mock_llm(*, with_tool_call_first: bool = False) -> unittest.mock.Mock:
    """Returns mock ExaoneClient; chat() cycles tool call then final JSON."""
    llm = unittest.mock.Mock()
    llm.model = "bench-model"
    calls: list[str] = []

    def _chat(messages, options=None):
        calls.append("chat")
        opts = options
        tools = getattr(opts, "tools", None) if opts else None
        if tools and with_tool_call_first and calls.count("chat") == 1:
            return ExaoneResponse(
                content="",
                tool_calls=[
                    {
                        "id": "c1",
                        "function": {
                            "name": "rag__retrieve",
                            "arguments": '{"query":"bench","top_k":3}',
                        },
                    }
                ],
                latency_ms=10.0,
            )
        return ExaoneResponse(
            content='{"answer":"ok","confidence":"high","sources":[]}',
            latency_ms=12.0,
        )

    llm.chat = unittest.mock.Mock(side_effect=_chat)
    llm._bench_calls = calls
    return llm


def _rag_strategy():
    s = unittest.mock.Mock()
    s.retrieve.return_value = [
        unittest.mock.Mock(text="Evidence passage.", score=1.0, metadata={}),
    ]
    return s


def _bench(label: str, fn, *, rounds: int = 20) -> dict:
    times: list[float] = []
    last_calls = 0
    for _ in range(rounds):
        t0 = time.perf_counter()
        fn()
        times.append(time.perf_counter() - t0)
    return {
        "label": label,
        "rounds": rounds,
        "mean_ms": statistics.mean(times) * 1000,
        "p50_ms": statistics.median(times) * 1000,
        "p95_ms": sorted(times)[int(0.95 * len(times)) - 1] * 1000,
        "llm_chat_calls": last_calls,
    }


def main() -> None:
    rounds = 30

    # (en) ----- finalize-only (no tools) -----
    # (kr) ----- finalize-only (도구 없음) -----
    def run_finalize_only():
        llm = _mock_llm()
        agent = ToolAgent(use_thinking_router=False)
        agent.run(AgentContext(query="hello"), llm=llm)
        return len(llm.chat.call_args_list)

    rows = []
    t0 = time.perf_counter()
    for _ in range(rounds):
        run_finalize_only()
    rows.append(
        {
            "scenario": "finalize_only (no tools, router off)",
            "mean_ms": (time.perf_counter() - t0) / rounds * 1000,
            "llm_calls_per_run": 1,
        }
    )

    # (en) ----- RAG tool enrich + finalize, router off -----
    # (kr) ----- RAG tool enrich + finalize, router off -----
    def run_rag_no_router():
        llm = _mock_llm(with_tool_call_first=True)
        agent = ToolAgent(
            retrieval_strategy=_rag_strategy(),
            use_thinking_router=False,
            use_next_step_planner=False,
            max_enrich_turns=3,
        )
        agent.run(AgentContext(query="What is in the docs?"), llm=llm)
        return len(llm.chat.call_args_list)

    chat_counts = []
    t0 = time.perf_counter()
    for _ in range(rounds):
        chat_counts.append(run_rag_no_router())
    rows.append(
        {
            "scenario": "rag tool enrich+finalize (router off, evaluate off)",
            "mean_ms": (time.perf_counter() - t0) / rounds * 1000,
            "llm_calls_per_run": statistics.mean(chat_counts),
        }
    )

    # (en) ----- RAG + mock ThinkingRouter -----
    # (kr) ----- RAG + mock ThinkingRouter -----
    def run_rag_router():
        llm = _mock_llm(with_tool_call_first=True)
        llm.chat.return_value = ExaoneResponse(
            content=(
                '{"enable_thinking":true,"temperature":1.0,"top_p":0.95,'
                '"semantic_intent":"general","confidence":"high","rationale":"ok"}'
            ),
            latency_ms=5,
        )

        call_n = [0]

        def _router_chat(messages, options=None):
            call_n[0] += 1
            rf = getattr(options, "response_format", None) if options else None
            name = (rf or {}).get("json_schema", {}).get("name", "")
            if name == "route_axes":
                return ExaoneResponse(
                    content=(
                        '{"enable_thinking":true,"temperature":1.0,"top_p":0.95,'
                        '"semantic_intent":"analytical","confidence":"high","rationale":"x"}'
                    ),
                    latency_ms=5,
                )
            if name == "route_plan_enrich_unified":
                return ExaoneResponse(
                    content=(
                        '{"enable_thinking":true,"temperature":1.0,"top_p":0.95,'
                        '"semantic_intent":"analytical","confidence":"high","rationale":"x",'
                        '"answerable":true,"tool_agent_key":"rag","rewritten_query":"bench",'
                        '"tool_hints":[{"name":"rag__retrieve","arguments":{"query":"bench"},'
                        '"reason":"need context"}]}'
                    ),
                    latency_ms=5,
                )
            if name == "route_plan_enrich":
                return ExaoneResponse(
                    content=(
                        '{"tool_agent_key":"rag","rewritten_query":"bench",'
                        '"tool_hints":[{"name":"rag__retrieve","arguments":{"query":"bench"},'
                        '"reason":"need context"}]}'
                    ),
                    latency_ms=5,
                )
            if name == "catalog_screen":
                return ExaoneResponse(
                    content=(
                        '{"answerable":true,"tool_agent_key":"rag",'
                        '"rationale":"ok","suggested_tools":["rag__retrieve"]}'
                    ),
                    latency_ms=5,
                )
            if name == "progress_evaluation":
                return ExaoneResponse(
                    content=(
                        '{"action":"finalize","sufficient":true,"no_progress":false,'
                        '"rationale":"ok","next_tool_calls":[]}'
                    ),
                    latency_ms=5,
                )
            if name == "route_plan_finalize":
                return ExaoneResponse(
                    content='{"answer_tool_agent_key":"rag","rewritten_query":"bench"}',
                    latency_ms=5,
                )
            return _mock_llm(with_tool_call_first=True).chat(messages, options)

        llm.chat.side_effect = _router_chat
        agent = ToolAgent(
            retrieval_strategy=_rag_strategy(),
            use_thinking_router=True,
            use_next_step_planner=True,
            max_enrich_turns=3,
        )
        agent.run(AgentContext(query="What is in the docs?"), llm=llm)
        return call_n[0]

    router_calls = []
    t0 = time.perf_counter()
    for _ in range(rounds):
        router_calls.append(run_rag_router())
    rows.append(
        {
            "scenario": "rag + ThinkingRouter (plan+evaluate+finalize)",
            "mean_ms": (time.perf_counter() - t0) / rounds * 1000,
            "llm_calls_per_run": statistics.mean(router_calls),
        }
    )

    print("ToolAgent micro-benchmark (mock LLM, local CPU)")
    print(f"rounds={rounds}\n")
    print(f"{'scenario':<52} {'mean_ms':>10} {'llm_calls':>10}")
    print("-" * 74)
    for r in rows:
        print(f"{r['scenario']:<52} {r['mean_ms']:>10.1f} {r['llm_calls_per_run']:>10.1f}")


if __name__ == "__main__":
    main()
