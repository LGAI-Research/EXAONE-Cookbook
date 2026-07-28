"""
(en) Lightweight faithfulness judge for M9 — token recall of the final answer in the
grounding context. This is a deterministic proxy until a separate LLM judge is wired;
it matches the HaluBench / RAGAS spirit at low cost.

Before overlap scoring, harness JSON finalize is normalized via `faithfulness_answer_text`
so naive plain text and harness `{"answer": ...}` are judged on the same surface.

(kr) M9용 경량 faithfulness judge — 최종 답변 토큰이 grounding context에 얼마나
포함되는지(recall)로 측정. 별도 LLM judge 연결 전 deterministic proxy이며
HaluBench / RAGAS 정신을 저비용으로 따른다.

overlap 채점 전 `faithfulness_answer_text`로 harness JSON finalize를 정규화해
naive plain text와 harness `{"answer": ...}`를 동일한 표면으로 비교한다.
"""
from __future__ import annotations

import json
from typing import Any, Mapping

from eval.metrics.types import TrialResult


def _unwrap_answer_text(raw: Any) -> str:
    """
    (en) Normalize an answer payload to plain text. Unwraps nested JSON strings
    (harness ``StructuredOutputPipeline`` sometimes stores the full JSON blob
    inside ``structured["answer"]``).

    (kr) answer payload를 plain text로 정규화. nested JSON 문자열을 unwrap한다
    (harness ``StructuredOutputPipeline``이 전체 JSON blob을 ``structured["answer"]``에
    넣는 경우가 있음).
    """
    if raw is None:
        return ""
    text = str(raw).strip()
    if not text:
        return ""
    if text.startswith("{"):
        try:
            parsed = json.loads(text)
        except json.JSONDecodeError:
            return text
        if isinstance(parsed, dict):
            inner = parsed.get("answer")
            if inner is not None:
                unwrapped = _unwrap_answer_text(inner)
                if unwrapped:
                    return unwrapped
    return text


def faithfulness_answer_text(trial: TrialResult) -> str:
    """
    (en) Text to score for M9 faithfulness. Prefer structured ``answer`` (harness
    finalize); fall back to JSON parse of ``final_content``; else plain text (naive).
    Nested JSON in ``structured["answer"]`` is unwrapped via ``_unwrap_answer_text``.

    (kr) M9 faithfulness 채점용 텍스트. structured ``answer``(harness finalize) 우선,
    ``final_content`` JSON 파싱, 없으면 plain text(naive).
    ``structured["answer"]``의 nested JSON은 ``_unwrap_answer_text``로 unwrap.
    """
    structured = trial.final_structured
    if isinstance(structured, dict):
        answer = structured.get("answer")
        if answer is not None:
            unwrapped = _unwrap_answer_text(answer)
            if unwrapped:
                return unwrapped

    content = (trial.final_content or "").strip()
    if content.startswith("{"):
        try:
            parsed = json.loads(content)
        except json.JSONDecodeError:
            parsed = None
        if isinstance(parsed, dict):
            answer = parsed.get("answer")
            if answer is not None:
                unwrapped = _unwrap_answer_text(answer)
                if unwrapped:
                    return unwrapped

    return trial.final_content or ""


class ContextTokenOverlapJudge:
    """
    (en) Returns the fraction of whitespace-delimited answer tokens that appear in
    the lowercase grounding context string. Uses `faithfulness_answer_text` so JSON
    wrappers do not dilute the score.

    (kr) 공백으로 나눈 답변 토큰 중 소문자 grounding context에 등장하는 비율을 반환.
    JSON wrapper가 점수를 희석하지 않도록 `faithfulness_answer_text`를 사용한다.
    """

    def __call__(self, *, trial: TrialResult, gold: Mapping[str, Any]) -> float:
        ctx = str(gold.get("context", "")).lower()
        ans = faithfulness_answer_text(trial).lower()
        toks = [t for t in ans.split() if t]
        if not toks:
            return 0.0
        hit = sum(1 for t in toks if t in ctx)
        return hit / len(toks)


__all__ = ["ContextTokenOverlapJudge", "faithfulness_answer_text"]
