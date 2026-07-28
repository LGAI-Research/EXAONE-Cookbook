from __future__ import annotations

import json
from unittest import mock

import pytest


from exaone.llm.exaone_client import ExaoneAPIClient
from exaone.observability.log_sanitize import _REDACTED, sanitize_for_log


class TestSanitizeForLog:
    def test_masks_bearer_token(self):
        text = "Authorization: Bearer sk-secret-key-12345"
        out = sanitize_for_log(text)
        assert "sk-secret-key" not in out
        assert _REDACTED in out

    def test_masks_json_api_key(self):
        text = json.dumps({"api_key": "super-secret", "model": "m"})
        out = sanitize_for_log(text)
        assert "super-secret" not in out
        assert _REDACTED in out
        assert '"model": "m"' in out

    def test_redacts_messages_content(self):
        payload = {
            "error": "invalid request",
            "messages": [{"role": "user", "content": "my private prompt"}],
        }
        out = sanitize_for_log(json.dumps(payload))
        assert "my private prompt" not in out
        assert "_redacted" in out or _REDACTED in out

    def test_truncates_long_text(self):
        out = sanitize_for_log("x" * 2000, max_len=100)
        assert len(out) == 100
        assert out.endswith("...")

    def test_empty_string_returns_empty(self):
        assert sanitize_for_log("") == ""
        assert sanitize_for_log("   ") == ""


class TestExaoneAPIClientClientError:
    def test_log_and_raise_client_error_uses_sanitized_body(self):
        client = ExaoneAPIClient(base_url="http://localhost:8000/v1")
        resp = mock.Mock()
        resp.status_code = 422
        resp.text = json.dumps(
            {
                "error": "validation",
                "messages": [{"role": "user", "content": "secret user data"}],
                "api_key": "leaked-key",
            }
        )

        with pytest.raises(RuntimeError, match="request rejected") as exc_info:
            client._log_and_raise_client_error(resp)

        msg = str(exc_info.value)
        assert "secret user data" not in msg
        assert "leaked-key" not in msg
        assert "422" in msg
