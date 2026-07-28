# eval/datasets/ — 외부 벤치마크 로더

`eval/README.md` 3.3절에서 정의한 4개 외부 벤치마크를
**단일 스키마(`EvalTask`)** 로 정규화해 `eval/runners/`, `eval/metrics/`, `eval/judges/`에 전달하는 모듈 모음입니다.

모든 로더는 provider 비의존(`exaone/` 의존 없음)이며 순수 파이썬으로 동작합니다.

---

## 1. 설치 (의존성)

이 폴더가 필요로 하는 외부 패키지는 두 가지입니다. **루트 `pyproject.toml`에 이미 둘 다 선언되어 있으므로** 보통 추가 설치는 필요 없습니다.

```bash
# 루트 lock에 둘 다 들어있음 — `uv sync` 만으로 충분
uv sync

# venv 만 살아있고 datasets / huggingface_hub 가 없는 경우의 미니 설치
pip install datasets huggingface_hub

# τ-bench (optional — retail / airline simulation)
uv pip install '.[eval-taubench]'
```

HuggingFace 익명 호출은 rate-limit 경고가 뜰 수 있습니다(태스크 진행에는 영향 없음). 토큰을 가지고 있다면:

```bash
export HF_TOKEN=hf_xxx
```

---

## 2. 공통 사용법

```python
from eval.datasets import load_dataset, available_datasets

available_datasets()
# ['bfcl_v3', 'bfcl_v3.irrelevance', 'bfcl_v3.multiple', 'bfcl_v3.parallel',
#  'bfcl_v3.simple', 'halubench', 'ifeval',
#  'tau_bench', 'tau_bench.airline', 'tau_bench.retail']

tasks = load_dataset("bfcl_v3.simple", limit=5)
# -> list[EvalTask]  (eval/datasets/schema.py)
```

`EvalTask` 필드 정의는 [`schema.py`](./schema.py) 참조. 모든 로더가 동일 스키마를 채워줍니다.

---

## 3. 데이터셋별 한 줄 스니펫

### BFCL v3 (M3, M4, M5, M6)

```python
from eval.datasets import load_dataset

simple      = load_dataset("bfcl_v3.simple",      limit=5)
multiple    = load_dataset("bfcl_v3.multiple",    limit=5)
parallel    = load_dataset("bfcl_v3.parallel",    limit=5)
irrelevance = load_dataset("bfcl_v3.irrelevance", limit=5)
```

- `expected_tool_calls` — `simple/multiple/parallel`은 채워지고 `irrelevance`는 `None`.
- `expected_no_tools` — `irrelevance`만 `True`.
- `metadata["bfcl_ground_truth"]` — BFCL 원본 possible_answer(인자별 허용값 리스트)를 보존.
  M4 argument F1 metric은 이 필드의 any-of 매칭을 사용해야 합니다.
- BFCL의 ``"type": "dict"`` 는 ``"type": "object"``로 정규화되어 ``tools[*].parameters``가 JSON Schema 호환 형태입니다(중첩 타입은 보존).

### τ-bench (M1, M2, M3, M4, M7, M8)

```python
# optional: uv pip install '.[eval-taubench]'
tasks = load_dataset("tau_bench.retail", limit=5)
tasks[0].metadata["tau_bench"]   # domain, task_index, user_strategy, ...
tasks[0].expected_answer         # 1 (reward target)
tasks[0].expected_tool_calls     # gold tool trajectory (no respond)
```

시뮬레이션 실행은 `eval.runners.tau_bench_runner`가 담당합니다(`python -m eval.run --dataset tau_bench.retail`).
User simulator는 LiteLLM으로 같은 EXAONE/Friendli 엔드포인트를 사용합니다.

### IFEval (M6)

```python
tasks = load_dataset("ifeval", limit=5)
tasks[0].metadata["ifeval_instructions"]
# [{"id": "punctuation:no_comma", "kwargs": {}},
#  {"id": "detectable_format:number_highlighted_sections", "kwargs": {"num_highlights": 3}},
#  ...]
```

각 프롬프트의 verifiable instruction 리스트(`id`, `kwargs`)가 `metadata["ifeval_instructions"]`에 들어갑니다.
M6 strict/loose 채점기가 그대로 사용합니다. IFEval은 free-form 텍스트 응답이므로 `json_schema=None`, `required_keys=None` 입니다.

### HaluBench (M9)

```python
tasks = load_dataset("halubench", limit=5)
t = tasks[0]
t.grounding_context   # 근거 passage
t.query               # 사용자 질문
t.expected_answer     # {"answer": "...", "label": "PASS"|"FAIL"}
```

`category` 필드에는 HaluBench의 `source_ds`(DROP, PubMedQA 등)가 들어갑니다.

---

## 4. 관찰된 row 수

| 데이터셋 | row 수 | 비고 |
|----------|--------|------|
| `bfcl_v3.simple`      | 400    | possible_answer 파일 포함 |
| `bfcl_v3.multiple`    | 200    | possible_answer 파일 포함 |
| `bfcl_v3.parallel`    | 200    | possible_answer 파일 포함 |
| `bfcl_v3.irrelevance` | 240    | possible_answer 없음 (정답 = no-call) |
| `ifeval`              | 541    | 단일 `train` split |
| `halubench`           | 14,900 | 단일 `test` split |
| `tau_bench.retail`    | 115    | `test` split |
| `tau_bench.airline`   | 50     | `test` split |

(2026-05-28 기준 다운로드 수치. 업스트림에서 row가 추가/삭제되면 변동될 수 있음.)

---

## 5. 라이선스 & 출처

| 데이터셋 | 라이선스 | 출처 |
|----------|----------|------|
| BFCL v3 | Apache 2.0 | <https://huggingface.co/datasets/gorilla-llm/Berkeley-Function-Calling-Leaderboard> · <https://gorilla.cs.berkeley.edu/leaderboard.html> |
| τ-bench | MIT | <https://github.com/sierra-research/tau-bench> · <https://arxiv.org/abs/2406.12045> |
| IFEval | Apache 2.0 | <https://huggingface.co/datasets/google/IFEval> · <https://arxiv.org/abs/2311.07911> |
| HaluBench | CDLA-Permissive-2.0 | <https://huggingface.co/datasets/PatronusAI/HaluBench> |

> 라이선스 표기는 업스트림 데이터 카드 기준 인용입니다 — 상업적 활용 전 각 원본 LICENSE를 직접 확인하세요.

---

## 6. 로컬 캐시 (`_dataset/`)

다운로드한 벤치마크 파일은 **레포 루트 `_dataset/`** 에 저장됩니다(gitignore). 사용자 홈의 `~/.cache/huggingface`를 쓰지 않습니다.

```
_dataset/                 # gitignored — first load_dataset() or eval.run 시 생성
├── hub/                  # BFCL JSONL (huggingface_hub)
└── hf_datasets/          # IFEval, HaluBench (datasets)
```

τ-bench는 설치된 `tau_bench` 패키지 데이터를 쓰며 `_dataset/`에 별도 저장하지 않습니다.

루트를 바꾸려면 `.env`에 `EVAL_DATASETS_DIR=/path/to/cache`를 설정하세요(선택). 개별 `HF_HUB_CACHE` / `HF_DATASETS_CACHE`가 이미 있으면 그 값이 우선합니다(`setdefault`).

---

## 7. 네트워크 정책 & 오프라인 동작

- 로더는 모두 **lazy / streaming** — 사용 시점에만 HuggingFace에서 다운로드합니다.
- `EVAL_DATASETS_FORCE_OFFLINE=1` 환경 변수로 강제 오프라인 모드 진입(테스트용).
- 테스트는 `eval.datasets._net.is_online()`을 통한 `pytest.mark.skipif`로 가드 — 네트워크 없는 CI에서도 깔끔하게 skip 됩니다.

```bash
# (en) Offline — schema only; online HF tests skip via is_online().
# (kr) 오프라인 — 스키마만 실행; HF 온라인 테스트는 is_online()으로 skip.
EVAL_DATASETS_FORCE_OFFLINE=1 python -m pytest test/unit_eval/datasets/ -v

# (en) Online — HF download smoke (main CI or local with network).
# (kr) 온라인 — HF 다운로드 스모크 (main CI 또는 로컬 네트워크).
python -m pytest test/unit_eval/datasets_smoke/ -v

# (en) Full datasets suite (schema + smoke when online / tau-bench installed).
# (kr) datasets 전체 (스키마 + 온라인/τ-bench 설치 시 스모크).
python -m pytest test/unit_eval/datasets/ test/unit_eval/datasets_smoke/ -v
```

---

## 8. 코드 트리

```
eval/datasets/
├── README.md          # (this file)
├── __init__.py        # load_dataset() registry + re-exports
├── _cache.py          # repo-local _dataset/ paths
├── _net.py            # is_online() helper for skip guards
├── schema.py          # EvalTask / ExpectedToolCall / ToolSpec
├── bfcl_v3.py         # BFCL v3 (simple/multiple/parallel/irrelevance)
├── tau_bench.py       # τ-bench retail/airline → EvalTask (+ tau_bench_runner)
├── ifeval.py          # google/IFEval loader
└── halubench.py       # PatronusAI/HaluBench loader
```
