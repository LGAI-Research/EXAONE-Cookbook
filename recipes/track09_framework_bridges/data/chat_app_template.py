#!/usr/bin/env python3
"""
(en) Minimal Gradio chat UI streaming EXAONE via exaone.llm.ExaoneAPIClient.

(kr) exaone.llm.ExaoneAPIClient 로 EXAONE 을 스트리밍하는 최소 Gradio 채팅 UI.
"""
from __future__ import annotations

import os
import sys
import unicodedata
from collections.abc import Generator
from pathlib import Path

_cwd = Path(__file__).resolve().parent
ROOT = next((p for p in [_cwd, *_cwd.parents] if (p / "exaone").is_dir()), None)
if ROOT is None:
    raise RuntimeError("Cannot find repo root (exaone/ directory).")
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import exaone

exaone.load_project_env()
import gradio as gr

API_KEY = os.environ.get("EXAONE_API_KEY", "").strip()
BASE_URL = os.environ.get("EXAONE_BASE_URL", "").strip() or "http://localhost:8000/v1"
MODEL = os.environ.get("EXAONE_MODEL", "").strip() or exaone.llm.ExaoneClient.DEFAULT_MODEL
DEFAULT_SYSTEM = "You are a helpful Korean/English assistant. Answer concisely in the user's language."

client = exaone.llm.ExaoneAPIClient(base_url=BASE_URL, model=MODEL, api_key=API_KEY)


def normalize_unicode(text: str) -> str:
    return unicodedata.normalize("NFC", text)


def stream_chat(
    message: str,
    history: list[dict],
    system_prompt: str,
    temperature: float,
    max_tokens: int,
) -> Generator[str, None, None]:
    messages: list[exaone.llm.ExaoneMessage] = [
        exaone.llm.ExaoneMessage(role="system", content=system_prompt or DEFAULT_SYSTEM)
    ]
    for turn in history or []:
        role = turn.get("role")
        content = turn.get("content")
        if role in ("user", "assistant") and content:
            messages.append(exaone.llm.ExaoneMessage(role=role, content=content))
    messages.append(exaone.llm.ExaoneMessage(role="user", content=message))
    chunks: list[str] = []
    stream_opts = exaone.llm.ExaoneGenerateOptions(
        max_new_tokens=int(max_tokens),
        temperature=temperature,
        enable_thinking=False,
    )
    for event in client.chat_stream(messages=messages, options=stream_opts):
        if getattr(event, "kind", None) == "text":
            delta = getattr(event, "text", "") or ""
        elif isinstance(event, dict):
            delta = event.get("text") or event.get("delta") or ""
        else:
            delta = ""
        if delta:
            chunks.append(delta)
            yield normalize_unicode("".join(chunks))


def build_demo() -> gr.Blocks:
    with gr.Blocks(title="EXAONE Chat (Track 09)") as demo:
        gr.Markdown(
            "# EXAONE Gradio Chat\n\n"
            "Track 09 export — streaming via `exaone.llm.ExaoneAPIClient.chat_stream`."
        )
        system = gr.Textbox(label="System prompt", value=DEFAULT_SYSTEM, lines=3)
        # (en) EXAONE convention is temperature=1.0 (greedy/very-low temp is discouraged); keep the floor near 1.0.
        # (kr) EXAONE 권장값은 temperature=1.0 입니다(greedy·아주 낮은 temp 비권장) — 하한을 1.0 근처로 둡니다.
        temperature = gr.Slider(0.9, 1.5, value=1.0, step=0.05, label="temperature (EXAONE 권장 1.0)")
        max_tokens = gr.Slider(256, 4096, value=1024, step=256, label="max_tokens")
        # (en) gradio 6 ChatInterface uses the messages history format by default (no `type=` arg).
        # (kr) gradio 6 의 ChatInterface 는 messages 히스토리 포맷이 기본이므로 `type=` 인자가 필요 없습니다.
        gr.ChatInterface(
            fn=stream_chat,
            additional_inputs=[system, temperature, max_tokens],
        )
    return demo


if __name__ == "__main__":
    if not API_KEY:
        raise SystemExit("Set EXAONE_API_KEY in .env before launching.")
    build_demo().launch()
