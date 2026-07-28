from __future__ import annotations

from eval.metrics._canonical import (
    canonical_args,
    canonical_call_key,
    normalize_arguments,
    normalize_scalar,
    values_match,
)


class TestCanonicalArgs:
    def test_sort_keys_stable(self):
        a = canonical_args({"b": 1, "a": 2})
        b = canonical_args({"a": 2, "b": 1})
        assert a == b
        assert a == '{"a": 2, "b": 1}'

    def test_ensure_ascii_false(self):
        s = canonical_args({"city": "서울"})
        assert "서울" in s

    def test_canonical_call_key_includes_name(self):
        k = canonical_call_key("search", {"q": "x"})
        assert k.startswith("search::")


class TestNormalizeScalar:
    def test_lowers_and_collapses_whitespace(self):
        assert normalize_scalar("  Seoul  City  ") == "seoul city"

    def test_strips_punctuation_only_at_edges(self):
        assert normalize_scalar(" 'Seoul.' ") == "seoul"
        assert normalize_scalar("seoul, busan") == "seoul, busan"

    def test_non_string_passthrough(self):
        assert normalize_scalar(42) == 42
        assert normalize_scalar(None) is None


class TestValuesMatch:
    def test_strings_normalized(self):
        assert values_match("Seoul", "seoul")
        assert values_match(" Seoul. ", "seoul")

    def test_dicts_recursive(self):
        assert values_match({"a": "X"}, {"a": "x"})
        assert not values_match({"a": "X"}, {"a": "y"})

    def test_scalar_lists_order_insensitive(self):
        assert values_match(["b", "a"], ["A", "B"])

    def test_nested_lists_keep_order(self):
        assert values_match([{"x": 1}, {"x": 2}], [{"x": 1}, {"x": 2}])
        assert not values_match([{"x": 1}, {"x": 2}], [{"x": 2}, {"x": 1}])


class TestNormalizeArguments:
    def test_recursive(self):
        out = normalize_arguments({"a": "X", "b": {"c": " Y "}})
        assert out == {"a": "x", "b": {"c": "y"}}
