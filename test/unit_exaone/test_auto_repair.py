from __future__ import annotations

from exaone.output.auto_repair import AutoRepair


class TestAutoRepair:
    def test_truncated_array_brackets(self):
        out = AutoRepair().process('{"answer":"ok","items":[1,2')
        assert out.success is True
        assert out.data == {"answer": "ok", "items": [1, 2]}
        assert out.raw is not None
        assert out.raw.endswith("]}")

    def test_unclosed_string_value(self):
        out = AutoRepair().process('{"answer":"ok')
        assert out.success is True
        assert out.data == {"answer": "ok"}
        assert out.raw is not None
        assert '"ok"' in out.raw

    def test_truncate_incomplete_trailing_field(self):
        out = AutoRepair().process('{"answer":"ok","confidence":0.')
        assert out.success is True
        assert out.data == {"answer": "ok"}

    def test_supports_retry_is_false(self):
        assert AutoRepair.supports_retry is False
