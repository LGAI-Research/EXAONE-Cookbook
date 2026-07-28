"""
(en) Low-temperature JSON-schema chat helper for router planners.

(kr) router planner용 저온 JSON-schema chat 헬퍼입니다.
"""
from __future__ import annotations

from typing import Any

from exaone.agents.run_trace import AgentRunPhase, schema_name_from_response_format, traced_chat
from exaone.agents.thinking_router.constants import TEMP_MIN, TOP_P_DEFAULT
from exaone.llm import ExaoneGenerateOptions, ExaoneMessage


def chat_json(
    client: Any,
    *,
    messages: list[dict[str, str]],
    max_new_tokens: int,
    response_format: dict[str, Any],
    phase: AgentRunPhase,
) -> str:
    exaone_messages = [
        ExaoneMessage(role=m["role"], content=m["content"]) for m in messages
    ]
    opts = ExaoneGenerateOptions(
        max_new_tokens=max_new_tokens,
        temperature=TEMP_MIN,
        top_p=TOP_P_DEFAULT,
        enable_thinking=False,
        response_format=response_format,
    )
    resp = traced_chat(
        client,
        exaone_messages,
        opts,
        phase=phase,
        schema_name=schema_name_from_response_format(response_format),
    )
    return (resp.content or "").strip()
