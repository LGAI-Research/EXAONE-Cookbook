#!/usr/bin/env python3
"""
(en) Cross-platform runner for the Proof Gallery demos (stdlib only).
     The .sh (macOS/Linux/Git Bash) and .cmd (Windows PowerShell/cmd) entrypoints are thin
     wrappers around this file, so the demo logic lives in one place.
(kr) Proof Gallery 데모용 크로스플랫폼 실행기(표준 라이브러리만 사용).
     .sh(macOS/Linux/Git Bash)와 .cmd(Windows PowerShell/cmd) 진입점은 모두 이 파일을 부르는
     얇은 래퍼라서, 데모 로직은 한 곳에만 있다.

Usage (cookbook root):
  uv run --no-project python implementations/gallery.py uv-run <repo> <command> [args...]
  uv run --no-project python implementations/gallery.py demo <repo> [--live] [--crew]
  uv run --no-project python implementations/gallery.py live-smoke [--repo <repo>] [--live] [--crew]
  uv run --no-project python implementations/gallery.py hermes [hermes args...]
  uv run --no-project python implementations/gallery.py nanoclaw-sync-env | nanoclaw-onecli | nanoclaw-prereqs
"""
from __future__ import annotations

import argparse
import os
import shlex
import shutil
import subprocess
import sys
from pathlib import Path

IMPLEMENTATIONS = Path(__file__).resolve().parent
ROOT = IMPLEMENTATIONS.parent
REPOS = ("hermes-agent", "smolagents", "crewai", "browser-use", "nanoclaw")
IS_WINDOWS = os.name == "nt"


class DemoError(Exception):
    def __init__(self, code: int, message: str = "") -> None:
        super().__init__(message)
        self.code = code


def _flag(name: str) -> bool:
    return os.environ.get(name, "0").strip() == "1"


def _log(prefix: str, msg: str) -> None:
    print(f"[{prefix}] {msg}", flush=True)


# --------------------------------------------------------------------------- uv-run


def uv_run_cmd(repo: str, command: list[str]) -> tuple[list[str], dict[str, str]]:
    # (en) Same contract as the old uv_run.sh: impl-isolated uv venv, PYTHONPATH=implementations/.
    # (kr) 기존 uv_run.sh 와 동일: implementation 전용 uv venv, PYTHONPATH=implementations/.
    impl = IMPLEMENTATIONS / repo
    if not impl.is_dir():
        raise DemoError(2, f"unknown implementation repo: {repo} (expected {impl})")
    if not (impl / "pyproject.toml").is_file():
        raise DemoError(2, f"missing pyproject.toml: {impl / 'pyproject.toml'}")
    if shutil.which("uv") is None:
        raise DemoError(127, "uv not found on PATH — install: https://docs.astral.sh/uv/getting-started/installation/")
    env = dict(os.environ)
    # (en) An outer venv (activated, or the one running this file) must not leak into the impl project.
    # (kr) 바깥 venv(활성화된 venv 또는 이 파일을 돌리는 venv)가 impl 프로젝트에 섞이지 않게 한다.
    env.pop("VIRTUAL_ENV", None)
    env["PYTHONPATH"] = str(IMPLEMENTATIONS)
    env.setdefault("EXAONE_IMPL_DIR", str(impl))
    cmd = ["uv", "run", "--project", str(impl), "--directory", str(impl), *command]
    return cmd, env


def uv_run(repo: str, *command: str, check: bool = True, capture: bool = False) -> subprocess.CompletedProcess[str]:
    cmd, env = uv_run_cmd(repo, list(command))
    if capture:
        # (en) Windows python writes pipes in the locale codepage (e.g. cp949) unless told otherwise.
        # (kr) Windows python 은 따로 지정하지 않으면 파이프에 로캘 코드페이지(cp949 등)로 쓴다.
        env["PYTHONIOENCODING"] = "utf-8"
    sys.stdout.flush()
    proc = subprocess.run(
        cmd,
        cwd=str(ROOT),
        env=env,
        encoding="utf-8" if capture else None,
        stdout=subprocess.PIPE if capture else None,
        check=False,
    )
    if check and proc.returncode != 0:
        raise DemoError(proc.returncode, f"command failed ({proc.returncode}): {' '.join(command)}")
    return proc


# --------------------------------------------------------------------------- simple demos


def demo_smolagents(live: bool, crew: bool) -> None:
    p = "smolagents-demo"
    _log(p, "Phase 0 — prerequisite smoke")
    uv_run("smolagents", "python", "scripts/check_env.py")
    if live:
        _log(p, "Phase 1 — E2E agent run + validate (_out/run.json)")
        uv_run("smolagents", "python", "eval_smoke.py", "--run")
    else:
        _log(p, "Phase 1 — skip live turn (use --live or RUN_LIVE_TURN=1 to call EXAONE API)")
        print(_live_hint("smolagents", "python eval_smoke.py --run"))


def demo_crewai(live: bool, crew: bool) -> None:
    p = "crewai-demo"
    _log(p, "Phase 0 — import smoke")
    uv_run("crewai", "python", "scripts/check_env.py")
    if live and crew:
        _log(p, "Phase 1 — spike + 3-agent crew + validate")
        uv_run("crewai", "python", "eval_smoke.py", "--run", "--full")
    elif live:
        _log(p, "Phase 1 — spike LLM + validate (_out/spike_llm.json)")
        uv_run("crewai", "python", "eval_smoke.py", "--run")
    else:
        _log(p, "Phase 1 — skip live turn (use --live or RUN_LIVE_TURN=1 to call EXAONE API)")
        print(_live_hint("crewai", "python eval_smoke.py --run", extra="--live --crew   # + run_crew.py"))


def demo_browser_use(live: bool, crew: bool) -> None:
    p = "browser-use-demo"
    _log(p, "Phase 0 — env smoke")
    uv_run("browser-use", "python", "scripts/check_env.py")
    _log(p, "Phase 0b — Playwright chromium")
    uv_run("browser-use", "python", "-m", "playwright", "install", "chromium")
    if live:
        _log(p, "Phase 1 — example.com task + validate (_out/run.json)")
        uv_run("browser-use", "python", "eval_smoke.py", "--run")
    else:
        _log(p, "Phase 1 — skip live turn (use --live or RUN_LIVE_TURN=1 to call EXAONE API + browser)")
        print(_live_hint("browser-use", "python eval_smoke.py --run"))


def _live_hint(repo: str, uv_args: str, extra: str | None = None) -> str:
    uv_entry = "implementations\\uv_run.cmd" if IS_WINDOWS else "./implementations/uv_run.sh"
    demo = f"implementations\\{repo}\\run_cli_demo.cmd" if IS_WINDOWS else f"implementations/{repo}/run_cli_demo.sh"
    lines = ["", f"=== {repo} + EXAONE — live test ===", f"  {demo} --live"]
    if extra:
        lines.append(f"  {demo} {extra}")
    lines.append(f"  # or: {uv_entry} {repo} {uv_args}")
    lines.append("")
    return "\n".join(lines)


# --------------------------------------------------------------------------- hermes-agent

HERMES_IMPL = IMPLEMENTATIONS / "hermes-agent"
HERMES_GLUE = HERMES_IMPL / "scripts" / "hermes_glue.py"
HERMES_SUBMODULE = ROOT / "submodules" / "hermes-agent"


def hermes_env() -> dict[str, str]:
    # (en) REPO_ROOT / HERMES_HOME / EXAONE_* from hermes_glue export-shell (same values env.sh exports).
    # (kr) hermes_glue export-shell 의 REPO_ROOT / HERMES_HOME / EXAONE_* (env.sh 가 export 하는 값과 동일).
    out = uv_run("hermes-agent", "python", str(HERMES_GLUE), "export-shell", capture=True).stdout
    pairs: dict[str, str] = {}
    for line in out.splitlines():
        parts = shlex.split(line.strip())
        if len(parts) == 2 and parts[0] == "export" and "=" in parts[1]:
            key, val = parts[1].split("=", 1)
            pairs[key] = val
    return pairs


def _venv_exe(venv: Path, name: str) -> Path | None:
    # (en) uv venv layout: .venv/bin/* on Linux/macOS, .venv/Scripts/*.exe on Windows.
    # (kr) uv venv 경로: Linux/macOS 는 .venv/bin/*, Windows 는 .venv/Scripts/*.exe.
    for sub in ("Scripts", "bin"):
        for fname in (f"{name}.exe", name):
            p = venv / sub / fname
            if p.is_file():
                return p
    return None


def run_hermes(args: list[str]) -> int:
    os.environ.update(hermes_env())
    os.makedirs(os.environ["HERMES_HOME"], exist_ok=True)
    if not HERMES_SUBMODULE.is_dir():
        raise DemoError(
            1,
            f"missing upstream: {HERMES_SUBMODULE}\n"
            "run: git clone https://github.com/NousResearch/hermes-agent.git submodules/hermes-agent",
        )
    venv = HERMES_SUBMODULE / ".venv"
    if _venv_exe(venv, "hermes") is None:
        print("== bootstrapping submodules/hermes-agent venv (first run may take a minute) ==", flush=True)
        env = {k: v for k, v in os.environ.items() if k != "VIRTUAL_ENV"}
        frozen = subprocess.run(["uv", "sync", "--frozen"], cwd=str(HERMES_SUBMODULE), env=env, stderr=subprocess.DEVNULL, check=False)
        if frozen.returncode != 0:
            subprocess.run(["uv", "sync"], cwd=str(HERMES_SUBMODULE), env=env, check=True)
    py = _venv_exe(venv, "python")
    if py is None:
        raise DemoError(1, f"missing venv python under {venv} (bin/ or Scripts/) — check the uv sync output above")
    # (en) CWD is impl glue — never submodules/ (agent file tools write relative paths).
    # (kr) CWD 는 impl 접착층 — submodules/ 아님(에이전트 파일 도구가 상대경로로 씀).
    sys.stdout.flush()
    return subprocess.run([str(py), str(HERMES_GLUE), "run", *args], cwd=str(HERMES_IMPL), check=False).returncode


def demo_hermes(live: bool, crew: bool) -> None:
    glue = "scripts/hermes_glue.py"
    print("== check ==", flush=True)
    uv_run("hermes-agent", "python", glue, "check")
    print("== render .hermes/config.yaml ==", flush=True)
    uv_run("hermes-agent", "python", glue, "render")
    print("== EXAONE ping ==", flush=True)
    uv_run("hermes-agent", "python", glue, "ping")
    print("== validate _out/cli_smoke.json ==", flush=True)
    uv_run("hermes-agent", "python", "eval_smoke.py")

    print("== hermes doctor ==", flush=True)
    uv_run("hermes-agent", "python", glue, "link-cli", check=False)
    if shutil.which("rg") is None and shutil.which("brew") is not None:
        subprocess.run(["brew", "install", "ripgrep"], check=False)
    # (en) doctor ⚠ lines are fine, but a non-zero exit (e.g. Hermes failed to start) must not print "smoke OK".
    # (kr) doctor 의 ⚠ 는 무시해도 되지만, 비정상 종료(Hermes 기동 실패 등)면 "smoke OK" 를 찍지 않는다.
    rc = run_hermes(["doctor"])
    if rc != 0:
        raise DemoError(rc, f"\n== smoke FAILED: hermes doctor exited with {rc} (see the error above) ==")

    run_entry = "implementations\\hermes-agent\\run_hermes.cmd" if IS_WINDOWS else "implementations/hermes-agent/scripts/run_hermes.sh"
    print(
        "\n== smoke OK ==\n"
        f"  NEXT  {run_entry}\n"
        "        # /model custom:exaone/<EXAONE_MODEL>\n"
        "  NOTE  doctor OAuth/web/discord ⚠ → EXAONE-only 데모에서는 무시"
    )


# --------------------------------------------------------------------------- nanoclaw

NANOCLAW_IMPL = IMPLEMENTATIONS / "nanoclaw"

_NANOCLAW_EXAONE_PY = """
from common.exaone_env import load_exaone_env, openai_compat_kwargs

load_exaone_env()
kw = openai_compat_kwargs()
model = kw["model"]
print(kw["base_url"])
print(model)
print(f"exaone/{model}")
"""

_NANOCLAW_ONECLI_PY = r'''
import json
import shutil
from urllib.parse import urlparse

from common.exaone_env import impl_dir, load_exaone_env, openai_compat_kwargs

load_exaone_env()
kw = openai_compat_kwargs()
host = urlparse(kw["base_url"]).hostname or "<host-from-EXAONE_BASE_URL>"
key_set = bool(kw["api_key"])
env_file = impl_dir() / ".env"

print("# (en) OneCLI — register EXAONE for NanoClaw container outbound proxy")
print("# (kr) OneCLI — NanoClaw 컨테이너 아웃바운드 프록시용 EXAONE 등록")
print()
if not key_set:
    print(f"# WARNING: EXAONE_API_KEY is not set in {env_file}")
    print()
print(f"# host-pattern derived from EXAONE_BASE_URL: {host}")
print()
print("onecli secrets create --name \"EXAONE\" --type generic \\")
print(f"  --value \"${{EXAONE_API_KEY:-<your-key>}}\" --host-pattern \"{host}\" \\")
print('  --header-name "Authorization" --value-format "Bearer {value}"')
print()
print("# (en) Grant the agent access (set-secrets replaces — include existing IDs):")
print("# (kr) 에이전트에 secret 부여 (set-secrets 는 교체 — 기존 ID 포함):")
print("# onecli agents list")
print("# onecli secrets list")
print("# onecli agents set-secrets --id <agent-id> --secret-ids <existing>,<exaone-secret-id>")
print()
print("# (en) After wiring, set groups/<folder>/container.json → \"provider\": \"opencode\"")
print("# (kr) wiring 후 groups/<folder>/container.json → \"provider\": \"opencode\"")
print()
report = {
    "host_pattern": host,
    "base_url": kw["base_url"],
    "model": kw["model"],
    "onecli_on_path": shutil.which("onecli"),
}
print("# check_env snapshot:")
print(json.dumps(report, ensure_ascii=False, indent=2))
'''

_NANOCLAW_STEPS_PY = """
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from common.exaone_env import load_exaone_env, openai_compat_kwargs

out = Path(sys.argv[1])
load_exaone_env()
kw = openai_compat_kwargs()
payload = {
    "timestamp": datetime.now(timezone.utc).isoformat(),
    "status": "artifacts_ready",
    "submodule_policy": "submodules/nanoclaw is read-only — apply vendor bundle in your fork",
    "model": kw["model"],
    "base_url": kw["base_url"],
    "integration_path": "B — add-opencode + EXAONE custom provider",
    "vendor_dir": "implementations/nanoclaw/vendor/opencode-from-providers",
    "env_file": "implementations/nanoclaw/_out/nanoclaw.exaone.env",
    "apply_doc": "implementations/nanoclaw/vendor/opencode-from-providers/APPLY-TO-YOUR-NANOCLAW-FORK.md",
    "demo_question_ko": (
        "EXAONE이 이 NanoClaw 에이전트의 LLM 백본이라는 걸 한국어로 한 문장만 말해줘."
    ),
}
out.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\\n", encoding="utf-8")
print("saved:", out)
"""


def nanoclaw_sync_env() -> None:
    # (en) Render implementations/nanoclaw/.env EXAONE_* as OpenCode vars under _out/ only.
    # (kr) implementations/nanoclaw/.env EXAONE_* 를 OpenCode 변수로 _out/ 에만 렌더한다.
    p = "sync-nanoclaw-env"
    out_env = NANOCLAW_IMPL / "_out" / "nanoclaw.exaone.env"
    lines = uv_run("nanoclaw", "python", "-c", _NANOCLAW_EXAONE_PY, capture=True).stdout.splitlines()
    base_url, model, opencode_model = (lines + ["", "", ""])[:3]
    content = (
        "# --- implementations/nanoclaw/.env → NanoClaw OpenCode (generated) ---\n"
        "# (en) Merge into YOUR NanoClaw fork .env — not submodules/nanoclaw (read-only pin).\n"
        "# (kr) 본인 NanoClaw fork .env 에 병합 — submodules/nanoclaw(read-only pin) 에 쓰지 말 것.\n"
        "# Generated: implementations/gallery.py nanoclaw-sync-env\n"
        "OPENCODE_PROVIDER=exaone\n"
        f"OPENCODE_MODEL={opencode_model}\n"
        f"OPENCODE_SMALL_MODEL={opencode_model}\n"
        f"ANTHROPIC_BASE_URL={base_url}\n"
    )
    _log(p, f"implementation model: {model}")
    _log(p, f"OPENCODE_MODEL: {opencode_model}")
    _log(p, f"ANTHROPIC_BASE_URL: {base_url}")
    if _flag("DRY_RUN"):
        print(content, end="")
        return
    out_env.parent.mkdir(parents=True, exist_ok=True)
    out_env.write_text(content, encoding="utf-8", newline="\n")
    _log(p, f"wrote: {out_env} (gitignored _out/)")


def nanoclaw_onecli(limit: int | None = None) -> None:
    # (en) Print OneCLI secret registration hints (does not call onecli).
    # (kr) OneCLI secret 등록 힌트만 출력한다(onecli 를 호출하지 않음).
    out = uv_run("nanoclaw", "python", "-c", _NANOCLAW_ONECLI_PY, capture=True).stdout
    lines = out.splitlines()
    print("\n".join(lines[:limit] if limit else lines))


def nanoclaw_prereqs() -> None:
    _log("nanoclaw-prereq", "Phase 0 JSON probe (Docker / Node / pnpm / submodule):")
    uv_run("nanoclaw", "python", "scripts/check_env.py", check=False)
    uv_entry = "implementations\\uv_run.cmd" if IS_WINDOWS else "./implementations/uv_run.sh"
    print(
        "\n=== Manual prerequisites (not installed by this script) ===\n\n"
        "1. Docker Desktop or Docker Engine\n"
        "2. Node.js 20+\n"
        "3. pnpm 10+  (upstream nanoclaw.sh can bootstrap)\n"
        "4. git clone https://github.com/nanocoai/nanoclaw.git submodules/nanoclaw\n"
        "5. cp implementations/nanoclaw/.env.example implementations/nanoclaw/.env\n"
        "6. uv sync --project implementations/nanoclaw\n\n"
        "Cookbook E2E (EXAONE 1-turn, no Docker):\n"
        f"  {uv_entry} nanoclaw python run_exaone_turn.py\n\n"
        "Full container E2E (your NanoClaw fork):\n"
        "  implementations/nanoclaw/vendor/opencode-from-providers/APPLY-TO-YOUR-NANOCLAW-FORK.md\n"
    )


def demo_nanoclaw(live: bool, crew: bool) -> None:
    p = "run-cli-demo"
    _log(p, "Phase 0 — prerequisite smoke")
    uv_run("nanoclaw", "python", "scripts/check_env.py", check=False)

    _log(p, "Phase 1 — render EXAONE env (_out/nanoclaw.exaone.env)")
    nanoclaw_sync_env()

    _log(p, "OneCLI registration hints:")
    nanoclaw_onecli(limit=20)

    out_dir = NANOCLAW_IMPL / "_out"
    out_dir.mkdir(parents=True, exist_ok=True)
    uv_run("nanoclaw", "python", "-c", _NANOCLAW_STEPS_PY, str(out_dir / "demo_steps.json"))

    uv_entry = "implementations\\uv_run.cmd" if IS_WINDOWS else "./implementations/uv_run.sh"
    demo = "implementations\\nanoclaw\\run_cli_demo.cmd" if IS_WINDOWS else "implementations/nanoclaw/run_cli_demo.sh"
    if live:
        _log(p, "Phase 2 — EXAONE 1-turn proof (cookbook, no Docker)")
        uv_run("nanoclaw", "python", "run_exaone_turn.py")
        _log(p, "Phase 2b — validate _out/nanoclaw_turn.json")
        uv_run("nanoclaw", "python", "eval_smoke.py")
    else:
        _log(p, "Phase 2 — skip live turn (use --live or RUN_LIVE_TURN=1 to call EXAONE API)")

    print(
        "\n=== NanoClaw + EXAONE — next steps (submodule NOT modified) ===\n\n"
        "Cookbook keeps submodules/nanoclaw as a read-only pin. Use your own NanoClaw fork:\n\n"
        "1. Vendor bundle:\n"
        "   implementations/nanoclaw/vendor/opencode-from-providers/APPLY-TO-YOUR-NANOCLAW-FORK.md\n\n"
        "2. Merge env into YOUR fork .env:\n"
        "   implementations/nanoclaw/_out/nanoclaw.exaone.env\n\n"
        "3. OneCLI: see commands printed above.\n\n"
        "4. Build + CLI chat in YOUR fork (not the submodule):\n"
        "   bash nanoclaw.sh\n"
        "   groups/<folder>/container.json → \"provider\": \"opencode\"\n"
        "   pnpm run chat\n\n"
        "5. Korean demo question:\n"
        "   EXAONE이 이 NanoClaw 에이전트의 LLM 백본이라는 걸 한국어로 한 문장만 말해줘.\n\n"
        "Cookbook EXAONE 1-turn (no Docker):\n"
        f"   {demo} --live\n"
        f"   # or: {uv_entry} nanoclaw python run_exaone_turn.py\n\n"
        "Sample turn shape: implementations/nanoclaw/samples/turn.example.json\n"
    )


# --------------------------------------------------------------------------- CLI

DEMOS = {
    "hermes-agent": demo_hermes,
    "smolagents": demo_smolagents,
    "crewai": demo_crewai,
    "browser-use": demo_browser_use,
    "nanoclaw": demo_nanoclaw,
}


def _live_flags(args: argparse.Namespace) -> tuple[bool, bool]:
    return args.live or _flag("RUN_LIVE_TURN"), args.crew or _flag("RUN_LIVE_CREW")


def cmd_demo(args: argparse.Namespace) -> int:
    live, crew = _live_flags(args)
    DEMOS[args.repo](live, crew)
    return 0


def cmd_live_smoke(args: argparse.Namespace) -> int:
    live, crew = _live_flags(args)
    repos = [args.repo] if args.repo else list(REPOS)
    failed = []
    for repo in repos:
        _log("live-smoke", f"===== {repo} =====")
        try:
            DEMOS[repo](live, crew)
        except DemoError as exc:
            if str(exc):
                print(str(exc), file=sys.stderr)
            failed.append(repo)
            _log("live-smoke", f"FAILED: {repo}")
    if failed:
        return 1
    _log("live-smoke", "all demos finished")
    return 0


def main(argv: list[str] | None = None) -> int:
    # (en) Windows consoles may not encode every symbol we print (✓, ⚠, →) — never crash on that.
    # (kr) Windows 콘솔은 일부 기호(✓, ⚠, →)를 인코딩하지 못할 수 있다 — 그걸로 죽지 않게 한다.
    # (en) Redirected output (CI logs, `> file`) is written as UTF-8 instead of the ANSI codepage.
    # (kr) 리다이렉트된 출력(CI 로그, `> file`)은 ANSI 코드페이지 대신 UTF-8 로 쓴다.
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            if stream.isatty():
                stream.reconfigure(errors="replace")
            else:
                stream.reconfigure(encoding="utf-8", errors="replace")

    argv = list(sys.argv[1:] if argv is None else argv)
    # (en) uv-run / hermes forward everything after the subcommand verbatim (no argparse on it).
    # (kr) uv-run / hermes 는 하위 명령 뒤 인자를 그대로 넘긴다(argparse 로 해석하지 않음).
    try:
        if argv and argv[0] == "uv-run":
            if len(argv) < 3:
                print("usage: gallery.py uv-run <repo> <command> [args...]", file=sys.stderr)
                print("example: gallery.py uv-run smolagents python run_agent.py", file=sys.stderr)
                return 2
            cmd, env = uv_run_cmd(argv[1], argv[2:])
            sys.stdout.flush()
            return subprocess.run(cmd, cwd=str(ROOT), env=env, check=False).returncode
        if argv and argv[0] == "hermes":
            return run_hermes(argv[1:])

        parser = argparse.ArgumentParser(prog="gallery.py", description="Proof Gallery demo runner (cross-platform)")
        sub = parser.add_subparsers(dest="cmd", required=True)
        sub.add_parser("uv-run", help="run a command in an implementation's uv venv")
        sub.add_parser("hermes", help="run Hermes with EXAONE env (args go to hermes)")
        p_demo = sub.add_parser("demo", help="non-interactive demo for one implementation")
        p_demo.add_argument("repo", choices=REPOS)
        p_smoke = sub.add_parser("live-smoke", help="run every demo (or --repo one)")
        p_smoke.add_argument("--repo", choices=REPOS)
        for p in (p_demo, p_smoke):
            p.add_argument("--live", action="store_true", help="call the EXAONE API (same as RUN_LIVE_TURN=1)")
            p.add_argument("--crew", action="store_true", help="crewai: also run the 3-agent crew (same as RUN_LIVE_CREW=1)")
        p_demo.set_defaults(func=cmd_demo)
        p_smoke.set_defaults(func=cmd_live_smoke)
        sub.add_parser("nanoclaw-sync-env", help="render _out/nanoclaw.exaone.env (DRY_RUN=1 prints only)").set_defaults(
            func=lambda _: nanoclaw_sync_env() or 0
        )
        sub.add_parser("nanoclaw-onecli", help="print OneCLI registration hints").set_defaults(func=lambda _: nanoclaw_onecli() or 0)
        sub.add_parser("nanoclaw-prereqs", help="print NanoClaw prerequisite checklist").set_defaults(
            func=lambda _: nanoclaw_prereqs() or 0
        )
        args = parser.parse_args(argv)
        return int(args.func(args))
    except DemoError as exc:
        if str(exc):
            print(str(exc), file=sys.stderr)
        return exc.code
    except KeyboardInterrupt:
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
