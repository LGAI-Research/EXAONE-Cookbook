---
layout: page
pageClass: ex-sub
title: Benchmarks — Cookbook vs naive
description: The M1–M10 cookbook metric matrix comparing a naive loop against the EXAONE harness on BFCL v3, IFEval and HaluBench, with published wins and costs.
---

<PageHeader
  eyebrow="Benchmarks"
  title="Cookbook vs naive, measured"
  lede="The eval harness runs the same 150 tasks twice — once through a naive single-shot loop, once through the cookbook harness — and scores both on ten metrics. Improvements and regressions are published together, because a harness that buys reliability with tokens should show the bill."
/>

<div class="ex-wrap ex-body">
<BenchNotes />

<div class="bench-table-block">
<BenchTable />
</div>

<div class="vp-doc ex-note">

## Reproduce it

```bash
# Cookbook matrix — the table above
python -m eval.run \
  --dataset bfcl_v3.simple,bfcl_v3.multiple,bfcl_v3.parallel,bfcl_v3.irrelevance,ifeval,halubench \
  --limit 25 --pass-k-trials 2 --sleep 3

# Quick smoke on BFCL only
python -m eval.run --limit 5 --pass-k-trials 1

# Harness runner alone
python -m eval.run --dataset bfcl_v3.simple --limit 2 --pass-k-trials 1 --runners harness
```

Each run writes a full report to `eval/reports/{timestamp}.{md,json}` — per-task traces, token counts and every metric. The numbers above are the latest such run. Metric definitions and the τ-bench table are in [`docs/eval.md`](https://github.com/LGAI-Research/EXAONE-Cookbook/blob/main/docs/eval.md).

## Suites

| Suite | Datasets | Focus |
| ----- | -------- | ----- |
| BFCL v3 | `simple`, `multiple`, `parallel`, `irrelevance` | Tool selection, arguments, abstention |
| IFEval | `ifeval` | Instruction following, schema adherence |
| HaluBench | `halubench` | Faithfulness to provided context |
| τ-bench | `tau_bench.retail`, `tau_bench.airline` | Multi-turn simulation, pass^k |

## Build your own gate

Public suites measure general capability; your golden set measures whether the agent works for you. [Track 08](./learn/track-08) walks through computing M1–M10 on your own traces and wiring a regression gate that fails CI before a change reaches users.

</div>
</div>
