"""
(en) Transport helpers: AgentEvent → Server-Sent Events (SSE) wire format.
Core agent logic does not depend on FastAPI or SSE.

(kr) 전송 헬퍼입니다. AgentEvent를 Server-Sent Events(SSE) wire 형식으로 변환합니다.
핵심 agent 로직은 FastAPI나 SSE에 의존하지 않습니다.
"""
from __future__ import annotations

import json
from typing import Iterator

from exaone.agents.events import AgentEvent


def agent_event_to_sse(event: AgentEvent) -> str:
    """(en) Format one AgentEvent as an SSE message (event type + JSON data).

    (kr) AgentEvent 하나를 SSE 메시지로 포맷합니다(event type + JSON data).
    """
    data = json.dumps(event.to_dict(), ensure_ascii=False)
    return f"event: {event.type}\ndata: {data}\n\n"


def iter_agent_events_as_sse(events: Iterator[AgentEvent]) -> Iterator[str]:
    """(en) Yield SSE-encoded strings from a stream of AgentEvent.

    (kr) AgentEvent 스트림에서 SSE 인코딩 문자열을 yield합니다.
    """
    for ev in events:
        yield agent_event_to_sse(ev)
