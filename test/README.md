# test/

`pytest`로 **exaone**, **infrastructure**, **eval**, **implementations glue** 를 검증합니다.

## 환경

| 대상 | `.env` |
|------|--------|
| `unit_exaone`, `unit_eval`, `unit_infrastructure` | 프로젝트 **루트** `.env` (`test/conftest.py`가 `setdefault` 로드) |
| `unit_implementations` | **`implementations/<repo>/.env`** — fixture·`EXAONE_IMPL_DIR` (루트 `.env` 와 분리) |

대부분의 unit test는 **API 키 없이** 통과합니다.

## 레이아웃

```
test/
├── conftest.py                     # REPO_ROOT path + 루트 .env
├── perf/                           # opt-in 벤치 (pytest 수집 제외)
│   └── tool_agent_microbench.py
├── unit_exaone/                    # exaone 패키지
│   └── test_thinking_router_hints.py
├── unit_eval/                      # eval metrics, runners, report, datasets
│   ├── metrics/
│   ├── runners/
│   │   ├── test_tau_bench_litellm.py
│   │   └── test_tau_bench_runner.py
│   ├── judges/
│   ├── datasets/                   # schema (PR fast suite)
│   ├── datasets_smoke/             # HF / τ-bench loader smoke (main push only)
│   └── test_checkpoint.py
├── unit_infrastructure/            # setup, ingestion (@integration)
└── unit_implementations/           # implementations/ glue (per-repo .env)
    ├── conftest.py
    ├── test_exaone_env.py
    ├── test_glue_layout.py
    ├── test_uv_run.py
    ├── test_check_env_smoke.py
    └── test_nanoclaw_glue.py
```

`test/unit_eval/datasets/` — 스키마는 PR fast suite에 포함. HF/τ-bench 스모크는 `datasets_smoke/` (main push CI). 상세: `eval/datasets/README.md`.

## 실행

설정 정본: 루트 [`pytest.ini`](../pytest.ini)

```bash
# PR / 로컬 기본 (CI와 동일, integration 제외)
pytest test/unit_exaone test/unit_eval test/unit_infrastructure test/unit_implementations \
  --ignore=test/unit_eval/datasets_smoke \
  -m "not integration and not eval_datasets" -q

# Postgres 등 필요 시
pytest test/unit_infrastructure -m integration

# Opt-in micro-benchmark (not pytest)
python test/perf/tool_agent_microbench.py
```

CI: [`.github/workflows/ci.yml`](../.github/workflows/ci.yml)

| Job | When | What |
|-----|------|------|
| `unit-tests` | PR + push | `unit_*` fast suite (`-m "not integration and not eval_datasets"`) |
| `eval-datasets` | **main/master push only** | `test/unit_eval/datasets/` + `datasets_smoke/` |

## 참고

- 예전 `reference_implementations/` 패키지는 **삭제**되었습니다. 동일 주제는 `recipes/trackNN_*` 노트북을 사용하세요.
