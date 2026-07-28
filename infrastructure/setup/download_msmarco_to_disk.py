#!/usr/bin/env python3
"""
Download MS MARCO (config v1.1) from Hugging Face and save to disk for offline RAG build.

Why retries: the Hub sometimes returns an empty or non-JSON body (JSONDecodeError) under
rate limits or transient errors; HF_TOKEN in .env usually helps.

회사망: .env 에 HTTP(S)_PROXY, REQUESTS_CA_BUNDLE(기업 루트 CA), HF_HUB_DISABLE_SSL_VERIFICATION 등
설정 후 step1 을 다시 실행하세요. (step1 이 `set -a` 로 .env 를 export 합니다)
"""
from __future__ import annotations

import argparse
import os
import random
import sys
import time
from pathlib import Path

# 이 디렉터리를 path 에 넣어서 hf_hub_httpx 를 import (datasets / hub import **전**)
_SETUP = Path(__file__).resolve().parent
if str(_SETUP) not in sys.path:
    sys.path.insert(0, str(_SETUP))

import hf_hub_httpx  # noqa: E402  — env 동기화(side effect)

# `datasets` import 전에 httpx client 등록
hf_hub_httpx.apply_huggingface_http_client()


def _main() -> int:
    p = argparse.ArgumentParser(description="Save HuggingFace ms_marco v1.1 to a local directory.")
    p.add_argument(
        "out_dir",
        nargs="?",
        default="_temp/ms_marco",
        help="Output directory (default: _temp/ms_marco, relative to cwd)",
    )
    p.add_argument("--retries", type=int, default=5, help="Number of load attempts (default: 5)")
    p.add_argument("--trust-remote-code", action="store_true", help="Pass trust_remote_code=True to load_dataset")
    args = p.parse_args()

    try:
        from datasets import load_dataset
    except ImportError:
        print("필요: pip install 'datasets>=2.14'", file=sys.stderr)
        return 1

    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)

    token = os.environ.get("HF_TOKEN") or None
    if not token and os.environ.get("HF_HUB_OFFLINE", "").lower() in ("1", "true", "yes"):
        print("HF_HUB_OFFLINE=1 이고, 로컬 캐시에 없으면 ms_marco 를 받을 수 없습니다.", file=sys.stderr)
        return 1

    # 권장 repo id (짧은 별칭 `ms_marco` 가 Hub/리다이렉트에 따라 404/JSON 오류를 유발하는 경우가 있음)
    dataset_ids = ("microsoft/ms_marco", "ms_marco")

    last: Exception | None = None
    for ds_name in dataset_ids:
        for attempt in range(1, args.retries + 1):
            try:
                ds = load_dataset(
                    ds_name,
                    "v1.1",
                    trust_remote_code=bool(args.trust_remote_code),
                    token=token,
                )
                ds.save_to_disk(str(out))
                print("MS MARCO dataset saved to", out.resolve(), f"(id={ds_name!r})", flush=True)
                return 0
            except KeyboardInterrupt:
                raise
            except Exception as e:
                last = e
                if attempt < args.retries:
                    base = min(60.0, 2.0**attempt)
                    wait = base + random.uniform(0, base * 0.25)
                    print(
                        f"[{ds_name} {attempt}/{args.retries}] load/save failed: {e!r}\n"
                        f"     Retrying in {wait:.0f}s… (Hub: HF_TOKEN / PROXY / CA / SSL)\n",
                        flush=True,
                    )
                    time.sleep(wait)
                else:
                    print(f"Giving up on {ds_name!r} after {args.retries} attempts.", file=sys.stderr, flush=True)

    print(
        "MS MARCO download failed after retries.\n"
        "  • Hub returned empty/invalid JSON (JSONDecodeError) — 레이트 리밋·일시 장애·회사망(프록시/차단) 가능.\n"
        "  • .env: HF_TOKEN, HTTP_PROXY/HTTPS_PROXY/NO_PROXY, REQUESTS_CA_BUNDLE (기업 루트 CA),\n"
        "    SSL 비검증: HF_HUB_DISABLE_SSL_VERIFICATION=1 (또는 DISABLE_SSL_VERIFY=1)\n"
        "  • https://status.huggingface.com/\n"
        f"  • Last error: {last!r}",
        file=sys.stderr,
    )
    return 1


if __name__ == "__main__":
    raise SystemExit(_main())
