---
layout: page
pageClass: ex-sub
title: 벤치마크 — Cookbook vs naive
description: BFCL v3 · IFEval · HaluBench에서 naive 루프와 EXAONE 하니스를 비교한 M1–M10 지표 매트릭스. 개선과 비용을 함께 공개합니다.
---

<PageHeader
  eyebrow="벤치마크"
  title="Cookbook vs naive, 측정값"
  lede="eval 하니스는 같은 150개 과제를 두 번 실행합니다. 한 번은 naive 단발 루프로, 한 번은 Cookbook 하니스로. 그리고 10개 지표로 둘 다 채점합니다. 개선과 퇴행을 함께 공개하는 이유는, 토큰으로 신뢰성을 사는 하니스라면 청구서도 보여야 하기 때문입니다."
/>

<div class="ex-wrap ex-body">
<BenchNotes />

<div class="bench-table-block">
<BenchTable />
</div>

<div class="vp-doc ex-note">

## 재현하기

```bash
# Cookbook matrix — 위 표
python -m eval.run \
  --dataset bfcl_v3.simple,bfcl_v3.multiple,bfcl_v3.parallel,bfcl_v3.irrelevance,ifeval,halubench \
  --limit 25 --pass-k-trials 2 --sleep 3

# BFCL만 빠르게 스모크
python -m eval.run --limit 5 --pass-k-trials 1

# harness 러너만 실행
python -m eval.run --dataset bfcl_v3.simple --limit 2 --pass-k-trials 1 --runners harness
```

실행할 때마다 `eval/reports/{timestamp}.{md,json}`에 과제별 trace · 토큰 수 · 전체 지표가 담긴 리포트가 남습니다. 위 수치는 가장 최근 run의 결과입니다. 지표 정의와 τ-bench 표는 [`docs/eval.md`](https://github.com/LGAI-Research/EXAONE-Cookbook/blob/main/docs/eval.md)에 있습니다.

## 스위트

| 스위트 | 데이터셋 | 초점 |
| ------ | -------- | ---- |
| BFCL v3 | `simple`, `multiple`, `parallel`, `irrelevance` | 도구 선택 · 인자 · abstention |
| IFEval | `ifeval` | 지시 따르기 · 스키마 준수 |
| HaluBench | `halubench` | 제공 컨텍스트에 대한 faithfulness |
| τ-bench | `tau_bench.retail`, `tau_bench.airline` | 멀티턴 시뮬레이션 · pass^k |

## 자기 게이트 만들기

공개 스위트는 일반적인 능력을, 골든셋은 "우리 업무에서 동작하는가"를 측정합니다. [Track 08](./learn/track-08)에서 자기 trace로 M1–M10을 계산하고, 변경이 사용자에게 닿기 전에 CI를 실패시키는 회귀 게이트를 만듭니다.

</div>
</div>
