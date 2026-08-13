# Recipes (Track 00–10)

Jupyter 노트북으로 EXAONE 에이전트를 단계별로 학습합니다. **정본 로드맵**은 이 디렉터리의 트랙 README 와 각 `trackNN_*_lab.ipynb` 입니다.

---

## 한 번만 설치 (저장소 루트)

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
pip install -e ./exaone
cp .env.example .env
python -m ipykernel install --user --name exaone-cookbook --display-name "Python (exaone-cookbook)"
```

Jupyter 에서 커널 **`Python (exaone-cookbook)`** (또는 `.venv/bin/python` 경로)을 선택하세요.

---

## 모든 노트북 공통 첫 셀

`sys.path` 로 루트를 찾지 않습니다. **editable 설치** 후 아래만 씁니다.

```python
import exaone

exaone.load_project_env()
ROOT = exaone.project_root()
```

- 비밀값·SSL·프록시: 저장소 루트 **`.env`** 한 파일 ([`PLAYBOOK.md`](../PLAYBOOK.md) Part 8).
- `.env` 에서 `KEY=value` **줄 끝에 `# 주석` 금지** — IDE/Jupyter 가 주석까지 값으로 읽을 수 있습니다.
- 트랙 데이터 경로: `ROOT / "recipes" / "trackNN_..."` (각 노트북의 `TRACKnn` 변수).

`from exaone.llm import ...` 처럼 서브모듈 직접 import 는 쓰지 않고, `import exaone` 뒤 점(`.`) 접근만 사용합니다.

**K-EXAONE 2.0 API:** chitchat·단발 QA는 `enable_thinking=False`, `preserve_thinking=False`. agentic(`ToolAgent`·Track 02+)은 둘 다 `True` — **효과**는 2.0+, 1.0 payload에는 실리지만 무시됩니다. → [`docs/k_exaone_2.md`](../docs/k_exaone_2.md)

---

## 트랙 목록

| Track | 디렉터리 | 시작 노트북 |
|-------|----------|-------------|
| 00 | [`track00_bootstrap/`](track00_bootstrap/) | [`00_bootstrap_lab.ipynb`](track00_bootstrap/00_bootstrap_lab.ipynb) |
| 01 | [`track01_exaone_foundation/`](track01_exaone_foundation/) | [`01_exaone_foundation_lab.ipynb`](track01_exaone_foundation/01_exaone_foundation_lab.ipynb) |
| 02–10 | `track02_*` … `track10_*` | 각 폴더의 `*_lab.ipynb` 또는 캡스톤 `10_0x_*.ipynb` |

상세 목표·체크포인트: 각 트랙 `README.md` · 루트 [`README.md`](../README.md).
