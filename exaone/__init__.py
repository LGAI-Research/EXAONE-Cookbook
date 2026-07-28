"""
(en) EXAONE Cookbook top-level facade.

A single `import exaone` is the only line learners need to start any track.
After it, the architecture is visible *in the dotted access* itself:

    import exaone

    exaone.load_project_env()
    client   = exaone.llm.ExaoneAPIClient(base_url=..., model=..., api_key=...)
    registry = exaone.tools.ToolRegistry()
    agent    = exaone.agents.ToolAgent(tool_registry=registry, ...)
    result   = agent.run(exaone.agents.AgentContext(query="..."), llm=client)

Submodules are eagerly imported so that attribute access never silently
fails after a fresh `import exaone`. Only the two most-used environment
helpers and `__version__` are bound at the top level; everything else
keeps its proper namespace (`exaone.agents.*`, `exaone.tools.*`, ...).

(kr) EXAONE Cookbook 최상위 facade.

학습자는 어느 트랙에서든 `import exaone` 한 줄로 시작한다. 그 뒤로는
점(.) 접근 그대로 패키지의 구조가 코드에 드러난다.

    import exaone

    exaone.load_project_env()
    client   = exaone.llm.ExaoneAPIClient(base_url=..., model=..., api_key=...)
    registry = exaone.tools.ToolRegistry()
    agent    = exaone.agents.ToolAgent(tool_registry=registry, ...)
    result   = agent.run(exaone.agents.AgentContext(query="..."), llm=client)

서브모듈은 `import exaone` 한 번으로 모두 로드되므로 속성 접근이
조용히 실패하지 않는다. 최상위에는 가장 자주 쓰는 환경 헬퍼 두 개와
`__version__` 만 노출하고 나머지는 본래 네임스페이스
(`exaone.agents.*`, `exaone.tools.*`, ...) 를 유지한다.
"""
from __future__ import annotations

from exaone import (
    agents,
    config,
    context_management,
    integrations,
    llm,
    memory,
    observability,
    output,
    retrieval,
    tools,
)
from exaone.config import load_project_env, project_root

__version__ = "0.1.0"

__all__ = [
    "__version__",
    "agents",
    "config",
    "context_management",
    "integrations",
    "llm",
    "load_project_env",
    "memory",
    "observability",
    "output",
    "project_root",
    "retrieval",
    "tools",
]
