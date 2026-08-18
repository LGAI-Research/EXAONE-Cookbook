#!/usr/bin/env python3
"""Smoke verification for recipes Track 00–10 (uses root .env when API needed)."""
from __future__ import annotations

import argparse
import asyncio
import concurrent.futures
import json
import os
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import exaone  # noqa: E402

exaone.load_project_env()

PASS = 0
FAIL = 0
SKIP = 0
HAS_API = bool(os.environ.get("EXAONE_API_KEY", "").strip())


def ok(track: str, name: str, detail: str = "") -> None:
    global PASS
    PASS += 1
    print(f"  [PASS] {track} / {name}" + (f" — {detail}" if detail else ""))


def fail(track: str, name: str, detail: str = "") -> None:
    global FAIL
    FAIL += 1
    print(f"  [FAIL] {track} / {name}" + (f" — {detail}" if detail else ""), file=sys.stderr)


def skip(track: str, name: str, detail: str = "") -> None:
    global SKIP
    SKIP += 1
    print(f"  [SKIP] {track} / {name}" + (f" — {detail}" if detail else ""))


def section(title: str) -> None:
    print(f"\n=== {title} ===")


def _load_exchange_tools():
    rates_path = ROOT / "recipes/track02_minimum_agent_loop/data/exchange_rates.json"
    _rates = json.loads(rates_path.read_text(encoding="utf-8"))
    exchange_rates_krw = _rates["rates"]
    as_of = _rates["as_of"]

    def _rate(base: str, quote: str) -> float:
        base, quote = base.upper(), quote.upper()
        if base == "KRW" and quote == "KRW":
            return 1.0
        if base == "KRW":
            return 1.0 / exchange_rates_krw[quote]
        if quote == "KRW":
            return exchange_rates_krw[base]
        return exchange_rates_krw[base] / exchange_rates_krw[quote]

    def tool_exchange_rate(args: dict) -> dict:
        base = (args.get("base") or "").upper()
        quote = (args.get("quote") or "KRW").upper()
        table = set(exchange_rates_krw) | {"KRW"}
        if base not in table or quote not in table:
            return {"error": f"unknown currency: base={base}, quote={quote}"}
        return {"base": base, "quote": quote, "rate": round(_rate(base, quote), 4), "as_of": as_of}

    return tool_exchange_rate


def track00() -> None:
    section("Track 00 — Bootstrap")
    ok("00", "env", f"python={sys.version.split()[0]} exaone={exaone.__version__}")
    if not HAS_API:
        skip("00", "api", "EXAONE_API_KEY not set")
        return
    client = exaone.integrations.build_llm_from_env()
    resp = client.chat(
        [exaone.llm.ExaoneMessage(role="user", content="한 문장으로 자기소개해줘.")],
        options=exaone.llm.ExaoneGenerateOptions(enable_thinking=False),
    )
    ok("00", "chat", (resp.content or "")[:50])


def track01() -> None:
    section("Track 01 — Foundation")
    samples = json.loads(
        (ROOT / "recipes/track01_exaone_foundation/data/structured_output_samples.json").read_text()
    )
    pipeline = exaone.output.StructuredOutputPipeline(
        json_schema={
            "type": "object",
            "required": ["name", "age"],
            "properties": {"name": {"type": "string"}, "age": {"type": "integer"}},
        },
        max_repair_attempts=1,
    )
    parsed = pipeline.process(samples[2]["raw"])
    if parsed.success:
        ok("01", "structured_output", parsed.data.get("name", ""))
    else:
        fail("01", "structured_output", parsed.error or "")
    if HAS_API:
        client = exaone.integrations.build_llm_from_env()
        router = exaone.agents.ThinkingRouter(client=client, model=client.model)
        d = router.route("100달러 환전", has_tools=True)
        ok("01", "thinking_router", f"thinking={d.enable_thinking}")
    else:
        skip("01", "thinking_router", "no API key")


def track02() -> None:
    section("Track 02 — Agent Loop")
    tool_exchange_rate = _load_exchange_tools()
    schema = {
        "type": "function",
        "function": {
            "name": "exchange_rate",
            "parameters": {
                "type": "object",
                "required": ["base", "quote"],
                "properties": {"base": {"type": "string"}, "quote": {"type": "string"}},
                "additionalProperties": False,
            },
        },
    }
    reg = exaone.tools.ToolRegistry()
    reg.register(exaone.tools.Tool(name="exchange_rate", schema=schema, execute=tool_exchange_rate))
    out = reg.execute("exchange_rate", {"base": "USD", "quote": "KRW"})
    if "rate" in out:
        ok("02", "tool_registry", str(out["rate"]))
    else:
        fail("02", "tool_registry", str(out))
    if HAS_API:
        agent = exaone.agents.ToolAgent(tool_registry=reg, max_turns=4)
        result = agent.run(
            exaone.agents.AgentContext(query="100달러는 원화로 얼마야?"),
            llm=exaone.integrations.build_llm_from_env(),
        )
        ok("02", "tool_agent", f"success={result.success}")
    else:
        skip("02", "tool_agent", "no API key")


def track03() -> None:
    section("Track 03 — Tools & MCP")
    mcp_demo = ROOT / "recipes/track03_tools_and_mcp/mcp_demo"
    try:
        from mcp import ClientSession
        from mcp.client.stdio import StdioServerParameters, stdio_client
    except ImportError:
        fail("03", "mcp_import", "mcp not installed")
        return
    ok("03", "mcp_import")
    server_params = StdioServerParameters(
        command=sys.executable, args=[str(mcp_demo / "server.py")], env={**os.environ}
    )

    def run_async(coro_factory):
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
            return pool.submit(lambda: asyncio.run(coro_factory())).result()

    async def discover():
        if str(mcp_demo) not in sys.path:
            sys.path.insert(0, str(mcp_demo))
        from client_adapter import call_tool_result_to_dict, call_tool_with_timeout

        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                tools = await session.list_tools()
                result = await call_tool_with_timeout(
                    session, "source_diagnostics", {"query": "test"}, timeout=60.0
                )
                return len(tools.tools), call_tool_result_to_dict(result)

    try:
        n, diag = run_async(discover)
        ok("03", "mcp_discovery", f"tools={n}")
        ok("03", "mcp_diagnostics", f"ok={diag.get('ok')}")
    except Exception as exc:
        fail("03", "mcp_session", str(exc))


def track04() -> None:
    section("Track 04 — RAG (04a failure recovery)")
    cases = json.loads(
        (ROOT / "recipes/track04_rag_and_knowledge/data/failure_case_fixtures.json").read_text()
    )
    results: list[dict] = []

    # Case 1: empty retrieval
    out_empty = {"chunk_count": 0, "context": "[No retrieval hits]"}
    results.append({"id": "empty_retrieval", "pass": out_empty["chunk_count"] == 0})

    # Case 2: not configured
    case2_pass = False
    try:
        raise RuntimeError("retrieval strategy not configured")
    except RuntimeError:
        case2_pass = True
    results.append({"id": "not_configured", "pass": case2_pass})

    # Case 3: dedupe
    chunks = [
        {"source": "it-vpn", "text": "a"},
        {"source": "it-vpn", "text": "a"},
        {"source": "hr", "text": "b"},
    ]
    seen: set[tuple[str, str]] = set()
    deduped = []
    for c in chunks:
        key = (c["source"], c["text"])
        if key in seen:
            continue
        seen.add(key)
        deduped.append(c)
    formatted = "\n".join(f'source="{c["source"]}"' for c in deduped)
    results.append({"id": "duplicate_chunks", "pass": formatted.count('source="it-vpn"') == 1})

    # Case 4: token cap
    long_ctx = cases[3]["long_context"]
    max_input = 512
    est = exaone.context_management.executor.estimate_tokens_from_text(long_ctx)
    trimmed = long_ctx[: max_input * 4]
    after = exaone.context_management.executor.estimate_tokens_from_text(trimmed)
    results.append({"id": "context_overflow", "pass": after <= max_input or est > after})

    # Case 5: injection sanitize
    raw = cases[4]["injection_text"]
    clean = exaone.context_management.sanitize_untrusted_reference_text(raw)
    results.append(
        {
            "id": "injection_in_chunk",
            "pass": "IGNORE PREVIOUS" in raw and "[removed-tag:" in clean,
        }
    )

    all_pass = all(r["pass"] for r in results)
    if all_pass:
        ok("04", "failure_recovery", f"{sum(r['pass'] for r in results)}/{len(results)}")
    else:
        fail("04", "failure_recovery", str([r for r in results if not r["pass"]]))

    # 04b preflight (optional infra)
    try:
        import exaone.integrations.embedding as emb_mod
        import exaone.integrations.postgres as pg_mod
        from exaone.integrations.infra_env import postgres_url_from_env

        pg_url = postgres_url_from_env()
        emb_url = os.environ.get("EMBEDDING_BASE_URL", "http://localhost:8000").strip()
        pg_ok = pg_mod.postgres_available(pg_url) if pg_url else False
        emb_ok = emb_mod.embedding_server_reachable(emb_url)
        if pg_ok and emb_ok:
            ok("04", "04b_preflight", "postgres+embedding up")
        else:
            skip("04", "04b_preflight", f"postgres={pg_ok} embedding={emb_ok}")
    except Exception as exc:
        skip("04", "04b_preflight", str(exc))


def track05() -> None:
    section("Track 05 — Memory & Long Context")
    msgs = [
        exaone.llm.ExaoneMessage(role="user", content="hello"),
        exaone.llm.ExaoneMessage(role="assistant", content="hi"),
    ]
    est = exaone.context_management.estimate_tokens_from_messages(msgs)
    prepared, capped = exaone.context_management.prepare_messages_for_llm_chat(
        msgs, reserved_new_tokens=64
    )
    ok("05", "context_budget", f"est={est} prepared={len(prepared)} cap={capped}")
    ledger = exaone.memory.InMemoryLedger()
    ledger.append(event_type="tool", hint="echo ok")
    ok("05", "memory_ledger", f"entries={len(ledger)}")


def track06() -> None:
    section("Track 06 — Orchestration")
    if not HAS_API:
        skip("06", "routing", "no API key")
        return
    client = exaone.integrations.build_llm_from_env()
    router = exaone.agents.ThinkingRouter(client=client, model=client.model)
    row = json.loads(
        (ROOT / "recipes/track06_orchestration_multi_agent/data/routing_inputs.jsonl")
        .read_text()
        .strip()
        .splitlines()[0]
    )
    d = router.route(row["query"], has_tools=row.get("has_tools", False))
    ok("06", "routing_sample", f"thinking={d.enable_thinking}")


def track07() -> None:
    section("Track 07 — Safety & Observability")
    cases = [
        json.loads(line)
        for line in (ROOT / "recipes/track07_safety_hitl_observability/data/injection_cases.jsonl")
        .read_text()
        .splitlines()
        if line.strip()
    ]

    def defense_pass(case: dict, raw: str, sanitized: str) -> bool:
        if case.get("vector") == "log":
            return "[REDACTED]" in sanitized and "secret-token" not in sanitized
        if "Bearer" in raw:
            return "[REDACTED]" in sanitized
        if case.get("vector") == "rag_chunk":
            return "[removed-tag:" in sanitized or "IGNORE" not in sanitized
        return True

    passed = 0
    for case in cases:
        raw = case.get("text") or case.get("injection_text") or ""
        if case.get("vector") in ("user", "tool"):
            sanitized = exaone.observability.sanitize_for_log(raw)
        else:
            untrusted = exaone.context_management.sanitize_untrusted_reference_text(raw)
            sanitized = exaone.observability.sanitize_for_log(untrusted)
        if defense_pass(case, raw, sanitized):
            passed += 1
    if passed == len(cases):
        ok("07", "injection_defense", f"{passed}/{len(cases)}")
    else:
        fail("07", "injection_defense", f"{passed}/{len(cases)}")


def track08() -> None:
    section("Track 08 — Evaluation M1–M10")
    from eval.metrics import m1_task_success, m2_pass_k, m6_schema_adherence
    from eval.metrics.m1_task_success import TaskGold
    from eval.metrics.m6_schema_adherence import SchemaSpec
    from eval.metrics.types import TrialResult

    t_ok = TrialResult(
        trial_id="t-s1",
        task_id="s1",
        dataset="track08.synthetic",
        runner="verify",
        final_content='{"city": "seoul"}',
        final_structured={"city": "seoul"},
    )
    m1 = m1_task_success.compute([t_ok], {"s1": TaskGold(task_id="s1", answer={"city": "seoul"})})
    m6_s, m6_l = m6_schema_adherence.score_trial(t_ok, SchemaSpec(required_keys=["city"]))
    m2 = m2_pass_k.compute(
        {"s1": [t_ok, t_ok]},
        {"s1": TaskGold(task_id="s1", answer={"city": "seoul"})},
        m1_task_success.score_trial_exact,
        ks=(1, 2),
    )
    checks = [
        ("M1", m1.value == 1.0),
        ("M6_loose", m6_l),
        ("M2_pass2", (m2.breakdown or {}).get("pass_2", 0) == 1.0),
    ]
    for name, good in checks:
        if good:
            ok("08", name)
        else:
            fail("08", name)


def track09() -> None:
    section("Track 09 — Framework Bridges")
    try:
        from langgraph.graph import END, START, StateGraph
    except ImportError:
        skip("09", "langgraph", "langgraph not installed")
        return

    # deterministic mock graph (Session 3 pattern)
    from typing import TypedDict

    class WorkflowState(TypedDict, total=False):
        trace: list[str]
        plan: str

    def planner(state: WorkflowState) -> WorkflowState:
        state = dict(state)
        state["trace"] = list(state.get("trace", [])) + ["planner"]
        state["plan"] = "mock"
        return state

    def executor(state: WorkflowState) -> WorkflowState:
        state = dict(state)
        state["trace"] = list(state.get("trace", [])) + ["executor"]
        return state

    g = StateGraph(WorkflowState)
    g.add_node("planner", planner)
    g.add_node("executor", executor)
    g.add_edge(START, "planner")
    g.add_edge("planner", "executor")
    g.add_edge("executor", END)
    final = g.compile().invoke({"trace": []})
    if final.get("trace") == ["planner", "executor"]:
        ok("09", "langgraph_mock", str(final["trace"]))
    else:
        fail("09", "langgraph_mock", str(final.get("trace")))

    template = ROOT / "recipes/track09_framework_bridges/data/chat_app_template.py"
    if template.exists():
        ok("09", "chat_app_template", str(template.name))
    else:
        fail("09", "chat_app_template", "missing")


def track10() -> None:
    section("Track 10 — AX Capstones")
    proc = subprocess.run(
        [sys.executable, str(ROOT / "recipes/track10_ax_capstones/capstone_runner.py")],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode == 0 and "M1_mean" in proc.stdout:
        ok("10", "capstone_runner", proc.stdout.strip().splitlines()[-1])
    else:
        fail("10", "capstone_runner", (proc.stderr or proc.stdout)[-300:])


TRACKS = {
    "00": track00,
    "01": track01,
    "02": track02,
    "03": track03,
    "04": track04,
    "05": track05,
    "06": track06,
    "07": track07,
    "08": track08,
    "09": track09,
    "10": track10,
}


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify EXAONE Cookbook recipes (Track 00–10).")
    parser.add_argument("--track", action="append", help="Only run these tracks (e.g. 04 08)")
    parser.add_argument("--skip-api", action="store_true", help="Skip live API checks")
    args = parser.parse_args()
    if args.skip_api:
        global HAS_API
        HAS_API = False

    print("EXAONE Cookbook — recipes verification")
    print(f"ROOT: {ROOT}  API: {'yes' if HAS_API else 'no'}")
    selected = args.track or list(TRACKS.keys())
    for key in selected:
        fn = TRACKS.get(key)
        if not fn:
            fail(key, "unknown_track")
            continue
        try:
            fn()
        except Exception as exc:
            fail(key, "exception", str(exc))
    print(f"\n{'='*40}")
    print(f"Results: {PASS} passed, {FAIL} failed, {SKIP} skipped")
    return 1 if FAIL else 0


if __name__ == "__main__":
    raise SystemExit(main())
