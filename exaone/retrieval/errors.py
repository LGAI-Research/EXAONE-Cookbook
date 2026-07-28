"""
(en) Retrieval strategy configuration errors.

(kr) Retrieval strategy 설정 오류이다.
"""


class RetrievalNotConfiguredError(RuntimeError):
    """
    (en) Raised when embed/search/query callbacks were not injected.

    (kr) embed/search/query 콜백이 주입되지 않았을 때 발생한다.
    """
