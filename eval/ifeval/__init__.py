"""
(en) Google IFEval verifiable instruction checkers (vendored from lm-evaluation-harness /
Google Research). Used by ``eval.metrics.m6_ifeval`` for M6 on ``--dataset ifeval``.

(kr) Google IFEval verifiable instruction checker(lm-evaluation-harness / Google Research
에서 vendored). ``--dataset ifeval`` M6 채점에 ``eval.metrics.m6_ifeval``이 사용.
"""

from eval.ifeval.utils import (
    InputExample,
    test_instruction_following_loose,
    test_instruction_following_strict,
)

__all__ = [
    "InputExample",
    "test_instruction_following_loose",
    "test_instruction_following_strict",
]
