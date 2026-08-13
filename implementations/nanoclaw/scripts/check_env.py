#!/usr/bin/env python3
"""
(en) Phase 0 smoke: cookbook EXAONE env, nanoclaw submodule, Docker/Node/pnpm probes.

(kr) Phase 0 스모크: cookbook EXAONE 환경, nanoclaw submodule, Docker/Node/pnpm 프로브.
"""
from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path
from urllib.parse import urlparse

_IMPL = Path(__file__).resolve().parent.parent.parent
if str(_IMPL) not in sys.path:
    sys.path.insert(0, str(_IMPL))

from common.exaone_env import load_exaone_env, openai_compat_kwargs, repo_root


def _node_major() -> int | None:
    node = shutil.which("node")
    if not node:
        return None
    import subprocess

    try:
        out = subprocess.check_output([node, "-v"], text=True).strip().lstrip("v")
        return int(out.split(".")[0])
    except (subprocess.CalledProcessError, ValueError, IndexError):
        return None


def main() -> int:
    impl = load_exaone_env()
    kw = openai_compat_kwargs()
    root = repo_root()
    submodule = root / "submodules" / "nanoclaw"
    parsed = urlparse(kw["base_url"])
    host_pattern = parsed.hostname or ""

    report: dict = {
        "repo_root": str(root),
        "impl_env": str(impl),
        "integration_path": "B — add-opencode + EXAONE custom provider (see INTEGRATION.md)",
        "model": kw["model"],
        "base_url": kw["base_url"],
        "exaone_host_pattern": host_pattern,
        "api_key_set": bool(kw["api_key"]),
        "submodule_nanoclaw": submodule.is_dir(),
        "docker": shutil.which("docker") or None,
        "node": shutil.which("node") or None,
        "node_major": _node_major(),
        "pnpm": shutil.which("pnpm") or None,
        "bun": shutil.which("bun") or None,
        "onecli": shutil.which("onecli") or None,
    }

    opencode_host = submodule / "src" / "providers" / "opencode.ts"
    opencode_container = submodule / "container" / "agent-runner" / "src" / "providers" / "opencode.ts"
    vendor_host = root / "implementations" / "nanoclaw" / "vendor" / "opencode-from-providers" / "src" / "providers" / "opencode.ts"
    report["opencode_vendor_ready"] = vendor_host.is_file()
    report["opencode_provider_in_submodule"] = opencode_host.is_file() and opencode_container.is_file()

    hints: list[str] = []
    if not report["submodule_nanoclaw"]:
        hints.append(
            "git clone https://github.com/nanocoai/nanoclaw.git submodules/nanoclaw"
        )
    if not report["api_key_set"]:
        hints.append("Set EXAONE_API_KEY in implementations/nanoclaw/.env")
    if not report["docker"]:
        hints.append("Install Docker Desktop or Docker Engine")
    if report["node_major"] is not None and report["node_major"] < 20:
        hints.append("Node.js 20+ required (see upstream README)")
    if not report["pnpm"]:
        hints.append("Install pnpm 10+ (upstream nanoclaw.sh can bootstrap)")
    if not report["opencode_vendor_ready"]:
        hints.append(
            "OpenCode vendor bundle missing — expected at "
            "implementations/nanoclaw/vendor/opencode-from-providers/"
        )
    if report["opencode_provider_in_submodule"]:
        hints.append(
            "OpenCode files detected inside submodules/nanoclaw — remove with: "
            "git -C submodules/nanoclaw clean -fd"
        )
    if not report["onecli"]:
        hints.append(
            "OneCLI optional for full NanoClaw; see scripts/print_onecli_exaone.sh "
            "after sync_nanoclaw_env.sh"
        )
    if hints:
        report["hints"] = hints

    print(json.dumps(report, ensure_ascii=False, indent=2))

    ok = (
        report["api_key_set"]
        and report["submodule_nanoclaw"]
        and report["docker"] is not None
        and (report["node_major"] is None or report["node_major"] >= 20)
    )
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
