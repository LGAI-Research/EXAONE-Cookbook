"""
(en) Provider-agnostic LLM streaming chunks.
OpenAI-compatible SSE lines are normalized here; the agent loop must not parse provider wire format.

(kr) 프로바이더에 독립적인 LLM 스트리밍 청크 모듈이다.
OpenAI 호환 SSE 라인을 여기서 정규화하며 에이전트 루프는 프로바이더 wire 포맷을 직접 파싱하지 않는다.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any, Iterator, Literal

from exaone.llm.exaone_client import ExaoneResponse

LlmStreamChunkKind = Literal["text", "reasoning", "tool_call", "usage", "done", "error"]


@dataclass(frozen=True)
class LlmStreamChunk:
    kind: LlmStreamChunkKind
    text: str = ""
    tool_calls: list[dict[str, Any]] | None = None
    finish_reason: str | None = None
    usage: dict[str, int] = field(default_factory=dict)
    raw: Any = None


def _delta_text(delta: dict[str, Any]) -> str:
    content = delta.get("content")
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: list[str] = []
        for item in content:
            if isinstance(item, dict) and item.get("type") == "text":
                parts.append(str(item.get("text") or ""))
            elif isinstance(item, str):
                parts.append(item)
        return "".join(parts)
    return ""


def _delta_reasoning(delta: dict[str, Any], choice: dict[str, Any]) -> str:
    for key in ("reasoning_content", "thinking", "reasoning"):
        val = delta.get(key) or choice.get(key)
        if isinstance(val, str) and val:
            return val
    return ""


def _merge_tool_call_delta(
    accumulated: list[dict[str, Any]],
    delta_tool_calls: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    (en) Merge streaming tool_call fragments (OpenAI index-based deltas).

    (kr) 스트리밍 tool_call 조각을 병합한다(OpenAI index 기반 delta).
    """
    out = [dict(x) for x in accumulated]
    for tc_delta in delta_tool_calls:
        idx = tc_delta.get("index", 0)
        while len(out) <= idx:
            out.append({"id": "", "type": "function", "function": {"name": "", "arguments": ""}})
        cur = out[idx]
        if tc_delta.get("id"):
            cur["id"] = tc_delta["id"]
        if tc_delta.get("type"):
            cur["type"] = tc_delta["type"]
        fn_delta = tc_delta.get("function") or {}
        fn_cur = cur.setdefault("function", {"name": "", "arguments": ""})
        if fn_delta.get("name"):
            fn_cur["name"] = (fn_cur.get("name") or "") + str(fn_delta["name"])
        if fn_delta.get("arguments"):
            fn_cur["arguments"] = (fn_cur.get("arguments") or "") + str(fn_delta["arguments"])
    return out


def parse_openai_compatible_sse_line(line: str) -> LlmStreamChunk | None:
    """
    (en) Parse one SSE ``data:`` payload line into a chunk, or None for heartbeat / [DONE].

    (kr) SSE ``data:`` 페이로드 한 줄을 청크로 파싱하며 heartbeat / [DONE]이면 None을 반환한다.
    """
    stripped = (line or "").strip()
    if not stripped.startswith("data:"):
        return None
    payload = stripped[5:].strip()
    if not payload or payload == "[DONE]":
        if payload == "[DONE]":
            return LlmStreamChunk(kind="done")
        return None
    try:
        data = json.loads(payload)
    except json.JSONDecodeError:
        return LlmStreamChunk(kind="error", text=payload, raw=payload)

    if isinstance(data, dict) and data.get("error"):
        err = data["error"]
        msg = err.get("message") if isinstance(err, dict) else str(err)
        return LlmStreamChunk(kind="error", text=msg or "stream error", raw=data)

    choices = data.get("choices") or []
    if not choices:
        usage = data.get("usage")
        if usage:
            return LlmStreamChunk(kind="usage", usage=dict(usage), raw=data)
        return None

    choice = choices[0] if isinstance(choices[0], dict) else {}
    delta = choice.get("delta") or choice.get("message") or {}
    if not isinstance(delta, dict):
        delta = {}

    reasoning = _delta_reasoning(delta, choice)
    if reasoning:
        return LlmStreamChunk(kind="reasoning", text=reasoning, raw=data)

    text = _delta_text(delta)
    if text:
        return LlmStreamChunk(kind="text", text=text, raw=data)

    delta_tool_calls = delta.get("tool_calls")
    if delta_tool_calls:
        return LlmStreamChunk(kind="tool_call", tool_calls=list(delta_tool_calls), raw=data)

    finish = choice.get("finish_reason")
    if finish:
        return LlmStreamChunk(kind="done", finish_reason=finish, raw=data)

    usage = data.get("usage")
    if usage:
        return LlmStreamChunk(kind="usage", usage=dict(usage), raw=data)
    return None


def iter_openai_compatible_sse(lines: Iterator[str]) -> Iterator[LlmStreamChunk]:
    """
    (en) Yield normalized chunks from raw SSE text lines (including ``data:`` prefix).

    (kr) raw SSE 텍스트 라인(``data:`` 접두 포함)에서 정규화된 청크를 순회한다.
    """
    tool_calls_acc: list[dict[str, Any]] = []
    for line in lines:
        chunk = parse_openai_compatible_sse_line(line)
        if chunk is None:
            continue
        if chunk.kind == "tool_call" and chunk.tool_calls:
            tool_calls_acc = _merge_tool_call_delta(tool_calls_acc, chunk.tool_calls)
            yield LlmStreamChunk(kind="tool_call", tool_calls=list(tool_calls_acc), raw=chunk.raw)
            continue
        if chunk.kind == "done" and tool_calls_acc:
            yield LlmStreamChunk(
                kind="done",
                finish_reason=chunk.finish_reason,
                tool_calls=list(tool_calls_acc),
                usage=chunk.usage,
                raw=chunk.raw,
            )
            continue
        yield chunk


def stream_chunks_to_response(
    chunks: Iterator[LlmStreamChunk],
    *,
    latency_ms: float | None = None,
) -> ExaoneResponse:
    """
    (en) Assemble normalized stream chunks into a single ExaoneResponse.

    (kr) 정규화된 스트림 청크를 하나의 ExaoneResponse로 조립한다.
    """
    content_parts: list[str] = []
    reasoning_parts: list[str] = []
    tool_calls: list[dict[str, Any]] | None = None
    finish_reason: str | None = None
    usage: dict[str, int] = {}
    last_raw: Any = None

    for chunk in chunks:
        last_raw = chunk.raw or last_raw
        if chunk.kind == "text":
            content_parts.append(chunk.text)
        elif chunk.kind == "reasoning":
            reasoning_parts.append(chunk.text)
        elif chunk.kind == "tool_call" and chunk.tool_calls:
            tool_calls = list(chunk.tool_calls)
        elif chunk.kind == "usage":
            usage = dict(chunk.usage)
        elif chunk.kind == "done":
            finish_reason = chunk.finish_reason or finish_reason
            if chunk.tool_calls:
                tool_calls = list(chunk.tool_calls)
            if chunk.usage:
                usage = dict(chunk.usage)
        elif chunk.kind == "error":
            raise RuntimeError(chunk.text or "LLM stream error")

    content = "".join(content_parts)
    reasoning_content = "".join(reasoning_parts).strip() or None

    return ExaoneResponse(
        content=content,
        raw=last_raw,
        usage=usage,
        finish_reason=finish_reason,
        tool_calls=tool_calls,
        latency_ms=latency_ms,
        reasoning_content=reasoning_content,
    )
