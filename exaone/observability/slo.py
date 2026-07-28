"""
(en) Production SLO (objective) spec — template dataclass. Targets vary by team and service; this type mirrors the axes in root `PLAYBOOK.md` Part 7 (SLO and logs) in code. Align secrets, PII, and external HTTP policy with Part 8. For planning and reporting only, not runtime validation.

(kr) 실무 SLO(목표) 스펙 템플릿용 데이터클래스이다. 수치는 팀/서비스마다 다르다. 이 타입은 루트 `PLAYBOOK.md` Part 7(SLO·로그)과 동일한 축을 코드로도 잡을 수 있게 둔다. 시크릿·PII·외부 HTTP 정책은 Part 8과 맞춰 쓰면 된다. 런타임 검증이 아니라 계획·리포트용이다.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class SLOSpec:
    """
    (en) Per-service SLO; fields are left empty for the team to fill in.

    (kr) 서비스 단위 SLO이다. 필드는 비워 둔 채 팀이 채운다.
    """

    name: str
    # (en) Availability and errors
    # (kr) 가용성·오류
    error_rate_max: str | None = None
    availability_min: str | None = None

    # (en) Latency
    # (kr) 지연
    p95_chat_latency_ms: int | None = None
    p99_chat_latency_ms: int | None = None

    # (en) Quality (structured JSON, RAG — repo-specific)
    # (kr) 품질(구조화 JSON·RAG — 레포 특성)
    structured_output_success_min: str | None = None
    rag_min_hit_count: int | None = None

    notes: str = ""
    extra: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {
            "name": self.name,
            "error_rate_max": self.error_rate_max,
            "availability_min": self.availability_min,
            "p95_chat_latency_ms": self.p95_chat_latency_ms,
            "p99_chat_latency_ms": self.p99_chat_latency_ms,
            "structured_output_success_min": self.structured_output_success_min,
            "rag_min_hit_count": self.rag_min_hit_count,
            "notes": self.notes,
        }
        d.update(self.extra)
        return d


__all__ = ["SLOSpec"]
