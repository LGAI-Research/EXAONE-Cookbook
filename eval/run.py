"""
(en) CLI entry for naive vs harness comparison benchmarks.

Loads `.env`, runs the pipeline, writes JSON + Markdown to `eval/reports/`,
and prints the summary table.

Examples::

    python -m eval.run --list-datasets
    python -m eval.run --limit 25 --pass-k-trials 2 --sleep 3
    python -m eval.run --dataset bfcl_v3.simple --limit 3
    python -m eval.run --dataset bfcl_v3.simple,bfcl_v3.irrelevance --limit 5
    python -m eval.run --dataset ifeval --limit 5 --pass-k-trials 1
    python -m eval.run \\
        --dataset bfcl_v3.simple,bfcl_v3.multiple,bfcl_v3.parallel,bfcl_v3.irrelevance \\
        --limit 25 --pass-k-trials 2 --sleep 3
    python -m eval.run --dataset ifeval,halubench --limit 5 --pass-k-trials 1
    # Cookbook matrix (BFCL + IFEval + HaluBench): use COOKBOOK_MATRIX_DATASETS in run.py

(kr) naive vs harness 비교 벤치마크 CLI entry.

`.env` 로드 → 파이프라인 실행 → `eval/reports/`에 JSON·Markdown 저장 → 요약 표 출력.

위 예시 참고. 태스크당 K trial을 runner마다 실행해 M2 pass^k를 관찰한다. K=1이면 M2 생략.
"""
from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from eval._env import DEFAULT_ENV_FILE, DEFAULT_REPORTS_DIR, configure_hf_hub_ssl, load_dotenv
from eval.pipeline import RunConfig, run_comparison
from eval.report import markdown_table, save_report

logger = logging.getLogger("eval.run")

DEFAULT_DATASETS = (
    "bfcl_v3.simple,bfcl_v3.multiple,bfcl_v3.parallel,bfcl_v3.irrelevance"
)

# (en) Cookbook matrix: BFCL + IFEval + HaluBench → one M1–M10 report (see docs/eval.md §4.1).
# (kr) Cookbook matrix: BFCL + IFEval + HaluBench → M1–M10 종합 표(docs/eval.md §4.1).
COOKBOOK_MATRIX_DATASETS = (
    "bfcl_v3.simple,bfcl_v3.multiple,bfcl_v3.parallel,bfcl_v3.irrelevance,"
    "ifeval,halubench"
)

# (en) τ-bench simulation — separate report (docs/eval.md §4.2).
# (kr) τ-bench 시뮬레이션 — 별도 리포트(docs/eval.md §4.2).
TAUBENCH_DATASETS = "tau_bench.retail,tau_bench.airline"


def build_parser() -> argparse.ArgumentParser:
    """(en) Argument parser for `python -m eval.run`. (kr) CLI 인자 파서."""
    parser = argparse.ArgumentParser(
        description="Compare naive Friendli API vs exaone harness on agentic benchmarks.",
    )
    parser.add_argument(
        "--list-datasets",
        action="store_true",
        help="print registered dataset names and exit",
    )
    parser.add_argument(
        "--dataset",
        default=DEFAULT_DATASETS,
        help=(
            "comma-separated dataset names "
            f"(default: {DEFAULT_DATASETS})"
        ),
    )
    parser.add_argument("--limit", type=int, default=None, help="cap tasks per dataset")
    parser.add_argument(
        "--pass-k-trials",
        type=int,
        default=1,
        help="trials per task per runner (K=1 disables M2 pass^k)",
    )
    parser.add_argument(
        "--runners",
        default="naive,harness",
        help="comma-separated runner names; default: naive,harness",
    )
    parser.add_argument("--out-dir", default=str(DEFAULT_REPORTS_DIR))
    parser.add_argument("--env-file", default=str(DEFAULT_ENV_FILE))
    parser.add_argument(
        "--max-turns",
        type=int,
        default=8,
        help="naive runner max ReAct turns",
    )
    parser.add_argument(
        "--harness-max-turns",
        type=int,
        default=10,
        help="harness ToolAgent.max_turns",
    )
    parser.add_argument(
        "--sleep",
        type=float,
        default=2.0,
        help="seconds between trials (anti-throttle for serverless endpoints)",
    )
    parser.add_argument(
        "--checkpoint",
        action="store_true",
        help="write per-trial JSONL and partial latest.md under out-dir/{run_id}/",
    )
    parser.add_argument(
        "--resume",
        metavar="RUN_ID",
        default=None,
        help="resume a checkpoint run (requires --checkpoint); RUN_ID = out-dir subfolder name",
    )
    parser.add_argument("--verbose", "-v", action="count", default=0)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.list_datasets:
        from eval.datasets import available_datasets

        for name in available_datasets():
            print(name)
        return 0

    logging.basicConfig(
        level=logging.WARNING if args.verbose == 0 else logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    loaded = load_dotenv(Path(args.env_file))
    logger.info("loaded %d env keys from %s", loaded, args.env_file)
    configure_hf_hub_ssl()

    from eval.datasets._cache import ensure_dataset_cache

    cache_root = ensure_dataset_cache()
    logger.info("eval dataset cache: %s", cache_root)

    datasets = tuple(d.strip() for d in args.dataset.split(",") if d.strip())
    if any(d.startswith("tau_bench") for d in datasets):
        from eval.runners.tau_bench_litellm import patch_litellm_completion_exaone

        patch_litellm_completion_exaone()

    runners = tuple(r.strip() for r in args.runners.split(",") if r.strip())
    if args.resume and not args.checkpoint:
        print("--resume requires --checkpoint", file=sys.stderr)
        return 2
    config = RunConfig(
        datasets=datasets,
        limit=args.limit,
        pass_k_trials=args.pass_k_trials,
        runners=runners,
        naive_max_turns=args.max_turns,
        harness_max_turns=args.harness_max_turns,
        sleep_between_trials=args.sleep,
        checkpoint=args.checkpoint,
        checkpoint_dir=Path(args.out_dir),
        resume_run_id=args.resume,
    )

    try:
        report = run_comparison(config)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 2

    table = markdown_table(report)
    out_dir = Path(args.out_dir)
    if args.checkpoint and report.checkpoint_run_id:
        run_dir = out_dir / report.checkpoint_run_id
        json_path, md_path = save_report(report, run_dir)
        print()
        print(table)
        print()
        print(f"Checkpoint: {run_dir}")
        print(f"Saved: {run_dir / 'report.json'}")
        print(f"Saved: {run_dir / 'latest.md'}")
        if not report.partial:
            print(f"Saved: {json_path}")
            print(f"Saved: {md_path}")
    else:
        json_path, md_path = save_report(report, out_dir)
        print()
        print(table)
        print()
        print(f"Saved: {json_path}")
        print(f"Saved: {md_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
