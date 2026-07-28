"""
관계 테이블 기반 그래프 검색 구현 (GraphRAG 스타일).
엔티티·관계 저장 후 텍스트/엔티티로 검색. exaone.retrieval.GraphRetrievalStrategy 에 query_fn 제공.
"""
from __future__ import annotations

import logging
import re
from contextlib import contextmanager
from typing import Any

try:
    import psycopg
except ImportError:
    psycopg = None

logger = logging.getLogger(__name__)

try:
    from kiwipiepy import Kiwi
except ImportError:
    Kiwi = None

try:
    from nltk.tokenize import wordpunct_tokenize
except ImportError:
    wordpunct_tokenize = None


class PgGraphAdapter:
    """PostgreSQL 테이블로 엔티티·관계·커뮤니티·리포트 저장 및 검색."""

    def __init__(
        self,
        connection_url: str,
        entities_table: str = "graph_entities",
        relations_table: str = "graph_relations",
        communities_table: str = "graph_communities",
        reports_table: str = "graph_reports",
        create_if_missing: bool = True,
    ):
        if psycopg is None:
            raise ImportError("psycopg 필요: pip install 'psycopg[binary]'")
        self.connection_url = connection_url
        self.entities_table = entities_table
        self.relations_table = relations_table
        self.communities_table = communities_table
        self.reports_table = reports_table
        self._create_if_missing = create_if_missing
        self._connection = None

    def _get_connection(self, force_reconnect: bool = False):
        if force_reconnect and self._connection is not None:
            try:
                self._connection.close()
            except Exception:
                pass
            self._connection = None
        if self._connection is None or getattr(self._connection, "closed", False):
            self._connection = psycopg.connect(self.connection_url)
        return self._connection

    @contextmanager
    def _conn(self):
        conn = self._get_connection()
        try:
            yield conn
        except Exception as exc:
            logger.debug("graph query failed, resetting connection: %s", exc)
            try:
                conn.rollback()
            except Exception:
                pass
            self._get_connection(force_reconnect=True)
            raise

    def ensure_schema(self) -> None:
        """엔티티·관계 테이블 생성."""
        with self._conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    f"""
                    CREATE TABLE IF NOT EXISTS {self.entities_table} (
                        id BIGSERIAL PRIMARY KEY,
                        name TEXT NOT NULL,
                        type TEXT NOT NULL DEFAULT 'entity',
                        description TEXT,
                        metadata JSONB DEFAULT '{{}}',
                        UNIQUE(name, type)
                    );
                    """
                )
                cur.execute(
                    f"""
                    CREATE TABLE IF NOT EXISTS {self.relations_table} (
                        id BIGSERIAL PRIMARY KEY,
                        head_id BIGINT NOT NULL REFERENCES {self.entities_table}(id),
                        tail_id BIGINT NOT NULL REFERENCES {self.entities_table}(id),
                        relation_type TEXT NOT NULL,
                        payload JSONB DEFAULT '{{}}'
                    );
                    """
                )
                cur.execute(f"CREATE INDEX IF NOT EXISTS idx_{self.entities_table}_name ON {self.entities_table}(name);")
                cur.execute(f"CREATE INDEX IF NOT EXISTS idx_{self.relations_table}_head ON {self.relations_table}(head_id);")
                conn.commit()

    def ensure_communities_schema(self) -> None:
        """graph_communities, graph_reports 테이블 생성 (step4 빌드용)."""
        self.ensure_schema()
        with self._conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    f"""
                    CREATE TABLE IF NOT EXISTS {self.communities_table} (
                        id BIGSERIAL PRIMARY KEY,
                        name TEXT NOT NULL,
                        description TEXT,
                        entity_ids JSONB NOT NULL DEFAULT '[]',
                        metadata JSONB DEFAULT '{{}}'
                    );
                    """
                )
                cur.execute(
                    f"""
                    CREATE TABLE IF NOT EXISTS {self.reports_table} (
                        id BIGSERIAL PRIMARY KEY,
                        community_id BIGINT NOT NULL REFERENCES {self.communities_table}(id) ON DELETE CASCADE,
                        content TEXT NOT NULL,
                        report_type TEXT NOT NULL DEFAULT 'summary'
                    );
                    """
                )
                cur.execute(f"CREATE INDEX IF NOT EXISTS idx_graph_reports_community ON {self.reports_table}(community_id);")
                conn.commit()

    def get_all_entities_and_relations(
        self,
    ) -> tuple[list[tuple[int, str, str, str | None]], list[tuple[int, int, str]]]:
        """엔티티 목록 (id, name, type, description), 관계 목록 (head_id, tail_id, relation_type) 반환. 커뮤니티 검출용."""
        with self._conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    f"SELECT id, name, type, description FROM {self.entities_table};"
                )
                entities = [tuple(r) for r in cur.fetchall()]
                cur.execute(
                    f"SELECT head_id, tail_id, relation_type FROM {self.relations_table};"
                )
                relations = [tuple(r) for r in cur.fetchall()]
        return entities, relations

    def insert_community(
        self,
        name: str,
        description: str | None = None,
        entity_ids: list[int] | None = None,
    ) -> int:
        """커뮤니티 한 건 삽입. entity_ids는 JSONB 배열로 저장."""
        import json
        ids_json = json.dumps(entity_ids or [])
        with self._conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    f"""
                    INSERT INTO {self.communities_table} (name, description, entity_ids)
                    VALUES (%s, %s, %s::jsonb)
                    RETURNING id;
                    """,
                    (name, description, ids_json),
                )
                row = cur.fetchone()
                conn.commit()
                return row[0] if row else 0

    def insert_report(self, community_id: int, content: str, report_type: str = "summary") -> int:
        """리포트 한 건 삽입."""
        with self._conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    f"""
                    INSERT INTO {self.reports_table} (community_id, content, report_type)
                    VALUES (%s, %s, %s)
                    RETURNING id;
                    """,
                    (community_id, content, report_type),
                )
                row = cur.fetchone()
                conn.commit()
                return row[0] if row else 0

    def upsert_entity(self, name: str, type_: str | None = None, description: str | None = None) -> int:
        """엔티티 삽입 또는 기존 id 반환."""
        if self._create_if_missing:
            self.ensure_schema()
        with self._conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    f"""
                    INSERT INTO {self.entities_table} (name, type, description)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (name, type) DO UPDATE SET description = EXCLUDED.description
                    RETURNING id;
                    """,
                    (name, type_ or "entity", description),
                )
                row = cur.fetchone()
                conn.commit()
                return row[0] if row else 0

    def insert_relation(self, head_id: int, tail_id: int, relation_type: str) -> int:
        """관계 한 건 삽입."""
        with self._conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    f"""
                    INSERT INTO {self.relations_table} (head_id, tail_id, relation_type)
                    VALUES (%s, %s, %s)
                    RETURNING id;
                    """,
                    (head_id, tail_id, relation_type),
                )
                row = cur.fetchone()
                conn.commit()
                return row[0] if row else 0

    # ---- Bulk / batch variants --------------------------------------------
    # 개별 `upsert_entity`·`insert_relation` 은 매 호출마다 commit 하므로 청크 단위
    # 루프에서 수만 건 인서트 시 매우 느림. MS MARCO 청크 대량 순회를 하며 엔티티
    # 추출 + 저장할 때 **메모리에 누적 후 한 번에 배치 인서트** 하도록 대체 경로.
    # VALUES (..), (..), ... 식 multi-row INSERT 를 기본 500 행씩 청크로 전송.

    def upsert_entities_batch(
        self,
        entities: list[tuple[str, str, str | None]],
        batch_size: int = 500,
    ) -> dict[tuple[str, str], int]:
        """대량 엔티티 upsert. `(name, type, description)` 튜플 리스트 입력.
        반환: `{(name, type): id}` 매핑. 후속 관계 삽입에 사용.
        ON CONFLICT(name, type) DO UPDATE description — 기존 설명을 새 값으로 대체
        (None 전달 시 기존 값 유지)."""
        if self._create_if_missing:
            self.ensure_schema()
        if not entities:
            return {}

        result: dict[tuple[str, str], int] = {}
        with self._conn() as conn:
            with conn.cursor() as cur:
                for i in range(0, len(entities), batch_size):
                    chunk = entities[i : i + batch_size]
                    values_sql = ",".join(["(%s, %s, %s)"] * len(chunk))
                    flat: list[Any] = []
                    for name, type_, desc in chunk:
                        flat.extend([name, type_ or "entity", desc])
                    cur.execute(
                        f"""
                        INSERT INTO {self.entities_table} (name, type, description)
                        VALUES {values_sql}
                        ON CONFLICT (name, type) DO UPDATE
                            SET description = COALESCE(EXCLUDED.description, {self.entities_table}.description)
                        RETURNING id, name, type;
                        """,
                        flat,
                    )
                    for row in cur.fetchall():
                        result[(row[1], row[2])] = row[0]
            conn.commit()
        return result

    def insert_relations_batch(
        self,
        relations: list[tuple[int, int, str]],
        batch_size: int = 1000,
    ) -> int:
        """대량 관계 insert. `(head_id, tail_id, relation_type)` 튜플 리스트.
        중복 체크·제약 없음 (동일 쌍 여러 번 허용)."""
        if not relations:
            return 0
        count = 0
        with self._conn() as conn:
            with conn.cursor() as cur:
                for i in range(0, len(relations), batch_size):
                    chunk = relations[i : i + batch_size]
                    values_sql = ",".join(["(%s, %s, %s)"] * len(chunk))
                    flat: list[Any] = []
                    for h, t, r in chunk:
                        flat.extend([h, t, r])
                    cur.execute(
                        f"""
                        INSERT INTO {self.relations_table} (head_id, tail_id, relation_type)
                        VALUES {values_sql};
                        """,
                        flat,
                    )
                    count += len(chunk)
            conn.commit()
        return count

    def truncate_graph(self) -> None:
        """build 재실행 시 중복 누적 방지용. graph_entities·relations 를 비움.
        communities/reports 는 entities FK CASCADE 로 같이 제거."""
        with self._conn() as conn:
            with conn.cursor() as cur:
                cur.execute(f"TRUNCATE {self.entities_table} CASCADE;")
            conn.commit()

    @staticmethod
    def _extract_search_terms(query: str) -> list[str]:
        """쿼리에서 검색용 핵심 단어/구문 추출 (한국어+영어 하이브리드)."""
        terms: list[str] = []

        # 1) 따옴표 안 구문 (정확 매칭용)
        quoted = re.findall(r'["\']([^"\']{2,})["\']', query)
        terms.extend(quoted)

        # 2) 영문: NLTK 토큰 기반 추출 + 기존 약어/Title-case 패턴 보강
        en_stop = {
            "what", "where", "when", "which", "how", "who", "why",
            "does", "did", "was", "are", "has", "have", "been",
            "the", "this", "that", "these", "those", "can", "could",
            "is", "a", "an", "of", "in", "to", "for", "and", "or",
        }
        if wordpunct_tokenize is not None:
            en_tokens = [t for t in wordpunct_tokenize(query) if re.fullmatch(r"[A-Za-z][A-Za-z0-9_]{1,}", t)]
            terms.extend([t for t in en_tokens if t.lower() not in en_stop])

        acronyms = re.findall(r"\b([A-Z][A-Z0-9_]{1,})\b", query)
        phrases = re.findall(r"\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)\b", query)
        singles = [w for w in re.findall(r"\b([A-Z][a-z]{2,})\b", query) if w.lower() not in en_stop]
        terms.extend(acronyms + phrases + singles)

        # 3) 한국어: Kiwi 형태소 기반 명사/고유명사/영문명사 추출
        ko_particles = {"은", "는", "이", "가", "을", "를", "의", "에", "와", "과",
                        "로", "으로", "에서", "까지", "부터", "이란", "란",
                        "에게", "한테", "께서", "도", "만", "뿐", "하고", "이고"}
        ko_stop = {"에서", "대해", "대한", "통해", "위해", "관해", "있는", "없는",
                   "하는", "되는", "알려", "알려줘", "설명", "무엇"}
        if Kiwi is not None:
            kiwi = Kiwi()
            for token in kiwi.tokenize(query):
                if token.tag in {"NNG", "NNP", "SL"}:
                    word = token.form.strip()
                    if len(word) >= 2 and word not in ko_stop:
                        terms.append(word)
        else:
            ko_words = re.findall(r"[\uac00-\ud7a3]{2,}", query)
            for w in ko_words:
                if w in ko_stop:
                    continue
                stripped = w
                for p in sorted(ko_particles, key=len, reverse=True):
                    if w.endswith(p) and len(w) > len(p):
                        stripped = w[: -len(p)]
                        break
                if len(stripped) >= 2:
                    terms.append(stripped)
                if stripped != w and len(w) >= 2:
                    terms.append(w)

        # 4) Fallback: 영문 긴 단어
        if not terms:
            stop = {
                "what", "is", "the", "a", "an", "of", "in", "to", "for",
                "and", "or", "how", "who", "where", "when", "which",
                "does", "did", "was", "are", "has", "have", "been",
            }
            words = [
                w for w in re.findall(r"\b\w{3,}\b", query.lower())
                if w not in stop
            ]
            terms.extend(words[:3])

        # 중복 제거, 순서 유지
        return list(dict.fromkeys(terms))[:8]

    def query_by_entity(self, query: str, top_k: int = 5) -> list[dict[str, Any]]:
        """엔티티 이름/설명으로 검색해 관련 텍스트(설명+관계 요약) 반환. GraphRetrievalStrategy.query_fn 형식."""
        if self._create_if_missing:
            self.ensure_schema()

        terms = self._extract_search_terms(query)
        if not terms:
            return []

        # Build OR conditions for each search term
        conditions = []
        params: list[Any] = []
        for term in terms:
            conditions.append("(e.name ILIKE %s OR e.description ILIKE %s)")
            params.extend([f"%{term}%", f"%{term}%"])
        where_clause = " OR ".join(conditions)
        params.append(top_k)

        with self._conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    f"""
                    SELECT e.id, e.name, e.type, e.description,
                           (
                             SELECT string_agg(rel.rel_text, ' | ')
                             FROM (
                               SELECT r.relation_type || ' -> ' || e2.name AS rel_text
                               FROM {self.relations_table} r
                               JOIN {self.entities_table} e2 ON e2.id = r.tail_id
                               WHERE r.head_id = e.id
                               LIMIT 5
                             ) rel
                           ) AS relations
                    FROM {self.entities_table} e
                    WHERE {where_clause}
                    LIMIT %s;
                    """,
                    params,
                )
                rows = cur.fetchall()
        return [
            {
                "text": _format_entity_row(r),
                "content": _format_entity_row(r),
                "score": _compute_keyword_score(query, r),
                "metadata": {"entity_id": r[0], "name": r[1], "type": r[2], "source": "entity"},
            }
            for i, r in enumerate(rows)
        ]

    def query_communities(self, query: str, top_k: int = 3) -> list[dict[str, Any]]:
        """커뮤니티 리포트에서 키워드 검색. 엔티티 검색을 보완하는 high-level 컨텍스트."""
        terms = self._extract_search_terms(query)
        if not terms:
            return []

        conditions = []
        params: list[Any] = []
        for term in terms:
            conditions.append("(r.content ILIKE %s OR c.description ILIKE %s)")
            params.extend([f"%{term}%", f"%{term}%"])
        where_clause = " OR ".join(conditions)
        params.append(top_k)

        try:
            with self._conn() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        f"""
                        SELECT c.id, c.name, c.description, r.content
                        FROM {self.reports_table} r
                        JOIN {self.communities_table} c ON c.id = r.community_id
                        WHERE {where_clause}
                        LIMIT %s;
                        """,
                        params,
                    )
                    rows = cur.fetchall()
        except Exception:
            return []

        return [
            {
                "text": f"Community: {r[1]}\n{r[3]}",
                "content": f"Community: {r[1]}\n{r[3]}",
                "score": _compute_keyword_score(query, (r[0], r[1], "community", r[2], None)),
                "metadata": {"community_id": r[0], "name": r[1], "source": "community"},
            }
            for r in rows
        ]

    def query_combined(self, query: str, top_k: int = 5) -> list[dict[str, Any]]:
        """엔티티 검색 + 커뮤니티 리포트 검색을 합쳐서 반환."""
        entity_hits = self.query_by_entity(query, top_k=top_k)
        community_hits = self.query_communities(query, top_k=max(2, top_k // 2))

        combined = entity_hits + community_hits
        combined.sort(key=lambda x: x.get("score", 0.0), reverse=True)

        # 중복 제거 (같은 텍스트)
        seen: set[str] = set()
        deduped: list[dict[str, Any]] = []
        for h in combined:
            text = h.get("text", "")[:200]
            if text not in seen:
                seen.add(text)
                deduped.append(h)
        return deduped[:top_k]

    def query_fn_for_exaone(self, top_k_default: int = 5):
        """exaone.retrieval.GraphRetrievalStrategy 의 query_fn 에 넣을 콜백."""
        def fn(query: str, top_k: int = top_k_default) -> list[dict[str, Any]]:
            return self.query_combined(query, top_k=top_k)
        return fn

    def close(self) -> None:
        if self._connection is not None and not getattr(self._connection, "closed", True):
            self._connection.close()

    def __del__(self):
        try:
            self.close()
        except Exception:
            pass


def _compute_keyword_score(query: str, row: tuple) -> float:
    """쿼리와 엔티티의 키워드 매칭 정도로 0~1 사이 스코어 계산."""
    query_lower = query.lower()
    name = (row[1] or "").lower()
    desc = (row[3] or "").lower()
    target = f"{name} {desc}"

    # 이름이 쿼리에 정확히 포함되면 높은 스코어
    if name and name in query_lower:
        return 0.95
    if name and query_lower in name:
        return 0.90

    # 단어 겹침 비율
    import re
    query_words = set(re.findall(r"\w{2,}", query_lower))
    target_words = set(re.findall(r"\w{2,}", target))
    if not query_words:
        return 0.1
    overlap = len(query_words & target_words)
    return min(0.85, 0.3 + 0.15 * overlap)


def _format_entity_row(r: tuple) -> str:
    id_, name, type_, desc, relations = r[0], r[1], r[2], r[3], r[4]
    parts = [f"Entity: {name} ({type_ or 'entity'})"]
    if desc:
        parts.append(desc)
    if relations:
        parts.append(f"Relations: {relations}")
    return "\n".join(parts)
