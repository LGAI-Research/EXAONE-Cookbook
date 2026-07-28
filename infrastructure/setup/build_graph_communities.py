#!/usr/bin/env python3
"""
step3에서 구축한 graph_entities, graph_relations를 기반으로
communities(소스별/연결 성분) 및 report(요약) 생성. infrastructure/setup step4_build_graph.sh 에서 호출.
"""
from __future__ import annotations

import logging
import sys
from collections import deque

import infrastructure.setup._bootstrap  # noqa: F401 — ROOT on sys.path
from infrastructure.setup.config import load_config
from tqdm import tqdm

from infrastructure.database.postgres import PgGraphAdapter

logger = logging.getLogger(__name__)


def _connected_components(
    entity_ids: set[int],
    relations: list[tuple[int, int, str]],
) -> list[set[int]]:
    """관계 그래프에서 연결 성분 계산. 무방향 그래프 BFS."""
    adj: dict[int, list[int]] = {eid: [] for eid in entity_ids}
    for h, t, _ in relations:
        if h in entity_ids and t in entity_ids:
            adj[h].append(t)
            adj[t].append(h)
    visited: set[int] = set()
    components: list[set[int]] = []
    for eid in entity_ids:
        if eid in visited:
            continue
        comp: set[int] = set()
        q: deque[int] = deque([eid])
        while q:
            u = q.popleft()
            if u in visited:
                continue
            visited.add(u)
            comp.add(u)
            for v in adj[u]:
                if v not in visited:
                    q.append(v)
        if comp:
            components.append(comp)
    return components


def _communities_by_source(
    entities: list[tuple[int, str, str, str | None]],
    relations: list[tuple[int, int, str]],
) -> list[set[int]]:
    """
    step3 스타 그래프(각 source -> benchmark part_of)에서 source별 커뮤니티 생성.
    커뮤니티 수 = source 엔티티 수 (benchmark는 각 커뮤니티에 포함).
    """
    entity_map = {e[0]: (e[1], e[2], e[3]) for e in entities}
    benchmark_ids = {eid for eid, (_, t, _) in entity_map.items() if t == "benchmark"}
    source_ids = [eid for eid, (_, t, _) in entity_map.items() if t == "source"]
    if not source_ids or not benchmark_ids:
        return []
    benchmark_id = next(iter(benchmark_ids))
    return [{sid, benchmark_id} for sid in source_ids]


def main() -> int:
    config = load_config("dev")
    if not config.postgres:
        logger.error("POSTGRES_ENABLED required. Check 프로젝트 루트 .env")
        return 1

    graph = PgGraphAdapter(connection_url=config.postgres.url)
    graph.ensure_communities_schema()

    entities, relations = graph.get_all_entities_and_relations()
    if not entities:
        logger.error("No graph_entities found. Run step3_build_rag.sh first.")
        return 1

    entity_map = {e[0]: (e[1], e[2], e[3]) for e in entities}
    entity_ids = set(entity_map.keys())

    by_source = _communities_by_source(entities, relations)
    if by_source:
        components = by_source
        logger.info("Found %d communities (one per source).", len(components))
    else:
        components = _connected_components(entity_ids, relations)
        logger.info("Found %d communities (connected components).", len(components))

    for i, comp in enumerate(tqdm(components, desc="Communities & reports", unit="community")):
        ids_list = sorted(comp)
        names_and_descs: list[str] = []
        for eid in ids_list:
            name, type_, desc = entity_map[eid]
            names_and_descs.append(f"- {name} ({type_})" + (f": {desc}" if desc else ""))
        primary_name = next((entity_map[eid][0] for eid in ids_list if entity_map[eid][1] == "source"), None) or f"Community_{i + 1}"
        name = primary_name if by_source else f"Community_{i + 1}"
        description = f"Entities: {', '.join(entity_map[eid][0] for eid in ids_list)}"
        report_content = "Community report:\n" + "\n".join(names_and_descs)

        cid = graph.insert_community(name=name, description=description, entity_ids=ids_list)
        graph.insert_report(community_id=cid, content=report_content, report_type="summary")

    logger.info("Graph communities & reports done: %d communities.", len(components))
    return 0


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    sys.exit(main())
