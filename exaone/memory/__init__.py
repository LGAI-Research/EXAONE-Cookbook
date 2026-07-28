"""
(en) Separates agent/tool run history (ledger) from large responses (artifact). **InMemoryLedger** keeps short hints plus `artifact_id` references; reads return snapshots and records are updated only via `append` (`LedgerEntry` is frozen). **InMemoryArtifactStore** holds full `payload` for large tool results; `get`/`pop` return snapshots (`StoredArtifact` is frozen) and `dict`/`list` payloads are isolated with deep copy. **store_large_tool_result** (helpers) writes artifact + ledger only above a byte threshold. Capacity and thresholds come from root **`.env`** / **`.env.example`** `CORE_MEMORY_*`, read via **`exaone.config`**. Default stores: `default_artifact_store`, `default_ledger`, `default_memory_pair` (`exaone.memory.defaults`). Best practice (summary): (1) **Two-tier** — body in artifact, index/audit in ledger (prompt gets ref + hint). (2) **Dual limits on count and bytes** — many deployments cap artifacts with `max_total_bytes` as well as item count (here InMemory uses count-based `max_items`/`max_entries`). (3) **Orphan ref** — if artifact is evicted first, ledger UUIDs may point to missing payload → handle `get` returning None or extend artifact retention (LRU) to recent ledger refs. (4) **Production** — ephemeral data on S3/Redis, ledger duplicated to OpenTelemetry/audit logs.

(kr) 에이전트/도구 실행 기록(ledger)과 대용량 응답(artifact) 분리 보관이다. **InMemoryLedger**는 짧은 힌트 + `artifact_id` 참조만 둔다. 조회 API는 스냅샷을 반환하며 내부 기록은 `append`로만 갱신한다(`LedgerEntry`는 frozen). **InMemoryArtifactStore**는 큰 tool 응답 등 전체 `payload`를 둔다. `get`/`pop`은 스냅샷을 반환하며(`StoredArtifact`는 frozen), `dict`/`list` payload는 deep copy로 분리한다. **store_large_tool_result**(helpers)는 임계 바이트 이상일 때만 artifact + ledger에 쓴다. 용량·임계값은 루트 **`.env`** / **`.env.example`**의 `CORE_MEMORY_*`, 읽기는 **`exaone.config`**이다. 기본 store 생성은 `default_artifact_store`, `default_ledger`, `default_memory_pair`(`exaone.memory.defaults`)이다. Best practice(요약): (1) **Two-tier** — 본문은 artifact, 인덱스/감사는 ledger(프롬프트엔 ref + hint). (2) **객체 수/바이트 이중 한도** — 항목 개수뿐 아니라 `max_total_bytes`로 artifact만 제한하는 경우도 많다(여기서는 InMemory에 개수 기반 `max_items`/`max_entries`). (3) **Orphan ref** — artifact만 먼저 evict되면 ledger의 UUID가 가리키는 payload가 사라질 수 있다 → `get` None 처리 또는 artifact retention을 ledger의 최근 참조에 맞춰 연장(LRU) 설계. (4) **Production** — 임시 데이터는 S3/Redis, ledger는 OpenTelemetry/감사 로그로 이중 기록한다.
"""

from exaone.memory.artifact_store import InMemoryArtifactStore
from exaone.memory.defaults import default_artifact_store, default_ledger, default_memory_pair
from exaone.memory.helpers import store_large_tool_result
from exaone.memory.ledger import InMemoryLedger
from exaone.memory.types import LedgerEntry, StoredArtifact

__all__ = [
    "InMemoryArtifactStore",
    "InMemoryLedger",
    "LedgerEntry",
    "StoredArtifact",
    "default_artifact_store",
    "default_ledger",
    "default_memory_pair",
    "store_large_tool_result",
]
