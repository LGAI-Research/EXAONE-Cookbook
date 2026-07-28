# 공통 셋업 (step1~4) — standalone

**infrastructure/setup** 독립 셋업입니다. DB·임베딩·RAG·그래프 구축에 필요한 스크립트와 설정을 모두 이 디렉터리에 두었습니다.

- **step1**: TEI 모델 캐시 + MS MARCO 데이터 다운로드 → `_temp/`, `_temp/ms_marco/`
- **step2**: Docker로 Postgres(pgvector) + embedding 서비스 기동
- **step3**: MS MARCO → pgvector + graph(엔티티/관계) 빌드 (`build_rag_from_ms_marco.py`). cookbook 기본은 `.env` 의 `STEP3_MAX_CONTEXTS=5000` (전체 ingest 는 `0` 또는 변수 제거). graph 단계 전 **spaCy NER**(`xx_ent_wiki_sm`) — `python -m infrastructure.ingestion.spacy_model` (step3 shell에서 자동).
- **step4**: graph communities·reports 생성 (`build_graph_communities.py`)

## 실행 방법

프로젝트 루트에서 **venv 활성화** 후 `.env` 설정:

```bash
source .venv/bin/activate    # step 스크립트는 python3(=venv) 기준으로 동작
cd infrastructure/setup
./step1_downloads.sh
./step2_docker.sh
./step3_build_rag.sh
./step4_build_graph.sh
```

각 step 스크립트는 루트 `.env` 를 읽어(export) docker compose·빌드에 반영합니다. 환경변수 상세는 루트 **.env** 참고.

## 트러블슈팅

### SSL 인증서 (회사망 / MITM 프록시)

step1(또는 step3)이 아래처럼 실패하면, HF 장애·레이트리밋이 아니라 **회사망 프록시가 자체 루트 CA 로 TLS 를 가로채는** 환경입니다:

```text
[SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed: self-signed certificate in certificate chain
```

> 이어서 나오는 `RuntimeError: Cannot send a request, as the client has been closed.` 는 부차 증상입니다(첫 SSL 실패 후 httpx 클라이언트가 닫혀 재시도가 헛돎). 원인은 인증서이며, CA 를 신뢰시키면 첫 시도에서 통과합니다.

#### 해결 (권장 — 검증 유지): 회사 루트 CA 를 신뢰 번들에 추가

macOS 는 MDM 이 설치한 회사 루트가 시스템 키체인에 있으므로, 시스템 신뢰 루트 + certifi 를 한 PEM 으로 추출합니다:

```bash
# (en) Export macOS trusted roots (incl. corporate MDM root) + certifi into one PEM bundle.
# (kr) macOS 신뢰 루트(회사 MDM 루트 포함) + certifi 를 한 PEM 번들로 추출.
security find-certificate -a -p /System/Library/Keychains/SystemRootCertificates.keychain >  ~/corp-ca-bundle.pem
security find-certificate -a -p /Library/Keychains/System.keychain                        >> ~/corp-ca-bundle.pem
python3 -c "import certifi; print(open(certifi.where()).read())"                           >> ~/corp-ca-bundle.pem
```

프로젝트 루트 `.env` 에 **절대 경로**로 추가합니다(값 줄에 trailing `# 주석` 금지 — dotenv 가 값으로 읽음):

```ini
REQUESTS_CA_BUNDLE=/absolute/path/to/corp-ca-bundle.pem
SSL_CERT_FILE=/absolute/path/to/corp-ca-bundle.pem
```

step1 이 `.env` 를 `set -a; source` 하므로 TEI·MS MARCO 다운로드·step3 빌드·노트북 HF 호출에 모두 적용됩니다. 확인:

```bash
python3 -c "import os, httpx; print(httpx.head('https://huggingface.co/datasets/microsoft/ms_marco/resolve/main/README.md', follow_redirects=True, timeout=30, verify=os.path.expanduser('~/corp-ca-bundle.pem')).status_code)"
# -> 200 이면 OK. 이후 ./step1_downloads.sh 재실행.
```

- **Linux:** 보통 `/etc/ssl/certs/ca-certificates.crt` 또는 IT 제공 PEM 을 가리키면 됩니다.
- **회사 루트 CA 갱신 시:** 위 `security find-certificate` 두 줄로 번들만 다시 만들면 됩니다.

#### 최후 수단 (권장 안 함 — 검증 끔): 신뢰망 일회성

```ini
DISABLE_SSL_VERIFY=1
```

`.env` 에 추가하면 `HF_HUB_DISABLE_SSL_VERIFICATION=1` 로 동기화되어 다운로드는 통과하지만 **TLS 검증이 꺼집니다**. 신뢰할 수 있는 사내망에서 일회성으로만 사용하세요.

### 호스트 포트 충돌
다른 Postgres·서비스가 이미 호스트 포트(기본 Postgres 5432 / embedding 8000)를 점유하면, `docker compose up` 이 bind 에 실패하거나 노트북이 엉뚱한 DB 에 붙어 `postgres_available: False` 가 됩니다.

→ `.env` 에서 **빈 포트로 바꾸되, 짝이 되는 두 변수를 같은 값**으로 설정합니다:

- `POSTGRES_HOST_PORT` (compose 가 노출하는 호스트 포트) 와 `POSTGRES_PORT` (앱·노트북이 연결하는 포트) — **반드시 일치** (예: 둘 다 `5433`). 컨테이너 내부 포트는 항상 5432 로 유지됩니다.
- embedding 도 충돌 시 `EMBEDDING_HOST_PORT` / `EMBEDDING_BASE_URL` 을 같은 원칙으로 맞춥니다.

확인: `docker compose ps` 의 호스트 포트 매핑, 노트북 preflight 의 `postgres_available: True`.

### `ModuleNotFoundError` (huggingface_hub / datasets / spacy 등)
step 스크립트가 `python3` 를 사용하므로 **venv 가 활성화돼 있어야** 합니다. 비활성 상태면 시스템 python 이 쓰여 위 에러가 납니다. `source .venv/bin/activate` 후 재실행하세요.

### 임베딩 모델 ↔ 차원 불일치
`EMBEDDING_MODEL` 을 바꾸면 `EMBEDDING_DIMENSIONS` 도 그 모델 차원에 맞춰야 합니다(기본 `multilingual-e5-small` = 384). 저장 차원과 `.env` 차원이 다르면 검색이 실패합니다.
