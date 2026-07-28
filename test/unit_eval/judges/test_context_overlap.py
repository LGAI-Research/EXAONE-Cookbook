from __future__ import annotations

import json

from eval.judges.context_overlap import ContextTokenOverlapJudge, faithfulness_answer_text
from eval.metrics.types import TrialResult

_CTX = "Seoul is the capital city of Korea."


def _trial(*, content: str = "", structured: object = None) -> TrialResult:
    return TrialResult(
        trial_id="t-1",
        task_id="hb-1",
        dataset="halubench",
        runner="harness",
        final_content=content,
        final_structured=structured,
    )


class TestFaithfulnessAnswerText:
    def test_plain_text_unchanged(self):
        t = _trial(content="Seoul is the capital city of Korea.")
        assert faithfulness_answer_text(t) == "Seoul is the capital city of Korea."

    def test_structured_answer_preferred(self):
        t = _trial(
            content='{"answer": "Seoul is the capital.", "confidence": "high"}',
            structured={"answer": "Seoul is the capital.", "confidence": "high"},
        )
        assert faithfulness_answer_text(t) == "Seoul is the capital."

    def test_json_content_parsed_when_no_structured(self):
        payload = {"answer": "Seoul is the capital.", "confidence": "medium", "sources": []}
        t = _trial(content=json.dumps(payload))
        assert faithfulness_answer_text(t) == "Seoul is the capital."

    def test_nested_json_in_structured_answer(self):
        payload = {"answer": "Seoul is the capital.", "confidence": "high"}
        nested = {"answer": json.dumps(payload)}
        t = _trial(content=json.dumps(payload), structured=nested)
        assert faithfulness_answer_text(t) == "Seoul is the capital."

    def test_invalid_json_falls_back_to_raw_content(self):
        t = _trial(content="not json at all")
        assert faithfulness_answer_text(t) == "not json at all"


class TestContextTokenOverlapJudge:
    def test_plain_text_overlap(self):
        t = _trial(content="Seoul is the capital city of Korea.")
        judge = ContextTokenOverlapJudge()
        assert judge(trial=t, gold={"context": _CTX}) == 1.0

    def test_json_finalize_matches_plain_text_score(self):
        answer = "Seoul is the capital city of Korea."
        payload = {"answer": answer, "confidence": "high", "sources": []}
        plain = _trial(content=answer)
        harness = _trial(
            content=json.dumps(payload),
            structured=payload,
        )
        judge = ContextTokenOverlapJudge()
        plain_score = judge(trial=plain, gold={"context": _CTX})
        harness_score = judge(trial=harness, gold={"context": _CTX})
        assert harness_score == plain_score == 1.0

    def test_harness_double_encoded_structured_answer(self):
        inner = {"answer": "Lawrence Tynes", "confidence": "high"}
        t = _trial(
            content=json.dumps(inner),
            structured={"answer": json.dumps(inner)},
        )
        judge = ContextTokenOverlapJudge()
        ctx = "Lawrence Tynes kicked the longest field goal for the Chiefs."
        assert faithfulness_answer_text(t) == "Lawrence Tynes"
        assert judge(trial=t, gold={"context": ctx}) > 0.0

    def test_json_wrapper_without_extraction_would_score_lower(self):
        answer = "Seoul is the capital city of Korea."
        payload = {"answer": answer, "confidence": "high", "sources": []}
        raw_json = json.dumps(payload).lower()
        raw_tokens = [t for t in raw_json.split() if t]
        raw_hits = sum(1 for t in raw_tokens if t in _CTX.lower())
        raw_ratio = raw_hits / len(raw_tokens)
        judge = ContextTokenOverlapJudge()
        extracted_score = judge(
            trial=_trial(content=json.dumps(payload), structured=payload),
            gold={"context": _CTX},
        )
        assert extracted_score == 1.0
        assert raw_ratio < extracted_score
