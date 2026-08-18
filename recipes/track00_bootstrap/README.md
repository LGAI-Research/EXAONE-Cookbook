# Track 00 — 부트스트랩 & 저장소 둘러보기

> [LG AI Research](https://www.lgresearch.ai/) **EXAONE Cookbook** — 환경을 준비하고 EXAONE 첫 호출을 해봅니다.
> Agent Learning Hub 매핑: **Stage 0**.

---

## 학습 목표

- [ ] 지금 노트북이 어떤 Python·가상환경·`.env` 위에서 도는지 확인한다.
- [ ] EXAONE 첫 호출을 하고, thinking 과 streaming 이 무엇을 바꾸는지 본다.

---

## 노트북

| 파일 | 다루는 내용 | 산출물 |
|---|---|---|
| [`00_bootstrap_lab.ipynb`](./00_bootstrap_lab.ipynb) | **Session 1** 환경 4단계 · **Session 2** API 5단계 (기준 / thinking / streaming / 저장) | `_out/first_calls.json` |

계층: `## Session N` → `### Session N-M` (가이드) → 코드 → **출력 해석** → **출력 해석** 마크다운.

---

## 코드 시작 패턴 (facade)

저장소 루트에서 **한 번**: `pip install -r requirements.txt && pip install -e .`

```python
import exaone

exaone.load_project_env()
ROOT = exaone.project_root()
```

API 클라이언트:

```python
client = exaone.integrations.build_llm_from_env()
resp = client.chat([exaone.llm.ExaoneMessage(role="user", content="안녕")])
```

전체 규칙: [`recipes/README.md`](../README.md).

---

## 체크포인트

- [ ] Session 1 4단계 — 해석 셀 기준으로 출력 확인
- [ ] Session 2 A/B/C 각각 답 출력
- [ ] `_out/first_calls.json` 저장 (Session 2-5)

---

## 문제 해결

- `EXAONE_API_KEY` / 401 / 403 → `.env` 의 키·base_url·model 확인.
- SSL `CERTIFICATE_VERIFY_FAILED` → [`PLAYBOOK.md` Part 8](../../PLAYBOOK.md#part-8).
- Jupyter 커널 → 노트북 설치 절의 `ipykernel install` 후 `Python (exaone-cookbook)` 선택.
