# 빠른 시작

API 키만 있으면 **Track 00–01**부터 바로 실행할 수 있습니다 (Postgres·Docker 불필요).

```bash
git clone https://github.com/LGAI-Research/EXAONE-Cookbook.git
cd EXAONE-Cookbook
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
pip install -e .
cp .env.example .env   # EXAONE_API_KEY, EXAONE_BASE_URL, EXAONE_MODEL
python -m ipykernel install --user --name exaone-cookbook --display-name "Python (exaone-cookbook)"
jupyter notebook recipes/track00_bootstrap/
```

Jupyter에서 커널은 **`Python (exaone-cookbook)`** 을 선택하세요.

## 환경 변수

| 변수 | 설명 |
| ---- | ---- |
| `EXAONE_API_KEY` | EXAONE 배포용 API 키 |
| `EXAONE_BASE_URL` | OpenAI 호환 base URL (`/v1`로 끝남) |
| `EXAONE_MODEL` | 엔드포인트의 모델 ID |

::: tip `.env` 하나, 줄 끝 주석 금지
비밀값·SSL·프록시 설정은 저장소 루트의 `.env` 한 파일에 모읍니다. `KEY=value` 줄 끝에 `# 주석`을 붙이지 마세요. 일부 편집기와 Jupyter가 주석까지 값으로 읽습니다.
:::

## 모든 노트북의 첫 셀

노트북은 `sys.path`를 손대지 않습니다. editable 설치 후에는 이것만 있으면 됩니다.

```python
import exaone

exaone.load_project_env()
ROOT = exaone.project_root()
```

## 설치 경로

| 용도 | 방법 | Python |
| ---- | ---- | ------ |
| 레시피·eval·exaone (기본) | `pip install -r requirements.txt` 후 `pip install -e .` | 3.12+ |
| Proof Gallery (선택) | `uv sync --project implementations/<repo>` | repo별 |
| 개발자 lockfile | 루트에서 `uv sync` | 3.12+ |

공식 OSS 경로는 CI와 동일한 `requirements.txt` + venv입니다. `pyproject.toml`·`uv.lock`은 maintainer용 재현 lockfile입니다.

## 프로젝트 구조

```
├── recipes/           # Track 00–10 노트북
├── exaone/            # LLM·에이전트·RAG 라이브러리
├── eval/              # 벤치마크 하니스
├── infrastructure/    # Postgres, 임베딩, setup 스크립트
├── implementations/   # Proof Gallery (선택)
└── docs/              # 저장소 문서
```

## K-EXAONE 2.0 thinking 플래그

| 워크로드 | `enable_thinking` | `preserve_thinking` |
| -------- | ----------------- | ------------------- |
| 잡담·단발 QA | `False` | `False` |
| Agentic 실행 (`ToolAgent`, Track 02+) | `True` | `True` |

효과는 2.0+에서 나타나며, 1.0에서는 payload에 실리되 무시됩니다. 자세한 내용: [`docs/k_exaone_2.md`](https://github.com/LGAI-Research/EXAONE-Cookbook/blob/main/docs/k_exaone_2.md).

## 트러블슈팅

| 증상 | 조치 |
| ---- | ---- |
| `EXAONE_API_KEY` 오류 또는 401 | `.env`의 키·base URL·모델 재확인 |
| 회사망에서 SSL 실패 | `REQUESTS_CA_BUNDLE` 설정 — [`PLAYBOOK.md`](https://github.com/LGAI-Research/EXAONE-Cookbook/blob/main/PLAYBOOK.md) Part 8 |
| MCP 서버 spawn 실패 | `pip install -r requirements.txt` 후 `python recipes/track03_tools_and_mcp/mcp_demo/server.py` 실행 |
| RAG connection refused | `infrastructure/setup` step 2–4 수행 |

::: warning Proof Gallery
`implementations/` upstream은 **포함되지 않습니다**. 직접 clone 하세요 — [implementations/README](https://github.com/LGAI-Research/EXAONE-Cookbook/blob/main/implementations/README.md).
:::

## 다음 단계

- [Track 00 — 부트스트랩](/ko/learn/track-00) 으로 설치 상태를 끝까지 검증합니다
- [Track 01 — EXAONE 기본기](/ko/learn/track-01) 에서 대화·JSON·도구·thinking 라우터를 다룹니다
- [에이전트 패턴](/ko/patterns/) 은 각 패턴을 구현 파일과 연결해 보여줍니다
