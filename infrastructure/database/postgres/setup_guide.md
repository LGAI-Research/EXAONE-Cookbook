# PostgreSQL + pgvector 설치 및 튜닝 가이드

RAG / Memory 인프라용 Production Reference Backend 설정 방법입니다.

## 1. 요구 사항

- PostgreSQL 15+ (권장 16)
- [pgvector](https://github.com/pgvector/pgvector) 확장

## 2. PostgreSQL에 pgvector 설치

### Ubuntu / Debian

```bash
sudo apt install postgresql-16-pgvector  # 버전은 PostgreSQL에 맞춤
```

### macOS (Homebrew)

```bash
brew install pgvector
# 확장은 PostgreSQL 공유 라이브러리 경로에 설치됨. 필요 시 pg_config --pkglibdir 확인
```

### 소스 빌드

```bash
git clone https://github.com/pgvector/pgvector.git
cd pgvector
make
make install
```

설치 후 PostgreSQL 재시작.

## 3. DB 및 확장 생성

```bash
psql -U postgres -c "CREATE DATABASE exaone;"
psql -U postgres -d exaone -c "CREATE EXTENSION IF NOT EXISTS vector;"
```

또는 `infrastructure/database/postgres/schema.sql` 전체 실행:

```bash
psql -U postgres -d exaone -f infrastructure/database/postgres/schema.sql
```

## 4. 환경 변수 / config 오버라이드

`exaone/config/dev.py` 또는 `production.py` 에서 다음을 설정:

- `POSTGRES_HOST`, `POSTGRES_PORT`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DBNAME`
- `POSTGRES_ENABLED = True`
- pgvector 테이블/차원: `PGVECTOR_TABLE_NAME`, `PGVECTOR_EMBEDDING_DIM`, `PGVECTOR_INDEX_TYPE`, `PGVECTOR_LISTS`

## 5. 인덱스 튜닝

### IVFFlat (기본)

- `lists`: 대략 `sqrt(행 수)` ~ `행 수 / 1000` 권장. 행이 10만 개면 100~300.
- 빌드: 데이터가 어느 정도 쌓인 뒤 인덱스 생성하는 것이 좋음 (빈 테이블에 만들면 효과 적음).

### HNSW (선택)

정확도 우선이면 HNSW 고려. `schema.sql` 주석 해제 후:

```sql
CREATE INDEX embeddings_hnsw_idx ON embeddings USING hnsw (embedding vector_cosine_ops);
```

메모리 사용과 인덱스 빌드 시간이 IVFFlat보다 큼.

## 6. 성능 참고

- 벡터 차원은 임베딩 모델과 일치 (예: OpenAI 1536).
- `work_mem`, `maintenance_work_mem` 늘리면 인덱스 빌드/큰 쿼리에 유리.
- RAG 검색 시 `LIMIT top_k` 로 작게 유지 (예: 5~20).

## 7. 참고 링크

- [pgvector GitHub](https://github.com/pgvector/pgvector)
- [Llama Cookbook RAG](https://github.com/meta-llama/llama-cookbook)
- [OpenAI Cookbook](https://cookbook.openai.com/)
