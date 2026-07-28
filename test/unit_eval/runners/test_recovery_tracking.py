from __future__ import annotations

from eval.runners.recovery_tracking import naive_response_needs_recovery


def test_naive_response_needs_recovery_reasoning_only():
    resp = {
        "choices": [
            {
                "message": {"content": "", "reasoning_content": "thinking"},
                "finish_reason": "stop",
            }
        ]
    }
    assert naive_response_needs_recovery(resp) is True


def test_naive_response_ok_with_content():
    resp = {
        "choices": [
            {
                "message": {"content": "hello"},
                "finish_reason": "stop",
            }
        ]
    }
    assert naive_response_needs_recovery(resp) is False
