# `infrastructure/` — DB·임베딩·RAG/그래프 빌드

**여기는 어떤 곳인가요?**  
**Postgres(pgvector)**, **임베딩 HTTP 서비스**, **데이터 인제스트/그래프** 등, “로컬·스테이징에서 RAG를 돌리기 위한” 인프라 코드와 셸 스크립트가 모여 있습니다. [`recipes/track04_rag_and_knowledge/`](../recipes/track04_rag_and_knowledge/)는 이 구성을 **전제**로 합니다.

---

## 이럴 때 이 폴더를 열어보세요

- 벡터 검색·그래프 검색을 **쓰기 전에** DB와 임베딩을 띄워야 할 때  
- `infrastructure/setup`의 **step1~4**로 데이터와 인덱스를 만들고 싶을 때  
- `Embedder`나 `vector_adapter` / `graph_adapter`를 **직접 코드**에서 쓰고 싶을 때

---

## 디렉터리를 넓은 나무로 이해하기

| 경로 | 설명 |
|------|------|
| `infrastructure/setup/` | **step1~4** 셸 스크립트, `docker-compose`, RAG/그래프 빌드 Python, MS MARCO 다운로드 등 |
| `infrastructure/setup/README.md` | step 요약(다운로드 → Docker → RAG → 그래프) — **가장 먼저** 읽기 좋습니다 |
| `infrastructure/embedding/` | 임베딩 **FastAPI** 앱, Docker 이미지, `Embedder` 클라이언트 |
| `infrastructure/database/postgres/` | **pgvector** / 그래프용 **어댑터**·스키마 |
| `infrastructure/ingestion/` | 엔티티 추출 등 인제스트 보조 |

---

## 대표 워크플로 (요약)

프로젝트 루트 `.env`를 맞춘 뒤, 보통은:

```bash
cd infrastructure/setup
./step1_downloads.sh   # 캐시·데이터
./step2_docker.sh      # Postgres + 임베딩
./step3_build_rag.sh   # 벡터(및 그래프 관련) 빌드
./step4_build_graph.sh # 그래프 커뮤니티 등(스크립트에 따름)
```

상세·환경 변수는 `setup/README.md`와 루트 **`.env.example`**, [PLAYBOOK.md](../PLAYBOOK.md)의 인프라·보안 절을 함께 봐 주세요. **회사망/프록시/SSL** 이슈는 `.env.example`의 **SSL / TLS** 블록과 PLAYBOOK을 함께 보세요.

---

## 막히면

- **컨테이너가 안 뜸** → Docker 데스크톱/권한, 포트 충돌(5432 등)  
- **임베딩 503/빈 응답** → `EMBEDDING_BASE_URL`, 배치/동시성, 프록시·CA 번들  
- **검색 0건** → step3·스키마·테이블명·임베딩 차원이 `.env`와 일치하는지  

한 번에 다 안 돼도 괜찮습니다. **step2만으로 DB·임베딩이 살아 있는지** 먼저 확인하고, RAG/그래프는 그다음에 붙이면 부담이 훨씬 적습니다.
