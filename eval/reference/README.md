# eval/reference — 공개 reference run 스냅샷

`eval/reports/` 는 gitignore — 로컬 실행마다 타임스탬프 JSON/MD가 쌓입니다.  
**문서·블로그용 고정 숫자**는 이 폴더의 **요약 snapshot** 만 커밋합니다 (trial 로그 없음).

| 파일 | 내용 |
|------|------|
| [`cookbook_matrix_pass2_20260608.snapshot.json`](./cookbook_matrix_pass2_20260608.snapshot.json) | **Table A** (current) — Cookbook matrix (BFCL 4 + IFEval + HaluBench) × 25, pass², M9 fair judge — [`docs/eval.md`](../../docs/eval.md) §4.1 |
| [`cookbook_matrix_pass2_20260531.snapshot.json`](./cookbook_matrix_pass2_20260531.snapshot.json) | Table A (previous) — same scope; M9 used raw JSON wrapper (superseded) |
| [`bfcl_pass2_20260528.snapshot.json`](./bfcl_pass2_20260528.snapshot.json) | BFCL 4종 × 25, pass² only — [`docs/eval.md`](../../docs/eval.md) §4 (subset baseline) |

## 재현

**Cookbook matrix (M1–M10 종합 표):**

```bash
python -m eval.run \
  --dataset bfcl_v3.simple,bfcl_v3.multiple,bfcl_v3.parallel,bfcl_v3.irrelevance,ifeval,halubench \
  --limit 25 --pass-k-trials 2 --sleep 3
```

**BFCL only (빠른 스모크):**

```bash
python -m eval.run \
  --dataset bfcl_v3.simple,bfcl_v3.multiple,bfcl_v3.parallel,bfcl_v3.irrelevance \
  --limit 25 --pass-k-trials 2 --sleep 3
```

`.env`: `EXAONE_API_KEY`, `EXAONE_BASE_URL`, `EXAONE_MODEL`

결과는 `eval/reports/{timestamp}.md` 에 생성됩니다. snapshot과 ±소수 차이는 API·모델 버전에 따라 달라질 수 있습니다.
