"""
(en) Shared EXAONE env bootstrap for implementations/* glue scripts.

(kr) implementations/* 접착 스크립트용 EXAONE 환경 부트스트랩이다.
"""
from __future__ import annotations

import inspect
import os
import ssl
import sys
from pathlib import Path
from typing import Any

_active_impl: Path | None = None
_loaded_impl_dirs: set[Path] = set()


def repo_root() -> Path:
    """
    (en) Walk up from this file until we find the cookbook root (contains exaone/ and implementations/).

    (kr) exaone/ 와 implementations/ 가 있는 cookbook 루트를 찾는다.
    """
    here = Path(__file__).resolve()
    for parent in [here.parent, *here.parents]:
        if (parent / "exaone").is_dir() and (parent / "implementations").is_dir():
            return parent
    raise RuntimeError("cookbook root not found (expected exaone/ and implementations/)")


def ensure_repo_on_path() -> Path:
    """
    (en) Insert repo root on sys.path so optional `import exaone` works from glue scripts.

    (kr) glue 스크립트에서 선택적 `import exaone` 이 되도록 repo 루트를 sys.path 에 넣는다.
    """
    root = repo_root()
    root_s = str(root)
    if root_s not in sys.path:
        sys.path.insert(0, root_s)
    return root


def _load_dotenv(path: Path, *, override: bool = False) -> bool:
    """
    (en) Load a `.env` file into os.environ; `override=True` replaces existing keys.

    (kr) `.env` 를 os.environ 에 로드한다. `override=True` 이면 기존 키를 덮어쓴다.
    """
    if not path.is_file():
        return False
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, _, v = line.partition("=")
                k, v = k.strip(), v.strip().strip("'\"").strip()
                if " #" in v:
                    v = v.split(" #", 1)[0].strip()
                if k:
                    if override:
                        os.environ[k] = v
                    else:
                        os.environ.setdefault(k, v)
    return True


def impl_dir(*, caller_file: Path | str | None = None) -> Path:
    """
    (en) Resolve implementations/<repo>/ for the calling glue script.

    (kr) 호출 glue 스크립트의 implementations/<repo>/ 경로를 반환한다.
    """
    global _active_impl

    override = os.environ.get("EXAONE_IMPL_DIR", "").strip()
    if override:
        path = Path(override).resolve()
        if path.is_dir():
            return path
        raise RuntimeError(f"EXAONE_IMPL_DIR is not a directory: {override}")

    if _active_impl is not None and caller_file is None:
        return _active_impl

    if caller_file is None:
        frame = inspect.currentframe()
        if frame is None or frame.f_back is None:
            raise RuntimeError(
                "cannot infer implementation dir (pass caller_file or set EXAONE_IMPL_DIR)"
            )
        caller_file = frame.f_back.f_code.co_filename

    here = Path(caller_file).resolve()
    implementations = repo_root() / "implementations"
    for parent in [here, *here.parents]:
        if parent.parent == implementations and parent.name != "common":
            return parent

    raise RuntimeError(
        f"cannot infer implementations/<repo>/ from {here}; set EXAONE_IMPL_DIR"
    )


def load_exaone_env(*, caller_file: Path | str | None = None) -> Path:
    """
    (en) Load implementations/<repo>/.env and return that implementation directory.

    (kr) implementations/<repo>/.env 를 로드하고 해당 구현 디렉터리를 반환한다.
    """
    global _active_impl

    impl = impl_dir(caller_file=caller_file)
    if impl not in _loaded_impl_dirs:
        env_path = impl / ".env"
        _load_dotenv(env_path, override=True)
        _loaded_impl_dirs.add(impl)
    _active_impl = impl
    return impl


def _env_bool(key: str, default: bool = False) -> bool:
    value = os.environ.get(key, "").strip().lower()
    if not value:
        return default
    return value in ("1", "true", "yes", "on")


def get_disable_ssl_verify() -> bool:
    """
    (en) Read DISABLE_SSL_VERIFY from the active implementation `.env`.

    (kr) 활성 implementation `.env` 의 DISABLE_SSL_VERIFY 를 읽는다.
    """
    load_exaone_env()
    return _env_bool("DISABLE_SSL_VERIFY", False)


def get_requests_ca_bundle() -> str:
    """
    (en) Optional corporate CA bundle path from the active implementation `.env`.

    (kr) 활성 implementation `.env` 의 REQUESTS_CA_BUNDLE(선택)을 읽는다.
    """
    load_exaone_env()
    return (os.environ.get("REQUESTS_CA_BUNDLE") or "").strip()


def build_urllib_ssl_context(*, caller_file: Path | str | None = None) -> ssl.SSLContext | None:
    """
    (en) SSL context for urllib — honors DISABLE_SSL_VERIFY and REQUESTS_CA_BUNDLE.

    (kr) urllib 용 SSL context — DISABLE_SSL_VERIFY·REQUESTS_CA_BUNDLE 를 반영한다.
    """
    load_exaone_env(caller_file=caller_file)
    if get_disable_ssl_verify():
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        return ctx
    ca_bundle = get_requests_ca_bundle()
    if ca_bundle:
        return ssl.create_default_context(cafile=ca_bundle)
    return None


def has_exaone_credentials(*, caller_file: Path | str | None = None) -> bool:
    """
    (en) True when both EXAONE_API_KEY and EXAONE_BASE_URL are set in the active impl `.env`.

    (kr) 활성 impl `.env` 에 EXAONE_API_KEY 와 EXAONE_BASE_URL 이 모두 있으면 True.
    """
    impl = load_exaone_env(caller_file=caller_file)
    api_key = (os.environ.get("EXAONE_API_KEY") or "").strip()
    base_url = (os.environ.get("EXAONE_BASE_URL") or "").strip()
    if not api_key or not base_url:
        return False
    if api_key.lower() in {"your-api-key", "changeme", "placeholder"}:
        return False
    if "your-openai-compatible-host" in base_url or base_url.endswith("://"):
        return False
    return True


def openai_compat_kwargs(*, require_credentials: bool = True) -> dict[str, Any]:
    """
    (en) Standard OpenAI-compatible kwargs for third-party SDKs (LangChain, browser-use, etc.).

    (kr) 서드파티 SDK(LangChain, browser-use 등)용 OpenAI 호환 kwargs 이다.
    """
    impl = load_exaone_env()
    base_url = (os.environ.get("EXAONE_BASE_URL") or "").strip()
    api_key = (os.environ.get("EXAONE_API_KEY") or "").strip()
    model = (os.environ.get("EXAONE_MODEL") or "").strip() or "k-exaone_v1"
    env_file = impl / ".env"
    if require_credentials:
        if not api_key:
            raise RuntimeError(f"EXAONE_API_KEY is missing; set it in {env_file}")
        if not base_url:
            raise RuntimeError(f"EXAONE_BASE_URL is missing; set it in {env_file}")
    else:
        if not base_url:
            base_url = "https://your-openai-compatible-host/v1"
        if not model or model == "your-model-id":
            model = "k-exaone_v1"
    return {"base_url": base_url, "api_key": api_key, "model": model}


__all__ = [
    "build_urllib_ssl_context",
    "ensure_repo_on_path",
    "get_disable_ssl_verify",
    "get_requests_ca_bundle",
    "has_exaone_credentials",
    "impl_dir",
    "load_exaone_env",
    "openai_compat_kwargs",
    "repo_root",
]
